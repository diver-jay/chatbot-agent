from dataclasses import dataclass
from typing import Optional
from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from src.utils.parser import parse_json_from_response
from typing_extensions import override

@dataclass
class TermDetectionResult:
    needs_search: bool
    search_term: Optional[str]

class TermDetectAgent(ChatAgent):
    def __init__(self, chat_model, file_path="prompts/term_detection_prompt.md"):
        self.chat_model = chat_model
        self.file_path = file_path

    @override
    def load_prompt(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")

    @override
    def act(self, **kwargs) -> TermDetectionResult:
        user_message = kwargs.get("user_message")
        if not user_message:
            return TermDetectionResult(needs_search=False, search_term=None)

        try:
            prompt = self.load_prompt().format(user_message=user_message)
            response = self.chat_model.invoke([HumanMessage(content=prompt)])

            response_text = response.content
            result = parse_json_from_response(response_text)

            needs_search = result.get("needs_search", False)
            # If search is not needed, search_term should be None
            search_term = result.get("search_term") if needs_search else None

            print(
                f"[TermDetectAgent] needs_search={needs_search}, term={search_term}, reason={result.get('reason', '')}"
            )

            return TermDetectionResult(needs_search=needs_search, search_term=search_term)

        except Exception as e:
            print(f"[TermDetectAgent] Error: {e}")
            return TermDetectionResult(needs_search=False, search_term=None)
