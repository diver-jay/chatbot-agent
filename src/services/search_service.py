import os
from typing import Optional, Dict, Any, List
import requests
import concurrent.futures
from src.utils.logger import log


class SearchService:
    """SerpAPI를 사용한 웹 검색 서비스 클래스"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        youtube_api_key: Optional[str] = None,
    ):
        """
        Args:
            api_key: SerpAPI API 키 (없으면 환경변수에서 로드)
            youtube_api_key: YouTube Data API v3 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY가 설정되지 않았습니다.")

        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.youtube_api_key:
            log(self.__class__.__name__, "[Warning] YOUTUBE_API_KEY가 설정되지 않았습니다. YouTube 검색이 비활성화됩니다.")

        self.base_url = "https://serpapi.com/search"
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3/search"

    def search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        검색어로 웹 검색을 수행하고 결과를 반환합니다.

        Args:
            query: 검색어
            num_results: 반환할 결과 개수 (기본 3개)

        Returns:
            검색 결과 딕셔너리
        """
        log(self.__class__.__name__, f"\n검색 시작")
        log(self.__class__.__name__, f"query: {query}")
        log(self.__class__.__name__, f"num_results: {num_results}")

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

            result = response.json()

            log(self.__class__.__name__, f"SerpAPI 응답 keys: {list(result.keys())}")

            if "organic_results" in result:
                organic_count = len(result["organic_results"])
                log(self.__class__.__name__, f"organic_results 개수: {organic_count}")

                if organic_count > 0:
                    log(self.__class__.__name__, f"상위 결과 제목:")
                    for i, item in enumerate(result["organic_results"][:3], 1):
                        title = item.get("title", "")
                        log(self.__class__.__name__, f"  [{i}] {title}")

            return result

        except requests.exceptions.RequestException as e:
            log(self.__class__.__name__, f"검색 오류: {e}")
            return {"error": str(e)}

    def extract_summary(self, search_results: Dict[str, Any]) -> str:
        """
        검색 결과에서 핵심 정보를 추출하여 요약합니다.
        """
        if "error" in search_results:
            return f"검색 중 오류 발생: {search_results['error']}"

        if "answer_box" in search_results:
            answer = search_results["answer_box"]
            if "answer" in answer:
                return f"✓ {answer['answer']}"
            elif "snippet" in answer:
                return f"✓ {answer['snippet']}"

        if "knowledge_graph" in search_results:
            kg = search_results["knowledge_graph"]
            summary = []
            if "title" in kg:
                summary.append(f"📌 {kg['title']}")
            if "description" in kg:
                summary.append(kg["description"])
            if summary:
                return "\n".join(summary)

        if "organic_results" in search_results and search_results["organic_results"]:
            results = []
            for result in search_results["organic_results"][:3]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                date = result.get("date", "")

                if snippet:
                    if date:
                        results.append(f"• [{date}] {snippet}")
                    else:
                        results.append(f"• {snippet}")

            if results:
                return "\n".join(results)

        return "검색 결과를 찾을 수 없습니다."

    def _get_youtube_time_filter(self, tbs_value: Optional[str]) -> Optional[str]:
        """
        Google tbs 값을 YouTube Data API v3의 publishedAfter 날짜로 변환합니다.
        """
        if not tbs_value:
            return None

        from datetime import datetime, timedelta

        now = datetime.utcnow()

        if tbs_value == "qdr:m3":
            published_after = now - timedelta(days=90)
        elif tbs_value == "qdr:m6":
            published_after = now - timedelta(days=180)
        elif tbs_value == "qdr:y":
            published_after = now - timedelta(days=365)
        else:
            return None

        return published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _search_google_images(self, query: str, tbs_value: Optional[str]) -> List[Dict[str, Any]]:
        """
        Google Images에서 SNS 콘텐츠를 검색합니다.
        """
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
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()

            candidates = []
            if "images_results" in results:
                for result in results["images_results"]:
                    link = result.get("link", "")

                    if "instagram.com" in link and ("/p/" in link or "/reel/" in link):
                        candidates.append({"platform": "instagram", "url": link, "thumbnail": result.get("thumbnail") or result.get("original", ""), "title": result.get("title") or result.get("source", ""), "source": "google_images"})
                    elif "youtube.com/watch" in link or "youtu.be/" in link:
                        candidates.append({"platform": "youtube", "url": link, "thumbnail": result.get("thumbnail") or result.get("original", ""), "title": result.get("title") or result.get("source", ""), "source": "google_images"})

                    if len(candidates) >= 5:
                        break
            return candidates
        except Exception as e:
            log(self.__class__.__name__, f"Google Images 검색 오류: {e}")
            return []

    def _search_youtube_direct(self, query: str, published_after: Optional[str]) -> List[Dict[str, Any]]:
        """
        YouTube Data API v3를 사용하여 직접 검색합니다.
        """
        if not self.youtube_api_key:
            log(self.__class__.__name__, "YouTube API 키가 없어 직접 검색을 건너뜁니다.")
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
            log(self.__class__.__name__, f"YouTube Direct 검색어: {query}, publishedAfter={published_after or 'None'}")
            response = requests.get(self.youtube_base_url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()
            log(self.__class__.__name__, f"YouTube Direct API 응답 keys: {results.keys()}")

            candidates = []
            if "items" in results:
                log(self.__class__.__name__, f"YouTube Direct items 개수: {len(results['items'])}")
                for idx, item in enumerate(results["items"]):
                    video_id = item.get("id", {}).get("videoId", "")
                    snippet = item.get("snippet", {})
                    title = snippet.get("title", "")
                    thumbnail = snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                    log(self.__class__.__name__, f"YouTube Direct #{idx}: {title[:50]}...")
                    if video_id:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                        candidates.append({"platform": "youtube", "url": url, "thumbnail": thumbnail, "title": title, "source": "youtube_api_v3"})
            log(self.__class__.__name__, f"YouTube Direct 후보 추출 완료: {len(candidates)}개")
            return candidates
        except Exception as e:
            log(self.__class__.__name__, f"YouTube Direct 검색 오류: {e}")
            return []

    def search_sns_content(self, query: str, user_question: str = "", relevance_checker=None, has_recency_keyword: bool = True) -> Dict[str, Any]:
        """
        SNS 콘텐츠(Instagram, YouTube 등)를 검색하고 링크와 썸네일을 추출합니다.
        """
        time_ranges = [("qdr:m3", "최근 3개월"), ("qdr:m6", "최근 6개월"), ("qdr:y", "최근 1년"), (None, "전체 기간")]
        log(self.__class__.__name__, f"\nSNS 검색 시작")
        log(self.__class__.__name__, f"query: {query}")
        time_filter_desc = [f"{tbs or 'None'} ({name})" for tbs, name in time_ranges]
        log(self.__class__.__name__, f"time_filters: {time_filter_desc}")

        for idx, (tbs_value, period_name) in enumerate(time_ranges, 1):
            try:
                log(self.__class__.__name__, f"\nSNS 검색 [{idx}/{len(time_ranges)}] 시도: {period_name} (tbs={tbs_value or 'None'})")
                log(self.__class__.__name__, f"SNS 검색 Debug - 검색 파라미터: tbs={tbs_value or 'None'} ({period_name})")

                published_after = self._get_youtube_time_filter(tbs_value)
                youtube_query = query
                remove_keywords = ["유튜브", "youtube", "영상", "동영상", "비디오", "video"]
                for keyword in remove_keywords:
                    youtube_query = youtube_query.replace(keyword, "").replace(keyword.upper(), "").replace(keyword.capitalize(), "")
                youtube_query = " ".join(youtube_query.split())

                if youtube_query != query:
                    log(self.__class__.__name__, f"YouTube Query 검색어 강화: '{query}' → '{youtube_query}'")

                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    images_future = executor.submit(self._search_google_images, query, tbs_value)
                    youtube_future = executor.submit(self._search_youtube_direct, youtube_query, published_after)
                    images_candidates = images_future.result()
                    youtube_candidates = youtube_future.result()

                log(self.__class__.__name__, f"SNS 검색 Debug - Google Images 후보: {len(images_candidates)}개")
                log(self.__class__.__name__, f"SNS 검색 Debug - YouTube Direct 후보: {len(youtube_candidates)}개")

                all_candidates = youtube_candidates + images_candidates
                seen_urls = set()
                unique_candidates = []
                for candidate in all_candidates:
                    url = candidate.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_candidates.append(candidate)

                log(self.__class__.__name__, f"SNS 검색 Debug - 병합 후 고유 후보: {len(unique_candidates)}개")

                for idx, candidate in enumerate(unique_candidates):
                    url = candidate.get("url", "")
                    platform = candidate.get("platform", "")
                    title = candidate.get("title", "")
                    thumbnail = candidate.get("thumbnail", "")
                    source = candidate.get("source", "")
                    log(self.__class__.__name__, f"SNS 검색 Debug - Candidate #{idx}: platform={platform}, url={url[:80] if url else 'None'}, source={source}")

                    if relevance_checker and user_question:
                        is_relevant = relevance_checker.act(user_question=user_question, sns_title=title, platform=platform, search_term=query)
                        if is_relevant:
                            log(self.__class__.__name__, f"SNS 검색 Debug - ✅ 관련성 확인 완료 ({period_name}) → 결과 반환")
                            return {"found": True, "platform": platform, "url": url, "thumbnail": thumbnail, "title": title}
                        else:
                            log(self.__class__.__name__, f"SNS 검색 Debug - ❌ 관련성 없음 → 다음 결과 탐색")
                            continue
                    else:
                        log(self.__class__.__name__, f"SNS 검색 Debug - ✅ 관련성 검증 없이 결과 반환 ({period_name})")
                        return {"found": True, "platform": platform, "url": url, "thumbnail": thumbnail, "title": title}

                log(self.__class__.__name__, f"SNS 검색 Debug - ❌ {period_name}에서 SNS 링크를 찾지 못함 → Fallback 시도")
                if idx < len(time_ranges):
                    next_period = time_ranges[idx][1]
                    log(self.__class__.__name__, f"다음 시도: {next_period}")

            except Exception as e:
                import traceback
                log(self.__class__.__name__, f"SNS 검색 오류 ({period_name}): {e}")
                log(self.__class__.__name__, f"Traceback:\n{traceback.format_exc()}")
                if idx < len(time_ranges):
                    next_period = time_ranges[idx][1]
                    log(self.__class__.__name__, f"오류 발생 - 다음 시도: {next_period}")
                continue

        log(self.__class__.__name__, f"\nSNS 검색 ❌ 최종 결과: 모든 시간 범위({len(time_ranges)}개)에서 SNS 링크를 찾지 못함")
        return {"found": False}