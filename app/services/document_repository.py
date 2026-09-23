import asyncio
import json
import os
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.services.document_chunker import DocumentChunk

StorageStatus = Literal["created", "updated", "unchanged"]


class DocumentRepositoryError(RuntimeError):
    """Raised when the local document store cannot be read or written."""


class JsonDocumentRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.documents_path = data_dir / "documents.json"
        self.chunks_path = data_dir / "chunks.json"
        self._lock = asyncio.Lock()

    async def save(
        self,
        *,
        document_id: str,
        title: str,
        source_url: str,
        text: str,
        content_hash: str,
        paragraph_count: int,
        chunks: Sequence[DocumentChunk],
    ) -> dict[str, str]:
        async with self._lock:
            return await asyncio.to_thread(
                self._save_sync,
                document_id=document_id,
                title=title,
                source_url=source_url,
                text=text,
                content_hash=content_hash,
                paragraph_count=paragraph_count,
                chunks=chunks,
            )

    async def list_documents(self) -> list[dict[str, Any]]:
        async with self._lock:
            return await asyncio.to_thread(self._list_documents_sync)

    async def get_chunks(self, document_id: str) -> list[dict[str, Any]] | None:
        async with self._lock:
            return await asyncio.to_thread(self._get_chunks_sync, document_id)

    def _save_sync(
        self,
        *,
        document_id: str,
        title: str,
        source_url: str,
        text: str,
        content_hash: str,
        paragraph_count: int,
        chunks: Sequence[DocumentChunk],
    ) -> dict[str, str]:
        documents_store = self._read_store(self.documents_path)
        chunks_store = self._read_store(self.chunks_path)
        previous = documents_store["documents"].get(document_id)

        if previous and previous.get("content_hash") == content_hash:
            return {
                "status": "unchanged",
                "document_id": document_id,
                "stored_at": str(previous["stored_at"]),
            }

        stored_at = datetime.now(UTC).isoformat()
        status: StorageStatus = "updated" if previous else "created"
        documents_store["documents"][document_id] = {
            "document_id": document_id,
            "title": title,
            "source_url": source_url,
            "text": text,
            "content_hash": content_hash,
            "char_count": len(text),
            "paragraph_count": paragraph_count,
            "chunk_count": len(chunks),
            "stored_at": stored_at,
        }
        chunks_store["documents"][document_id] = [chunk.to_dict() for chunk in chunks]

        self._write_store(self.documents_path, documents_store)
        self._write_store(self.chunks_path, chunks_store)
        return {
            "status": status,
            "document_id": document_id,
            "stored_at": stored_at,
        }

    def _list_documents_sync(self) -> list[dict[str, Any]]:
        store = self._read_store(self.documents_path)
        documents = list(store["documents"].values())
        return sorted(documents, key=lambda item: str(item.get("stored_at", "")), reverse=True)

    def _get_chunks_sync(self, document_id: str) -> list[dict[str, Any]] | None:
        store = self._read_store(self.chunks_path)
        chunks = store["documents"].get(document_id)
        return list(chunks) if isinstance(chunks, list) else None

    def _read_store(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"version": 1, "documents": {}}

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DocumentRepositoryError(f"저장 파일을 읽지 못했습니다: {path.name}") from exc

        documents = data.get("documents") if isinstance(data, Mapping) else None
        if (
            not isinstance(data, Mapping)
            or data.get("version") != 1
            or not isinstance(documents, Mapping)
        ):
            raise DocumentRepositoryError(f"저장 파일 형식이 올바르지 않습니다: {path.name}")
        return {"version": 1, "documents": dict(documents)}

    def _write_store(self, path: Path, data: Mapping[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary_path, path)
        except OSError as exc:
            raise DocumentRepositoryError(f"저장 파일을 쓰지 못했습니다: {path.name}") from exc
