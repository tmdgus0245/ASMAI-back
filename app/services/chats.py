from app.core.config import settings
from app.services.chat import ChatService
from app.services.searches import search_service

chat_service = ChatService(
    search=search_service,
    top_k=settings.chat_top_k,
    max_excerpt_chars=settings.chat_max_excerpt_chars,
)
