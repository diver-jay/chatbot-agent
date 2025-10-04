"""
심심이 스타일 챗봇 - 메인 진입점

실행 방법:
    streamlit run main.py
"""

from src.views.streamlit import configure_page, apply_custom_css, run_app


def main():
    """메인 애플리케이션 진입점"""
    # 페이지 설정
    configure_page()

    # 커스텀 CSS 적용
    apply_custom_css()

    # 애플리케이션 실행
    run_app()


if __name__ == "__main__":
    main()
