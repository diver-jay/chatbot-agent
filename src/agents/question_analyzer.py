from dataclasses import dataclass
from typing import Optional
from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from src.utils.parser import parse_json_from_response
from typing_extensions import override
from src.utils.logger import log


@dataclass
class QuestionAnalysisResult:
    """통합 질문 분석 결과"""
    analysis_type: str  # "TERM_SEARCH" | "SNS_SEARCH" | "GENERAL_SEARCH" | "NO_SEARCH"
    search_term: Optional[str]
    detected_term: Optional[str]
    is_daily_life: bool
    is_media_requested: bool
    reason: str


class QuestionAnalyzer(ChatAgent):
    """사용자 질문을 분석하여 검색 전략을 결정하는 통합 에이전트"""

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
    def act(self, **kwargs) -> QuestionAnalysisResult:
        """
        사용자 질문을 분석하여 검색 전략을 결정합니다.

        Args:
            user_message: 사용자 메시지
            influencer_name: 인플루언서 이름

        Returns:
            QuestionAnalysisResult: 분석 결과
        """
        user_message = kwargs.get("user_message")
        influencer_name = kwargs.get("influencer_name", "")

        if not user_message:
            return QuestionAnalysisResult(
                analysis_type="NO_SEARCH",
                search_term=None,
                detected_term=None,
                is_daily_life=False,
                is_media_requested=False,
                reason="빈 메시지"
            )

        try:
            # 대화 히스토리 로드
            chat_history = self.session_manager.get_chat_history()
            history_context = ""
            if chat_history:
                recent_history = (
                    chat_history[-4:] if len(chat_history) > 4 else chat_history
                )
                history_lines = []
                for msg in recent_history:
                    role = "사용자" if msg.get("role") == "human" else "AI"
                    content = msg.get("content", "")
                    history_lines.append(f"{role}: {content}")
                history_context = "\n".join(history_lines)

            # 프롬프트 생성
            prompt_template = self.load_prompt()
            prompt = prompt_template.format(
                history_context=history_context if history_context else "없음",
                user_message=user_message,
                influencer_name=influencer_name if influencer_name else "없음"
            )

            # LLM 호출
            response = self.chat_model.invoke([HumanMessage(content=prompt)])
            result = parse_json_from_response(response.content)

            # 결과 파싱 (기본값 설정으로 안전하게 처리)
            analysis_type = result.get("analysis_type", "NO_SEARCH")
            search_term = result.get("search_term", None)
            detected_term = result.get("detected_term", None)
            is_daily_life = result.get("is_daily_life", False)
            is_media_requested = result.get("is_media_requested", False)
            reason = result.get("reason", "")

            log(
                self.__class__.__name__,
                f"📊 분석 완료 | 타입: {analysis_type} | 검색어: {search_term or 'None'} | "
                f"신조어: {detected_term or 'None'} | 일상: {is_daily_life} | "
                f"미디어 요청: {is_media_requested} | 이유: {reason}"
            )

            return QuestionAnalysisResult(
                analysis_type=analysis_type,
                search_term=search_term,
                detected_term=detected_term,
                is_daily_life=is_daily_life,
                is_media_requested=is_media_requested,
                reason=reason
            )

        except Exception as e:
            import traceback
            log(self.__class__.__name__, f"분석 중 오류: {e}")
            log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
            return QuestionAnalysisResult(
                analysis_type="NO_SEARCH",
                search_term=None,
                detected_term=None,
                is_daily_life=False,
                is_media_requested=False,
                reason=f"오류 발생: {str(e)}"
            )
