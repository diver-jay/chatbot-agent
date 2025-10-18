"""
사용자 입력에서 신조어/모르는 용어를 감지하는 모듈
"""

import json
from langchain_core.messages import HumanMessage


class TermDetector:
    """신조어 및 모르는 용어를 감지하는 클래스"""

    def __init__(self, chat_model):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
        """
        self.chat_model = chat_model
        self.detection_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """프롬프트 파일을 로드합니다."""
        prompt_path = "prompts/term_detection_prompt.md"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"[TermDetector] Warning: {prompt_path} not found, using default prompt")
            return """당신은 한국어 신조어 및 유행어 전문가입니다.

사용자의 메시지를 분석하여 다음을 판단하세요:
1. 신조어, 유행어, 인터넷 밈, 줄임말 등이 포함되어 있는가?
2. 일반적인 AI 모델이 모를 가능성이 높은 최신 용어가 있는가?

**중요**:
- 일상적인 대화, 일반 단어는 검색 불필요
- 명확히 신조어/유행어로 보이는 경우만 검색 필요
- 예시: "자낳괴", "점메추", "갓생", "억텐", "MZ", "TMI" 등

응답은 반드시 다음 JSON 형식으로만 출력하세요:
{{
    "needs_search": true 또는 false,
    "search_term": "검색할 용어 (needs_search가 true일 때만)",
    "reason": "판단 이유 (간단히)"
}}

사용자 메시지: {user_message}
"""

    def detect(self, user_message: str) -> bool:
        """
        사용자 메시지에서 검색이 필요한지 감지합니다.

        Args:
            user_message: 사용자 입력 메시지

        Returns:
            검색 필요 여부 (bool)
        """
        return self._detect(user_message)

    def _detect(self, user_message: str) -> bool:
        """
        사용자 메시지에서 신조어/유행어를 감지하는 내부 메서드.

        Args:
            user_message: 사용자 입력 메시지

        Returns:
            검색 필요 여부 (bool)
        """
        try:
            prompt = self.detection_prompt.format(user_message=user_message)
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
                f"[TermDetector] needs_search={needs_search}, term={search_term}, reason={result.get('reason', '')}"
            )

            return needs_search

        except Exception as e:
            print(f"[TermDetector] Error: {e}")
            return False
