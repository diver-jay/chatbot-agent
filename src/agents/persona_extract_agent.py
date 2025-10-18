from typing import Optional
from src.services.search_service import SearchService
from src.agents.prompt_loader import PersonaExtractionPromptLoader


class PersonaExtractAgent:
    def __init__(self, chat_model, serpapi_key: Optional[str] = None):
        self.chat_model = chat_model
        self.serpapi_key = serpapi_key
        self.prompt_loader = PersonaExtractionPromptLoader()

    def act(self, influencer_name: str) -> str:
        if not self.serpapi_key:
            return ""

        try:
            search_service = SearchService(api_key=self.serpapi_key)
            search_results = search_service.search(influencer_name)
            search_summary = search_service.extract_summary(search_results)

            prompt_template = self.prompt_loader.load()
            persona_extraction_prompt = prompt_template.format(
                influencer_name=influencer_name, search_summary=search_summary
            )

            response = self.chat_model.invoke(persona_extraction_prompt)
            persona_context = response.content.strip()

            return persona_context

        except Exception as e:
            return ""
