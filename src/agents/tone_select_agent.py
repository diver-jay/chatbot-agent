from typing import Literal
from src.agents.chat_agent import ChatAgent
from typing_extensions import override
from src.utils.logger import log

ToneType = Literal["mentor", "influencer_20s", "celebrity_20s"]


class ToneSelectAgent(ChatAgent):
    TONE_TEMPLATES = {
        "influencer_20s": "prompts/tone_influencer_20s.md",
        "celebrity_20s": "prompts/tone_celebrity_20s.md",
        "mentor": "prompts/tone_mentor.md",  # 기본 멘토/박사님 스타일
    }

    def __init__(self, chat_model, file_path="prompts/tone_selection_prompt.md"):
        self.chat_model = chat_model
        self.file_path = file_path
        self._selected_tone: ToneType = "mentor"  # Default tone

    @override
    def load_prompt(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")

    @override
    def act(self, **kwargs) -> None:
        influencer_name = kwargs.get("influencer_name")
        if not influencer_name:
            self._selected_tone = "mentor"
            return

        try:
            analysis_prompt = self.load_prompt().format(influencer_name=influencer_name)
            ai_response = self.chat_model.invoke(analysis_prompt).content.strip()
            self._selected_tone = self._get_tone_type(ai_response)

        except Exception as e:
            log(self.__class__.__name__, f"Error: {e}")
            self._selected_tone = "mentor"

    def get_tone_type(self) -> ToneType:
        """Returns the selected tone type."""
        return self._selected_tone

    def get_tone_path(self) -> str:
        """Returns the file path for the selected tone."""
        return self.TONE_TEMPLATES[self._selected_tone]

    def _get_tone_type(self, ai_response: str) -> ToneType:
        for line in ai_response.split("\n"):
            if "카테고리:" in line:
                tone_type = line.split("카테고리:")[1].strip()
                tone_type = tone_type.replace("[", "").replace("]", "").strip()

                if tone_type in self.TONE_TEMPLATES:
                    return tone_type
                else:
                    return "mentor"

        return "mentor"
