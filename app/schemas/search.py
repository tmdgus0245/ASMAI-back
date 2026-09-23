from pydantic import BaseModel, Field

from app.schemas.sync import DocumentChunk


class IndexResponse(BaseModel):
    document_id: str
    model: str
    dimension: int
    indexed_count: int
    indexed_at: str


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: str | None = None


class SearchResult(BaseModel):
    score: float
    chunk: DocumentChunk


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
