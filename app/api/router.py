from fastapi import APIRouter

from app.api.routes import chat, documents, health, search, sync
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router, prefix=settings.api_v1_prefix)
api_router.include_router(sync.router, prefix=settings.api_v1_prefix)
api_router.include_router(documents.router, prefix=settings.api_v1_prefix)
api_router.include_router(search.router, prefix=settings.api_v1_prefix)
