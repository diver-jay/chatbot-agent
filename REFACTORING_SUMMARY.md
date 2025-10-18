# Refactoring Summary

## 개요
챗봇 애플리케이션의 질문 분석 및 검색 로직을 Orchestrator 패턴과 Decorator 패턴을 적용하여 리팩토링

---

## 1. 아키텍처 변경

### 1.1 Orchestrator 패턴 도입
**Before:**
- `perform_search_if_needed()` 함수에서 질문 분석과 검색 실행이 결합됨
- 책임이 명확하게 분리되지 않음

**After:**
- `SearchOrchestrator` 클래스 생성 (`src/services/search_orchestrator.py`)
- 질문 분석(`analyze_question()`)과 검색 실행(`execute_search()`) 분리
- 모든 검색 관련 로직을 중앙에서 관리

**위치:** `src/services/search_orchestrator.py`

```python
class SearchOrchestrator:
    def __init__(self, chat_model, session_manager):
        self.chat_model = chat_model
        self.session_manager = session_manager
        self.term_detector = TermDetector(chat_model)
        self.entity_detector = EntityDetector(chat_model, session_manager)
        self.relevance_checker = SNSRelevanceChecker(chat_model)
        self.search_service = SearchService(...)

    def analyze_question(self, question: str, influencer_name: str):
        # 질문 분석 로직

    def execute_search(self, question: str) -> Tuple[str, Optional[Dict]]:
        # 검색 실행 로직
```

---

### 1.2 Decorator 패턴 적용
**생성된 파일:** `src/utils/decorators.py`

**구현된 데코레이터:**
1. `@log_analysis_result` - 질문 분석 결과 로깅 (현재 미사용)
2. `@retry_on_error` - 오류 시 재시도 (최대 3회, 지수 백오프)
3. `@log_search_execution` - 검색 실행 시간 측정 및 로깅

**적용 위치:**
```python
@retry_on_error(max_attempts=2, delay=2.0)
def _search_general_context(self, search_term: str, ...):
    # 검색 로직

@log_search_execution
def execute_search(self, question: str):
    # 검색 실행
```

---

## 2. 책임 분리 (Single Responsibility Principle)

### 2.1 응답 생성/표시 분리
**Before:**
```python
def generate_and_display_response(question, conversation, search_context, sns_content, ...):
    # 생성 + 표시를 한 함수에서 처리
```

**After:**
```python
def generate_response(question, conversation, search_context, sns_content):
    # 응답 생성만 담당

def display_response(split_parts, sns_content, requests_content, ...):
    # 응답 표시만 담당
```

**위치:** `src/views/streamlit.py`

---

### 2.2 상태 캡슐화

#### QuestionAnalysisResult 제거
**Before:**
- `QuestionAnalysisResult` 데이터클래스가 분석 결과를 반환
- 불필요한 데이터 전달 (`is_term_search`, `is_daily_life` 등)

**After:**
- 모든 분석 상태를 `SearchOrchestrator`의 private 변수로 관리
- `QuestionAnalysisResult` 파일 삭제
- Property를 통한 접근 제공

**Private 상태 변수:**
```python
self._is_term_search = False
self._is_daily_life = False
self._needs_search = False
self._search_term = None
self._requests_content = False

@property
def needs_search(self) -> bool:
    return self._needs_search

@property
def requests_content(self) -> bool:
    return self._requests_content
```

---

## 3. 의존성 주입 (Dependency Injection)

### 3.1 EntityDetector 개선
**Before:**
```python
def detect(self, user_message: str, influencer_name: str, chat_history: List):
    # chat_history를 파라미터로 받음
```

**After:**
```python
class EntityDetector:
    def __init__(self, chat_model, session_manager):
        self.session_manager = session_manager

    def detect(self, user_message: str, influencer_name: str):
        # 내부에서 session_manager를 통해 history 조회
        chat_history = self.session_manager.get_chat_history()
```

