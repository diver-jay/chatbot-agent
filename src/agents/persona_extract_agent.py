from typing import Optional
from src.agents.chat_agent import ChatAgent
from src.services.general_search_service import GeneralSearchService
from typing_extensions import override
from src.utils.logger import log

# Type alias for persona extraction result
PersonaContext = str


class PersonaExtractAgent(ChatAgent):
    def __init__(
        self,
        chat_model,
        serpapi_key: Optional[str] = None,
        file_path="prompts/persona_extraction_prompt.md",
    ):
        self.chat_model = chat_model
        self.serpapi_key = serpapi_key
        self.file_path = file_path

    @override
    def load_prompt(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")

    @override
    def act(self, **kwargs) -> PersonaContext:
        influencer_name = kwargs.get("influencer_name")
        if not self.serpapi_key or not influencer_name:
            return ""

        try:
            search_service = GeneralSearchService()
            search_summary, _ = search_service.search(
                query=influencer_name, question=""
            )

            prompt_template = self.load_prompt()
            persona_extraction_prompt = prompt_template.format(
                influencer_name=influencer_name, search_summary=search_summary
            )

            response = self.chat_model.invoke(persona_extraction_prompt)
            persona_context = response.content.strip()

            return persona_context

        except Exception as e:
            log(self.__class__.__name__, f"페르소나 추출 중 오류 발생: {e}")
            return ""
