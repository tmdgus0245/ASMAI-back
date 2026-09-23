import re
import unicodedata
from dataclasses import asdict, dataclass

INVISIBLE_CHARACTERS = str.maketrans(
    {
        "\u00ad": None,
        "\u200b": None,
        "\u200c": None,
        "\u200d": None,
        "\u2060": None,
        "\ufeff": None,
    }
)
HORIZONTAL_WHITESPACE = re.compile(r"[^\S\r\n]+")
NOTION_UI_LINES = {
    "콘텐츠로 건너뛰기",
    "Skip to content",
    "지금 시작하기",
    "Get started",
    "Get Notion free",
    "Notion을 무료로 사용해 보세요",
    "갤러리 보기",
    "Gallery view",
    "표 보기",
    "Table view",
    "목록 보기",
    "List view",
    "보드 보기",
    "Board view",
}


@dataclass(frozen=True)
class CleaningStats:
    original_char_count: int
    cleaned_char_count: int
    original_paragraph_count: int
    cleaned_paragraph_count: int
    removed_paragraph_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class CleaningResult:
    text: str
    stats: CleaningStats


def normalize_line(raw_line: str) -> str:
    line = unicodedata.normalize("NFC", raw_line)
    line = line.translate(INVISIBLE_CHARACTERS).replace("\u00a0", " ")
    return HORIZONTAL_WHITESPACE.sub(" ", line).strip()


class DocumentCleaner:
    def clean(self, raw_text: str, *, title: str | None = None) -> CleaningResult:
        raw_lines = [line for line in raw_text.splitlines() if line.strip()]
        cleaned_lines: list[str] = []
        previous = ""

        for raw_line in raw_lines:
            line = normalize_line(raw_line)
            if not line or line in NOTION_UI_LINES:
                continue
            if title and line == title:
                continue
            if line == previous:
                continue

            cleaned_lines.append(line)
            previous = line

        text = "\n\n".join(cleaned_lines)
        stats = CleaningStats(
            original_char_count=len(raw_text),
            cleaned_char_count=len(text),
            original_paragraph_count=len(raw_lines),
            cleaned_paragraph_count=len(cleaned_lines),
            removed_paragraph_count=len(raw_lines) - len(cleaned_lines),
        )
        return CleaningResult(text=text, stats=stats)


document_cleaner = DocumentCleaner()
