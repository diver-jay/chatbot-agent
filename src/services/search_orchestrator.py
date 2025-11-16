from typing import Tuple, Optional, Dict, Any

from src.utils.decorators import log_search_execution
from src.agents.question_analyzer import QuestionAnalyzer
from src.agents.sns_relevance_check_agent import SNSRelevanceCheckAgent
from src.models.analysis_result import AnalysisResult
from src.utils.logger import log
from src.services.search_service import SearchService
from src.services.no_search_service import NoSearchService
from src.services.term_search_service import TermSearchService
from src.services.sns_search_service import SnsSearchService
from src.services.general_search_service import GeneralSearchService


class SearchOrchestrator:
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

        self.question_analyzer = QuestionAnalyzer(chat_model, session_manager)
        self.relevance_check_agent = SNSRelevanceCheckAgent(chat_model)

        self._strategies: Dict[str, SearchService] = {
            "NO_SEARCH": NoSearchService(),
            "TERM_SEARCH": TermSearchService(),
            "SNS_SEARCH": SnsSearchService(
                relevance_checker=self.relevance_check_agent
            ),
            "GENERAL_SEARCH": GeneralSearchService(),
        }

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
            # 선제적 공유인지 확인 (명시적 요청이 아닌 경우)
            is_proactive_sns_search = (
                query_type == "SNS_SEARCH"
                and not self._analysis_result.is_media_requested
            )

            # 최근 10개의 대화에서 공유 여부 확인
            did_share_in_last_n_turns = False
            chat_history = self.session_manager.get_chat_history()
            for message in chat_history[-10:]:
                if message.get("role") == "assistant" and "sns_content" in message:
                    did_share_in_last_n_turns = True
                    break

            # 선제적 공유인데 이미 최근에 공유했다면 검색하지 않음
            if is_proactive_sns_search and did_share_in_last_n_turns:
                log(
                    self.__class__.__name__,
                    "⏭️ 최근 12턴 내에 이미 공유했으므로 중복 공유 방지",
                )
                return "", None

            strategy = self._strategies.get(query_type, self._strategies["NO_SEARCH"])
            search_context, sns_content = strategy.search(query, question)

            was_successful = sns_content and sns_content.get("found")

            # 선제적 공유가 성공했다면 세션 상태를 업데이트합니다.
            if is_proactive_sns_search and was_successful:
                log(
                    self.__class__.__name__,
                    "선제적 공유 성공! 세션 상태를 업데이트합니다.",
                )
                self.session_manager.increment_proactive_share_count()

                topic = self._analysis_result.query
                if topic:
                    self.session_manager.add_shared_topic(topic)

            return search_context, sns_content

        except Exception as e:
            import traceback

            log(self.__class__.__name__, f"검색 중 오류: {e}")
            log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
            return "", None

    @property
    def needs_search(self) -> bool:
        return self._analysis_result.query_type != "NO_SEARCH"

    @property
    def is_media_requested(self) -> bool:
        return self._analysis_result.is_media_requested
