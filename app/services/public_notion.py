import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx

NOTION_API_URL = "https://www.notion.so/api/v3/loadPageChunk"
NOTION_HOSTS = {"notion.site", "notion.so", "www.notion.so"}
PAGE_ID_PATTERN = re.compile(r"([0-9a-fA-F]{32})(?:[/?#]|$)")


class PublicNotionError(RuntimeError):
    """Raised when a public Notion page cannot be retrieved or parsed."""


def extract_page_id(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if not any(hostname == host or hostname.endswith(f".{host}") for host in NOTION_HOSTS):
        raise PublicNotionError("Notion 공개 페이지 URL만 동기화할 수 있습니다.")

    match = PAGE_ID_PATTERN.search(parsed.path)
    if not match:
        raise PublicNotionError("URL에서 Notion 페이지 ID를 찾을 수 없습니다.")

    return str(UUID(match.group(1)))


def _unwrap_block(entry: Any) -> dict[str, Any] | None:
    value = entry
    for _ in range(3):
        if not isinstance(value, Mapping):
            return None
        if "id" in value and "type" in value:
            return dict(value)
        value = value.get("value")
    return None


def _plain_text(properties: Any) -> str:
    if not isinstance(properties, Mapping):
        return ""
    title = properties.get("title")
    if not isinstance(title, list):
        return ""

    parts: list[str] = []
    for fragment in title:
        if isinstance(fragment, list) and fragment and isinstance(fragment[0], str):
            parts.append(fragment[0])
    return "".join(parts).strip()


def parse_record_map(record_map: Mapping[str, Any], root_page_id: str) -> dict[str, Any]:
    raw_blocks = record_map.get("block")
    if not isinstance(raw_blocks, Mapping):
        raise PublicNotionError("Notion 응답에 페이지 블록이 없습니다.")

    blocks = {
        block_id: block
        for block_id, entry in raw_blocks.items()
        if (block := _unwrap_block(entry)) is not None
    }
    root = blocks.get(root_page_id)
    if root is None:
        raise PublicNotionError("Notion 응답에서 최상위 페이지를 찾을 수 없습니다.")

    title = _plain_text(root.get("properties")) or "Untitled Notion page"
    lines: list[str] = []
    visited: set[str] = set()

    def walk(block_id: str) -> None:
        if block_id in visited:
            return

        block = blocks.get(block_id)
        if block is None:
            return
        visited.add(block_id)

        text = _plain_text(block.get("properties"))
        if text:
            lines.append(text)

        content = block.get("content")
        if isinstance(content, list):
            for child_id in content:
                if isinstance(child_id, str):
                    walk(child_id)

    content = root.get("content")
    if isinstance(content, list):
        for child_id in content:
            if isinstance(child_id, str):
                walk(child_id)

    return {
        "title": title,
        "text": "\n\n".join(lines),
        "block_count": len(visited),
    }


class PublicNotionService:
    def __init__(self, *, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def fetch(self, url: str) -> dict[str, Any]:
        page_id = extract_page_id(url)
        payload = {
            "pageId": page_id,
            "limit": 100,
            "cursor": {"stack": []},
            "chunkNumber": 0,
            "verticalColumns": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(NOTION_API_URL, json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PublicNotionError("공개 Notion 페이지를 불러오지 못했습니다.") from exc

        record_map = data.get("recordMap")
        if not isinstance(record_map, Mapping):
            raise PublicNotionError("Notion 응답 형식이 예상과 다릅니다.")

        document = parse_record_map(record_map, page_id)
        return {
            "source_url": url,
            "page_id": page_id,
            **document,
        }


public_notion_service = PublicNotionService()
