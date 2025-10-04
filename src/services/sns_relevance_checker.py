"""
SNS 게시물과 사용자 질문의 관련성을 검증하는 모듈
"""
from typing import Tuple
import json
from langchain_core.messages import HumanMessage


class SNSRelevanceChecker:
    """SNS 게시물이 사용자 질문과 관련있는지 판단하는 클래스"""

    def __init__(self, chat_model):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
        """
        self.chat_model = chat_model

    def check_relevance(self, user_question: str, sns_title: str, platform: str) -> Tuple[bool, str]:
        """
        사용자 질문과 SNS 게시물의 관련성을 판단합니다.

        Args:
            user_question: 사용자의 질문
            sns_title: SNS 게시물 제목/설명
            platform: SNS 플랫폼 (instagram/youtube)

        Returns:
            (관련성 있음 여부, 판단 이유) 튜플
        """
        try:
            prompt = f"""
당신은 사용자 질문과 SNS 게시물의 관련성을 판단하는 전문가입니다.

## 사용자 질문
{user_question}

## SNS 게시물 정보
플랫폼: {platform}
제목/내용: {sns_title}

## 판단 기준
1. 사용자 질문의 핵심 주제와 SNS 게시물 내용이 **직접적으로 관련**있는가?
2. 예시:
   - 질문: "최근에 먹방 찍었어?" / 게시물: "초밥 10접시 먹방" → ✅ 관련있음
   - 질문: "최근에 먹방 찍었어?" / 게시물: "건강 고백" → ❌ 관련없음
   - 질문: "요즘 뭐해?" / 게시물: 어떤 내용이든 → ✅ 관련있음 (일반적 근황)
   - 질문: "화보 봤어요" / 게시물: "패션 화보 촬영" → ✅ 관련있음
   - 질문: "화보 봤어요" / 게시물: "먹방 영상" → ❌ 관련없음
   - 질문: "최근에 강연 하셨어요?" / 게시물: "아동 심리 강연 후기" → ✅ 관련있음
   - 질문: "최근에 강연 하셨어요?" / 게시물: "개인 일상 사진" → ❌ 관련없음
   - 질문: "새 책 나왔다며요?" / 게시물: "신간 출간 소식" → ✅ 관련있음
   - 질문: "새 책 나왔다며요?" / 게시물: "TV 프로그램 출연" → ❌ 관련없음

## 중요
- **구체적인 주제**를 묻는 질문(먹방, 화보, 운동 등)인 경우: 게시물이 그 주제와 직접 관련있어야 함
- **일반적인 근황**을 묻는 질문(요즘 뭐해, 최근에 뭐했어)인 경우: 어떤 게시물이든 관련있음

## 응답 형식
반드시 JSON 형식으로만 응답하세요:

```json
{{
    "is_relevant": true,
    "reason": "판단 이유"
}}
```

또는

```json
{{
    "is_relevant": false,
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
            is_relevant = result.get("is_relevant", False)
            reason = result.get("reason", "")

            print(f"[SNS Relevance] 관련성: {is_relevant} | 이유: {reason}")

            return is_relevant, reason

        except Exception as e:
            print(f"[SNS Relevance] 검증 중 오류: {e}")
            # 오류 발생 시 안전하게 관련있다고 판단 (false negative 방지)
            return True, "검증 오류로 인해 기본값으로 관련있음 처리"
