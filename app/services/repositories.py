from app.core.config import settings
from app.services.document_repository import JsonDocumentRepository
from app.services.embedding_repository import JsonEmbeddingRepository

document_repository = JsonDocumentRepository(settings.data_dir)
embedding_repository = JsonEmbeddingRepository(settings.data_dir)
