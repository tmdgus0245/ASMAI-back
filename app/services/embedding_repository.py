import asyncio
import json
import os
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class EmbeddingRepositoryError(RuntimeError):
    """Raised when the local embedding index cannot be read or written."""


class JsonEmbeddingRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.path = data_dir / "embeddings.json"
        self._lock = asyncio.Lock()

    async def save(
        self,
        *,
        document_id: str,
        model: str,
        chunk_ids: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> dict[str, Any]:
        if len(chunk_ids) != len(vectors):
            raise EmbeddingRepositoryError("청크와 임베딩 개수가 일치하지 않습니다.")
        async with self._lock:
            return await asyncio.to_thread(
                self._save_sync,
                document_id=document_id,
                model=model,
                chunk_ids=chunk_ids,
                vectors=vectors,
            )

    async def read(self, document_id: str | None = None) -> dict[str, Any]:
        async with self._lock:
            return await asyncio.to_thread(self._read_sync, document_id)

    def _save_sync(
        self,
        *,
        document_id: str,
        model: str,
        chunk_ids: Sequence[str],
        vectors: Sequence[Sequence[float]],
    ) -> dict[str, Any]:
        store = self._read_store()
        indexed_at = datetime.now(UTC).isoformat()
        dimension = len(vectors[0]) if vectors else 0
        store["documents"][document_id] = {
            "document_id": document_id,
            "model": model,
            "dimension": dimension,
            "indexed_at": indexed_at,
            "chunk_ids": list(chunk_ids),
            "vectors": [list(vector) for vector in vectors],
        }
        self._write_store(store)
        return {
            "document_id": document_id,
            "model": model,
            "dimension": dimension,
            "indexed_count": len(chunk_ids),
            "indexed_at": indexed_at,
        }

    def _read_sync(self, document_id: str | None) -> dict[str, Any]:
        documents = self._read_store()["documents"]
        if document_id is None:
            return dict(documents)
        item = documents.get(document_id)
        return {document_id: item} if isinstance(item, Mapping) else {}

    def _read_store(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "documents": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EmbeddingRepositoryError("임베딩 저장 파일을 읽지 못했습니다.") from exc

        documents = data.get("documents") if isinstance(data, Mapping) else None
        if (
            not isinstance(data, Mapping)
            or data.get("version") != 1
            or not isinstance(documents, Mapping)
        ):
            raise EmbeddingRepositoryError("임베딩 저장 파일 형식이 올바르지 않습니다.")
        return {"version": 1, "documents": dict(documents)}

    def _write_store(self, data: Mapping[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False),
                encoding="utf-8",
            )
            os.replace(temporary_path, self.path)
        except OSError as exc:
            raise EmbeddingRepositoryError("임베딩 저장 파일을 쓰지 못했습니다.") from exc
