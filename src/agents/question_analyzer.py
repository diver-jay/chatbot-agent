from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from src.models.analysis_result import AnalysisResult
from src.utils.parser import parse_json_from_response
from typing_extensions import override
from src.utils.logger import log


class QuestionAnalyzer(ChatAgent):
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager
        self.file_path = "prompts/question_analysis_prompt.md"

    @override
    def load_prompt(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")

    @override
    def act(self, **kwargs) -> AnalysisResult:
        user_message = kwargs.get("user_message")
        influencer_name = kwargs.get("influencer_name", "")

        if not user_message:
            return AnalysisResult(
                query_type="NO_SEARCH",
                query=None,
                is_daily_life=False,
                is_media_requested=False,
                reason="빈 메시지",
            )

        try:
            chat_history = self.session_manager.get_chat_history()
            log(
                self.__class__.__name__,
                f"[DEBUG] History for cooldown check: {chat_history}",
            )

            history_context = self._get_recent_chat_history()

            # 선제적 공유 상태를 세션에서 가져옵니다.
            proactive_share_count = self.session_manager.get_proactive_share_count()
            shared_topics_list = self.session_manager.get_shared_topics_list()

            prompt_template = self.load_prompt()
            prompt = prompt_template.format(
                history_context=history_context,
                user_message=user_message,
                influencer_name=influencer_name if influencer_name else "없음",
                proactive_share_count=proactive_share_count,
                shared_topics_list=str(shared_topics_list),
            )

            response = self.chat_model.invoke([HumanMessage(content=prompt)])
            log(
                self.__class__.__name__,
                f"🔍 [DEBUG] LLM 원본 응답:\n{response.content}",
            )
            return self._parse_analysis_response(response.content)

        except Exception as e:
            import traceback

            log(self.__class__.__name__, f"분석 중 오류: {e}")
            log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
            return AnalysisResult(
                query_type="NO_SEARCH",
                query=None,
                is_daily_life=False,
                is_media_requested=False,
                reason=f"오류 발생: {str(e)}",
            )

    def _get_recent_chat_history(self, max_messages: int = 4) -> str:
        chat_history = self.session_manager.get_chat_history()

        if not chat_history:
            return "없음"

        recent_history = (
            chat_history[-max_messages:]
            if len(chat_history) > max_messages
            else chat_history
        )

        history_lines = []
        for msg in recent_history:
            role = "사용자" if msg.get("role") == "human" else "AI"
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")

        return "\n".join(history_lines)

    def _parse_analysis_response(self, response_content: str) -> AnalysisResult:
        result = parse_json_from_response(response_content)

        query_type = result.get("query_type", "NO_SEARCH")
        query = result.get("search_term", None)  # LLM은 여전히 "search_term"으로 반환
        detected_term = result.get("detected_term", None)  # 로깅 전용
        is_daily_life = result.get("is_daily_life", False)
        is_media_requested = result.get("is_media_requested", False)
        reason = result.get("reason", "")

        log(
            self.__class__.__name__,
            f"📊 분석 완료 | 타입: {query_type} | 검색어: {query or 'None'} | "
            f"신조어: {detected_term or 'None'} | 일상: {is_daily_life} | "
            f"미디어 요청: {is_media_requested} | 이유: {reason}",
        )

        return AnalysisResult(
            query_type=query_type,
            query=query,
            is_daily_life=is_daily_life,
            is_media_requested=is_media_requested,
            reason=reason,
        )
