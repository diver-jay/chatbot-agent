"""
Tone Selector Module
AI를 사용하여 인플루언서 이름을 분석하고 적절한 Tone 템플릿을 선택합니다.
"""

from typing import Tuple, Optional
from search_service import SearchService


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

    def __init__(self, chat_model, serpapi_key: Optional[str] = None):
        """
        Args:
            chat_model: Anthropic Claude 모델 인스턴스
            serpapi_key: SerpAPI 키 (선택사항)
        """
        self.chat_model = chat_model
        self.serpapi_key = serpapi_key

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
        # 프롬프트 템플릿 파일에서 로드
        prompt_template_path = "prompts/tone_selection_prompt.md"

        try:
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # 템플릿에 변수 주입
            analysis_prompt = prompt_template.format(influencer_name=influencer_name)

        except FileNotFoundError:
            return "mentor", self.TONE_TEMPLATES["mentor"]

        try:
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
        for line in ai_response.split('\n'):
            if '카테고리:' in line:
                tone_type = line.split('카테고리:')[1].strip()
                tone_type = tone_type.replace('[', '').replace(']', '').strip()

                if tone_type in self.TONE_TEMPLATES:
                    return tone_type
                else:
                    return "mentor"

        return "mentor"

    def fetch_persona_context(self, influencer_name: str) -> str:
        """
        SerpAPI를 사용하여 인플루언서 정보를 검색하고 페르소나 컨텍스트를 생성합니다.

        Args:
            influencer_name: 사용자가 입력한 인플루언서 이름

        Returns:
            str: 페르소나 컨텍스트 (배경, 활동, 최근 근황 등)
        """
        if not self.serpapi_key:
            return ""

        try:
            search_service = SearchService(api_key=self.serpapi_key)
            search_results = search_service.search(influencer_name)
            search_summary = search_service.extract_summary(search_results)

            prompt_template_path = "prompts/persona_extraction_prompt.md"
            with open(prompt_template_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            persona_extraction_prompt = prompt_template.format(
                influencer_name=influencer_name,
                search_summary=search_summary
            )

            response = self.chat_model.invoke(persona_extraction_prompt)
            persona_context = response.content.strip()

            return persona_context

        except Exception as e:
            return ""
