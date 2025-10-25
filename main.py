"""
심심이 스타일 챗봇 - 메인 진입점

실행 방법:
    streamlit run main.py
"""

from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 코드는 다른 모듈이 import 되기 전에 실행되어야 합니다.
load_dotenv()

from src.views.streamlit import configure_page, apply_custom_css, run_app


def main():
    configure_page()
    apply_custom_css()

    run_app()


if __name__ == "__main__":
    main()
