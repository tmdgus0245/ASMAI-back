import asyncio

from app.services.embedding_repository import JsonEmbeddingRepository


def test_embedding_repository_saves_and_reads_vectors(tmp_path) -> None:
    repository = JsonEmbeddingRepository(tmp_path)

    result = asyncio.run(
        repository.save(
            document_id="doc",
            model="model",
            chunk_ids=["a", "b"],
            vectors=[[1.0, 0.0], [0.0, 1.0]],
        )
    )
    stored = asyncio.run(repository.read("doc"))

    assert result["dimension"] == 2
    assert result["indexed_count"] == 2
    assert stored["doc"]["chunk_ids"] == ["a", "b"]