**위치:** `src/services/entity_detector.py`

---

### 3.2 SearchService 초기화 개선
**Before:**
```python
def _get_search_service(self) -> Optional[SearchService]:
    # 매번 새로운 인스턴스 생성
    serpapi_key = self.session_manager.get_serpapi_key()
    youtube_key = st.session_state.get('youtube_api_key', None)
    return SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
```

**After:**
```python
def __init__(self, chat_model, session_manager):
    # 초기화 시 한 번만 생성
    serpapi_key = session_manager.get_serpapi_key()
    youtube_key = session_manager.get_youtube_api_key()
    self.search_service = SearchService(api_key=serpapi_key, youtube_api_key=youtube_key)
```

---

## 4. SessionManager 확장

### 4.1 새로운 메서드 추가
**위치:** `src/models/session_manager.py`

```python
@abstractmethod
def get_youtube_api_key(self):
    """YouTube API 키를 반환합니다."""
    pass

@abstractmethod
def get_chat_history(self):
    """대화 히스토리를 반환합니다."""
    pass
```

**구현:**
```python
def get_youtube_api_key(self):
    return st.session_state.get('youtube_api_key', None)

def get_chat_history(self):
    return st.session_state.get('messages', [])
```

---

## 5. 검색 로직 개선

### 5.1 Early Return 패턴
**Before:**
```python
def execute_search(self, question: str):
    if not self._needs_search:
        return "", None
    # 검색 로직
```

**After:**
```python
# streamlit.py
if orchestrator.needs_search:
    search_context, sns_content = orchestrator.execute_search(question)
else:
    search_context = ""
    sns_content = None
```

**개선점:** 검색 필요 여부 판단을 호출부에서 처리하여 책임 명확화

---

### 5.2 시간 필터 Fallback 추가
**위치:** `src/services/search_service.py`

**Before:**
```python
def search(self, query: str, num_results: int = 3):
    # 단일 검색만 수행
```

**After:**
```python
def search(self, query: str, num_results: int = 3, time_filter: Optional[str] = None):
    time_filters = ["qdr:m3", "qdr:m6", "qdr:y", None]  # 3개월 → 6개월 → 1년 → 전체

    for tbs in time_filters:
        result = # SerpAPI 호출
        if result has organic_results:
            return result

    return {"error": "모든 시간 필터에서 검색 결과를 찾을 수 없습니다."}
```

**개선점:** 검색 결과가 없을 때 자동으로 시간 범위를 확장하여 재시도

---

### 5.3 신조어 검색 개선
**Before:**
```python
if term_needs_search:
    self._search_term = term_search_term  # "금쪽이"
    self._requests_content = False
```

**After:**
```python
if term_needs_search:
    # 검색어 확장: 인플루언서 이름 + 전체 질문
    enhanced_term = f"{influencer_name} {question}".strip()
    self._search_term = enhanced_term  # "오은영 최근에 이상인 금쪽이 영상..."

    # 콘텐츠 요청 여부 확인
    requests_content = self.entity_detector._check_content_request(question)
    self._requests_content = requests_content
```

**개선점:**
- 신조어만 검색하는 게 아니라 전체 컨텍스트를 포함하여 검색 정확도 향상
- 콘텐츠 요청 감지를 통해 영상/링크 표시 가능

---

## 6. 로깅 개선

### 6.1 상세한 디버그 로깅 추가

**위치:** `src/services/search_orchestrator.py`, `src/services/search_service.py`

**추가된 로그:**
1. **analyze_question():**
   ```
   [Analyze Question] 사용자 질문: ...
   [Analyze Question] 인플루언서: ...
   ✅ 신조어 검색 모드 활성화
   [Analyze Question] 원본 신조어: '...' → 확장 검색어: '...'
   [Analyze Question] 최종 상태 - needs_search: ..., search_term: ..., ...
   ```

