import re
from langchain_core.messages import HumanMessage
from src.services.prompt_loader import SplitPromptLoader


class ResponseSplitter:
    """AI Agent 답변을 맥락 단위로 분할하는 클래스"""

    def __init__(self, chat_model):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
        """
        self.chat_model = chat_model
        self.prompt_loader = SplitPromptLoader()

    def split_by_context(self, response: str) -> list[str]:
        """Claude API를 사용하여 답변을 맥락 단위로 분할

        Args:
            response: 분할할 응답 텍스트

        Returns:
            분할된 텍스트 리스트. 실패 시 원본 응답을 담은 리스트 반환
        """
        try:
            split_prompt = self.prompt_loader.load()
        except FileNotFoundError:
            return [response]  # 프롬프트 로드 실패 시 원본 그대로 반환

        try:
            # 분할 요청을 위한 프롬프트 구성
            split_request = f"{split_prompt}\n\n다음 텍스트를 위 가이드라인에 따라 분할해주세요:\n\n{response}"

            # Claude API 호출
            split_result = self.chat_model.invoke([HumanMessage(content=split_request)])
            split_text = split_result.content

            # [[SPLIT_N]] 마커를 기준으로 분할
            parts = re.split(r"\[\[SPLIT_\d+\]\]", split_text)
            # 빈 문자열 제거 및 공백 정리
            parts = [part.strip() for part in parts if part.strip()]

            return parts if parts else [response]
        except Exception as e:
            print(f"답변 분할 중 오류 발생: {str(e)}")
            return [response]  # 오류 발생 시 원본 그대로 반환
