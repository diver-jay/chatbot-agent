"""
Tone Selector Module
AI를 사용하여 인플루언서 이름을 분석하고 적절한 Tone 템플릿을 선택합니다.
"""

from typing import Tuple, Optional
from src.services.prompt_loader import ToneSelectionPromptLoader


class ToneSelector:
    """
    인플루언서 이름을 분석하여 적절한 Tone 템플릿을 선택하는 클래스
    """

    # 사용 가능한 Tone 템플릿 경로
    TONE_TEMPLATES = {
        "influencer_20s": "prompts/tone_influencer_20s.md",
        "celebrity_20s": "prompts/tone_celebrity_20s.md",
        "mentor": "prompts/tone_mentor.md",  # 기본 멘토/박사님 스타일
    }

    def __init__(self, chat_model):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
        """
        self.chat_model = chat_model
        self.tone_selection_loader = ToneSelectionPromptLoader()

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
        try:
            # 프롬프트 로더를 통해 템플릿 로드
            prompt_template = self.tone_selection_loader.load()
            # 템플릿에 변수 주입
            analysis_prompt = prompt_template.format(influencer_name=influencer_name)

            response = self.chat_model.invoke(analysis_prompt)
            ai_response = response.content.strip()
            tone_type = self._parse_ai_response(ai_response)
            tone_file_path = self.TONE_TEMPLATES[tone_type]
            return tone_type, tone_file_path

        except Exception as e:
            return "mentor", self.TONE_TEMPLATES["mentor"]

    def _parse_ai_response(self, ai_response: str) -> str:
        """
        AI 응답을 파싱하여 tone_type을 추출합니다.

        Args:
            ai_response: AI의 원본 응답 텍스트

        Returns:
            str: tone_type ("influencer_20s", "celebrity_20s", "mentor")
        """
        for line in ai_response.split("\n"):
            if "카테고리:" in line:
                tone_type = line.split("카테고리:")[1].strip()
                tone_type = tone_type.replace("[", "").replace("]", "").strip()

                if tone_type in self.TONE_TEMPLATES:
                    return tone_type
                else:
                    return "mentor"

        return "mentor"
