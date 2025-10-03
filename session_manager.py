import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory


# 메시지 히스토리 초기화 함수
def get_session_history():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = StreamlitChatMessageHistory(key="chat_messages")
    return st.session_state.chat_history
