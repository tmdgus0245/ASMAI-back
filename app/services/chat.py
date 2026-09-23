import re

from app.schemas.chat import ChatRequest, ChatResponse, Source
from app.services.search import SearchService

_WORD_PATTERN = re.compile(r"[0-9A-Za-z가-힣]{2,}")


class ChatServiceError(RuntimeError):
    """Raised when a grounded chat response cannot be produced."""


class ChatService:
    def __init__(
        self,
        *,
        search: SearchService,
        top_k: int = 3,
        max_excerpt_chars: int = 700,
    ) -> None:
        self.search = search
        self.top_k = top_k
        self.max_excerpt_chars = max_excerpt_chars

    async def reply(self, request: ChatRequest) -> ChatResponse:
        results = await self.search.search(request.message, top_k=self.top_k)
        relevant = [result for result in results if float(result.get("score", 0.0)) > 0.0]
        if not relevant:
            raise ChatServiceError("질문과 관련된 내용을 저장된 문서에서 찾지 못했습니다.")

        answer_parts = ["문서에서 다음과 같은 관련 내용을 찾았습니다."]
        sources: list[Source] = []
        seen_chunks: set[str] = set()

        for number, result in enumerate(relevant, start=1):
            chunk = result["chunk"]
            chunk_id = str(chunk["chunk_id"])
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            title = str(chunk.get("title") or "문서")
            section = str(chunk.get("section") or title)
            excerpt = self._select_excerpt(str(chunk.get("text", "")), request.message)
            answer_parts.append(f"{number}. [{section}]\n{excerpt}")
            sources.append(
                Source(
                    title=title,
                    url=str(chunk.get("source_url") or "") or None,
                    section=section,
                    chunk_id=chunk_id,
                    score=round(float(result["score"]), 4),
                )
            )

        return ChatResponse(answer="\n\n".join(answer_parts), sources=sources)

    def _select_excerpt(self, text: str, query: str) -> str:
        paragraphs = [part.strip() for part in re.split(r"\n+", text) if part.strip()]
        if not paragraphs:
            return "관련 내용이 비어 있습니다."

        query_terms = {term.lower() for term in _WORD_PATTERN.findall(query)}
        ranked: list[tuple[int, int, str]] = []
        for index, paragraph in enumerate(paragraphs):
            paragraph_terms = {term.lower() for term in _WORD_PATTERN.findall(paragraph)}
            ranked.append((len(query_terms & paragraph_terms), -index, paragraph))
        ranked.sort(reverse=True)

        selected: list[str] = []
        current_length = 0
        for overlap, _, paragraph in ranked:
            if selected and overlap == 0:
                continue
            remaining = self.max_excerpt_chars - current_length
            if remaining <= 0:
                break
            selected.append(paragraph[:remaining])
            current_length += len(selected[-1]) + 2
            if current_length >= self.max_excerpt_chars or len(selected) >= 4:
                break

        excerpt = "\n\n".join(selected or [paragraphs[0]])
        if len(excerpt) < len(text) and not excerpt.endswith("…"):
            excerpt = excerpt.rstrip() + "…"
        return excerpt
