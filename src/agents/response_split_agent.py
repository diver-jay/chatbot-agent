import re
from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from typing_extensions import override
from src.utils.logger import log


class ResponseSplitAgent(ChatAgent):
    def __init__(self, chat_model, file_path="prompts/split_response_prompt.md"):
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
    def act(self, **kwargs) -> list[str]:
        response = kwargs.get("response")
        if not response:
            return []
        try:
            prompt = self.load_prompt()
            split_request = f"{prompt}\n\n다음 텍스트를 위 가이드라인에 따라 분할해주세요:\n\n{response}"
            split_text = self.chat_model.invoke(
                [HumanMessage(content=split_request)]
            ).content
            parts = [
                part.strip()
                for part in re.split(r"\[\[SPLIT_\d+\]\]", split_text)
                if part.strip()
            ]
            return parts if parts else [response]
        except Exception as e:
            log(self.__class__.__name__, f"답변 분할 중 오류 발생: {str(e)}")
            return [response]
