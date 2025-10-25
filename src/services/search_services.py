from abc import ABC, abstractmethod
import os
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import requests
import concurrent.futures

from src.utils.logger import log
from src.utils.date_utils import get_formatted_date
from src.utils.decorators import retry_on_error


class SearchService(ABC):
    """검색 서비스에 대한 인터페이스"""

    @abstractmethod
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        pass


class NoSearchService(SearchService):
    """검색이 필요 없을 때 사용하는 서비스"""

    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        log(self.__class__.__name__, "→ 검색 필요 없음 경로")
        return "", None


class GeneralSearchService(SearchService):
    """일반적인 웹 검색을 수행하는 독립적인 서비스"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com/search")

    @retry_on_error(max_attempts=2, delay=2.0)
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        log(self.__class__.__name__, "→ 일반 인물/사건 검색 경로")
        if not self.api_key:
            log(self.__class__.__name__, "SerpAPI 키가 없어 검색을 건너뜁니다.")
            return "", None

        current_date = get_formatted_date(datetime.now())
        search_results = self._search_web(query)
        search_summary = self._extract_summary(search_results)

        search_context = f"\n\n[검색 정보: '{query}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"
        log(self.__class__.__name__, "검색 완료")
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


class TermSearchService(SearchService):
    """신조어/용어 검색을 위한 독립적인 서비스"""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com/search")

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


class SnsSearchService(SearchService):
    """SNS 콘텐츠를 검색하고, 실패 시 일반 검색으로 fallback하는 독립적인 서비스"""

    def __init__(self, relevance_checker):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.relevance_checker = relevance_checker
        self.serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com/search")
        self.youtube_base_url = os.getenv("YOUTUBE_BASE_URL", "https://www.googleapis.com/youtube/v3/search")
        self._fallback_service = GeneralSearchService()

    @retry_on_error(max_attempts=2, delay=2.0)
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        log(self.__class__.__name__, "→ 일상 질문 (SNS) 경로")
        if not self.api_key:
            log(self.__class__.__name__, "SerpAPI 키가 없어 SNS 검색을 건너뜁니다.")
            return "", None

        sns_content = self._search_sns_content(query=query, user_question=question)

        if sns_content and sns_content.get("found"):
            log(self.__class__.__name__, f"✅ 관련 SNS 콘텐츠 발견 → SNS 정보 사용")
            platform_name = (
                "Instagram" if sns_content.get("platform") == "instagram" else "YouTube"
            )
            sns_title = sns_content.get("title", "")
            current_date = get_formatted_date(datetime.now())
            search_context = f"\n\n[{platform_name} 게시물 정보]\n{sns_title}\n\n[참고] 오늘 날짜: {current_date}\n"
            return search_context, sns_content
        else:
            log(self.__class__.__name__, f"SNS 콘텐츠 없음 → 일반 검색으로 Fallback")
            return self._fallback_service.search(query, question)

    def _search_sns_content(
        self, query: str, user_question: str = ""
    ) -> Dict[str, Any]:
        time_ranges = [
            ("qdr:m3", "최근 3개월"),
            ("qdr:m6", "최근 6개월"),
            ("qdr:y", "최근 1년"),
            (None, "전체 기간"),
        ]
        youtube_query = self._clean_youtube_query(query)

        all_candidates = self._search_all_time_ranges_parallel(
            query, youtube_query, time_ranges
        )
        if not all_candidates:
            return {"found": False}

        sorted_candidates = self._sort_by_recency(all_candidates)

        for candidate in sorted_candidates:
            if self.relevance_checker.act(
                user_question=user_question,
                sns_title=candidate.get("title", ""),
                platform=candidate.get("platform", ""),
                search_term=query,
            ):
                return {"found": True, **candidate}
        return {"found": False}

    def _clean_youtube_query(self, query: str) -> str:
        for keyword in ["유튜브", "youtube", "영상", "동영상", "비디오", "video"]:
            query = (
                query.replace(keyword, "")
                .replace(keyword.upper(), "")
                .replace(keyword.capitalize(), "")
            )
        return " ".join(query.split())

    def _search_all_time_ranges_parallel(
        self, query: str, youtube_query: str, time_ranges: List[tuple]
    ) -> List[Dict[str, Any]]:
        all_candidates = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for tbs, period in time_ranges:
                futures.append(
                    executor.submit(
                        self._search_google_images_with_metadata, query, tbs, period
                    )
                )
                if self.youtube_api_key:
                    futures.append(
                        executor.submit(
                            self._search_youtube_direct_with_metadata,
                            youtube_query,
                            self._get_youtube_time_filter(tbs),
                            period,
                        )
                    )

            for future in concurrent.futures.as_completed(futures):
                all_candidates.extend(future.result())

        seen_urls = set()
        unique_candidates = [
            c
            for c in all_candidates
            if c.get("url")
            and c["url"] not in seen_urls
            and not seen_urls.add(c["url"])
        ]
        return unique_candidates

    def _search_google_images_with_metadata(
        self, query: str, tbs_value: Optional[str], period_name: str
    ) -> List[Dict[str, Any]]:
        candidates = self._search_google_images(query, tbs_value)
        for c in candidates:
            c.update({"time_range_priority": period_name, "time_range_tbs": tbs_value})
        return candidates

    def _search_youtube_direct_with_metadata(
        self, query: str, published_after: Optional[str], period_name: str
    ) -> List[Dict[str, Any]]:
        candidates = self._search_youtube_direct(query, published_after)
        for c in candidates:
            c.update(
                {
                    "time_range_priority": period_name,
                    "time_range_published_after": published_after,
                }
            )
        return candidates

    def _sort_by_recency(
        self, candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        order = {"최근 3개월": 0, "최근 6개월": 1, "최근 1년": 2, "전체 기간": 3}
        return sorted(
            candidates,
            key=lambda c: order.get(c.get("time_range_priority", "전체 기간"), 99),
        )

    def _search_google_images(
        self, query: str, tbs_value: Optional[str]
    ) -> List[Dict[str, Any]]:
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google_images",
            "num": 50,
            "hl": "ko",
            "gl": "kr",
        }
        if tbs_value:
            params["tbs"] = tbs_value
        try:
            response = requests.get(self.serpapi_base_url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json().get("images_results", [])
            candidates = []
            for res in results:
                link = res.get("link", "")
                if "instagram.com" in link and ("/p/" in link or "/reel/" in link):
                    candidates.append(
                        {
                            "platform": "instagram",
                            "url": link,
                            "thumbnail": res.get("thumbnail"),
                            "title": res.get("title"),
                            "source": "google_images",
                        }
                    )
                elif "youtube.com/watch" in link or "youtu.be/" in link:
                    candidates.append(
                        {
                            "platform": "youtube",
                            "url": link,
                            "thumbnail": res.get("thumbnail"),
                            "title": res.get("title"),
                            "source": "google_images",
                        }
                    )
                if len(candidates) >= 5:
                    break
            return candidates
        except Exception as e:
            log(self.__class__.__name__, f"Google Images 검색 오류: {e}")
            return []

    def _search_youtube_direct(
        self, query: str, published_after: Optional[str]
    ) -> List[Dict[str, Any]]:
        if not self.youtube_api_key:
            return []
        params = {
            "part": "snippet",
            "q": query,
            "key": self.youtube_api_key,
            "type": "video",
            "maxResults": 5,
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "order": "relevance",
        }
        if published_after:
            params["publishedAfter"] = published_after
        try:
            response = requests.get(self.youtube_base_url, params=params, timeout=30)
            response.raise_for_status()
            items = response.json().get("items", [])
            return [
                {
                    "platform": "youtube",
                    "url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId')}",
                    "thumbnail": item.get("snippet", {})
                    .get("thumbnails", {})
                    .get("high", {})
                    .get("url"),
                    "title": item.get("snippet", {}).get("title"),
                    "source": "youtube_api_v3",
                }
                for item in items
                if item.get("id", {}).get("videoId")
            ]
        except Exception as e:
            log(self.__class__.__name__, f"YouTube Direct 검색 오류: {e}")
            return []

    def _get_youtube_time_filter(self, tbs_value: Optional[str]) -> Optional[str]:
        if not tbs_value:
            return None
        days = {"qdr:m3": 90, "qdr:m6": 180, "qdr:y": 365}.get(tbs_value)
        return (
            (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
            if days
            else None
        )
