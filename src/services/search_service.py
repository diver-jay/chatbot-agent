from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any


class SearchService(ABC):
    """검색 서비스에 대한 인터페이스"""

    @abstractmethod
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        pass
