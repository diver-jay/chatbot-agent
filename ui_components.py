import streamlit as st
import os
from langchain_community.chat_message_histories import StreamlitChatMessageHistory


# 사이드바에 API 키 입력 UI
def sidebar_api_input():
    with st.sidebar:
        st.header("API 설정")

        # 이전에 입력한 API 키가 있다면 불러오기
        if 'anthropic_api_key' not in st.session_state:
            st.session_state.anthropic_api_key = ""
            st.session_state.api_key_submitted = False

        # API 키 입력 폼
        with st.form("api_key_form"):
            anthropic_key = st.text_input(
                "Anthropic API 키를 입력하세요",
                type="password",
                value=st.session_state.anthropic_api_key,
                help="API 키는 안전하게 저장되며 서버로 전송되지 않습니다"
            )

            submitted = st.form_submit_button("API 키 등록")
            if submitted:
                if anthropic_key:
                    st.session_state.anthropic_api_key = anthropic_key
                    st.session_state.api_key_submitted = True
                    st.success("API 키가 등록되었습니다!")
                else:
                    st.error("API 키를 입력해주세요")

        # API 키가 등록된 상태 표시
        if st.session_state.get('api_key_submitted', False):
            st.success("✅ API 키 등록 완료")
        else:
            st.warning("⚠️ API 키를 등록해주세요")

        # 키 삭제 버튼
        if st.session_state.get('api_key_submitted', False):
            if st.button("API 키 삭제"):
                st.session_state.anthropic_api_key = ""
                st.session_state.api_key_submitted = False
                st.rerun()

        # 대화 초기화 버튼
        if st.button("대화 초기화"):
            st.session_state.messages = []
            st.session_state.chat_history = StreamlitChatMessageHistory(key="chat_messages")
            st.rerun()

        st.divider()
        st.caption("© 2025 심심이 스타일 챗봇. Powered by Claude")


# 이전 메시지 표시 함수
def display_previous_messages():
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
            # 어시스턴트 메시지에 이미지가 있으면 표시
            if message['role'] == 'assistant' and 'image' in message:
                if os.path.exists(message['image']):
                    st.image(message['image'], width=200, caption="😊")
