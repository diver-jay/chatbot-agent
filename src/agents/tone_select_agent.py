from src.agents.chat_agent import ChatAgent
from typing_extensions import override
from src.utils.logger import log


class ToneSelectAgent(ChatAgent):
    # 사용 가능한 Tone 템플릿 경로
    TONE_TEMPLATES = {
        "influencer_20s": "prompts/tone_influencer_20s.md",
        "celebrity_20s": "prompts/tone_celebrity_20s.md",
        "mentor": "prompts/tone_mentor.md",  # 기본 멘토/박사님 스타일
    }

    def __init__(self, chat_model, file_path="prompts/tone_selection_prompt.md"):
        self.chat_model = chat_model
        self.file_path = file_path

    @override
    def load_prompt(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")

    @override
    def act(self, **kwargs) -> str:
        influencer_name = kwargs.get("influencer_name")
        if not influencer_name:
            return self.TONE_TEMPLATES["mentor"]  # Return default

        try:
            analysis_prompt = self.load_prompt().format(
                influencer_name=influencer_name
            )
            ai_response = self.chat_model.invoke(analysis_prompt).content.strip()
            tone_type = self._get_tone_type(ai_response)
            return self.TONE_TEMPLATES[tone_type]

        except Exception as e:
            log(self.__class__.__name__, f"Error: {e}")
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
