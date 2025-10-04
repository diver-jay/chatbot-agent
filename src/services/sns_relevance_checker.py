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

    def check_relevance(self, user_question: str, sns_title: str, platform: str, search_term: str = "") -> Tuple[bool, str]:
        """
        사용자 질문과 SNS 게시물의 관련성을 판단합니다.

        Args:
            user_question: 사용자의 질문
            sns_title: SNS 게시물 제목/설명
            platform: SNS 플랫폼 (instagram/youtube)
            search_term: 검색에 사용된 검색어 (인물/주제 포함)

        Returns:
            (관련성 있음 여부, 판단 이유) 튜플
        """
        try:
            prompt = f"""
당신은 사용자 질문과 SNS 게시물의 관련성을 판단하는 전문가입니다.

## 사용자 질문
{user_question}

## 검색어
{search_term}

## SNS 게시물 정보
플랫폼: {platform}
제목/내용: {sns_title}

## 판단 기준
사용자 질문과 SNS 게시물이 **모두** 다음 조건을 만족해야 관련있음으로 판단합니다:

### 1. 주요 인물/주체 일치 ⭐ 최우선
- **검색어**에 명시된 **특정 인물**과 SNS 게시물의 **주인공**이 일치해야 함
- 검색어에 인물이 포함되어 있으면, 반드시 그 인물이 게시물의 주인공이어야 함
- 예시:
  - 검색어: "아이유 웃지 않는 생일 영상" / 게시물: "G-DRAGON's No-Laughing Birthday Party" → ❌ 관련없음 (인물 불일치: 아이유 ≠ 지드래곤)
  - 검색어: "아이유 웃지 않는 생일 영상" / 게시물: "차은우의 웃으면 안되는 생일파티" → ❌ 관련없음 (인물 불일치: 아이유 ≠ 차은우)
  - 검색어: "아이유 웃지 않는 생일 영상" / 게시물: "아이유의 웃으면 안되는 생일파티" → ✅ 관련있음 (인물 일치)
  - 검색어: "아이유 유튜브 최근 영상" / 게시물: "공유 게스트 출연" → ❌ 관련없음 (주인공 불일치: 아이유 ≠ 공유)

### 2. 핵심 주제/콘텐츠 일치
- 사용자 질문의 **핵심 키워드**와 SNS 게시물 내용이 직접적으로 관련있어야 함
- 예시:
  - 질문: "웃지 않는 생일 영상 공유해주세요" / 게시물: "웃으면 안되는 생일파티 개최 안내" → ❌ 관련없음 (영상이 아닌 이벤트 안내)
  - 질문: "웃지 않는 생일 영상 공유해주세요" / 게시물: "웃으면 안되는 생일파티 YouTube 영상" → ✅ 관련있음 (영상 콘텐츠)
  - 질문: "최근에 먹방 찍었어?" / 게시물: "초밥 10접시 먹방" → ✅ 관련있음
  - 질문: "화보 봤어요" / 게시물: "패션 화보 촬영" → ✅ 관련있음
  - 질문: "화보 봤어요" / 게시물: "먹방 영상" → ❌ 관련없음

### 3. 일반적 근황 질문 예외
- 질문이 **구체적 주제 없이** 일반적 근황을 묻는 경우: 인물만 일치하면 관련있음
- 예시:
  - 질문: "요즘 뭐해?" / 게시물: 어떤 내용이든 → ✅ 관련있음 (일반 근황)
  - 질문: "최근에 뭐했어?" / 게시물: 어떤 내용이든 → ✅ 관련있음 (일반 근황)

## 중요 원칙
1. **검색어에 명시된 인물과 게시물 주인공 불일치** → 무조건 ❌ 관련없음
2. **구체적인 주제**(웃지 않는 생일, 먹방, 화보, 영상 등)를 묻는 질문 → 게시물이 그 주제와 직접 관련있어야 ✅
3. **일반적 근황** 질문 → 인물만 일치하면 ✅
4. **반드시 검색어를 우선 참고**하여 인물/주제를 파악하세요

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
