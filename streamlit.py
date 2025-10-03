import streamlit as st
import time
from langchain_core.runnables.history import RunnableWithMessageHistory

# 분리된 모듈 임포트
from prompt_loader import ToneAwarePromptLoader
from model_factory import ChatModelFactory
from response_processor import split_response_by_context
# from image_selector import select_image_for_context
from session_manager import get_session_history
from ui_components import sidebar_api_input, display_previous_messages
from tone_selector import ToneSelector

# 페이지 설정
st.set_page_config(
    page_title="심심이 스타일 챗봇",
    page_icon="😊",
    layout="wide"
)

# 커스텀 스피너 CSS
st.markdown("""
<style>
.wave-loader {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 4px;
    padding: 8px 0;
    margin-left: 20px;
}
.wave-loader .dot {
    width: 6px;
    height: 6px;
    background-color: #ff4b4b;
    border-radius: 50%;
    animation: wave 1.2s ease-in-out infinite;
}
.wave-loader .dot:nth-child(1) {
    animation-delay: 0s;
}
.wave-loader .dot:nth-child(2) {
    animation-delay: 0.2s;
}
.wave-loader .dot:nth-child(3) {
    animation-delay: 0.4s;
}
@keyframes wave {
    0%, 60%, 100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-10px);
    }
}

/* 로딩 화면용 큰 wave-loader */
.wave-loader-large {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding: 20px 0;
}
.wave-loader-large .dot {
    width: 20px;
    height: 20px;
    background-color: #ff4b4b;
    border-radius: 50%;
    animation: wave 1.2s ease-in-out infinite;
}
.wave-loader-large .dot:nth-child(1) {
    animation-delay: 0s;
}
.wave-loader-large .dot:nth-child(2) {
    animation-delay: 0.2s;
}
.wave-loader-large .dot:nth-child(3) {
    animation-delay: 0.4s;
}
</style>
""", unsafe_allow_html=True)


# 캐싱된 모델 로드 함수
@st.cache_resource(show_spinner=False)
def load_cached_chat_model(model_name, api_key):
    return ChatModelFactory.create_model(model_name, api_key)


# 캐싱된 프롬프트 로드 함수
@st.cache_data()
def load_cached_prompt(prompt_path):
    """
    지정된 tone 파일 경로로 프롬프트를 로드합니다.

    Args:
        tone_file_path: tone 템플릿 파일 경로
    """
    loader = ToneAwarePromptLoader(prompt_path=prompt_path)
    return loader.load()


