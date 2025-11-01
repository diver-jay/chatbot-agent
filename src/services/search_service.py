from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any


class SearchService(ABC):

    @abstractmethod
    def search(self, query: str, question: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        pass
