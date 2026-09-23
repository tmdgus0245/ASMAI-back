import math
from typing import Any

from app.services.document_repository import JsonDocumentRepository
from app.services.embedding_repository import JsonEmbeddingRepository
from app.services.embedding_service import EmbeddingService


class SearchServiceError(RuntimeError):
    """Raised when a document cannot be indexed or searched."""


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot_product = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot_product / (left_norm * right_norm)


class SearchService:
    def __init__(
        self,
        *,
        documents: JsonDocumentRepository,
        embeddings: JsonEmbeddingRepository,
        embedder: EmbeddingService,
    ) -> None:
        self.documents = documents
        self.embeddings = embeddings
        self.embedder = embedder

    async def index(self, document_id: str) -> dict[str, Any]:
        chunks = await self.documents.get_chunks(document_id)
        if chunks is None:
            raise SearchServiceError("저장된 문서를 찾을 수 없습니다.")

        texts = [str(chunk["text"]) for chunk in chunks]
        vectors = await self.embedder.embed(texts)
        return await self.embeddings.save(
            document_id=document_id,
            model=self.embedder.model_name,
            chunk_ids=[str(chunk["chunk_id"]) for chunk in chunks],
            vectors=vectors,
        )

    async def search(
        self,
        query: str,
        *,
        top_k: int,
        document_id: str | None = None,
    ) -> list[dict[str, Any]]:
        indexes = await self.embeddings.read(document_id)
        if not indexes:
            raise SearchServiceError("검색 인덱스가 없습니다. 먼저 문서를 인덱싱해 주세요.")

        query_vector = (await self.embedder.embed([query]))[0]
        results: list[dict[str, Any]] = []

        for indexed_document_id, index in indexes.items():
            if index.get("model") != self.embedder.model_name:
                continue
            chunks = await self.documents.get_chunks(indexed_document_id)
            if chunks is None:
                continue
            chunks_by_id = {str(chunk["chunk_id"]): chunk for chunk in chunks}

            for chunk_id, vector in zip(
                index.get("chunk_ids", []),
                index.get("vectors", []),
                strict=False,
            ):
                chunk = chunks_by_id.get(str(chunk_id))
                if chunk is None or not isinstance(vector, list):
                    continue
                results.append(
                    {
                        "score": cosine_similarity(query_vector, vector),
                        "chunk": chunk,
                    }
                )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
