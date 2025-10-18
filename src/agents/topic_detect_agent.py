from typing import Tuple, Optional
from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from typing_extensions import override
from src.utils.parser import parse_json_from_response


class TopicDetectAgent(ChatAgent):
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager

    @override
    def load_prompt(self, prompt_path="prompts/entity_detection_prompt.md"):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_content_request_prompt(
        self, prompt_path="prompts/content_request_detection_prompt.md"
    ):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _check_content_request(self, user_message: str) -> bool:
        try:
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

            prompt_template = self._load_content_request_prompt()
            prompt = prompt_template.format(
                history_context=history_context if history_context else "없음",
                user_message=user_message,
            )

            response = self.chat_model.invoke([HumanMessage(content=prompt)])
            result = parse_json_from_response(response.content)
            requests_content = result.get("requests_content", False)
            reason = result.get("reason", "")

            print(
                f"[Content Request Check] 콘텐츠 요청: {requests_content} | 이유: {reason}"
            )

            return requests_content

        except Exception as e:
            print(f"[Content Request Check] 오류: {e}")
            return False

    @override
    def act(self, **kwargs) -> Tuple[bool, Optional[str], bool, bool]:
        user_message = kwargs.get("user_message")
        influencer_name = kwargs.get("influencer_name")

        if not user_message:
            return False, None, False, False

        try:
            prompt_template = self.load_prompt()
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

            if history_context:
                detection_prompt = prompt_template.format(
                    user_message=f"[이전 대화]\n{history_context}\n\n[현재 질문]\n{user_message}"
                )
            else:
                detection_prompt = prompt_template.format(user_message=user_message)

            response = self.chat_model.invoke([HumanMessage(content=detection_prompt)])
            result = parse_json_from_response(response.content)

            needs_search = result.get("needs_search", False)
            search_term = result.get("search_term", None)
            is_daily_life = result.get("is_daily_life", False)

            requests_content = self._check_content_request(user_message)

            if needs_search and search_term and influencer_name:
                if "인물명" in search_term:
                    search_term = search_term.replace("인물명", influencer_name)
                elif influencer_name.lower() not in search_term.lower():
                    search_term = f"{influencer_name} {search_term}"

            print(
                f"[TopicDetectAgent] 🔍 검색 필요: {needs_search} | 검색어: {search_term} | 일상: {is_daily_life} | 콘텐츠 요청: {requests_content} | 판단 근거: {result.get('reason', 'N/A')}"
            )

            return needs_search, search_term, is_daily_life, requests_content

        except Exception as e:
            print(f"[TopicDetectAgent] Error: {e}")
            return False, None, False, False
