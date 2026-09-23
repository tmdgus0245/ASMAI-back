from pydantic import BaseModel, HttpUrl


class UrlSyncRequest(BaseModel):
    url: HttpUrl


class CleaningStats(BaseModel):
    original_char_count: int
    cleaned_char_count: int
    original_paragraph_count: int
    cleaned_paragraph_count: int
    removed_paragraph_count: int


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    index: int
    title: str
    section: str
    source_url: str
    text: str
    char_count: int
    content_hash: str


class StorageResult(BaseModel):
    status: str
    document_id: str
    stored_at: str


class UrlSyncResponse(BaseModel):
    source_url: str
    page_id: str
    title: str
    text: str
    block_count: int
    cleaning: CleaningStats
    chunk_count: int
    chunks: list[DocumentChunk]
    storage: StorageResult
