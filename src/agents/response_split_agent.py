import re
from langchain_core.messages import HumanMessage
from src.agents.prompt_loader import SplitPromptLoader


class ResponseSplitAgent:
    def __init__(self, chat_model):
        self.chat_model = chat_model
        self.prompt_loader = SplitPromptLoader()

    def act(self, response: str) -> list[str]:
        try:
            split_request = f"{self.prompt_loader.load()}\n\n다음 텍스트를 위 가이드라인에 따라 분할해주세요:\n\n{response}"
            split_text = self.chat_model.invoke([HumanMessage(content=split_request)]).content
            parts = [part.strip() for part in re.split(r"\[\[SPLIT_\d+\]\]", split_text) if part.strip()]
            return parts if parts else [response]
        except Exception as e:
            print(f"답변 분할 중 오류 발생: {str(e)}")
            return [response]
