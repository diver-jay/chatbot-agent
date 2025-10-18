import os
from typing import Optional, Dict, Any, List
import requests
import concurrent.futures
from src.utils.logger import log


class SearchService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        youtube_api_key: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY가 설정되지 않았습니다.")

        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.youtube_api_key:
            log(
                self.__class__.__name__,
                "[Warning] YOUTUBE_API_KEY가 설정되지 않았습니다. YouTube 검색이 비활성화됩니다.",
            )

        self.base_url = "https://serpapi.com/search"
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3/search"

    def search_web(self, query: str, num_results: int = 3) -> Dict[str, Any]:
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
                log(
                    self.__class__.__name__,
                    f"organic_results 개수: {len(result['organic_results'])}",
                )

                if len(result["organic_results"]) > 0:
                    log(self.__class__.__name__, f"상위 결과 제목:")
                    for i, item in enumerate(result["organic_results"][:3], 1):
                        log(self.__class__.__name__, f"  [{i}] {item.get('title', '')}")

            return result

        except requests.exceptions.RequestException as e:
            log(self.__class__.__name__, f"검색 오류: {e}")
            return {"error": str(e)}

    def search_sns_content(
        self,
        query: str,
        user_question: str = "",
        relevance_checker=None,
    ) -> Dict[str, Any]:
        """
        SNS 콘텐츠(Instagram, YouTube 등)를 검색하고 링크와 썸네일을 추출합니다.
        모든 시간 범위를 병렬로 검색하고, 최신 콘텐츠부터 우선순위화합니다.
        """
        time_ranges = [
            ("qdr:m3", "최근 3개월"),
            ("qdr:m6", "최근 6개월"),
            ("qdr:y", "최근 1년"),
            (None, "전체 기간"),
        ]
        log(self.__class__.__name__, f"\nSNS 검색 시작 (병렬 검색)")
        log(self.__class__.__name__, f"query: {query}")
        log(self.__class__.__name__, f"time_filters: {[(tbs or 'None', name) for tbs, name in time_ranges]}")

        # YouTube 검색어 정제
        youtube_query = self._clean_youtube_query(query)
        if youtube_query != query:
            log(
                self.__class__.__name__,
                f"YouTube Query 검색어 강화: '{query}' → '{youtube_query}'",
            )

        # 모든 시간 범위를 병렬로 검색
        all_candidates = self._search_all_time_ranges_parallel(query, youtube_query, time_ranges)

        log(
            self.__class__.__name__,
            f"병렬 검색 완료 - 총 후보: {len(all_candidates)}개",
        )

        if not all_candidates:
            log(
                self.__class__.__name__,
                f"\nSNS 검색 ❌ 최종 결과: 모든 시간 범위에서 SNS 링크를 찾지 못함",
            )
            return {"found": False}

        # 최신순으로 정렬 (우선순위화)
        sorted_candidates = self._sort_by_recency(all_candidates)
        log(
            self.__class__.__name__,
            f"최신순 정렬 완료 - 우선순위 후보: {len(sorted_candidates)}개",
        )

        # 관련성 검사 (최신 것부터)
        for idx, candidate in enumerate(sorted_candidates):
            url = candidate.get("url", "")
            platform = candidate.get("platform", "")
            title = candidate.get("title", "")
            thumbnail = candidate.get("thumbnail", "")
            source = candidate.get("source", "")
            time_range_priority = candidate.get("time_range_priority", "unknown")

            log(
                self.__class__.__name__,
                f"Candidate #{idx}: platform={platform}, time_range={time_range_priority}, url={url[:80] if url else 'None'}, source={source}",
            )

            if relevance_checker and user_question:
                is_relevant = relevance_checker.act(
                    user_question=user_question,
                    sns_title=title,
                    platform=platform,
                    search_term=query,
                )
                if is_relevant:
                    log(
                        self.__class__.__name__,
                        f"✅ 관련성 확인 완료 (time_range={time_range_priority}) → 결과 반환",
                    )
                    return {
                        "found": True,
                        "platform": platform,
                        "url": url,
                        "thumbnail": thumbnail,
                        "title": title,
                    }
                else:
                    log(
                        self.__class__.__name__,
                        f"❌ 관련성 없음 → 다음 결과 탐색",
                    )
                    continue
            else:
                log(
                    self.__class__.__name__,
                    f"✅ 관련성 검증 없이 결과 반환 (time_range={time_range_priority})",
                )
                return {
                    "found": True,
                    "platform": platform,
                    "url": url,
                    "thumbnail": thumbnail,
                    "title": title,
                }

        log(
            self.__class__.__name__,
            f"\nSNS 검색 ❌ 최종 결과: 후보는 있었으나 관련성 있는 콘텐츠를 찾지 못함",
        )
        return {"found": False}

    def _clean_youtube_query(self, query: str) -> str:
        """YouTube 검색어에서 불필요한 키워드 제거"""
        youtube_query = query
        remove_keywords = [
            "유튜브",
            "youtube",
            "영상",
            "동영상",
            "비디오",
            "video",
        ]
        for keyword in remove_keywords:
            youtube_query = (
                youtube_query.replace(keyword, "")
                .replace(keyword.upper(), "")
                .replace(keyword.capitalize(), "")
            )
        return " ".join(youtube_query.split())

    def _search_all_time_ranges_parallel(
        self, query: str, youtube_query: str, time_ranges: List[tuple]
    ) -> List[Dict[str, Any]]:
        """모든 시간 범위를 병렬로 검색하고 결과를 취합"""
        all_candidates = []

        # 각 시간 범위별로 병렬 검색 태스크 생성
        search_tasks = []
        for tbs_value, period_name in time_ranges:
            published_after = self._get_youtube_time_filter(tbs_value)
            search_tasks.append((query, youtube_query, tbs_value, published_after, period_name))

        # 병렬 실행 (max_workers=8: 4개 시간 범위 * 2개 검색 엔진)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for search_query, yt_query, tbs_value, published_after, period_name in search_tasks:
                # Google Images 검색
                images_future = executor.submit(
                    self._search_google_images_with_metadata,
                    search_query,
                    tbs_value,
                    period_name
                )
                futures.append(images_future)

                # YouTube Direct 검색
                youtube_future = executor.submit(
                    self._search_youtube_direct_with_metadata,
                    yt_query,
                    published_after,
                    period_name
                )
                futures.append(youtube_future)

            # 모든 결과 수집
            for future in concurrent.futures.as_completed(futures):
                try:
                    candidates = future.result()
                    all_candidates.extend(candidates)
                except Exception as e:
                    log(self.__class__.__name__, f"병렬 검색 중 오류: {e}")
                    continue

        # 중복 URL 제거
        seen_urls = set()
        unique_candidates = []
        for candidate in all_candidates:
            url = candidate.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(candidate)

        log(
            self.__class__.__name__,
            f"병렬 검색 결과 - 전체: {len(all_candidates)}개, 고유: {len(unique_candidates)}개",
        )

        return unique_candidates

    def _search_google_images_with_metadata(
        self, query: str, tbs_value: Optional[str], period_name: str
    ) -> List[Dict[str, Any]]:
        """Google Images 검색 + 메타데이터 추가"""
        candidates = self._search_google_images(query, tbs_value)
        # 시간 범위 우선순위 메타데이터 추가
        for candidate in candidates:
            candidate["time_range_priority"] = period_name
            candidate["time_range_tbs"] = tbs_value
        return candidates

    def _search_youtube_direct_with_metadata(
        self, query: str, published_after: Optional[str], period_name: str
    ) -> List[Dict[str, Any]]:
        """YouTube Direct 검색 + 메타데이터 추가"""
        candidates = self._search_youtube_direct(query, published_after)
        # 시간 범위 우선순위 메타데이터 추가
        for candidate in candidates:
            candidate["time_range_priority"] = period_name
            candidate["time_range_published_after"] = published_after
        return candidates

    def _sort_by_recency(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """후보를 최신순으로 정렬 (시간 범위 우선순위 기반)"""
        # 시간 범위 우선순위 (최근일수록 높은 우선순위)
        time_range_order = {
            "최근 3개월": 0,
            "최근 6개월": 1,
            "최근 1년": 2,
            "전체 기간": 3,
        }

        def get_priority(candidate: Dict[str, Any]) -> int:
            time_range = candidate.get("time_range_priority", "전체 기간")
            return time_range_order.get(time_range, 999)

        return sorted(candidates, key=get_priority)

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

    def _search_google_images(
        self, query: str, tbs_value: Optional[str]
    ) -> List[Dict[str, Any]]:
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
                        candidates.append(
                            {
                                "platform": "instagram",
                                "url": link,
                                "thumbnail": result.get("thumbnail")
                                or result.get("original", ""),
                                "title": result.get("title")
                                or result.get("source", ""),
                                "source": "google_images",
                            }
                        )
                    elif "youtube.com/watch" in link or "youtu.be/" in link:
                        candidates.append(
                            {
                                "platform": "youtube",
                                "url": link,
                                "thumbnail": result.get("thumbnail")
                                or result.get("original", ""),
                                "title": result.get("title")
                                or result.get("source", ""),
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
        """
        YouTube Data API v3를 사용하여 직접 검색합니다.
        """
        if not self.youtube_api_key:
            log(
                self.__class__.__name__, "YouTube API 키가 없어 직접 검색을 건너뜁니다."
            )
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
            log(
                self.__class__.__name__,
                f"YouTube Direct 검색어: {query}, publishedAfter={published_after or 'None'}",
            )
            response = requests.get(self.youtube_base_url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()
            log(
                self.__class__.__name__,
                f"YouTube Direct API 응답 keys: {results.keys()}",
            )

            candidates = []
            if "items" in results:
                log(
                    self.__class__.__name__,
                    f"YouTube Direct items 개수: {len(results['items'])}",
                )
                for idx, item in enumerate(results["items"]):
                    video_id = item.get("id", {}).get("videoId", "")
                    snippet = item.get("snippet", {})
                    title = snippet.get("title", "")
                    thumbnail = (
                        snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                    )
                    log(
                        self.__class__.__name__,
                        f"YouTube Direct #{idx}: {title[:50]}...",
                    )
                    if video_id:
                        url = f"https://www.youtube.com/watch?v={video_id}"
                        candidates.append(
                            {
                                "platform": "youtube",
                                "url": url,
                                "thumbnail": thumbnail,
                                "title": title,
                                "source": "youtube_api_v3",
                            }
                        )
            log(
                self.__class__.__name__,
                f"YouTube Direct 후보 추출 완료: {len(candidates)}개",
            )
            return candidates
        except Exception as e:
            log(self.__class__.__name__, f"YouTube Direct 검색 오류: {e}")
            return []

    def _get_youtube_time_filter(self, tbs_value: Optional[str]) -> Optional[str]:
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
