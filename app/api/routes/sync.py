from fastapi import APIRouter, HTTPException, status

from app.schemas.sync import UrlSyncRequest, UrlSyncResponse
from app.services.document_chunker import (
    content_hash_for,
    document_chunker,
    document_id_for,
)
from app.services.document_repository import DocumentRepositoryError
from app.services.public_notion import PublicNotionError
from app.services.public_notion_browser import public_notion_browser_service
from app.services.repositories import document_repository

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/url", response_model=UrlSyncResponse)
async def sync_public_url(request: UrlSyncRequest) -> UrlSyncResponse:
    try:
        document = await public_notion_browser_service.fetch(str(request.url))
    except PublicNotionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    chunks = document_chunker.chunk(
        document["text"],
        title=document["title"],
        source_url=document["source_url"],
    )
    document["chunks"] = [chunk.to_dict() for chunk in chunks]
    document["chunk_count"] = len(chunks)
    try:
        document["storage"] = await document_repository.save(
            document_id=document_id_for(document["source_url"]),
            title=document["title"],
            source_url=document["source_url"],
            text=document["text"],
            content_hash=content_hash_for(document["text"]),
            paragraph_count=document["block_count"],
            chunks=chunks,
        )
    except DocumentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return UrlSyncResponse(**document)
