from src.agents.prompt_loader import ToneSelectionPromptLoader


class ToneSelectAgent:
    # 사용 가능한 Tone 템플릿 경로
    TONE_TEMPLATES = {
        "influencer_20s": "prompts/tone_influencer_20s.md",
        "celebrity_20s": "prompts/tone_celebrity_20s.md",
        "mentor": "prompts/tone_mentor.md",  # 기본 멘토/박사님 스타일
    }

    def __init__(self, chat_model):
        self.chat_model = chat_model
        self.tone_selection_loader = ToneSelectionPromptLoader()

    def act(self, influencer_name: str) -> str:
        try:
            analysis_prompt = self.tone_selection_loader.load().format(
                influencer_name=influencer_name
            )
            ai_response = self.chat_model.invoke(analysis_prompt).content.strip()
            tone_type = self._get_tone_type(ai_response)
            return self.TONE_TEMPLATES[tone_type]

        except Exception as e:
            return self.TONE_TEMPLATES["mentor"]

    def _get_tone_type(self, ai_response: str) -> str:
        for line in ai_response.split("\n"):
            if "카테고리:" in line:
                tone_type = line.split("카테고리:")[1].strip()
                tone_type = tone_type.replace("[", "").replace("]", "").strip()

                if tone_type in self.TONE_TEMPLATES:
                    return tone_type
                else:
                    return "mentor"

        return "mentor"
