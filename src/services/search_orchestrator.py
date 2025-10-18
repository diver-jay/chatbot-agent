from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from src.utils.decorators import retry_on_error, log_search_execution
from src.agents.term_detect_agent import TermDetectAgent
from src.agents.topic_detect_agent import TopicDetectAgent
from src.services.search_service import SearchService
from src.agents.sns_relevance_check_agent import SNSRelevanceCheckAgent
from src.utils.date_utils import get_formatted_date
from src.services.search_type import SearchType
from src.models.analysis_result import AnalysisResult
from src.utils.logger import log


class SearchOrchestrator:
    """질문 분석 및 검색 실행을 오케스트레이션하는 클래스"""

    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

        self.term_detect_agent = TermDetectAgent(chat_model)
        self.topic_detect_agent = TopicDetectAgent(chat_model, session_manager)
        self.relevance_check_agent = SNSRelevanceCheckAgent(chat_model)

        # SearchService 초기화
        serpapi_key = session_manager.get_serpapi_key()
        youtube_key = session_manager.get_youtube_api_key()
        self.search_service = (
            SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
            if serpapi_key
            else None
        )

        # 분석 상태를 AnalysisResult 객체로 캡슐화
        self._analysis_result = AnalysisResult()

    def analyze_question(self, question: str, influencer_name: str):
        """분석 유형을 결정하고 해당 분석 메서드를 호출합니다."""
        log(self.__class__.__name__, f"\n{'='*60}")
        log(self.__class__.__name__, f"사용자 질문: {question}")
        log(self.__class__.__name__, f"인플루언서 이름: {influencer_name}")
        log(self.__class__.__name__, f"{ '='*60}\n")

        # 항상 새로운 분석을 위해 상태 초기화
        self._analysis_result = AnalysisResult()

        term_detection_result = self.term_detect_agent.act(user_message=question)

        if term_detection_result.needs_search:
            self._handle_term_search(term_detection_result, question)
        else:
            self._handle_topic_search(question, influencer_name)

        log(self.__class__.__name__, f"최종 분석 상태: {self._analysis_result}")

    @log_search_execution
    def execute_search(self, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        분석 결과에 따라 적절한 검색을 실행하고 컨텍스트를 반환합니다.

        Note: 호출 전에 needs_search 프로퍼티로 검색 필요 여부를 확인해야 합니다.
        """
        search_term = self._analysis_result.search_term
        search_type = self._analysis_result.search_type

        log(self.__class__.__name__, f"\n{'='*60}")
        log(self.__class__.__name__, f"검색 시작")
        log(self.__class__.__name__, f"analysis_result: {self._analysis_result}")
        log(self.__class__.__name__, f"{ '='*60}\n")

        try:
            if search_type == SearchType.TERM_SEARCH:
                log(self.__class__.__name__, "→ 신조어/용어 검색 경로")
                return self._search_general_context(
                    search_term, add_term_instruction=True
                )

            elif search_type == SearchType.SNS_SEARCH:
                log(self.__class__.__name__, "→ 일상 질문 (SNS) 경로")
                return self._search_sns_content_with_fallback(search_term, question)

            elif search_type == SearchType.GENERAL_TOPIC_SEARCH:
                log(self.__class__.__name__, "→ 일반 인물/사건 검색 경로")
                return self._search_general_context(
                    search_term, add_term_instruction=False
                )

        except Exception as e:
            import traceback

            log(self.__class__.__name__, f"검색 중 오류: {e}")
            log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
            return "", None
        
        return "", None

    @property
    def needs_search(self) -> bool:
        """검색 필요 여부를 반환합니다."""
        return self._analysis_result.search_type != SearchType.NO_SEARCH

    @property
    def is_media_requested(self) -> bool:
        """콘텐츠 요청 여부를 반환합니다."""
        return self._analysis_result.is_media_requested

    def _handle_term_search(self, term_detection_result, question: str):
        """Handles the analysis logic when a term/slang is detected."""
        log(self.__class__.__name__, "✅ 신조어 검색 모드 활성화")
        self._analysis_result.search_type = SearchType.TERM_SEARCH
        self._analysis_result.search_term = (
            f"{term_detection_result.search_term} 뜻"
            if term_detection_result.search_term
            else ""
        )
        log(self.__class__.__name__, f"생성된 검색어: '{self._analysis_result.search_term}'")

        self._analysis_result.is_media_requested = self.topic_detect_agent.is_media_requested(question)
        log(self.__class__.__name__, f"미디어 요청 여부 확인: {self._analysis_result.is_media_requested}")

    def _handle_topic_search(self, question: str, influencer_name: str):
        """Handles the analysis logic for general topics (person/event)."""
        log(self.__class__.__name__, "➡️ TopicDetectAgent로 넘어감")

        detection_result = self.topic_detect_agent.act(
            user_message=question, influencer_name=influencer_name
        )
        
        if detection_result.needs_search:
            self._analysis_result.search_term = detection_result.search_term
            if detection_result.is_daily_life:
                self._analysis_result.search_type = SearchType.SNS_SEARCH
            else:
                self._analysis_result.search_type = SearchType.GENERAL_TOPIC_SEARCH
        else:
            self._analysis_result.search_type = SearchType.NO_SEARCH
            self._analysis_result.search_term = None

        self._analysis_result.is_media_requested = self.topic_detect_agent.is_media_requested(question)

        log(
            self.__class__.__name__,
            f"TopicDetectAgent 결과 - search_type: {self._analysis_result.search_type.name}, 검색어: {self._analysis_result.search_term}"
        )
        log(self.__class__.__name__, f"TopicDetectAgent 결과 - 미디어 요청: {self._analysis_result.is_media_requested}")

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_general_context(
        self, search_term: str, add_term_instruction: bool = False
    ) -> Tuple[str, None]:
        """일반 웹 검색을 수행합니다."""
        if not self.search_service:
            log(self.__class__.__name__, "SearchService가 초기화되지 않음 (API 키 없음)")
            return "", None

        current_date = get_formatted_date(datetime.now())
        log(self.__class__.__name__, f"Current Date: {current_date}")
        log(self.__class__.__name__, f"SNS 검색 건너뜀 (일상 질문 아님)")

        search_results = self.search_service.search_web(search_term)
        search_summary = self.search_service.extract_summary(search_results)

        # 기본 검색 컨텍스트
        search_context = f"\n\n[검색 정보: '{search_term}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"

        # 신조어 검색인 경우 특별 지시 추가
        if add_term_instruction:
            search_context += f"\n[지시사항] 위 검색 정보를 바탕으로 자연스럽게 답변하세요. 검색어('{search_term}')를 그대로 반복하지 말고, 그 의미를 이해한 상태로 대화하세요.\n"

        log(self.__class__.__name__, f"검색 완료")
        return search_context, None

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_sns_content_with_fallback(
        self, search_term: str, question: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """SNS 콘텐츠를 검색하고, 실패 시 일반 검색으로 fallback합니다."""
        if not self.search_service:
            log(self.__class__.__name__, "SearchService가 초기화되지 않음 (API 키 없음)")
            return "", None

        current_date = get_formatted_date(datetime.now())
        log(self.__class__.__name__, f"Current Date: {current_date}")
        log(self.__class__.__name__, f"✅ 일상 질문 감지 → SNS 검색 시작")

        # SNS 콘텐츠 검색
        sns_content = self.search_service.search_sns_content(
            query=search_term,
            user_question=question,
            relevance_checker=self.relevance_check_agent,
        )
        log(self.__class__.__name__, f"SNS 검색어: {search_term}")
        log(self.__class__.__name__, f"SNS 검색 결과: {sns_content}")

        # SNS 콘텐츠를 찾았으면
        if sns_content and sns_content.get("found"):
            log(self.__class__.__name__, f"✅ 관련 SNS 콘텐츠 발견 → SNS 정보 사용")
            platform_name = (
                "Instagram" if sns_content.get("platform") == "instagram" else "YouTube"
            )
            sns_title = sns_content.get("title", "")
            search_context = f"\n\n[{platform_name} 게시물 정보]\n{sns_title}\n\n[참고] 오늘 날짜: {current_date}\n"
            return search_context, sns_content
        else:
            # SNS를 못 찾았으면 일반 검색 수행
            log(self.__class__.__name__, f"SNS 콘텐츠 없음 → 일반 검색으로 Fallback")
            return self._search_general_context(search_term)