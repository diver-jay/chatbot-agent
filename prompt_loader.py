from abc import ABC, abstractmethod
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder


class PromptLoader(ABC):
    @abstractmethod
    def load(self):
        pass


class SplitPromptLoader(PromptLoader):
    def __init__(self, file_path="prompts/split_response_prompt.md"):
        self.file_path = file_path

    def load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.file_path} 파일을 찾을 수 없습니다.")


class ToneAwarePromptLoader(PromptLoader):
    """
    단일 프롬프트 파일을 로드하여 시스템 프롬프트를 생성하는 Loader.
    다양한 Tone 스타일의 프롬프트 파일을 지원합니다.

    예시:
    - prompts/converstation_prompt.md (기본 멘토 스타일, 톤앤매너 포함)
    - prompts/tone_influencer_20s.md (20대 인플루언서 스타일)
    - prompts/tone_celebrity_20s.md (20대 연예인 스타일)
    """

    def __init__(self, prompt_path="prompts/converstation_prompt.md"):
        self.prompt_path = prompt_path

    def load(self):
        try:
            # 프롬프트 파일 로드
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                prompt_content = f.read()

            return ChatPromptTemplate.from_messages(
                [
                    ("system", prompt_content),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ]
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {e}")
