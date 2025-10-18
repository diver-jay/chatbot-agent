from datetime import datetime

def get_formatted_date(date_to_format: datetime) -> str:
    """Formats a datetime object into a "YYYY년 mm월 dd일" string."""
    return date_to_format.strftime("%Y년 %m월 %d일")