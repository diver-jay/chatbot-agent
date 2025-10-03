import re
from langchain_core.messages import HumanMessage
from prompt_loader import SplitPromptLoader


# 답변을 맥락 단위로 분할하는 함수
def split_response_by_context(response, chat_model):
    """Claude API를 사용하여 답변을 맥락 단위로 분할"""
    try:
        loader = SplitPromptLoader()
        split_prompt = loader.load()
    except FileNotFoundError:
        return [response]  # 프롬프트 로드 실패 시 원본 그대로 반환

    try:
        # 분할 요청을 위한 프롬프트 구성
        split_request = f"{split_prompt}\n\n다음 텍스트를 위 가이드라인에 따라 분할해주세요:\n\n{response}"

        # Claude API 호출
        split_result = chat_model.invoke([HumanMessage(content=split_request)])
        split_text = split_result.content

        # [[SPLIT_N]] 마커를 기준으로 분할
        parts = re.split(r'\[\[SPLIT_\d+\]\]', split_text)
        # 빈 문자열 제거 및 공백 정리
        parts = [part.strip() for part in parts if part.strip()]

        return parts if parts else [response]
    except Exception as e:
        print(f"답변 분할 중 오류 발생: {str(e)}")
        return [response]  # 오류 발생 시 원본 그대로 반환
