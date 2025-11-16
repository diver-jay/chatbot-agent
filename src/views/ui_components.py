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
                value=st.session_state.get("anthropic_api_key", ""),
                help="Claude API 사용을 위한 Anthropic API 키를 입력하세요",
            )

            # API 키 등록 버튼
            if st.button("API 키 등록"):
                if anthropic_api_key:
                    st.session_state.anthropic_api_key = anthropic_api_key
                    st.session_state.api_key_submitted = True

                    # .env 파일에서 API 키를 읽어와 세션 상태에 저장
                    st.session_state.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
                    st.session_state.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

                    st.success("✅ API 키가 등록되었습니다")
                else:
                    st.error("❌ Anthropic API 키를 입력해주세요")

            st.divider()

            # 커스텀 Tone Prompt 업로드
            st.subheader("커스텀 페르소나 설정")
            uploaded_file = st.file_uploader(
                "Tone Prompt 파일 업로드 (.md)",
                type=["md"],
                help="커스텀 페르소나 tone prompt를 업로드하여 AI의 말투와 성격을 변경할 수 있습니다",
                key="custom_tone_uploader"
            )

            if uploaded_file is not None:
                # 이미 처리된 파일인지 확인 (무한 루프 방지)
                current_uploaded_file = st.session_state.get("last_uploaded_file")

                if current_uploaded_file != uploaded_file.name:
                    # 새로운 파일이 업로드됨
                    # 업로드된 파일 내용 읽기
                    file_content = uploaded_file.read().decode("utf-8")

                    # custom 디렉토리 생성
                    custom_dir = "prompts/custom"
                    os.makedirs(custom_dir, exist_ok=True)

                    # 파일 저장 경로 생성
                    custom_file_path = os.path.join(custom_dir, uploaded_file.name)

                    # 파일 저장
                    with open(custom_file_path, "w", encoding="utf-8") as f:
                        f.write(file_content)

                    # 세션에 커스텀 tone 경로 저장
                    st.session_state.custom_tone_path = custom_file_path
                    st.session_state.last_uploaded_file = uploaded_file.name

                    # 자동으로 대화 초기화 및 인플루언서 설정 화면으로 이동
                    st.session_state.messages = []
                    st.session_state.chat_history = StreamlitChatMessageHistory(
                        key="chat_messages"
                    )
                    st.session_state.setup_complete = False
                    st.session_state.loading = False

                    # 메시지 없이 바로 인플루언서 입력 화면으로 전환
                    st.rerun()

            # 현재 적용된 커스텀 Tone 표시
            if st.session_state.get("custom_tone_path"):
                st.caption(f"📝 현재 커스텀 Tone: {os.path.basename(st.session_state.custom_tone_path)}")
                if st.button("커스텀 Tone 제거"):
                    st.session_state.custom_tone_path = None
                    st.session_state.last_uploaded_file = None
                    st.session_state.messages = []
                    st.session_state.chat_history = StreamlitChatMessageHistory(
                        key="chat_messages"
                    )
                    st.session_state.setup_complete = False
                    st.session_state.loading = False
                    st.rerun()

            st.divider()
            st.caption("© 2025 심심이 스타일 챗봇. Powered by Claude")

    def display_chat_header(self):
        """채팅 헤더를 표시합니다."""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title("💬")
            st.markdown(
                """친한 친구와 대화하는 것처럼 편안하게 이야기해보세요!
        어떤 일상 이야기든 환영이에요 😊"""
            )

    def display_previous_messages(self):
        """저장된 모든 메시지를 표시합니다."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # 어시스턴트 메시지에 SNS 콘텐츠가 있으면 표시
                if message["role"] == "assistant" and "sns_content" in message:
                    sns_content = message["sns_content"]
                    if sns_content and sns_content.get("found"):
                        thumbnail = sns_content.get("thumbnail", "")
                        url = sns_content.get("url", "")
                        platform = sns_content.get("platform", "")

                        if thumbnail:
                            st.markdown(
                                f"""
                                <a href="{url}" target="_blank" style="text-decoration: none;">
                                    <img src="{thumbnail}" width="300" style="border-radius: 8px; cursor: pointer; display: block; transition: opacity 0.2s;">
                                </a>
                                """,
                                unsafe_allow_html=True
                            )

                # 어시스턴트 메시지에 이미지가 있으면 표시 (레거시 지원)
                if message["role"] == "assistant" and "image" in message:
                    if os.path.exists(message["image"]):
                        st.image(message["image"], width=200, caption="😊")

    def get_chat_input(self, placeholder: str = ""):
        """채팅 입력을 받아옵니다."""
        return st.chat_input(placeholder)

    def display_user_message(self, question: str):
        """사용자 메시지를 화면에 표시합니다."""
        with st.chat_message("human", avatar=None):
            st.markdown(question)

    def display_assistant_message(self, message: str):
        """어시스턴트 메시지를 화면에 표시합니다."""
        with st.chat_message("assistant"):
            st.markdown(message)

    def display_assistant_error(self, error_msg: str):
        """어시스턴트 에러 메시지를 화면에 표시합니다."""
        with st.chat_message("assistant"):
            st.error(error_msg)

    def display_assistant_warning(self, warning_msg: str):
        """어시스턴트 경고 메시지를 화면에 표시합니다."""
        with st.chat_message("assistant"):
            st.warning(warning_msg)

    def create_assistant_spinner(self):
        """어시스턴트 메시지 영역에 스피너를 생성하고 placeholder를 반환합니다."""
        chat_message_context = st.chat_message("assistant")
        chat_message_context.__enter__()
        spinner_placeholder = st.empty()
        spinner_placeholder.markdown(
            '<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>',
            unsafe_allow_html=True,
        )
        return chat_message_context, spinner_placeholder

    def display_typing_animation(self, char_count: int):
        """타이핑 애니메이션을 표시하고 placeholder를 반환합니다."""
        import time

        chat_message_context = st.chat_message("assistant")
        chat_message_context.__enter__()
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            '<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>',
            unsafe_allow_html=True,
        )

        # 답변 길이에 따라 동적으로 대기 시간 계산 (최소 0.5초, 최대 2초)
        typing_delay = min(
            max(0.5, char_count / 200), 2
        )  # 200자당 1초, 최소 0.5초, 최대 2초
        time.sleep(typing_delay)

        return chat_message_context, typing_placeholder
