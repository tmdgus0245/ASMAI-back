from fastapi import APIRouter, HTTPException, status

from app.schemas.search import IndexResponse, SearchRequest, SearchResponse
from app.services.document_repository import DocumentRepositoryError
from app.services.embedding_repository import EmbeddingRepositoryError
from app.services.search import SearchServiceError
from app.services.searches import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/index/{document_id}", response_model=IndexResponse)
async def index_document(document_id: str) -> IndexResponse:
    try:
        result = await search_service.index(document_id)
    except SearchServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (DocumentRepositoryError, EmbeddingRepositoryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return IndexResponse(**result)


@router.post("", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    try:
        results = await search_service.search(
            request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except SearchServiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (DocumentRepositoryError, EmbeddingRepositoryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    return SearchResponse(query=request.query, results=results)
