from pydantic import BaseModel

from app.schemas.sync import DocumentChunk


class StoredDocument(BaseModel):
    document_id: str
    title: str
    source_url: str
    text: str
    content_hash: str
    char_count: int
    paragraph_count: int
    chunk_count: int
    stored_at: str


class DocumentListResponse(BaseModel):
    documents: list[StoredDocument]


class ChunkListResponse(BaseModel):
    document_id: str
    chunks: list[DocumentChunk]
