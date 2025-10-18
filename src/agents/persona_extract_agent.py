from typing import Optional
from src.services.search_service import SearchService
from src.agents.chat_agent import ChatAgent
from typing_extensions import override


class PersonaExtractAgent(ChatAgent):
    def __init__(self, chat_model, serpapi_key: Optional[str] = None, file_path="prompts/persona_extraction_prompt.md"):
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
    def act(self, **kwargs) -> str:
        influencer_name = kwargs.get("influencer_name")
        if not self.serpapi_key or not influencer_name:
            return ""

        try:
            search_service = SearchService(api_key=self.serpapi_key)
            search_results = search_service.search(influencer_name)
            search_summary = search_service.extract_summary(search_results)

            prompt_template = self.load_prompt()
            persona_extraction_prompt = prompt_template.format(
                influencer_name=influencer_name, search_summary=search_summary
            )

            response = self.chat_model.invoke(persona_extraction_prompt)
            persona_context = response.content.strip()

            return persona_context

        except Exception as e:
            print(f"페르소나 추출 중 오류 발생: {e}")
            return ""