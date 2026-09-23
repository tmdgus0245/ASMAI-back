import hashlib
import re
from dataclasses import asdict, dataclass

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?。！？])\s+")


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    index: int
    title: str
    section: str
    source_url: str
    text: str
    char_count: int
    content_hash: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def content_hash_for(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def document_id_for(source_url: str) -> str:
    return content_hash_for(source_url)[:16]


def _hard_split(text: str, max_chars: int) -> list[str]:
    parts: list[str] = []
    remaining = text.strip()

    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars + 1)
        if split_at < max_chars // 2:
            split_at = max_chars
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    if remaining:
        parts.append(remaining)
    return parts


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = [sentence.strip() for sentence in SENTENCE_BOUNDARY.split(paragraph)]
    segments: list[str] = []
    current: list[str] = []

    for sentence in sentences:
        if not sentence:
            continue
        candidate = " ".join([*current, sentence])
        if current and len(candidate) > max_chars:
            segments.extend(_hard_split(" ".join(current), max_chars))
            current = []
        current.append(sentence)

    if current:
        segments.extend(_hard_split(" ".join(current), max_chars))
    return segments


class DocumentChunker:
    def __init__(
        self,
        *,
        target_chars: int = 1_200,
        overlap_chars: int = 200,
        max_paragraph_chars: int = 1_600,
    ) -> None:
        if target_chars <= 0:
            raise ValueError("target_chars must be positive")
        if overlap_chars < 0 or overlap_chars >= target_chars:
            raise ValueError("overlap_chars must be between 0 and target_chars")
        if max_paragraph_chars < target_chars:
            raise ValueError("max_paragraph_chars must be at least target_chars")

        self.target_chars = target_chars
        self.overlap_chars = overlap_chars
        self.max_paragraph_chars = max_paragraph_chars

    def chunk(
        self,
        text: str,
        *,
        title: str,
        source_url: str,
    ) -> list[DocumentChunk]:
        paragraphs = self._prepare_paragraphs(text)
        if not paragraphs:
            return []

        groups = self._group_paragraphs(paragraphs)
        document_id = document_id_for(source_url)
        chunks: list[DocumentChunk] = []

        for index, group in enumerate(groups):
            chunk_text = "\n\n".join(group)
            content_hash = content_hash_for(chunk_text)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}-{index:04d}-{content_hash[:12]}",
                    document_id=document_id,
                    index=index,
                    title=title,
                    section=title,
                    source_url=source_url,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    content_hash=content_hash,
                )
            )
        return chunks

    def _prepare_paragraphs(self, text: str) -> list[str]:
        prepared: list[str] = []
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                prepared.extend(_split_long_paragraph(paragraph, self.max_paragraph_chars))
        return prepared

    def _group_paragraphs(self, paragraphs: list[str]) -> list[list[str]]:
        groups: list[list[str]] = []
        start = 0

        while start < len(paragraphs):
            end = start
            length = 0

            while end < len(paragraphs):
                separator_length = 2 if end > start else 0
                next_length = length + separator_length + len(paragraphs[end])
                if end > start and next_length > self.target_chars:
                    break
                length = next_length
                end += 1

            groups.append(paragraphs[start:end])
            if end >= len(paragraphs):
                break

            overlap_start = end
            overlap_length = 0
            while overlap_start > start:
                candidate = paragraphs[overlap_start - 1]
                candidate_length = len(candidate) + (2 if overlap_length else 0)
                if overlap_length + candidate_length > self.overlap_chars:
                    break
                overlap_start -= 1
                overlap_length += candidate_length

            start = max(overlap_start, start + 1) if overlap_start < end else end

        return groups


document_chunker = DocumentChunker()
