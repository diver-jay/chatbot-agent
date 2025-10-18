import json
from langchain_core.messages import HumanMessage
from src.agents.chat_agent import ChatAgent
from src.utils.parser import parse_json_from_response
from typing_extensions import override


class SNSRelevanceCheckAgent(ChatAgent):
    def __init__(self, chat_model, file_path="prompts/sns_relevance_check_prompt.md"):
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
    def act(self, **kwargs) -> bool:
        user_question = kwargs.get("user_question")
        sns_title = kwargs.get("sns_title")
        platform = kwargs.get("platform")
        search_term = kwargs.get("search_term", "")

        if not all([user_question, sns_title, platform]):
            return True

        try:
            prompt_template = self.load_prompt()
            prompt = prompt_template.format(
                user_question=user_question,
                search_term=search_term,
                platform=platform,
                sns_title=sns_title,
            )

            response_text = self.chat_model.invoke([HumanMessage(content=prompt)]).content
            result = parse_json_from_response(response_text)
            is_relevant = result.get("is_relevant", False)
            reason = result.get("reason", "")

            # 로깅
            print(f"[SNSRelevanceCheckAgent] 관련성: {is_relevant} | 이유: {reason}")

            return is_relevant

        except Exception as e:
            print(f"[SNSRelevanceCheckAgent] 검증 중 오류: {e}")
            # 오류 발생 시 안전하게 관련있다고 판단 (false negative 방지)
            return True