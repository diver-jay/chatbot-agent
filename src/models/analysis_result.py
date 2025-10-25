from dataclasses import dataclass
from typing import Optional, Literal

QueryType = Literal["TERM_SEARCH", "SNS_SEARCH", "GENERAL_SEARCH", "NO_SEARCH"]


@dataclass
class AnalysisResult:
    query_type: QueryType
    query: Optional[str]
    is_daily_life: bool
    is_media_requested: bool
    reason: str
