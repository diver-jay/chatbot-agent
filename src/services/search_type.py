from enum import Enum, auto

class SearchType(Enum):
    """검색의 종류를 정의하는 열거형 클래스"""
    NO_SEARCH = auto()              # 검색 불필요
    TERM_SEARCH = auto()            # 신조어 검색
    SNS_SEARCH = auto()             # SNS 검색 (일상 질문)
    GENERAL_TOPIC_SEARCH = auto()   # 일반 토픽 검색
