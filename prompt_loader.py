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

    def __init__(self, prompt_path="prompts/converstation_prompt.md", influencer_name=None, persona_context=None):
        self.prompt_path = prompt_path
        self.influencer_name = influencer_name
        self.persona_context = persona_context

    def load(self):
        try:
            # 프롬프트 파일 로드
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                prompt_content = f.read()

            # 페르소나 정보 주입
            if self.influencer_name:
                persona_injection = f"\n\n**중요**: 당신은 '{self.influencer_name}' 본인입니다. 팬들이 '{self.influencer_name}님 팬이에요' 또는 '{self.influencer_name} 좋아해요'라고 말하면, {self.influencer_name}을 제3자로 언급하지 말고 본인의 시점('나')에서 답변하세요.\n"

                # 페르소나 컨텍스트가 있으면 추가
                if self.persona_context:
                    persona_injection += f"\n**당신의 배경 정보**:\n{self.persona_context}\n\n위 정보를 바탕으로 답변할 때 자연스럽게 활용하세요. 특히 일상 질문이나 최근 근황을 물어볼 때 이 정보를 참고하세요.\n"

                prompt_content = prompt_content + persona_injection
                print(f"[DEBUG] prompt_content:\n{prompt_content}\n")

            return ChatPromptTemplate.from_messages(
                [
                    ("system", prompt_content),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}")
                ]
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {e}")
