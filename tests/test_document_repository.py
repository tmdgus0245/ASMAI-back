import asyncio
import json

from app.services.document_chunker import DocumentChunk
from app.services.document_repository import JsonDocumentRepository


def make_chunk(text: str, *, index: int = 0) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=f"doc-{index}",
        document_id="doc",
        index=index,
        title="문서",
        section="문서",
        source_url="https://notion.site/page",
        text=text,
        char_count=len(text),
        content_hash=f"hash-{index}",
    )


def save(repository: JsonDocumentRepository, text: str, content_hash: str) -> dict[str, str]:
    return asyncio.run(
        repository.save(
            document_id="doc",
            title="문서",
            source_url="https://notion.site/page",
            text=text,
            content_hash=content_hash,
            paragraph_count=1,
            chunks=[make_chunk(text)],
        )
    )


def test_repository_creates_and_reads_json_files(tmp_path) -> None:
    repository = JsonDocumentRepository(tmp_path)

    result = save(repository, "본문", "hash-1")
    documents = asyncio.run(repository.list_documents())
    chunks = asyncio.run(repository.get_chunks("doc"))

    assert result["status"] == "created"
    assert documents[0]["text"] == "본문"
    assert chunks is not None
    assert chunks[0]["text"] == "본문"
    assert json.loads(repository.documents_path.read_text(encoding="utf-8"))["version"] == 1


def test_repository_detects_unchanged_content(tmp_path) -> None:
    repository = JsonDocumentRepository(tmp_path)

    first = save(repository, "본문", "same-hash")
    second = save(repository, "본문", "same-hash")

    assert first["status"] == "created"
    assert second == {
        "status": "unchanged",
        "document_id": "doc",
        "stored_at": first["stored_at"],
    }


def test_repository_replaces_changed_document_and_chunks(tmp_path) -> None:
    repository = JsonDocumentRepository(tmp_path)
    save(repository, "이전 본문", "old-hash")

    result = save(repository, "새 본문", "new-hash")
    documents = asyncio.run(repository.list_documents())
    chunks = asyncio.run(repository.get_chunks("doc"))

    assert result["status"] == "updated"
    assert documents[0]["text"] == "새 본문"
    assert chunks is not None
    assert chunks[0]["text"] == "새 본문"
