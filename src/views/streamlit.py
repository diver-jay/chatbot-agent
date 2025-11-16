import streamlit as st
import time
from langchain_core.runnables.history import RunnableWithMessageHistory

# 분리된 모듈 임포트
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from src.models.model_factory import ChatModelFactory
from src.models.session_manager import StreamlitSessionManager
from src.views.ui_components import StreamlitUIComponent
from src.agents.tone_select_agent import ToneSelectAgent
from src.agents.response_split_agent import ResponseSplitAgent
from src.agents.persona_extract_agent import PersonaExtractAgent
from src.services.search_orchestrator import SearchOrchestrator

# SessionManager 및 UIComponent 인스턴스 생성
session_manager = StreamlitSessionManager()
ui_component = StreamlitUIComponent()


def configure_page():
    """페이지 설정을 구성합니다."""
    st.set_page_config(page_title="심심이 스타일 챗봇", page_icon="😊", layout="wide")


def apply_custom_css():
    """커스텀 스피너 CSS를 적용합니다."""
    st.markdown(
        """
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

/* 사용자 메시지의 아바타 영역 숨기기 */
[data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}

/* SNS 썸네일 hover 효과 */
.stMarkdown a img {
    transition: all 0.3s ease;
}
.stMarkdown a img:hover {
    opacity: 0.8;
    transform: scale(1.02);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_cached_chat_model(model_name, api_key):
    return ChatModelFactory.create_model(model_name, api_key)


@st.cache_data()
def load_cached_prompt(prompt_path, influencer_name=None, persona_context=None):
    """
    지정된 tone 파일 경로로 프롬프트를 로드하고 페르소나를 주입합니다.
    """
    try:
        # 프롬프트 파일 로드
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_content = f.read()

        # ========== 디버깅 로그 추가 ==========
        print("\n" + "=" * 80)
        print("[DEBUG] load_cached_prompt - 프롬프트 로드")
        print("=" * 80)
        print(f"프롬프트 경로: {prompt_path}")
        print(f"인플루언서 이름: {influencer_name}")

        # {chat_histories} 플레이스홀더 체크
        if "{chat_histories}" in prompt_content:
            print("✅ {chat_histories} 플레이스홀더 발견")
        else:
            print("❌ {chat_histories} 플레이스홀더 없음")
        print("=" * 80 + "\n")
        # ========================================

        # 페르소나 정보 주입
        if influencer_name:
            persona_injection = f"\n\n**중요**: 당신은 '{influencer_name}' 본인입니다. 팬들이 '{influencer_name}님 팬이에요' 또는 '{influencer_name} 좋아해요'라고 말하면, {influencer_name}을 제3자로 언급하지 말고 본인의 시점('나')에서 답변하세요.\n"

            # 페르소나 컨텍스트가 있으면 추가
            if persona_context:
                persona_injection += f"\n**당신의 배경 정보**:\n{persona_context}\n\n위 정보를 바탕으로 답변할 때 자연스럽게 활용하세요. 특히 일상 질문이나 최근 근황을 물어볼 때 이 정보를 참고하세요.\n"

            prompt_content = prompt_content + persona_injection
            print(f"[DEBUG] prompt_content:\n{prompt_content}\n")

        return ChatPromptTemplate.from_messages(
            [
                ("system", prompt_content),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
    except FileNotFoundError as e:
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {e}")


def setup_influencer_persona(influencer_name: str):
    """
    인플루언서의 Tone과 페르소나를 설정하고 세션 상태를 업데이트합니다.

    최적화: Tone 선택과 페르소나 추출을 병렬로 실행하여 속도 개선 (4-10초 → 2-5초)

    Args:
        influencer_name: 사용자가 입력한 인플루언서 이름
    """
    from concurrent.futures import ThreadPoolExecutor

    chat_model = load_cached_chat_model(
        "claude-3-7-sonnet-latest", session_manager.get_api_key()
    )
    tone_select_agent = ToneSelectAgent(chat_model)
    persona_extract_agent = PersonaExtractAgent(chat_model)

    # 병렬 실행으로 속도 개선
    with ThreadPoolExecutor(max_workers=2) as executor:
        tone_future = executor.submit(
            tone_select_agent.act, influencer_name=influencer_name
        )
        persona_future = executor.submit(
            persona_extract_agent.act, influencer_name=influencer_name
        )

        tone_future.result()  # Wait for tone selection to complete
        persona_context = persona_future.result()

        tone_file_path = tone_select_agent.get_tone_path()

    # 세션에 인플루언서 이름 및 Tone 정보 저장
    session_manager.save_influencer_setup(
        influencer_name, tone_file_path, persona_context
    )


# 인플루언서 이름 입력 화면
def show_influencer_input_screen():
    """인플루언서 이름 입력 UI를 표시합니다."""
    # 로딩 상태 확인
    if session_manager.is_loading():
        # 로딩 애니메이션을 중앙에 표시
        st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

        influencer_name = session_manager.get_temp_influencer_name()

        # 중앙 정렬된 텍스트와 큰 로딩 애니메이션만 표시
        st.markdown(
            f"""
        <div style="text-align: center;">
            <h2>AI {influencer_name}를 준비중입니다...</h2>
            <br><br>
            <div class="wave-loader-large">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    # 일반 입력 화면
    st.title("🌟 나만의 AI 친구 만들기")
    st.markdown("### 가장 좋아하는 인플루언서의 이름을 써주세요")

    influencer_name = st.text_input(
        "인플루언서 이름",
        placeholder="예: 박사님, 최애, 친구 이름 등...",
        key="influencer_name_input",
        label_visibility="collapsed",
    )

    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        if st.button("시작하기", type="primary", use_container_width=True):
            if influencer_name.strip():
                # 로딩 상태로 전환
                session_manager.set_loading_state(influencer_name)
                st.rerun()
            else:
                st.warning("인플루언서 이름을 입력해주세요!")


def generate_response(question, conversation, search_context, sns_content):
    """
    대화 체인을 통해 응답을 생성합니다.

    Returns:
        str: 생성된 응답
    """
    # 최근 3개의 대화 쌍 가져오기
    recent_turns = session_manager.get_recent_conversation_turns(2)

    # 대화 히스토리 텍스트 생성
    chat_histories = ""
    if recent_turns:
        for idx, turn in enumerate(recent_turns, 1):
            chat_histories += f"[대화 {idx}]\n"
            chat_histories += f"User: {turn['user']}\n"
            chat_histories += f"AI: {turn['ai']}\n\n"

    # ========== 디버깅 로그 ==========
    print("\n" + "=" * 80)
    print("[DEBUG] generate_response - 대화 히스토리 분석")
    print("=" * 80)
    print(f"최근 대화 턴 개수: {len(recent_turns)}")
    print(
        f"\nchat_histories 내용:\n{chat_histories if chat_histories else '(비어있음)'}"
    )
    print("=" * 80 + "\n")
    # ===================================

    # 검색 컨텍스트가 있으면 질문에 추가
    enhanced_question = question + search_context

    # SNS 콘텐츠가 있으면 추가 지시사항 삽입
    if sns_content and sns_content.get("found"):
        platform = sns_content.get("platform", "")
        platform_name = "인스타그램" if platform == "instagram" else "유튜브"

        print(
            f"[Response Generation] ✅ SNS 콘텐츠 발견 → AI에게 {platform_name} 게시물 집중 지시"
        )
        sns_instruction = f"""

[중요 지시사항]
답변은 반드시 위의 {platform_name} 게시물 내용에 대해서만 이야기하세요.
다른 검색 정보는 무시하고, 오직 {platform_name} 게시물 주제에만 집중하세요.

답변 방식:
- 자연스럽게 "{platform_name}에 올렸는데 봤어?", "어제 {platform_name}에 올린 거 있는데~" 같은 표현 사용
- SNS 링크 URL은 절대 출력하지 마세요 (시스템이 자동으로 첨부)
- **매우 간단하게 1-2문장으로만 소개**하고 끝내세요 (상세한 설명은 하지 마세요)
- 예시: "아, 혹시 유튜브에 올린 영상 보셨나요? [주제]에 관한 내용이었어요..." 정도로만 말하고 끝
"""
        enhanced_question += sns_instruction
    else:
        print(f"[Response Generation] ❌ SNS 콘텐츠 없음 → 일반 답변")

    # ========== 최종 전달 파라미터 디버깅 ==========
    print("\n" + "=" * 80)
    print("[DEBUG] conversation.invoke - 최종 전달 파라미터")
    print("=" * 80)
    print(f"enhanced_question 길이: {len(enhanced_question)}")
    print(f"enhanced_question 앞 200자:\n{enhanced_question[:200]}")
    print(f"\nchat_histories가 비어있나? {len(chat_histories) == 0}")
    print(f"chat_histories 길이: {len(chat_histories)}")
    print("=" * 80 + "\n")
    # ===============================================

    result = conversation.invoke(
        {"input": enhanced_question, "chat_histories": chat_histories},
        config={"configurable": {"session_id": "default"}},
    )
    return result.content


def display_response(
    split_parts,
    sns_content,
    is_media_requested,
    ui_component,
    session_manager,
    spinner_context,
    spinner_placeholder,
):
    """
    분할된 응답을 화면에 표시하고 세션에 저장합니다.
    """
    for i, part in enumerate(split_parts):
        if i == 0:
            # 첫 번째 메시지는 스피너를 대체
            spinner_placeholder.markdown(part)
            spinner_context.__exit__(None, None, None)

            # SNS 콘텐츠가 있으면 항상 표시
            if sns_content and sns_content.get("found"):
                platform = sns_content.get("platform", "")
                url = sns_content.get("url", "")
                thumbnail = sns_content.get("thumbnail", "")

                # 썸네일 표시 (Instagram: 이미지만, YouTube: 클릭 가능한 링크)
                if thumbnail:
                    if platform == "instagram":
                        # Instagram: 링크 없이 이미지만 표시
                        st.markdown(
                            f"""
                            <img src="{thumbnail}" width="300" style="border-radius: 8px; display: block;">
                            """,
                            unsafe_allow_html=True,
                        )
                    elif platform == "youtube":
                        # YouTube: 썸네일을 클릭 가능한 링크로 표시
                        st.markdown(
                            f"""
                            <a href="{url}" target="_blank" style="text-decoration: none;">
                                <img src="{thumbnail}" width="300" style="border-radius: 8px; cursor: pointer; display: block; transition: opacity 0.2s;">
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        # 그 외 플랫폼은 표시하지 않음
                        return

                # SNS 콘텐츠와 함께 메시지 저장
                session_manager.add_message("assistant", part, sns_content=sns_content)
            else:
                # SNS 콘텐츠 없이 메시지 저장
                session_manager.add_message("assistant", part)
        else:
            # 두 번째 메시지부터는 타이핑 중 표시 후 새 메시지
            typing_context, typing_placeholder = ui_component.display_typing_animation(
                len(part)
            )
            typing_placeholder.markdown(part)
            typing_context.__exit__(None, None, None)
            session_manager.add_message("assistant", part)


# 메인 애플리케이션 UI
def run_app():
    # 사이드바 표시
    ui_component.sidebar_api_input()

    # 세션 상태 초기화
    session_manager.initialize_session_state()

    # API 키가 등록되지 않은 경우 알림 표시
    if not session_manager.is_api_key_submitted():
        st.info("채팅을 시작하려면 사이드바에서 Anthropic API 키를 등록해주세요.")
        st.chat_input("API 키를 먼저 등록하세요", disabled=True)
        return

    # 인플루언서 이름 입력 화면 표시
    if not session_manager.is_setup_complete():
        show_influencer_input_screen()

        # 로딩 상태일 때 페르소나 설정
        if session_manager.is_loading():
            influencer_name = session_manager.get_temp_influencer_name()
            setup_influencer_persona(influencer_name)
            st.rerun()

        return

    # 채팅 헤더 및 이전 메시지 표시
    ui_component.display_chat_header()

    # 이전 메시지 표시
    ui_component.display_previous_messages()

    # API 모델 로드
    chat_model = load_cached_chat_model(
        "claude-3-7-sonnet-latest", session_manager.get_api_key()
    )

    # SearchOrchestrator 초기화
    orchestrator = SearchOrchestrator(chat_model, session_manager)

    # ResponseSplitAgent 초기화
    response_split_agent = ResponseSplitAgent(chat_model)

    # 선택된 Tone으로 대화 체인 구성
    tone_file_path = session_manager.get_tone_file_path()
    influencer_name = session_manager.get_influencer_name()
    persona_context = session_manager.get_persona_context()

    # tone_file_path, influencer_name, persona_context로 프롬프트 로드
    prompt = load_cached_prompt(tone_file_path, influencer_name, persona_context)

    chain = prompt | chat_model
    conversation = RunnableWithMessageHistory(
        chain,
        session_manager.get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    # 채팅 입력 활성화
    if question := ui_component.get_chat_input(""):
        # 사용자 질문 저장 및 표시
        ui_component.display_user_message(question)
        session_manager.add_message("human", question)

        # 1. 질문 분석 (Orchestrator에 위임)
        orchestrator.analyze_question(question, influencer_name)

        # 2. 검색 실행 (Orchestrator에 위임)
        search_context = ""
        sns_content = None
        if orchestrator.needs_search:
            search_context, sns_content = orchestrator.execute_search(question)

        # 3. 응답 생성 및 표시 (재시도 로직 포함)
        max_retries = 3
        retry_count = 0

        # 스피너를 어시스턴트 메시지 컨텍스트 안에 표시
        spinner_context, spinner_placeholder = ui_component.create_assistant_spinner()
        error_placeholder = st.empty()

        while retry_count < max_retries:
            try:
                # 3-1. 응답 생성
                response = generate_response(
                    question, conversation, search_context, sns_content
                )

                # 3-2. 응답 분할
                split_parts = response_split_agent.act(response=response)

                error_placeholder.empty()

                # 3-3. 응답 표시
                display_response(
                    split_parts,
                    sns_content,
                    orchestrator.is_media_requested,
                    ui_component,
                    session_manager,
                    spinner_context,
                    spinner_placeholder,
                )

                # 3-4. 대화 쌍 저장 (질문 체크용)
                session_manager.add_conversation_turn(question, response)

                break  # 성공하면 반복 중단

            except Exception as e:
                error_text = str(e)
                retry_count += 1
                spinner_placeholder.empty()

                # 오류 타입 확인 및 사용자 친화적 메시지 생성
                if "overloaded_error" in error_text or "529" in error_text:
                    if retry_count < max_retries:
                        with error_placeholder.container():
                            ui_component.display_assistant_warning(
                                f"⚠️ 재시도 중... ({retry_count}/{max_retries})"
                            )
                        time.sleep(2)  # 재시도 전 잠시 대기
                    else:
                        spinner_placeholder.empty()
                        error_placeholder.empty()
                        error_final = "⚠️ 잠시 후 다시 시도해주세요."
                        ui_component.display_assistant_error(error_final)
                        session_manager.add_message("assistant", error_final)
                else:
                    spinner_placeholder.empty()
                    error_msg = f"오류가 발생했습니다: {error_text}"
                    ui_component.display_assistant_error(error_msg)
                    session_manager.add_message("assistant", error_msg)
                    break  # 다른 오류는 재시도하지 않음
