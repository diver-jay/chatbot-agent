"""
SerpAPI를 사용한 웹 검색 서비스
"""
import os
from typing import Optional, Dict, Any
import requests


class SearchService:
    """SerpAPI를 사용한 웹 검색 서비스 클래스"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: SerpAPI API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY가 설정되지 않았습니다.")

        self.base_url = "https://serpapi.com/search"

    def search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        검색어로 웹 검색을 수행하고 결과를 반환합니다.

        Args:
            query: 검색어
            num_results: 반환할 결과 개수 (기본 3개)

        Returns:
            검색 결과 딕셔너리
        """
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "hl": "ko",  # 한국어 결과
                "gl": "kr",  # 한국 지역
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def extract_summary(self, search_results: Dict[str, Any]) -> str:
        """
        검색 결과에서 핵심 정보를 추출하여 요약합니다.

        Args:
            search_results: search() 메서드의 반환값

        Returns:
            요약된 검색 결과 문자열
        """
        if "error" in search_results:
            return f"검색 중 오류 발생: {search_results['error']}"

        # Answer box (구글 직접 답변)가 있으면 우선 사용
        if "answer_box" in search_results:
            answer = search_results["answer_box"]
            if "answer" in answer:
                return f"✓ {answer['answer']}"
            elif "snippet" in answer:
                return f"✓ {answer['snippet']}"

        # Knowledge graph (지식 그래프)
        if "knowledge_graph" in search_results:
            kg = search_results["knowledge_graph"]
            summary = []
            if "title" in kg:
                summary.append(f"📌 {kg['title']}")
            if "description" in kg:
                summary.append(kg["description"])
            if summary:
                return "\n".join(summary)

        # Organic results (일반 검색 결과)
        if "organic_results" in search_results and search_results["organic_results"]:
            results = []
            for result in search_results["organic_results"][:3]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                if snippet:
                    results.append(f"• {snippet}")

            if results:
                return "\n".join(results)

        return "검색 결과를 찾을 수 없습니다."
