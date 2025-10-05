import time
from typing import Callable, Any


def log_analysis_result(analysis_type: str) -> Callable:
    """질문 분석 메서드의 결과를 로깅하는 데코레이터 팩토리.

    Note: 이 데코레이터는 현재 사용되지 않음 (SearchOrchestrator가 내부 상태로 관리)
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            print(f"\n{'='*60}")
            print(f"[{analysis_type} Analysis START]")
            print(f"{'='*60}")

            result = func(*args, **kwargs)

            print(f"[{analysis_type} Analysis END] 완료")
            print(f"{'='*60}\n")

            return result

        return wrapper

    return decorator


def retry_on_error(max_attempts: int = 3, delay: float = 2.0) -> Callable:
    """오류 발생 시 재시도하는 데코레이터 팩토리."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            method_name = func.__name__
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_text = str(e)

                    if attempt < max_attempts:
                        print(
                            f"⚠️ [{method_name}] 오류 발생. 재시도 ({attempt}/{max_attempts}): {error_text}"
                        )
                        time.sleep(delay)
                    else:
                        print(f"❌ [{method_name}] 최대 재시도 횟수 초과: {error_text}")
                        raise

        return wrapper

    return decorator


def log_search_execution(func: Callable) -> Callable:
    """검색 실행 시간을 측정하고 결과를 로깅하는 데코레이터."""

    def wrapper(*args, **kwargs) -> Any:
        # self, question 순서로 전달됨
        question = args[1] if len(args) > 1 else kwargs.get("question", "Unknown")

        start_time = time.time()

        print(f"\n🔍 [Search Orchestration START] - 질문: '{question[:50]}...'")

        try:
            result = func(*args, **kwargs)

            end_time = time.time()
            duration = end_time - start_time

            search_context = result[0][:50] + "..." if result[0] else "N/A"
            sns_found = bool(result[1] and result[1].get("found"))

            print(
                f"✅ [Search Orchestration END] - 성공 | 시간: {duration:.2f}s | SNS 발견: {sns_found}\n"
            )

            return result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(
                f"❌ [Search Orchestration FAILED] - 오류: {e} | 시간: {duration:.2f}s\n"
            )
            raise

    return wrapper
