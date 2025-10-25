from typing import Tuple, Optional, Dict, Any

from src.utils.decorators import log_search_execution
from src.agents.question_analyzer import QuestionAnalyzer
from src.agents.sns_relevance_check_agent import SNSRelevanceCheckAgent
from src.models.analysis_result import AnalysisResult
from src.utils.logger import log
from src.services.search_strategies import (
    SearchStrategy,
    NoSearchStrategy,
    TermSearchStrategy,
    SnsSearchStrategy,
    GeneralSearchStrategy,
)


class SearchOrchestrator:
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

        self.question_analyzer = QuestionAnalyzer(chat_model, session_manager)
        self.relevance_check_agent = SNSRelevanceCheckAgent(chat_model)

        serpapi_key = session_manager.get_serpapi_key()
        youtube_key = session_manager.get_youtube_api_key()

        strategy_args = {
            "serpapi_key": serpapi_key,
            "youtube_api_key": youtube_key,
            "relevance_checker": self.relevance_check_agent,
        }

        self._strategies: Dict[str, SearchStrategy] = {
            "NO_SEARCH": NoSearchStrategy(**strategy_args),
            "TERM_SEARCH": TermSearchStrategy(**strategy_args),
            "SNS_SEARCH": SnsSearchStrategy(**strategy_args),
            "GENERAL_SEARCH": GeneralSearchStrategy(**strategy_args),
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
            strategy = self._strategies.get(query_type, self._strategies["NO_SEARCH"])
            return strategy.search(query, question)

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

