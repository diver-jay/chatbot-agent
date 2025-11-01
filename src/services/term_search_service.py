import os
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import requests

from src.services.search_service import SearchService
from src.utils.logger import log
from src.utils.date_utils import get_formatted_date
from src.utils.decorators import retry_on_error


class TermSearchService(SearchService):

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.serpapi_base_url = os.getenv(
            "SERPAPI_BASE_URL", "https://serpapi.com/search"
        )

    @retry_on_error(max_attempts=2, delay=2.0)
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        log(self.__class__.__name__, "→ 신조어/용어 검색 경로")
        if not self.api_key:
            log(self.__class__.__name__, "SerpAPI 키가 없어 검색을 건너뜁니다.")
            return "", None

        current_date = get_formatted_date(datetime.now())
        search_results = self._search_web(query)
        search_summary = self._extract_summary(search_results)

        search_context = f"\n\n[검색 정보: '{query}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"
        search_context += f"\n[지시사항] 위 검색 정보를 바탕으로 자연스럽게 답변하세요. 검색어('{query}')를 그대로 반복하지 말고, 그 의미를 이해한 상태로 대화하세요.\n"
        return search_context, None

    def _search_web(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "hl": "ko",
                "gl": "kr",
            }
            response = requests.get(self.serpapi_base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log(self.__class__.__name__, f"SerpAPI 웹 검색 오류: {e}")
            return {"error": str(e)}

    def _extract_summary(self, search_results: Dict[str, Any]) -> str:
        if "error" in search_results:
            return f"검색 중 오류 발생: {search_results['error']}"
        if "answer_box" in search_results and search_results["answer_box"].get(
            "answer"
        ):
            return f"✓ {search_results['answer_box']['answer']}"
        if "knowledge_graph" in search_results:
            kg = search_results["knowledge_graph"]
            return f"📌 {kg.get('title', '')}\n{kg.get('description', '')}"
        if "organic_results" in search_results and search_results["organic_results"]:
            return "\n".join(
                [
                    f"• {r.get('snippet', '')}"
                    for r in search_results["organic_results"][:3]
                ]
            )
        return "검색 결과를 찾을 수 없습니다."
