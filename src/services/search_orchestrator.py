from datetime import datetime
from typing import Tuple, Optional, Dict, Any

from src.utils.decorators import retry_on_error, log_search_execution
from src.agents.question_analyzer import QuestionAnalyzer
from src.services.search_service import SearchService
from src.agents.sns_relevance_check_agent import SNSRelevanceCheckAgent
from src.utils.date_utils import get_formatted_date
from src.models.analysis_result import AnalysisResult
from src.utils.logger import log


class SearchOrchestrator:
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

        self.question_analyzer = QuestionAnalyzer(chat_model, session_manager)
        self.relevance_check_agent = SNSRelevanceCheckAgent(chat_model)

        serpapi_key = session_manager.get_serpapi_key()
        youtube_key = session_manager.get_youtube_api_key()
        self.search_service = (
            SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
            if serpapi_key
            else None
        )

        self._analysis_result = AnalysisResult(
            query_type="NO_SEARCH",
            query=None,
            is_daily_life=False,
            is_media_requested=False,
            reason="초기화",
        )

    def analyze_question(self, question: str, influencer_name: str):
        log(self.__class__.__name__, f"\n{'='*60}")
        log(self.__class__.__name__, f"사용자 질문: {question}")
        log(self.__class__.__name__, f"인플루언서 이름: {influencer_name}")
        log(self.__class__.__name__, f"{ '='*60}\n")

        self._analysis_result = self.question_analyzer.act(
            user_message=question, influencer_name=influencer_name
        )

        log(self.__class__.__name__, f"최종 분석 상태: {self._analysis_result}")

    @log_search_execution
    def execute_search(self, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        query = self._analysis_result.query
        query_type = self._analysis_result.query_type

        log(self.__class__.__name__, f"\n{'='*60}")
        log(self.__class__.__name__, f"검색 시작")
        log(self.__class__.__name__, f"analysis_result: {self._analysis_result}")
        log(self.__class__.__name__, f"{ '='*60}\n")

        try:
            match query_type:
                case "TERM_SEARCH":
                    log(self.__class__.__name__, "→ 신조어/용어 검색 경로")
                    return self._search_general_context(
                        query, add_term_instruction=True
                    )
                case "SNS_SEARCH":
                    log(self.__class__.__name__, "→ 일상 질문 (SNS) 경로")
                    return self._search_sns_content_with_fallback(query, question)
                case "GENERAL_SEARCH":
                    log(self.__class__.__name__, "→ 일반 인물/사건 검색 경로")
                    return self._search_general_context(
                        query, add_term_instruction=False
                    )

        except Exception as e:
            import traceback

            log(self.__class__.__name__, f"검색 중 오류: {e}")
            log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
            return "", None

        return "", None

    @property
    def needs_search(self) -> bool:
        return self._analysis_result.query_type != "NO_SEARCH"

    @property
    def is_media_requested(self) -> bool:
        return self._analysis_result.is_media_requested

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_general_context(
        self, query: str, add_term_instruction: bool = False
    ) -> Tuple[str, None]:
        if not self.search_service:
            log(
                self.__class__.__name__, "SearchService가 초기화되지 않음 (API 키 없음)"
            )
            return "", None

        current_date = get_formatted_date(datetime.now())
        log(self.__class__.__name__, f"Current Date: {current_date}")
        log(self.__class__.__name__, f"SNS 검색 건너뜀 (일상 질문 아님)")

        search_results = self.search_service.search_web(query)
        search_summary = self.search_service.extract_summary(search_results)

        # 기본 검색 컨텍스트
        search_context = f"\n\n[검색 정보: '{query}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"

        # 신조어 검색인 경우 특별 지시 추가
        if add_term_instruction:
            search_context += f"\n[지시사항] 위 검색 정보를 바탕으로 자연스럽게 답변하세요. 검색어('{query}')를 그대로 반복하지 말고, 그 의미를 이해한 상태로 대화하세요.\n"

        log(self.__class__.__name__, f"검색 완료")
        return search_context, None

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_sns_content_with_fallback(
        self, query: str, question: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """SNS 콘텐츠를 검색하고, 실패 시 일반 검색으로 fallback합니다."""
        if not self.search_service:
            log(
                self.__class__.__name__, "SearchService가 초기화되지 않음 (API 키 없음)"
            )
            return "", None

        current_date = get_formatted_date(datetime.now())
        log(self.__class__.__name__, f"Current Date: {current_date}")
        log(self.__class__.__name__, f"✅ 일상 질문 감지 → SNS 검색 시작")

        # SNS 콘텐츠 검색
        sns_content = self.search_service.search_sns_content(
            query=query,
            user_question=question,
            relevance_checker=self.relevance_check_agent,
        )
        log(self.__class__.__name__, f"SNS 검색어: {query}")
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
            return self._search_general_context(query)
