"""
Tone Selector Module
AI를 사용하여 인플루언서 이름을 분석하고 적절한 Tone 템플릿을 선택합니다.
"""

import logging
from typing import Tuple

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ToneSelector:
    """
    인플루언서 이름을 분석하여 적절한 Tone 템플릿을 선택하는 클래스
    """

    # 사용 가능한 Tone 템플릿 경로
    TONE_TEMPLATES = {
        "influencer_20s": "prompts/tone_influencer_20s.md",
        "celebrity_20s": "prompts/tone_celebrity_20s.md",
        "mentor": "prompts/converstation_prompt.md"  # 기본 멘토/박사님 스타일
    }

    def __init__(self, chat_model):
        """
        Args:
            chat_model: Anthropic Claude 모델 인스턴스
        """
        self.chat_model = chat_model
        logger.info("ToneSelector 초기화 완료")

    def select_tone(self, influencer_name: str) -> Tuple[str, str]:
        """
        AI를 사용하여 인플루언서 이름을 분석하고 적절한 Tone을 선택합니다.

        Args:
            influencer_name: 사용자가 입력한 인플루언서 이름

        Returns:
            Tuple[str, str]: (tone_type, tone_file_path)
            - tone_type: "influencer_20s", "celebrity_20s", "mentor" 중 하나
            - tone_file_path: 해당 tone 템플릿 파일 경로
        """
        logger.info(f"=== Tone 선택 시작 ===")
        logger.info(f"입력된 인플루언서 이름: '{influencer_name}'")

        # AI에게 분석 요청
        analysis_prompt = f"""
다음 인물의 이름을 보고, 어떤 카테고리에 속하는지 판단해주세요.

인물 이름: {influencer_name}

카테고리:
1. influencer_20s: 20대 인스타그램 인플루언서, 유튜버 등 (밝고 캐주얼한 톤, 신조어 많이 사용)
2. celebrity_20s: 20대 가수, 연예인, 아이돌 등 (밝지만 예의 바른 톤)
3. mentor: 30대 이상의 박사님, 전문가, 멘토 등 (따뜻하고 전문적인 톤)

판단 기준:
- 실제 유명 인물이라면 그 사람의 특징을 고려
- 일반적인 호칭(박사님, 선생님 등)이라면 mentor 카테고리
- 친구 이름이나 애칭이라면 나이대와 분위기로 추정

응답은 반드시 다음 형식으로만 답변하세요:
카테고리: [influencer_20s/celebrity_20s/mentor]
이유: [한 문장으로 간단히]
"""

        try:
            logger.debug(f"AI 분석 요청 프롬프트:\n{analysis_prompt}")

            # AI 호출
            response = self.chat_model.invoke(analysis_prompt)
            ai_response = response.content.strip()

            logger.info(f"AI 응답:\n{ai_response}")

            # AI 응답 파싱
            tone_type = self._parse_ai_response(ai_response)

            tone_file_path = self.TONE_TEMPLATES[tone_type]

            logger.info(f"✅ 선택된 Tone: {tone_type}")
            logger.info(f"✅ Tone 파일 경로: {tone_file_path}")
            logger.info(f"=== Tone 선택 완료 ===\n")

            return tone_type, tone_file_path

        except Exception as e:
            logger.error(f"❌ Tone 선택 중 오류 발생: {e}")
            logger.warning(f"⚠️ 기본 Tone(mentor)으로 폴백")

            # 오류 발생 시 기본값(mentor) 반환
            return "mentor", self.TONE_TEMPLATES["mentor"]

    def _parse_ai_response(self, ai_response: str) -> str:
        """
        AI 응답을 파싱하여 tone_type을 추출합니다.

        Args:
            ai_response: AI의 원본 응답 텍스트

        Returns:
            str: tone_type ("influencer_20s", "celebrity_20s", "mentor")
        """
        logger.debug("AI 응답 파싱 시작")

        # "카테고리:" 뒤의 값 추출
        for line in ai_response.split('\n'):
            if '카테고리:' in line:
                # "카테고리: influencer_20s" 형태에서 값 추출
                tone_type = line.split('카테고리:')[1].strip()

                # 대괄호 제거 및 정리
                tone_type = tone_type.replace('[', '').replace(']', '').strip()

                logger.debug(f"파싱된 카테고리: {tone_type}")

                # 유효한 카테고리인지 확인
                if tone_type in self.TONE_TEMPLATES:
                    return tone_type
                else:
                    logger.warning(f"⚠️ 유효하지 않은 카테고리: {tone_type}, 기본값(mentor) 사용")
                    return "mentor"

        # 파싱 실패 시 기본값
        logger.warning("⚠️ 카테고리 파싱 실패, 기본값(mentor) 사용")
        return "mentor"
