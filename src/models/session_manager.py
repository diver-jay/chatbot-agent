import streamlit as st
from abc import ABC, abstractmethod
from langchain_community.chat_message_histories import StreamlitChatMessageHistory


class SessionManager(ABC):
    """세션 상태 관리 인터페이스"""

    @abstractmethod
    def get_session_history(self):
        """메시지 히스토리를 반환합니다."""
        pass

    @abstractmethod
    def initialize_session_state(self):
        """세션 상태를 초기화합니다."""
        pass

    @abstractmethod
    def save_influencer_setup(
        self,
        influencer_name: str,
        tone_type: str,
        tone_file_path: str,
        persona_context: str,
    ):
        """인플루언서 설정을 세션에 저장합니다."""
        pass

    @abstractmethod
    def set_loading_state(self, influencer_name: str):
        """로딩 상태로 전환합니다."""
        pass

    @abstractmethod
    def add_message(self, role: str, content: str, sns_content=None):
        """메시지를 세션에 추가합니다."""
        pass

    @abstractmethod
    def get_api_key(self):
        """Anthropic API 키를 반환합니다."""
        pass

    @abstractmethod
    def get_serpapi_key(self):
        """SerpAPI 키를 반환합니다."""
        pass

    @abstractmethod
    def get_youtube_api_key(self):
        """YouTube API 키를 반환합니다."""
        pass

    @abstractmethod
    def is_api_key_submitted(self):
        """API 키 제출 여부를 반환합니다."""
        pass

    @abstractmethod
    def is_setup_complete(self):
        """인플루언서 설정 완료 여부를 반환합니다."""
        pass

    @abstractmethod
    def is_loading(self):
        """로딩 상태 여부를 반환합니다."""
        pass

    @abstractmethod
    def get_temp_influencer_name(self):
        """임시 인플루언서 이름을 반환합니다."""
        pass

    @abstractmethod
    def get_tone_file_path(self):
        """Tone 파일 경로를 반환합니다."""
        pass

    @abstractmethod
    def get_influencer_name(self):
        """인플루언서 이름을 반환합니다."""
        pass

    @abstractmethod
    def get_persona_context(self):
        """페르소나 컨텍스트를 반환합니다."""
        pass

    @abstractmethod
    def get_chat_history(self):
        """대화 히스토리를 반환합니다."""
        pass


class StreamlitSessionManager(SessionManager):
    """Streamlit 기반 세션 상태 관리 구현체"""

    def get_session_history(self):
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = StreamlitChatMessageHistory(
                key="chat_messages"
            )
        return st.session_state.chat_history

    def initialize_session_state(self):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "setup_complete" not in st.session_state:
            st.session_state.setup_complete = False

    def save_influencer_setup(
        self,
        influencer_name: str,
        tone_type: str,
        tone_file_path: str,
        persona_context: str,
    ):
        st.session_state.influencer_name = influencer_name
        st.session_state.tone_type = tone_type
        st.session_state.tone_file_path = tone_file_path
        st.session_state.persona_context = persona_context
        st.session_state.setup_complete = True
        st.session_state.loading = False

    def set_loading_state(self, influencer_name: str):
        st.session_state.temp_influencer_name = influencer_name.strip()
        st.session_state.loading = True

    def add_message(self, role: str, content: str, sns_content=None):
        message = {"role": role, "content": content}
        if sns_content:
            message["sns_content"] = sns_content
        st.session_state.messages.append(message)

    def get_api_key(self):
        return st.session_state.anthropic_api_key

    def get_serpapi_key(self):
        return st.session_state.get("serpapi_api_key", None)

    def get_youtube_api_key(self):
        return st.session_state.get("youtube_api_key", None)

    def is_api_key_submitted(self):
        return st.session_state.get("api_key_submitted", False)

    def is_setup_complete(self):
        return st.session_state.setup_complete

    def is_loading(self):
        return st.session_state.get("loading", False)

    def get_temp_influencer_name(self):
        return st.session_state.get("temp_influencer_name", "")

    def get_tone_file_path(self):
        return st.session_state.get("tone_file_path", "prompts/tone_mentor.md")

    def get_influencer_name(self):
        return st.session_state.get("influencer_name", None)

    def get_persona_context(self):
        return st.session_state.get("persona_context", None)

    def get_chat_history(self):
        return st.session_state.get("messages", [])
