from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.repositories import document_repository, embedding_repository
from app.services.search import SearchService

embedding_service = EmbeddingService(
    model_name=settings.embedding_model,
    batch_size=settings.embedding_batch_size,
    cache_dir=settings.data_dir / "models",
)
search_service = SearchService(
    documents=document_repository,
    embeddings=embedding_repository,
    embedder=embedding_service,
)
