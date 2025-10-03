from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI


class ChatModelFactory:
    @staticmethod
    def create_model(model_name, api_key):
        if not api_key:
            return None

        if model_name.startswith("claude"):
            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=api_key,
                max_tokens=64000
            )
        elif model_name.startswith("gemini"):
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.7
            )
        else:
            raise ValueError(f"Unsupported model: {model_name}")
