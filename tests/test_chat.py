import asyncio

from app.schemas.chat import ChatRequest
from app.services.chat import ChatService


class FakeSearch:
    async def search(self, query: str, *, top_k: int) -> list[dict[str, object]]:
        return [
            {
                "score": 0.8,
                "chunk": {
                    "chunk_id": "one",
                    "title": "기술지원",
                    "section": "로그 수집",
                    "source_url": "https://example.com/docs",
                    "text": (
                        "일반 안내 문단입니다.\n\n장애 로그 수집 경로는 제품 설정에서 확인합니다."
                    ),
                },
            }
        ]


def test_reply_selects_query_related_paragraph() -> None:
    service = ChatService(search=FakeSearch(), top_k=3, max_excerpt_chars=100)  # type: ignore[arg-type]

    response = asyncio.run(service.reply(ChatRequest(message="장애 로그 수집 경로")))

    assert response.sources[0].section == "로그 수집"
    assert "장애 로그 수집 경로" in response.answer
