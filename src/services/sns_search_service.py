import os
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import requests
import concurrent.futures

from src.services.search_service import SearchService
from src.services.general_search_service import GeneralSearchService
from src.utils.logger import log
from src.utils.date_utils import get_formatted_date
from src.utils.decorators import retry_on_error


class SnsSearchService(SearchService):

    def __init__(self, relevance_checker):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.relevance_checker = relevance_checker
        self.serpapi_base_url = os.getenv(
            "SERPAPI_BASE_URL", "https://serpapi.com/search"
        )
        self.youtube_base_url = os.getenv(
            "YOUTUBE_BASE_URL", "https://www.googleapis.com/youtube/v3/search"
        )
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
            published_at = sns_content.get("published_at")
            current_date = get_formatted_date(datetime.now())

            date_info = ""
            if published_at:
                try:
                    # The 'Z' in the ISO format string is not supported by fromisoformat in all python versions.
                    # Replacing 'Z' with '+00:00' makes it compatible.
                    pub_date = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                    date_info = f"게시물 등록일: {get_formatted_date(pub_date)}\n"
                except (ValueError, TypeError):
                    log(
                        self.__class__.__name__, f"Could not parse date: {published_at}"
                    )

            search_context = f"\n\n[{platform_name} 게시물 정보]\n제목: {sns_title}\n{date_info}\n[참고] 오늘 날짜: {current_date}\n"
            return search_context, sns_content
        else:
            log(self.__class__.__name__, f"SNS 콘텐츠 없음 → 일반 검색으로 Fallback")
            return self._fallback_service.search(query, question)

    def _search_sns_content(
        self, query: str, user_question: str = ""
    ) -> Dict[str, Any]:
        time_ranges = [
            ("qdr:m6", "최근 6개월"),
            (None, "전체 기간"),
        ]
        youtube_query = self._clean_youtube_query(query)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for tbs, period in time_ranges:
                log(self.__class__.__name__, f"Searching SNS for period: {period}")

                period_futures = []
                period_futures.append(
                    executor.submit(
                        self._search_google_images_with_metadata, query, tbs, period
                    )
                )
                if self.youtube_api_key:
                    period_futures.append(
                        executor.submit(
                            self._search_youtube_direct_with_metadata,
                            youtube_query,
                            self._get_youtube_time_filter(tbs),
                            period,
                        )
                    )

                for future in concurrent.futures.as_completed(period_futures):
                    try:
                        candidates = future.result()
                        for candidate in candidates:
                            if self.relevance_checker.act(
                                user_question=user_question,
                                sns_title=candidate.get("title", ""),
                                platform=candidate.get("platform", ""),
                                search_term=query,
                            ):
                                log(
                                    self.__class__.__name__,
                                    f"Found relevant SNS content in period: {period}",
                                )
                                return {"found": True, **candidate}
                    except Exception as e:
                        log(
                            self.__class__.__name__,
                            f"Error processing future in SNS search: {e}",
                        )

        log(
            self.__class__.__name__,
            "No relevant SNS content found across all time periods.",
        )
        return {"found": False}

    def _clean_youtube_query(self, query: str) -> str:
        for keyword in ["유튜브", "youtube", "영상", "동영상", "비디오", "video"]:
            query = (
                query.replace(keyword, "")
                .replace(keyword.upper(), "")
                .replace(keyword.capitalize(), "")
            )
        return " ".join(query.split())

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

    def _search_google_images(
        self, query: str, tbs_value: Optional[str]
    ) -> List[Dict[str, Any]]:
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google_images",
            "num": 20,
            "hl": "ko",
            "gl": "kr",
        }
        if tbs_value:
            params["tbs"] = tbs_value
        try:
            response = requests.get(self.serpapi_base_url, params=params, timeout=15)
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
            response = requests.get(self.youtube_base_url, params=params, timeout=15)
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
                    "published_at": item.get("snippet", {}).get("publishedAt"),
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
