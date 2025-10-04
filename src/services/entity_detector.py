"""
사용자 입력에서 특정 인물/사건을 감지하는 모듈
"""
from typing import Tuple, Optional
import json
from langchain_core.messages import HumanMessage


class EntityDetector:
    """특정 인물 및 사건을 감지하는 클래스"""

    def __init__(self, chat_model):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
        """
        self.chat_model = chat_model

    def detect(self, user_message: str, influencer_name: Optional[str] = None, chat_history: Optional[list] = None) -> Tuple[bool, Optional[str], bool]:
        """
        사용자 메시지에서 검색이 필요한 인물/사건을 감지합니다.

        Args:
            user_message: 사용자 입력 메시지
            influencer_name: 인플루언서 이름 (선택사항)
            chat_history: 대화 히스토리 (선택사항) - [{"role": "human/assistant", "content": "..."}, ...]

        Returns:
            (검색 필요 여부, 검색할 용어, 일상 관련 여부) 튜플
        """
        try:
            # 프롬프트 템플릿 파일에서 로드
            prompt_template_path = "prompts/entity_detection_prompt.md"

            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # 대화 히스토리를 문자열로 포맷팅
            history_context = ""
            if chat_history:
                # 최근 4개 메시지만 사용 (2턴)
                recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
                history_lines = []
                for msg in recent_history:
                    role = "사용자" if msg.get("role") == "human" else "AI"
                    content = msg.get("content", "")
                    history_lines.append(f"{role}: {content}")
                history_context = "\n".join(history_lines)

            # 템플릿에 변수 주입
            if history_context:
                detection_prompt = prompt_template.format(
                    user_message=f"[이전 대화]\n{history_context}\n\n[현재 질문]\n{user_message}"
                )
            else:
                detection_prompt = prompt_template.format(user_message=user_message)

            # LLM을 사용하여 인물/사건 감지
            response = self.chat_model.invoke([HumanMessage(content=detection_prompt)])

            # JSON 응답 파싱
            response_text = response.content.strip()

            # JSON 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            result = json.loads(response_text)

            needs_search = result.get("needs_search", False)
            search_term = result.get("search_term", None)
            is_daily_life = result.get("is_daily_life", False)

            # influencer_name이 있고, search_term에 아직 포함되지 않았으면 앞에 추가
            if needs_search and search_term and influencer_name:
                # "인물명" 플레이스홀더를 실제 이름으로 치환
                if "인물명" in search_term:
                    search_term = search_term.replace("인물명", influencer_name)
                # 이미 influencer_name이 search_term에 포함되어 있는지 확인
                elif influencer_name.lower() not in search_term.lower():
                    search_term = f"{influencer_name} {search_term}"

            print(f"[EntityDetector] 🔍 검색 필요: {needs_search} | 검색어: {search_term} | 일상: {is_daily_life} | 판단 근거: {result.get('reason', 'N/A')}")

            return needs_search, search_term, is_daily_life

        except Exception as e:
            print(f"[EntityDetector] Error: {e}")
            # 에러 발생 시 검색하지 않음
            return False, None, False
