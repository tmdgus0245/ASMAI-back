import pytest

from app.services.public_notion import PublicNotionError, extract_page_id, parse_record_map

PUBLIC_URL = "https://est-tech.notion.site/EST-SECURITY-386fe935d7a78059aecafce8bc5c430b"
PAGE_ID = "386fe935-d7a7-8059-aeca-fce8bc5c430b"


def wrapped(block: dict[str, object]) -> dict[str, object]:
    return {"value": {"value": block}}


def test_extract_page_id() -> None:
    assert extract_page_id(PUBLIC_URL) == PAGE_ID


def test_rejects_non_notion_hosts() -> None:
    with pytest.raises(PublicNotionError):
        extract_page_id(f"https://example.com/{PAGE_ID.replace('-', '')}")


def test_parse_record_map_preserves_page_order() -> None:
    child_id = "11111111-1111-1111-1111-111111111111"
    grandchild_id = "22222222-2222-2222-2222-222222222222"
    record_map = {
        "block": {
            PAGE_ID: wrapped(
                {
                    "id": PAGE_ID,
                    "type": "page",
                    "properties": {"title": [["테스트 페이지"]]},
                    "content": [child_id],
                }
            ),
            child_id: wrapped(
                {
                    "id": child_id,
                    "type": "toggle",
                    "properties": {"title": [["첫 번째 문단"]]},
                    "content": [grandchild_id],
                }
            ),
            grandchild_id: wrapped(
                {
                    "id": grandchild_id,
                    "type": "text",
                    "properties": {"title": [["하위 문단"]]},
                }
            ),
        }
    }

    result = parse_record_map(record_map, PAGE_ID)

    assert result == {
        "title": "테스트 페이지",
        "text": "첫 번째 문단\n\n하위 문단",
        "block_count": 2,
    }
