"""
SerpAPI를 사용한 웹 검색 서비스
"""

import os
from typing import Optional, Dict, Any, List
import requests
import concurrent.futures


class SearchService:
    """SerpAPI를 사용한 웹 검색 서비스 클래스"""

    def __init__(
        self, api_key: Optional[str] = None, youtube_api_key: Optional[str] = None
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
            print(
                "[Warning] YOUTUBE_API_KEY가 설정되지 않았습니다. YouTube 검색이 비활성화됩니다."
            )

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

    def _get_youtube_time_filter(self, tbs_value: Optional[str]) -> Optional[str]:
        """
        Google tbs 값을 YouTube Data API v3의 publishedAfter 날짜로 변환합니다.

        Args:
            tbs_value: Google 시간 필터 (예: "qdr:m3")

        Returns:
            RFC 3339 형식의 날짜 문자열 (예: "2024-07-01T00:00:00Z") 또는 None
        """
        if not tbs_value:
            return None

        from datetime import datetime, timedelta

        now = datetime.utcnow()

        # tbs 값을 날짜로 변환
        if tbs_value == "qdr:m3":
            # 최근 3개월
            published_after = now - timedelta(days=90)
        elif tbs_value == "qdr:m6":
            # 최근 6개월
            published_after = now - timedelta(days=180)
        elif tbs_value == "qdr:y":
            # 최근 1년
            published_after = now - timedelta(days=365)
        else:
            return None

        # RFC 3339 형식으로 변환 (YouTube API 요구 형식)
        return published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _search_google_images(
        self, query: str, tbs_value: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Google Images에서 SNS 콘텐츠를 검색합니다.

        Returns:
            SNS 후보 리스트 [{"platform": "instagram", "url": "...", ...}, ...]
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
                # 50개 전체를 순회하며 Instagram/YouTube 링크 찾기
                for result in results["images_results"]:
                    link = result.get("link", "")

                    # Instagram 게시물
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
                    # YouTube 영상
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

                    # 5개 찾으면 중단
                    if len(candidates) >= 5:
                        break

            return candidates
        except Exception as e:
            print(f"[Google Images Search] 오류: {e}")
            return []

    def _search_youtube_direct(
        self, query: str, published_after: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        YouTube Data API v3를 사용하여 직접 검색합니다.

        Args:
            query: 검색어
            published_after: 업로드 날짜 필터 (RFC 3339 format, 예: "2024-07-01T00:00:00Z")

        Returns:
            YouTube 후보 리스트 [{"platform": "youtube", "url": "...", ...}, ...]
        """
        if not self.youtube_api_key:
            print("[YouTube Direct] YouTube API 키가 없어 검색을 건너뜁니다.")
            return []

        params = {
            "part": "snippet",
            "q": query,
            "key": self.youtube_api_key,
            "type": "video",
            "maxResults": 5,
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "order": "relevance",  # 관련성 순
        }

        if published_after:
            params["publishedAfter"] = published_after

        try:
            print(
                f"[YouTube Direct] 검색어: {query}, publishedAfter={published_after or 'None'}"
            )
            response = requests.get(self.youtube_base_url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()

            print(f"[YouTube Direct] API 응답 키: {results.keys()}")

            candidates = []
            if "items" in results:
                print(f"[YouTube Direct] items 개수: {len(results['items'])}")
                for idx, item in enumerate(results["items"]):
                    video_id = item.get("id", {}).get("videoId", "")
                    snippet = item.get("snippet", {})
                    title = snippet.get("title", "")
                    thumbnail = (
                        snippet.get("thumbnails", {}).get("high", {}).get("url", "")
                    )

                    print(f"[YouTube Direct] #{idx}: {title[:50]}...")

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

            print(f"[YouTube Direct] 후보 추출 완료: {len(candidates)}개")
            return candidates
        except Exception as e:
            print(f"[YouTube Direct Search] 오류: {e}")
            return []

    def search_sns_content(
        self,
        query: str,
        user_question: str = "",
        relevance_checker=None,
        has_recency_keyword: bool = True,
    ) -> Dict[str, Any]:
        """
        SNS 콘텐츠(Instagram, YouTube 등)를 검색하고 링크와 썸네일을 추출합니다.
        검색 결과가 없으면 시간 범위를 점차 확장합니다 (3개월 → 6개월 → 1년 → 전체).

        Args:
            query: 검색어 (예: "인플루언서명 인스타그램 최근")
            user_question: 사용자의 원래 질문 (관련성 검증용)
            relevance_checker: SNSRelevanceChecker 인스턴스 (관련성 검증용)
            has_recency_keyword: '최근', '요즘' 등의 시간 키워드가 포함되어 있는지 여부

        Returns:
            {
                "found": bool,
                "platform": str,  # "instagram" or "youtube"
                "url": str,
                "thumbnail": str,
                "title": str
            }
        """
        # Fallback 시간 범위 정의
        time_ranges = [
            ("qdr:m3", "최근 3개월"),
            ("qdr:m6", "최근 6개월"),
            ("qdr:y", "최근 1년"),
            (None, "전체 기간"),
        ]

        for tbs_value, period_name in time_ranges:
            try:
                print(
                    f"[SNS Search Debug] 검색 파라미터: tbs={tbs_value or 'None'} ({period_name})"
                )

                # YouTube 시간 필터 변환 (RFC 3339 날짜로)
                published_after = self._get_youtube_time_filter(tbs_value)

                # 병렬 검색 실행
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    images_future = executor.submit(
                        self._search_google_images, query, tbs_value
                    )
                    youtube_future = executor.submit(
                        self._search_youtube_direct, query, published_after
                    )

                    # 결과 대기
                    images_candidates = images_future.result()
                    youtube_candidates = youtube_future.result()

                print(
                    f"[SNS Search Debug] Google Images 후보: {len(images_candidates)}개"
                )
                print(
                    f"[SNS Search Debug] YouTube Direct 후보: {len(youtube_candidates)}개"
                )

                # 결과 병합: YouTube Direct 우선, 그 다음 Images
                all_candidates = youtube_candidates + images_candidates

                # 중복 URL 제거 (YouTube Direct가 우선순위)
                seen_urls = set()
                unique_candidates = []
                for candidate in all_candidates:
                    url = candidate.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_candidates.append(candidate)

                print(
                    f"[SNS Search Debug] 병합 후 고유 후보: {len(unique_candidates)}개"
                )

                # 각 후보에 대해 관련성 검증
                for idx, candidate in enumerate(unique_candidates):
                    url = candidate.get("url", "")
                    platform = candidate.get("platform", "")
                    title = candidate.get("title", "")
                    thumbnail = candidate.get("thumbnail", "")
                    source = candidate.get("source", "")

                    print(
                        f"[SNS Search Debug] Candidate #{idx}: platform={platform}, url={url[:80] if url else 'None'}, source={source}"
                    )

                    # 관련성 검증 (relevance_checker가 있고 user_question이 있을 때만)
                    if relevance_checker and user_question:
                        is_relevant, reason = relevance_checker.check_relevance(
                            user_question=user_question,
                            sns_title=title,
                            platform=platform,
                            search_term=query,
                        )
                        print(f"[SNS Relevance] 관련성: {is_relevant} | 이유: {reason}")

                        if is_relevant:
                            print(
                                f"[SNS Search Debug] ✅ 관련성 확인 완료 ({period_name}) → 결과 반환"
                            )
                            return {
                                "found": True,
                                "platform": platform,
                                "url": url,
                                "thumbnail": thumbnail,
                                "title": title,
                            }
                        else:
                            print(f"[SNS Search Debug] ❌ 관련성 없음 → 다음 결과 탐색")
                            continue
                    else:
                        # 관련성 검증 없이 바로 반환
                        print(
                            f"[SNS Search Debug] ✅ 관련성 검증 없이 결과 반환 ({period_name})"
                        )
                        return {
                            "found": True,
                            "platform": platform,
                            "url": url,
                            "thumbnail": thumbnail,
                            "title": title,
                        }

                # 결과를 못 찾았으면 다음 시간 범위로 fallback
                print(
                    f"[SNS Search Debug] ❌ {period_name}에서 SNS 링크를 찾지 못함 → Fallback 시도"
                )

            except Exception as e:
                print(f"[SearchService] SNS 검색 오류 ({period_name}): {e}")
                continue  # 다음 시간 범위로 이동

        # 모든 시간 범위에서 찾지 못함
        print(f"[SNS Search Debug] ❌ 모든 시간 범위에서 SNS 링크를 찾지 못함")
        return {"found": False}
