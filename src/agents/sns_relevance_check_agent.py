import json
from langchain_core.messages import HumanMessage
from src.agents.prompt_loader import SNSRelevancePromptLoader


class SNSRelevanceCheckAgent:
    def __init__(self, chat_model):
        self.chat_model = chat_model
        self.prompt_loader = SNSRelevancePromptLoader()

    def act(
        self, user_question: str, sns_title: str, platform: str, search_term: str = ""
    ) -> bool:
        try:
            prompt = self.prompt_loader.load().format(
                user_question=user_question,
                search_term=search_term,
                platform=platform,
                sns_title=sns_title,
            )

            response_text = self.chat_model.invoke([HumanMessage(content=prompt)]).content.strip()

            # JSON 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            result = json.loads(response_text)
            is_relevant = result.get("is_relevant", False)
            reason = result.get("reason", "")

            # 로깅
            print(f"[SNSRelevanceCheckAgent] 관련성: {is_relevant} | 이유: {reason}")

            return is_relevant

        except Exception as e:
            print(f"[SNSRelevanceCheckAgent] 검증 중 오류: {e}")
            # 오류 발생 시 안전하게 관련있다고 판단 (false negative 방지)
            return True
