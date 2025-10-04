import streamlit as st
import time
from datetime import datetime
from langchain_core.runnables.history import RunnableWithMessageHistory

# 분리된 모듈 임포트
from src.services.prompt_loader import ToneAwarePromptLoader
from src.models.model_factory import ChatModelFactory
from src.services.response_processor import split_response_by_context
# from src.services.image_selector import select_image_for_context
from src.models.session_manager import StreamlitSessionManager
from src.views.ui_components import StreamlitUIComponent
from src.services.tone_selector import ToneSelector
from src.services.search_service import SearchService
from src.services.term_detector import TermDetector
from src.services.entity_detector import EntityDetector
from src.services.sns_relevance_checker import SNSRelevanceChecker

# SessionManager 및 UIComponent 인스턴스 생성
session_manager = StreamlitSessionManager()
ui_component = StreamlitUIComponent()


def configure_page():
    """페이지 설정을 구성합니다."""
    st.set_page_config(
        page_title="심심이 스타일 챗봇",
        page_icon="😊",
        layout="wide"
    )


def apply_custom_css():
    """커스텀 스피너 CSS를 적용합니다."""
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

/* 사용자 메시지의 아바타 영역 숨기기 */
[data-testid="stChatMessageAvatarUser"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# 캐싱된 모델 로드 함수
@st.cache_resource(show_spinner=False)
def load_cached_chat_model(model_name, api_key):
    return ChatModelFactory.create_model(model_name, api_key)


# 캐싱된 프롬프트 로드 함수
@st.cache_data()
def load_cached_prompt(prompt_path, influencer_name=None, persona_context=None):
    """
    지정된 tone 파일 경로로 프롬프트를 로드합니다.

    Args:
        prompt_path: tone 템플릿 파일 경로
        influencer_name: 인플루언서 이름 (선택사항)
        persona_context: 페르소나 컨텍스트 (선택사항)
    """
    loader = ToneAwarePromptLoader(prompt_path=prompt_path, influencer_name=influencer_name, persona_context=persona_context)
    return loader.load()


def setup_influencer_persona(influencer_name: str):
    """
    인플루언서의 Tone과 페르소나를 설정하고 세션 상태를 업데이트합니다.

    Args:
        influencer_name: 사용자가 입력한 인플루언서 이름
    """
    chat_model = load_cached_chat_model("claude-3-7-sonnet-latest", session_manager.get_api_key())
    tone_selector = ToneSelector(chat_model, session_manager.get_serpapi_key())

    # Tone 선택 (로그 자동 출력됨)
    tone_type, tone_file_path = tone_selector.select_tone(influencer_name)

    # 페르소나 컨텍스트 검색
    persona_context = tone_selector.fetch_persona_context(influencer_name)

    # 세션에 인플루언서 이름 및 Tone 정보 저장
    session_manager.save_influencer_setup(influencer_name, tone_type, tone_file_path, persona_context)


# 인플루언서 이름 입력 화면
def show_influencer_input_screen():
    """인플루언서 이름 입력 UI를 표시합니다."""
    # 로딩 상태 확인
    if session_manager.is_loading():
        # 로딩 애니메이션을 중앙에 표시
        st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

        influencer_name = session_manager.get_temp_influencer_name()

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
                session_manager.set_loading_state(influencer_name)
                st.rerun()
            else:
                st.warning("인플루언서 이름을 입력해주세요!")


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
    chat_model = load_cached_chat_model("claude-3-7-sonnet-latest", session_manager.get_api_key())

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
        history_messages_key="chat_history"
    )

    # 채팅 입력 활성화
    if question := ui_component.get_chat_input(""):
        # 사용자 질문 저장 및 표시
        ui_component.display_user_message(question)
        session_manager.add_message("human", question)

        # 응답 생성 및 표시
        # 재시도 횟수 설정
        max_retries = 3
        retry_count = 0

        # 스피너를 어시스턴트 메시지 컨텍스트 안에 표시
        spinner_context, spinner_placeholder = ui_component.create_assistant_spinner()

        error_placeholder = st.empty()

        # 신조어/모르는 용어 및 인물/사건 감지 및 검색
        search_context = ""
        sns_content = None
        try:
            print(f"\n{'='*60}")
            print(f"[DEBUG] 사용자 질문: {question}")
            print(f"{'='*60}\n")

            # Detector 초기화
            term_detector = TermDetector(chat_model)
            entity_detector = EntityDetector(chat_model)

            # 용어 감지
            term_needs_search, term_search_term = term_detector.detect(question)
            print(f"[TermDetector] 검색 필요: {term_needs_search} | 검색어: {term_search_term}")

            # TermDetector가 신조어를 감지했으면 EntityDetector 건너뛰기
            if term_needs_search:
                print(f"[EntityDetector] ⏭️ 건너뜀 (TermDetector에서 신조어 감지)")
                needs_search = True
                search_term = term_search_term
                is_daily_life = False  # 신조어는 일상 질문 아님
            else:
                # 대화 히스토리 가져오기
                chat_history = st.session_state.get('messages', [])

                # 인물/사건 감지 (influencer_name 및 chat_history 전달)
                entity_needs_search, entity_search_term, is_daily_life, requests_content = entity_detector.detect(
                    question,
                    influencer_name,
                    chat_history
                )
                print(f"[EntityDetector] 검색 필요: {entity_needs_search} | 검색어: {entity_search_term} | 일상: {is_daily_life} | 콘텐츠 요청: {requests_content}")
                needs_search = entity_needs_search
                search_term = entity_search_term

            print(f"[Search Decision] 최종 검색 필요: {needs_search} | 최종 검색어: {search_term} | 일상: {is_daily_life if not term_needs_search else 'N/A'}")

            if needs_search and search_term:
                # 현재 날짜 정보 (KST 기준)
                current_date = datetime.now().strftime("%Y년 %m월 %d일")
                print(f"[Current Date] {current_date}")

                # SearchService 초기화 (SerpAPI 키 및 YouTube API 키 필요)
                serpapi_key = session_manager.get_serpapi_key()
                youtube_key = st.session_state.get('youtube_api_key', None)
                if serpapi_key:
                    search_service = SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
                    print(f"[SearchService] 초기화 완료")

                    # 일상 관련 질문일 때만 SNS 콘텐츠 검색
                    if is_daily_life:
                        print(f"[SNS Search] ✅ 일상 질문 감지 → SNS 검색 시작")

                        # 관련성 검증을 위한 SNSRelevanceChecker 초기화
                        relevance_checker = SNSRelevanceChecker(chat_model)

                        # SNS 콘텐츠 검색 (관련성 검증 포함)
                        sns_content = search_service.search_sns_content(
                            query=search_term,
                            user_question=question,
                            relevance_checker=relevance_checker
                        )
                        print(f"[SNS Search] 검색어: {search_term}")
                        print(f"[SNS Search] 검색 결과: {sns_content}")

                        # SNS 콘텐츠를 찾았으면 (이미 관련성 검증 완료됨)
                        if sns_content and sns_content.get("found"):
                            print(f"[Search] ✅ 관련 SNS 콘텐츠 발견 → SNS 정보 사용")
                            # SNS 게시물 정보만 컨텍스트로 전달
                            platform_name = "Instagram" if sns_content.get("platform") == "instagram" else "YouTube"
                            sns_title = sns_content.get("title", "")
                            search_context = f"\n\n[{platform_name} 게시물 정보]\n{sns_title}\n\n[참고] 오늘 날짜: {current_date}\n"
                            print(f"[Search] SNS 컨텍스트: {search_context}")
                        else:
                            # SNS를 못 찾았으면 일반 검색 수행
                            print(f"[Search] SNS 콘텐츠 없음 → 일반 검색 수행")
                            sns_content = None
                            search_results = search_service.search(search_term)
                            search_summary = search_service.extract_summary(search_results)
                            search_context = f"\n\n[검색 정보: '{search_term}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"
                            print(f"[Search] 검색 완료: {search_context}")
                    else:
                        print(f"[SNS Search] ❌ 일상 질문 아님 → SNS 검색 건너뜀")
                        # 일반 검색만 수행
                        search_results = search_service.search(search_term)
                        search_summary = search_service.extract_summary(search_results)

                        # 신조어 검색인 경우 특별 지시 추가
                        if term_needs_search:
                            search_context = f"\n\n[검색 정보: '{search_term}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n\n[지시사항] 위 검색 정보를 바탕으로 자연스럽게 답변하세요. 검색어('{search_term}')를 그대로 반복하지 말고, 그 의미를 이해한 상태로 대화하세요.\n"
                        else:
                            search_context = f"\n\n[검색 정보: '{search_term}']\n{search_summary}\n\n[참고] 오늘 날짜: {current_date}\n"
                        print(f"[Search] 검색 완료: {search_context}")
                else:
                    print("[Search] SerpAPI 키가 설정되지 않음")

        except Exception as e:
            print(f"[Search] 검색 중 오류: {e}")

        while retry_count < max_retries:
            try:
                # 대화 체인을 통한 응답 생성

                # 검색 컨텍스트가 있으면 질문에 추가
                enhanced_question = question + search_context

                # SNS 콘텐츠가 있으면 추가 지시사항 삽입
                if sns_content and sns_content.get("found"):
                    platform = sns_content.get("platform", "")
                    url = sns_content.get("url", "")
                    sns_title = sns_content.get("title", "")
                    platform_name = "인스타그램" if platform == "instagram" else "유튜브"

                    print(f"[Response Generation] ✅ SNS 콘텐츠 발견 → AI에게 {platform_name} 게시물 집중 지시")
                    sns_instruction = f"""

[중요 지시사항]
답변은 반드시 위의 {platform_name} 게시물 내용에 대해서만 이야기하세요.
다른 검색 정보는 무시하고, 오직 {platform_name} 게시물 주제에만 집중하세요.

답변 방식:
- 자연스럽게 "{platform_name}에 올렸는데 봤어?", "어제 {platform_name}에 올린 거 있는데~" 같은 표현 사용
- SNS 링크 URL은 절대 출력하지 마세요 (시스템이 자동으로 첨부)
- {platform_name} 게시물 내용과 관련된 이야기만 하세요
"""
                    enhanced_question += sns_instruction
                else:
                    print(f"[Response Generation] ❌ SNS 콘텐츠 없음 → 일반 답변")
                
                result = conversation.invoke(
                    {"input": enhanced_question},
                    config={"configurable": {"session_id": "default"}}
                )
                response = result.content

                # # 응답에 맞는 이미지 선택
                # selected_image = select_image_for_context(response)

                # Claude API를 사용하여 답변을 맥락 단위로 분할
                split_parts = split_response_by_context(response, chat_model)

                error_placeholder.empty()

                # 분할된 답변을 개별 메시지로 표시 및 저장
                for i, part in enumerate(split_parts):
                    if i == 0:
                        # 첫 번째 메시지는 스피너를 대체
                        spinner_placeholder.markdown(part)
                        spinner_context.__exit__(None, None, None)

                        # SNS 콘텐츠가 있고, 사용자가 명시적으로 콘텐츠를 요청했을 때만 표시
                        if sns_content and sns_content.get("found") and requests_content:
                            platform = sns_content.get("platform", "")
                            url = sns_content.get("url", "")
                            thumbnail = sns_content.get("thumbnail", "")

                            # 썸네일이 있으면 표시
                            if thumbnail:
                                st.image(thumbnail, use_container_width=False, width=300)

                            # 링크 버튼 표시
                            platform_emoji = "📷" if platform == "instagram" else "🎥"
                            platform_name = "Instagram" if platform == "instagram" else "YouTube"
                            st.markdown(f"{platform_emoji} [{platform_name}에서 보기]({url})")

                            # SNS 콘텐츠와 함께 메시지 저장
                            session_manager.add_message("assistant", part, sns_content=sns_content)
                        else:
                            # SNS 콘텐츠 없이 메시지 저장
                            session_manager.add_message("assistant", part)
                    else:
                        # 두 번째 메시지부터는 타이핑 중 표시 후 새 메시지
                        typing_context, typing_placeholder = ui_component.display_typing_animation(len(part))
                        typing_placeholder.markdown(part)
                        typing_context.__exit__(None, None, None)
                        session_manager.add_message("assistant", part)

                break  # 성공하면 반복 중단

            except Exception as e:
                error_text = str(e)
                retry_count += 1
                spinner_placeholder.empty()

                # 오류 타입 확인 및 사용자 친화적 메시지 생성
                if "overloaded_error" in error_text or "529" in error_text:
                    if retry_count < max_retries:
                        with error_placeholder.container():
                            ui_component.display_assistant_warning(f"⚠️ 재시도 중... ({retry_count}/{max_retries})")
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
