from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ASMAI_",
        extra="ignore",
    )

    app_name: str = "ASMAI Backend"
    environment: Literal["local", "development", "test", "production"] = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    notion_public_page_url: str | None = None
    data_dir: Path = Path("data")
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_batch_size: int = 16
    chat_top_k: int = 3
    chat_max_excerpt_chars: int = 700


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
