import streamlit as st
import os
from abc import ABC, abstractmethod
from langchain_community.chat_message_histories import StreamlitChatMessageHistory


class UIComponent(ABC):
    """UI 컴포넌트 인터페이스"""

    @abstractmethod
    def sidebar_api_input(self):
        """사이드바 API 입력을 처리합니다."""
        pass

    @abstractmethod
    def display_chat_header(self):
        """채팅 헤더를 표시합니다."""
        pass

    @abstractmethod
    def display_previous_messages(self):
        """저장된 모든 메시지를 표시합니다."""
        pass

    @abstractmethod
    def get_chat_input(self, placeholder: str = ""):
        """채팅 입력을 받아옵니다."""
        pass

    @abstractmethod
    def display_user_message(self, question: str):
        """사용자 메시지를 화면에 표시합니다."""
        pass

    @abstractmethod
    def display_assistant_message(self, message: str):
        """어시스턴트 메시지를 화면에 표시합니다."""
        pass

    @abstractmethod
    def display_assistant_error(self, error_msg: str):
        """어시스턴트 에러 메시지를 화면에 표시합니다."""
        pass

    @abstractmethod
    def display_assistant_warning(self, warning_msg: str):
        """어시스턴트 경고 메시지를 화면에 표시합니다."""
        pass

    @abstractmethod
    def create_assistant_spinner(self):
        """어시스턴트 메시지 영역에 스피너를 생성하고 placeholder를 반환합니다."""
        pass

    @abstractmethod
    def display_typing_animation(self, char_count: int):
        """타이핑 애니메이션을 표시하고 placeholder를 반환합니다."""
        pass


class StreamlitUIComponent(UIComponent):
    """Streamlit 기반 UI 컴포넌트 구현체"""

    def sidebar_api_input(self):
        with st.sidebar:
            st.header("API 설정")

            # Anthropic API 키 입력
            anthropic_api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=st.session_state.get('anthropic_api_key', ''),
                help="Claude API 사용을 위한 Anthropic API 키를 입력하세요"
            )

            # SerpAPI 키 입력
            serpapi_api_key = st.text_input(
                "SerpAPI Key",
                type="password",
                value=st.session_state.get('serpapi_api_key', ''),
                help="검색 기능 사용을 위한 SerpAPI 키를 입력하세요"
            )

            # API 키 저장
            if anthropic_api_key:
                st.session_state.anthropic_api_key = anthropic_api_key
                st.session_state.api_key_submitted = True

            if serpapi_api_key:
                st.session_state.serpapi_api_key = serpapi_api_key

            # 대화 초기화 버튼
            if st.button("대화 초기화"):
                st.session_state.messages = []
                st.session_state.chat_history = StreamlitChatMessageHistory(key="chat_messages")
                st.rerun()

            st.divider()
            st.caption("© 2025 심심이 스타일 챗봇. Powered by Claude")

    def display_chat_header(self):
        """채팅 헤더를 표시합니다."""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title("💬")
            st.markdown("""친한 친구와 대화하는 것처럼 편안하게 이야기해보세요!
        어떤 일상 이야기든 환영이에요 😊""")

    def display_previous_messages(self):
        """저장된 모든 메시지를 표시합니다."""
        for message in st.session_state.messages:
            with st.chat_message(message['role']):
                st.markdown(message['content'])
                # 어시스턴트 메시지에 이미지가 있으면 표시
                if message['role'] == 'assistant' and 'image' in message:
                    if os.path.exists(message['image']):
                        st.image(message['image'], width=200, caption="😊")

    def get_chat_input(self, placeholder: str = ""):
        """채팅 입력을 받아옵니다."""
        return st.chat_input(placeholder)

    def display_user_message(self, question: str):
        """사용자 메시지를 화면에 표시합니다."""
        with st.chat_message('human', avatar=None):
            st.markdown(question)

    def display_assistant_message(self, message: str):
        """어시스턴트 메시지를 화면에 표시합니다."""
        with st.chat_message('assistant'):
            st.markdown(message)

    def display_assistant_error(self, error_msg: str):
        """어시스턴트 에러 메시지를 화면에 표시합니다."""
        with st.chat_message('assistant'):
            st.error(error_msg)

    def display_assistant_warning(self, warning_msg: str):
        """어시스턴트 경고 메시지를 화면에 표시합니다."""
        with st.chat_message('assistant'):
            st.warning(warning_msg)

    def create_assistant_spinner(self):
        """어시스턴트 메시지 영역에 스피너를 생성하고 placeholder를 반환합니다."""
        chat_message_context = st.chat_message('assistant')
        chat_message_context.__enter__()
        spinner_placeholder = st.empty()
        spinner_placeholder.markdown('<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)
        return chat_message_context, spinner_placeholder

    def display_typing_animation(self, char_count: int):
        """타이핑 애니메이션을 표시하고 placeholder를 반환합니다."""
        import time

        chat_message_context = st.chat_message('assistant')
        chat_message_context.__enter__()
        typing_placeholder = st.empty()
        typing_placeholder.markdown('<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)

        # 답변 길이에 따라 동적으로 대기 시간 계산 (최소 4초, 최대 10초)
        typing_delay = min(max(4, char_count / 50), 10)  # 50자당 1초, 최소 4초, 최대 10초
        time.sleep(typing_delay)

        return chat_message_context, typing_placeholder
