import asyncio

from app.services.document_chunker import DocumentChunk
from app.services.document_repository import JsonDocumentRepository
from app.services.embedding_repository import JsonEmbeddingRepository
from app.services.search import SearchService, cosine_similarity


class FakeEmbedder:
    model_name = "fake-model"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "설치" in text else [0.0, 1.0] for text in texts]


def make_chunk(chunk_id: str, text: str, index: int) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="doc",
        index=index,
        title="문서",
        section="문서",
        source_url="https://notion.site/page",
        text=text,
        char_count=len(text),
        content_hash=f"hash-{index}",
    )


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_search_returns_most_similar_chunk_first(tmp_path) -> None:
    documents = JsonDocumentRepository(tmp_path)
    embeddings = JsonEmbeddingRepository(tmp_path)
    service = SearchService(
        documents=documents,
        embeddings=embeddings,
        embedder=FakeEmbedder(),  # type: ignore[arg-type]
    )
    chunks = [
        make_chunk("install", "설치 방법", 0),
        make_chunk("logs", "로그 수집", 1),
    ]
    asyncio.run(
        documents.save(
            document_id="doc",
            title="문서",
            source_url="https://notion.site/page",
            text="설치 방법\n\n로그 수집",
            content_hash="hash",
            paragraph_count=2,
            chunks=chunks,
        )
    )
    asyncio.run(service.index("doc"))

    results = asyncio.run(service.search("설치 오류", top_k=2))

    assert results[0]["chunk"]["chunk_id"] == "install"
    assert results[0]["score"] == 1.0
