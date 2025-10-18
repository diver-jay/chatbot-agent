from dataclasses import dataclass, field
from typing import Optional
from src.services.search_type import SearchType

@dataclass
class AnalysisResult:
    """질문 분석 결과를 담는 데이터 클래스"""
    search_type: SearchType = SearchType.NO_SEARCH
    search_term: Optional[str] = None
    is_media_requested: bool = False
