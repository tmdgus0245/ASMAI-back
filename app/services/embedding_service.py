import asyncio
from pathlib import Path
from threading import Lock

from fastembed import TextEmbedding


class EmbeddingService:
    def __init__(
        self,
        *,
        model_name: str,
        batch_size: int = 16,
        cache_dir: Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        self._model: TextEmbedding | None = None
        self._model_lock = Lock()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_sync, texts)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        return [
            vector.astype("float32").tolist()
            for vector in model.embed(texts, batch_size=self.batch_size)
        ]

    def _get_model(self) -> TextEmbedding:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._model = TextEmbedding(
                        model_name=self.model_name,
                        cache_dir=str(self.cache_dir) if self.cache_dir else None,
                    )
        return self._model
