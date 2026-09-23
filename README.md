# ASMAI Backend

앤서시스템 ASM AI 데스크톱 앱을 위한 Python 백엔드입니다. 공개 Notion 문서를 수집하고 로컬 의미 검색을 거쳐 근거가 포함된 채팅 응답을 제공합니다.

## 준비

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

```powershell
uv python install 3.12
uv sync
uv run playwright install chromium
Copy-Item .env.example .env
```

## 실행

```powershell
uv run uvicorn app.main:app --reload
```

서버 실행 후 아래 주소를 사용할 수 있습니다.

- API 문서: <http://127.0.0.1:8000/docs>
- 상태 확인: <http://127.0.0.1:8000/health>
- 채팅 API: `POST http://127.0.0.1:8000/api/v1/chat`
- 공개 Notion 동기화: `POST http://127.0.0.1:8000/api/v1/sync/url`

채팅 요청 예시:

```json
{
  "message": "ASMAI가 무엇인가요?"
}
```

채팅 API는 저장된 임베딩에서 질문과 가까운 문서 청크를 검색하고, 관련 문단과 출처를 함께 반환합니다. 현재 단계는 외부 API 키 없이 실행되는 검색 기반 응답입니다.

응답 예시:

```json
{
  "answer": "문서에서 다음과 같은 관련 내용을 찾았습니다. ...",
  "sources": [
    {
      "title": "EST SECURITY",
      "url": "https://est-tech.notion.site/...",
      "section": "ASM 서버 설치",
      "chunk_id": "...",
      "score": 0.7766
    }
  ]
}
```

공개 Notion 페이지 동기화 요청 예시:

```json
{
  "url": "https://est-tech.notion.site/EST-SECURITY-386fe935d7a78059aecafce8bc5c430b"
}
```

공식 Notion API 토큰 없이 공개 페이지를 Chromium으로 렌더링하고, 접힌 항목을 모두 펼쳐 본문을 수집합니다. Notion 화면 구조가 변경되면 수집 어댑터를 수정해야 할 수 있습니다.

수집된 본문은 검색 전에 자동으로 정제됩니다.

- 제로폭 문자와 불필요한 공백 제거
- Notion 탐색 및 보기 UI 문구 제거
- 페이지 제목 반복 제거
- 바로 이어지는 중복 문단 제거
- 표, 명령어, 제품명에 필요한 비연속 반복은 보존

동기화 응답의 `cleaning` 필드에서 정제 전후 글자 수와 제거된 문단 수를 확인할 수 있습니다.

정제된 본문은 문단 경계를 유지하면서 검색용 청크로 분할됩니다.

- 청크 목표 크기: 약 1,200자
- 문맥 중첩: 최대 약 200자
- 긴 단일 문단: 최대 1,600자 단위로 분할
- 문서 ID, 청크 ID, 순번, 원본 URL, 내용 해시 포함

동기화 응답의 `chunk_count`와 `chunks` 필드에서 생성 결과를 확인할 수 있습니다.

동기화가 완료되면 정제 문서와 청크를 로컬 JSON에 원자적으로 저장합니다.

- `data/documents.json`: 문서 본문, 해시, 동기화 시각
- `data/chunks.json`: 문서별 검색 청크
- 최초 저장: `created`
- 내용 변경: `updated`
- 동일 내용 재수집: `unchanged`

저장 내용 조회:

```text
GET /api/v1/documents
GET /api/v1/documents/{document_id}/chunks
```

## 로컬 의미 검색

한국어를 포함한 다국어 문서를 CPU에서 검색하기 위해 FastEmbed와 `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`를 사용합니다.

문서 인덱싱:

```text
POST /api/v1/search/index/{document_id}
```

검색:

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "ASM 서버 설치 방법",
  "top_k": 5
}
```

임베딩은 `data/embeddings.json`에 저장되고 모델 파일은 `data/models`에 캐시됩니다. 모델은 처음 인덱싱할 때 한 번 다운로드됩니다.

## 검사

```powershell
uv run ruff check .
uv run pytest
```

## 구조

```text
app/
  api/          HTTP 라우트
  core/         설정
  schemas/      요청 및 응답 모델
  services/     비즈니스 로직과 외부 연동 경계
tests/          API 테스트
```
