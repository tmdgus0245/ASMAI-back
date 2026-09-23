from fastapi import APIRouter, HTTPException, status

from app.schemas.documents import ChunkListResponse, DocumentListResponse
from app.services.document_repository import DocumentRepositoryError
from app.services.repositories import document_repository

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    try:
        documents = await document_repository.list_documents()
    except DocumentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return DocumentListResponse(documents=documents)


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def list_document_chunks(document_id: str) -> ChunkListResponse:
    try:
        chunks = await document_repository.get_chunks(document_id)
    except DocumentRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    if chunks is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 문서를 찾을 수 없습니다.",
        )
    return ChunkListResponse(document_id=document_id, chunks=chunks)
