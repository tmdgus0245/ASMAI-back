from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class Source(BaseModel):
    title: str
    url: str | None = None
    section: str | None = None
    chunk_id: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
