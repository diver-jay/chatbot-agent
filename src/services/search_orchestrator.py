from typing import Tuple, Optional, Dict, Any

from src.utils.decorators import retry_on_error, log_search_execution
from src.agents.term_detect_agent import TermDetectAgent
from src.agents.topic_detect_agent import TopicDetectAgent
from src.services.search_service import SearchService
from src.agents.sns_relevance_check_agent import SNSRelevanceCheckAgent
from src.utils.date_utils import get_formatted_current_date


class SearchOrchestrator:
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

        self.term_detect_agent = TermDetectAgent(chat_model)
        self.topic_detect_agent = TopicDetectAgent(chat_model, session_manager)
        self.relevance_check_agent = SNSRelevanceCheckAgent(chat_model)

        serpapi_key = session_manager.get_serpapi_key()
        youtube_key = session_manager.get_youtube_api_key()
        self.search_service = (
            SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
            if serpapi_key
            else None
        )

        self._is_term_search = False
        self._is_daily_life = False
        self._is_media_requested = False
        self._needs_search = False
        self._search_term = None

    def analyze_question(self, question: str, influencer_name: str):
        print(f"\n{'='*60}")
        print(f"[Analyze Question] 사용자 질문: {question}")
        print(f"[Analyze Question] 인플루언서 이름: {influencer_name}")
        print(f"{ '='*60}\n")

        term_detection_result = self.term_detect_agent.act(user_message=question)

        if term_detection_result.needs_search:
            self._handle_term_search(term_detection_result, question)
        else:
            self._handle_topic_search(question, influencer_name)

        print(
            f"[Analyze Question] 최종 상태 - needs_search: {self._needs_search}, search_term: '{self._search_term}', is_term_search: {self._is_term_search}, is_daily_life: {self._is_daily_life}, is_media_requested: {self._is_media_requested}"
        )

    @log_search_execution
    def execute_search(self, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        search_term = self._search_term

        print(f"\n{'='*60}")
        print(f"[Execute Search] 검색 시작")
        print(f"[Execute Search] search_term: {search_term}")
        print(f"[Execute Search] is_term_search: {self._is_term_search}")
        print(f"[Execute Search] is_daily_life: {self._is_daily_life}")
        print(f"[Execute Search] needs_search: {self._needs_search}")
        print(f"[Execute Search] is_media_requested: {self._is_media_requested}")
        print(f"{ '='*60}\n")

        try:
            # 1. 신조어/용어 검색
            if self._is_term_search:
                print("→ 신조어/용어 검색 경로")
                return self._search_general_context(
                    search_term, add_term_instruction=True
                )

            # 2. 일상 질문 (SNS 시도)
            elif self._is_daily_life:
                print("→ 일상 질문 (SNS) 경로")
                return self._search_sns_content_with_fallback(search_term, question)

            # 3. 일반 인물/사건 검색
            else:
                print("→ 일반 인물/사건 검색 경로")
                return self._search_general_context(
                    search_term, add_term_instruction=False
                )

        except Exception as e:
            import traceback

            print(f"[Search] 검색 중 오류: {e}")
            print(f"[Search] Traceback:\n{traceback.format_exc()}")
            return "", None

    @property
    def needs_search(self) -> bool:
        return self._needs_search

    @property
    def is_media_requested(self) -> bool:
        return self._is_media_requested

    def _handle_term_search(self, term_detection_result, question: str):
        print("✅ 신조어 검색 모드 활성화")
        self._is_term_search = True
        self._is_daily_life = False
        self._needs_search = True

        self._search_term = (
            f"{term_detection_result.search_term} 뜻"
            if term_detection_result.search_term
            else ""
        )
        print(f"[Analyze Question] 생성된 검색어: '{self._search_term}'")

        self._is_media_requested = self.topic_detect_agent.is_media_requested(question)
        print(f"[Analyze Question] 콘텐츠 요청 여부 확인: {self._is_media_requested}")

    def _handle_topic_search(self, question: str, influencer_name: str):
        """Handles the analysis logic for general topics (person/event)."""
        self._is_term_search = False
        print("➡️ TopicDetectAgent로 넘어감")

        detection_result = self.topic_detect_agent.act(
            user_message=question, influencer_name=influencer_name
        )
        self._needs_search = detection_result.needs_search
        self._search_term = detection_result.search_term
        self._is_daily_life = detection_result.is_daily_life

        self._is_media_requested = self.topic_detect_agent.is_media_requested(question)

        print(
            f"[TopicDetectAgent] 검색 필요: {self._needs_search} | 검색어: {self._search_term} | 일상: {self._is_daily_life}"
        )
        print(f"[Media Request Check] 미디어 요청: {self._is_media_requested}")

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_general_context(
        self, search_term: str, add_term_instruction: bool = False
    ) -> Tuple[str, None]:
        """일반 웹 검색을 수행합니다."""
        if not self.search_service:
            print("[Search] SearchService가 초기화되지 않음 (API 키 없음)")
            return "", None

        current_date = get_formatted_current_date()
        print(f"[Current Date] {current_date}")
        print(f"[SNS Search] ❌ 일상 질문 아님 → SNS 검색 건너뜀")

        search_results = self.search_service.search(search_term)
        search_summary = self.search_service.extract_summary(search_results)

        # 기본 검색 컨텍스트
        search_context = f"\n\n[검색 정보: '{search_term}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"

        # 신조어 검색인 경우 특별 지시 추가
        if add_term_instruction:
            search_context += f"\n[지시사항] 위 검색 정보를 바탕으로 자연스럽게 답변하세요. 검색어('{search_term}')를 그대로 반복하지 말고, 그 의미를 이해한 상태로 대화하세요.\n"

        print(f"[Search] 검색 완료:\n{search_context}")
        return search_context, None

    @retry_on_error(max_attempts=2, delay=2.0)
    def _search_sns_content_with_fallback(
        self, search_term: str, question: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """SNS 콘텐츠를 검색하고, 실패 시 일반 검색으로 fallback합니다."""
        if not self.search_service:
            print("[Search] SearchService가 초기화되지 않음 (API 키 없음)")
            return "", None

        current_date = get_formatted_current_date()
        print(f"[Current Date] {current_date}")
        print(f"[SNS Search] ✅ 일상 질문 감지 → SNS 검색 시작")

        # SNS 콘텐츠 검색
        sns_content = self.search_service.search_sns_content(
            query=search_term,
            user_question=question,
            relevance_checker=self.relevance_check_agent,
        )
        print(f"[SNS Search] 검색어: {search_term}")
        print(f"[SNS Search] 검색 결과: {sns_content}")

        # SNS 콘텐츠를 찾았으면
        if sns_content and sns_content.get("found"):
            print(f"[Search] ✅ 관련 SNS 콘텐츠 발견 → SNS 정보 사용")
            platform_name = (
                "Instagram" if sns_content.get("platform") == "instagram" else "YouTube"
            )
            sns_title = sns_content.get("title", "")
            search_context = f"\n\n[{platform_name} 게시물 정보]\n{sns_title}\n\n[참고] 오늘 날짜: {current_date}\n"
            print(f"[Search] SNS 컨텍스트:\n{search_context}")
            return search_context, sns_content
        else:
            # SNS를 못 찾았으면 일반 검색 수행
            print(f"[Search] SNS 콘텐츠 없음 → 일반 검색으로 Fallback")
            return self._search_general_context(search_term)