# 인플루언서 이름 입력 화면
def show_influencer_input_screen():
    # 로딩 상태 확인
    if st.session_state.get('loading', False):
        # 로딩 애니메이션을 중앙에 표시
        st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

        influencer_name = st.session_state.get('temp_influencer_name', '')

        # 중앙 정렬된 텍스트와 큰 로딩 애니메이션만 표시
        st.markdown(f"""
        <div style="text-align: center;">
            <h2>AI {influencer_name}를 준비중입니다...</h2>
            <br><br>
            <div class="wave-loader-large">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI를 사용하여 Tone 선택
        chat_model = load_cached_chat_model("claude-3-7-sonnet-latest", st.session_state.anthropic_api_key)
        tone_selector = ToneSelector(chat_model)

        # Tone 선택 (로그 자동 출력됨)
        tone_type, tone_file_path = tone_selector.select_tone(influencer_name)

        # 세션에 인플루언서 이름 및 Tone 정보 저장
        st.session_state.influencer_name = influencer_name
        st.session_state.tone_type = tone_type
        st.session_state.tone_file_path = tone_file_path
        st.session_state.setup_complete = True
        st.session_state.loading = False

        st.rerun()
        return

    # 일반 입력 화면
    st.title("🌟 나만의 AI 친구 만들기")
    st.markdown("### 가장 좋아하는 인플루언서의 이름을 써주세요")

    influencer_name = st.text_input(
        "인플루언서 이름",
        placeholder="예: 박사님, 최애, 친구 이름 등...",
        key="influencer_name_input",
        label_visibility="collapsed"
    )

    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        if st.button("시작하기", type="primary", use_container_width=True):
            if influencer_name.strip():
                # 로딩 상태로 전환
                st.session_state.temp_influencer_name = influencer_name.strip()
                st.session_state.loading = True
                st.rerun()
            else:
                st.warning("인플루언서 이름을 입력해주세요!")


# 메인 애플리케이션 UI
def main():
    # 사이드바 표시
    sidebar_api_input()

    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False

    # API 키가 등록되지 않은 경우 알림 표시
    if not st.session_state.get('api_key_submitted', False):
        st.info("채팅을 시작하려면 사이드바에서 Anthropic API 키를 등록해주세요.")
        st.chat_input("API 키를 먼저 등록하세요", disabled=True)
        return

    # 인플루언서 이름 입력 화면 표시
    if not st.session_state.setup_complete:
        show_influencer_input_screen()
        return

    # 메인 컨텐츠
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("심심이 스타일 챗봇 💬")
        st.markdown("""친한 친구와 대화하는 것처럼 편안하게 이야기해보세요!
        어떤 일상 이야기든 환영이에요 😊""")

    # 이전 메시지 표시
    display_previous_messages()

    # API 모델 로드
    chat_model = load_cached_chat_model("claude-3-7-sonnet-latest", st.session_state.anthropic_api_key)

    # 선택된 Tone으로 대화 체인 구성
    tone_file_path = st.session_state.get('tone_file_path', "prompts/converstation_prompt.md")

    # tone_file_path로 프롬프트 로드
    prompt = load_cached_prompt(tone_file_path)

    chain = prompt | chat_model
    conversation = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )

    # 채팅 입력 활성화
    if question := st.chat_input("오늘 뭐했어?"):
        # 사용자 질문 저장 및 표시
        st.session_state.messages.append({"role": "human", "content": question})
        with st.chat_message('human'):
            st.markdown(question)

        # 응답 생성 및 표시
        # 재시도 횟수 설정
        max_retries = 3
        retry_count = 0
        spinner_placeholder = st.empty()
        error_placeholder = st.empty()

        while retry_count < max_retries:
            try:
                # 대화 체인을 통한 응답 생성
                spinner_placeholder.markdown('<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)

                result = conversation.invoke(
                    {"input": question},
                    config={"configurable": {"session_id": "default"}}
                )
                response = result.content

                # # 응답에 맞는 이미지 선택
                # selected_image = select_image_for_context(response)

                # Claude API를 사용하여 답변을 맥락 단위로 분할
                split_parts = split_response_by_context(response, chat_model)

                spinner_placeholder.empty()
                error_placeholder.empty()

                # 분할된 답변을 개별 메시지로 표시
                for i, part in enumerate(split_parts):
                    # 첫 번째 메시지가 아니면 타이핑 중 표시
                    if i > 0:
                        typing_placeholder = st.empty()
                        typing_placeholder.markdown('<div class="wave-loader"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>', unsafe_allow_html=True)
                        time.sleep(4)  # 타이핑 중 시뮬레이션
                        typing_placeholder.empty()

                    with st.chat_message('assistant'):
                        st.markdown(part)

                # # 이미지 표시 (선택된 이미지가 있는 경우)
                # if selected_image:
                #     st.image(selected_image, width=200)

                # 메시지 저장 (이미지 경로도 함께 저장)
                message_data = {"role": "assistant", "content": response}
                # if selected_image:
                #     message_data["image"] = selected_image
                st.session_state.messages.append(message_data)
                break  # 성공하면 반복 중단

            except Exception as e:
                error_text = str(e)
                retry_count += 1
                spinner_placeholder.empty()

                # 오류 타입 확인 및 사용자 친화적 메시지 생성
                if "overloaded_error" in error_text or "529" in error_text:
                    if retry_count < max_retries:
                        with error_placeholder.container():
                            with st.chat_message('assistant'):
                                st.warning(f"⚠️ 재시도 중... ({retry_count}/{max_retries})")
                        time.sleep(2)  # 재시도 전 잠시 대기
                    else:
                        spinner_placeholder.empty()
                        error_placeholder.empty()
                        error_final = "⚠️ 잠시 후 다시 시도해주세요."
                        with st.chat_message('assistant'):
                            st.error(error_final)
                        st.session_state.messages.append({"role": "assistant", "content": error_final})
                else:
                    spinner_placeholder.empty()
                    error_msg = f"오류가 발생했습니다: {error_text}"
                    with st.chat_message('assistant'):
                        st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    break  # 다른 오류는 재시도하지 않음

if __name__ == "__main__":
    main()
