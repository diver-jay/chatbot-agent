from typing import Tuple, Optional, Dict, Any

from src.services.search_service import SearchService
from src.utils.logger import log


class NoSearchService(SearchService):

    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        log(self.__class__.__name__, "→ 검색 필요 없음 경로")
        return "", None
