"""
Persona Extractor Module
인플루언서 정보를 검색하고 페르소나 컨텍스트를 추출합니다.
"""

from typing import Optional
from src.services.search_service import SearchService
from src.services.prompt_loader import PersonaExtractionPromptLoader


class PersonaExtractor:
    """인플루언서의 페르소나 컨텍스트를 추출하는 클래스"""

    def __init__(self, chat_model, serpapi_key: Optional[str] = None):
        """
        Args:
            chat_model: LangChain 채팅 모델 인스턴스
            serpapi_key: SerpAPI 키 (선택사항)
        """
        self.chat_model = chat_model
        self.serpapi_key = serpapi_key
        self.prompt_loader = PersonaExtractionPromptLoader()

    def extract(self, influencer_name: str) -> str:
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

            # 프롬프트 로더를 통해 템플릿 로드
            prompt_template = self.prompt_loader.load()
            persona_extraction_prompt = prompt_template.format(
                influencer_name=influencer_name, search_summary=search_summary
            )

            response = self.chat_model.invoke(persona_extraction_prompt)
            persona_context = response.content.strip()

            return persona_context

        except Exception as e:
            return ""
