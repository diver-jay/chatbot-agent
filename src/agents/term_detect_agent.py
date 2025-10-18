import json
from langchain_core.messages import HumanMessage
from src.agents.prompt_loader import TermDetectionPromptLoader


class TermDetectAgent:
    def __init__(self, chat_model):
        self.chat_model = chat_model
        self.prompt_loader = TermDetectionPromptLoader()

    def act(self, user_message: str) -> bool:
        try:
            prompt = self.prompt_loader.load().format(user_message=user_message)
            response = self.chat_model.invoke([HumanMessage(content=prompt)])

            response_text = response.content.strip()

            if response_text.startswith("```json"):
                response_text = (
                    response_text.replace("```json", "").replace("```", "").strip()
                )
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            result = json.loads(response_text)

            needs_search = result.get("needs_search", False)
            search_term = result.get("search_term", None)

            print(
                f"[TermDetectAgent] needs_search={needs_search}, term={search_term}, reason={result.get('reason', '')}"
            )

            return needs_search

        except Exception as e:
            print(f"[TermDetectAgent] Error: {e}")
            return False