2. **execute_search():**
   ```
   [Execute Search] 검색 시작
   [Execute Search] search_term: ...
   [Execute Search] is_term_search: ...
   → 신조어/용어 검색 경로
   ```

3. **search_service.py:**
   ```
   [Search Service] 검색 시작
   [Search Service] SerpAPI 응답 keys: [...]
   [Search Service] organic_results 개수: N
   [Search Service] 상위 결과 제목:
     [1] 제목1
     [2] 제목2
   ```

---

### 6.2 불필요한 주석 제거
**대상 파일:** 모든 Python 파일

**제거된 주석:**
- 코드를 단순 반복 설명하는 주석
- 명백한 코드를 설명하는 주석 (예: `# 초기화`, `# 리턴`)
- 구분선 주석

**유지된 주석:**
- Docstrings
- 복잡한 로직 설명
- TODO/FIXME/NOTE
- 주석 처리된 코드

---

## 7. 코드 스타일

### 7.1 VS Code 설정 추가
**파일:** `.vscode/settings.json`

```json
{
  "editor.formatOnSave": true,
  "editor.tabSize": 2,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.insertSpaces": true
  }
}
```

---

## 8. 삭제된 파일
- `src/models/question_analysis_result.py` - 더 이상 필요 없음 (상태 캡슐화로 대체)

---

## 9. 주요 파일 변경 요약

### 새로 생성된 파일:
- `src/services/search_orchestrator.py` - Orchestrator 패턴 구현
- `src/utils/decorators.py` - Decorator 패턴 구현
- `.vscode/settings.json` - 코드 포맷 설정

### 대폭 수정된 파일:
- `src/views/streamlit.py` - Orchestrator 사용, 함수 분리
- `src/services/entity_detector.py` - 의존성 주입
- `src/services/search_service.py` - 시간 필터 fallback, 로깅
- `src/models/session_manager.py` - 메서드 추가

### 소폭 수정된 파일:
- 모든 Python 파일 - 불필요한 주석 제거

---

## 10. 리팩토링 효과

### 개선 사항:
✅ **관심사 분리**: 분석/검색/표시 로직이 명확히 분리됨
✅ **재사용성**: SearchOrchestrator를 다른 곳에서도 사용 가능
✅ **테스트 용이성**: 각 컴포넌트를 독립적으로 테스트 가능
✅ **유지보수성**: 로직 변경 시 영향 범위가 명확함
✅ **확장성**: 새로운 검색 타입 추가가 용이함
✅ **디버깅**: 상세한 로그로 문제 파악이 쉬움
✅ **성능**: SearchService 재사용으로 인스턴스 생성 오버헤드 감소

### 기능 개선:
✅ 시간 필터 자동 fallback (3개월 → 6개월 → 1년 → 전체)
✅ 신조어 검색 시 전체 컨텍스트 활용
✅ 신조어 검색에서도 콘텐츠 요청 감지
✅ 더 정확한 검색어 생성

---

## 11. 패턴 적용 요약

| 패턴 | 적용 위치 | 효과 |
|------|----------|------|
| **Orchestrator** | SearchOrchestrator | 복잡한 워크플로우 관리 |
| **Decorator** | 로깅, 재시도 | 횡단 관심사 분리 |
| **Dependency Injection** | EntityDetector, SearchService | 결합도 감소 |
| **Single Responsibility** | generate_response, display_response | 책임 명확화 |
| **Early Return** | streamlit.py | 가독성 향상 |
| **Encapsulation** | Private 변수 + Property | 상태 은닉 |

---

## 12. 향후 개선 가능 사항

1. **TermDetector도 의존성 주입 적용** (현재는 미적용)
2. **ResponseProcessor도 Orchestrator 패턴 적용 고려**
3. **통합 테스트 코드 작성**
4. **로깅 레벨 설정 추가** (DEBUG, INFO, WARNING 등)
5. **설정 파일로 시간 필터 범위 관리**
