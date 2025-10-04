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

    def _check_content_request(self, user_message: str, chat_history: Optional[list] = None) -> bool:
        """
        AI를 사용하여 사용자가 영상/사진/링크 등 콘텐츠를 명시적으로 요청했는지 판단합니다.

        Args:
            user_message: 사용자 메시지
            chat_history: 대화 히스토리

        Returns:
            콘텐츠 요청 여부
        """
        try:
            # 최근 대화 히스토리 포맷팅
            history_context = ""
            if chat_history:
                recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
                history_lines = []
                for msg in recent_history:
                    role = "사용자" if msg.get("role") == "human" else "AI"
                    content = msg.get("content", "")
                    history_lines.append(f"{role}: {content}")
                history_context = "\n".join(history_lines)

            prompt = f"""
사용자가 **영상, 사진, 링크 등의 콘텐츠를 명시적으로 요청**했는지 판단하세요.

## 이전 대화 (있는 경우)
{history_context if history_context else "없음"}

## 현재 사용자 메시지
{user_message}

## 판단 기준
다음 중 **하나라도 해당**하면 콘텐츠 요청으로 판단합니다:
1. 영상/동영상/비디오를 보여달라고 요청
2. 사진/이미지를 보여달라고 요청
3. 링크/URL을 공유해달라고 요청
4. "공유해줘", "보내줘", "보여줘" + (영상/사진/인스타/유튜브 관련 맥락)
5. 인스타그램/유튜브 게시물을 직접 요청

## 콘텐츠 요청이 **아닌** 경우 (중요!)
- 단순히 사실 확인하는 질문 (예: "맞아요?", "진짜요?", "본 적 있어?")
- 일반적인 대화 (예: "대박", "헐 진짜?", "언제 나와요?")
- 내용에 대한 질문 (예: "누구 나왔어?", "뭐 했어?")

## 응답 형식
JSON 형식으로만 응답하세요:

```json
{{
    "requests_content": true,
    "reason": "판단 이유"
}}
```

또는

```json
{{
    "requests_content": false,
    "reason": "판단 이유"
}}
```
"""

            response = self.chat_model.invoke([HumanMessage(content=prompt)])
            response_text = response.content.strip()

            # JSON 코드 블록 제거
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            result = json.loads(response_text)
            requests_content = result.get("requests_content", False)
            reason = result.get("reason", "")

            print(f"[Content Request Check] 콘텐츠 요청: {requests_content} | 이유: {reason}")

            return requests_content

        except Exception as e:
            print(f"[Content Request Check] 오류: {e}")
            # 오류 발생 시 안전하게 False 반환 (콘텐츠 보여주지 않음)
            return False

    def detect(self, user_message: str, influencer_name: Optional[str] = None, chat_history: Optional[list] = None) -> Tuple[bool, Optional[str], bool, bool]:
        """
        사용자 메시지에서 검색이 필요한 인물/사건을 감지합니다.

        Args:
            user_message: 사용자 입력 메시지
            influencer_name: 인플루언서 이름 (선택사항)
            chat_history: 대화 히스토리 (선택사항) - [{"role": "human/assistant", "content": "..."}, ...]

        Returns:
            (검색 필요 여부, 검색할 용어, 일상 관련 여부, 콘텐츠 요청 여부) 튜플
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

            # 콘텐츠 요청 여부 판단 (영상, 사진, 링크 등)
            requests_content = self._check_content_request(user_message, chat_history)

            # influencer_name이 있고, search_term에 아직 포함되지 않았으면 앞에 추가
            if needs_search and search_term and influencer_name:
                # "인물명" 플레이스홀더를 실제 이름으로 치환
                if "인물명" in search_term:
                    search_term = search_term.replace("인물명", influencer_name)
                # 이미 influencer_name이 search_term에 포함되어 있는지 확인
                elif influencer_name.lower() not in search_term.lower():
                    search_term = f"{influencer_name} {search_term}"

            print(f"[EntityDetector] 🔍 검색 필요: {needs_search} | 검색어: {search_term} | 일상: {is_daily_life} | 콘텐츠 요청: {requests_content} | 판단 근거: {result.get('reason', 'N/A')}")

            return needs_search, search_term, is_daily_life, requests_content

        except Exception as e:
            print(f"[EntityDetector] Error: {e}")
            # 에러 발생 시 검색하지 않음
            return False, None, False, False
