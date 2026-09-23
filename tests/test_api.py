from fastapi.testclient import TestClient

from app.main import app
from app.services.chats import chat_service

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "local"}


class FakeSearchService:
    async def search(self, query: str, *, top_k: int) -> list[dict[str, object]]:
        assert query == "ASM 설치 방법"
        assert top_k == 3
        return [
            {
                "score": 0.87654,
                "chunk": {
                    "chunk_id": "doc-1-0",
                    "title": "ASM 기술지원",
                    "section": "서버 설치",
                    "source_url": "https://notion.site/asm",
                    "text": "ASM 서버 설치 방법입니다.\n\n설치 파일을 실행하고 안내를 따릅니다.",
                },
            }
        ]


def test_chat_returns_grounded_response(monkeypatch) -> None:
    monkeypatch.setattr(chat_service, "search", FakeSearchService())

    response = client.post("/api/v1/chat", json={"message": "ASM 설치 방법"})

    assert response.status_code == 200
    body = response.json()
    assert "ASM 서버 설치 방법입니다." in body["answer"]
    assert body["sources"] == [
        {
            "title": "ASM 기술지원",
            "url": "https://notion.site/asm",
            "section": "서버 설치",
            "chunk_id": "doc-1-0",
            "score": 0.8765,
        }
    ]
