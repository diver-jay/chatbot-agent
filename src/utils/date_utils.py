from datetime import datetime


def get_formatted_current_date() -> str:
    """현재 날짜를 "YYYY년 mm월 dd일" 형식의 문자열로 반환합니다."""
    return datetime.now().strftime("%Y년 %m월 %d일")
