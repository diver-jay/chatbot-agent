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
                date = result.get("date", "")  # 날짜 정보 추출

                if snippet:
                    # 날짜 정보가 있으면 함께 표시
                    if date:
                        results.append(f"• [{date}] {snippet}")
                    else:
                        results.append(f"• {snippet}")

            if results:
                return "\n".join(results)

        return "검색 결과를 찾을 수 없습니다."

    def search_sns_content(self, query: str) -> Dict[str, Any]:
        """
        SNS 콘텐츠(Instagram, YouTube 등)를 검색하고 링크와 썸네일을 추출합니다.

        Args:
            query: 검색어 (예: "인플루언서명 인스타그램 최근")

        Returns:
            {
                "found": bool,
                "platform": str,  # "instagram" or "youtube"
                "url": str,
                "thumbnail": str,
                "title": str
            }
        """
        try:
            # Google Images 검색을 사용하여 Instagram/YouTube 게시물 찾기
            # 최근 1개월 이내 결과만 검색
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google_images",  # 이미지 검색 엔진
                "num": 20,  # 더 많은 결과
                "hl": "ko",
                "gl": "kr",
                "tbs": "qdr:m",  # 최근 1개월 (past month)
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            search_results = response.json()

            print(f"[SNS Search Debug] 검색 파라미터: tbs=qdr:m (최근 1개월)")

            if "error" in search_results:
                print(f"[SNS Search Debug] 검색 오류: {search_results['error']}")
                return {"found": False}

            print(f"[SNS Search Debug] 전체 검색 결과 키: {search_results.keys()}")

            # Google Images 결과에서 Instagram/YouTube 링크 찾기
            if "images_results" in search_results:
                print(f"[SNS Search Debug] images_results 개수: {len(search_results['images_results'])}")

                for idx, result in enumerate(search_results["images_results"]):
                    # 원본 링크 (이미지가 게시된 페이지)
                    link = result.get("link", "")
                    original = result.get("original", "")  # 원본 이미지
                    thumbnail = result.get("thumbnail", "")
                    title = result.get("title", "")
                    source = result.get("source", "")  # 출처

                    print(f"[SNS Search Debug] Image #{idx}: link={link[:80] if link else 'None'}, source={source}")

                    # Instagram 게시물 링크만 감지 (프로필 제외)
                    if "instagram.com" in link:
                        # 특정 게시물만: /p/ (포스트) 또는 /reel/ (릴스)
                        if "/p/" in link or "/reel/" in link:
                            print(f"[SNS Search Debug] ✅ Instagram 게시물 링크 발견: {link}")
                            return {
                                "found": True,
                                "platform": "instagram",
                                "url": link,
                                "thumbnail": thumbnail or original,
                                "title": title or source
                            }
                        else:
                            print(f"[SNS Search Debug] ⏭️ Instagram 프로필 링크 건너뜀: {link}")

                    # YouTube 링크 감지
                    elif "youtube.com/watch" in link or "youtu.be/" in link:
                        print(f"[SNS Search Debug] ✅ YouTube 링크 발견: {link}")
                        return {
                            "found": True,
                            "platform": "youtube",
                            "url": link,
                            "thumbnail": thumbnail or original,
                            "title": title or source
                        }

            print(f"[SNS Search Debug] ❌ SNS 링크를 찾지 못함")
            return {"found": False}

        except Exception as e:
            print(f"[SearchService] SNS 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return {"found": False}
