from app.services.document_chunker import DocumentChunker


def test_chunker_preserves_content_and_adds_metadata() -> None:
    chunker = DocumentChunker(target_chars=25, overlap_chars=10, max_paragraph_chars=50)
    text = "첫 번째 문단입니다.\n\n두 번째 문단입니다.\n\n세 번째 문단입니다."

    chunks = chunker.chunk(
        text,
        title="테스트 문서",
        source_url="https://example.notion.site/page-1234567890abcdef1234567890abcdef",
    )

    assert len(chunks) == 2
    assert chunks[0].index == 0
    assert chunks[0].title == "테스트 문서"
    assert chunks[0].section == "테스트 문서"
    assert chunks[0].char_count == len(chunks[0].text)
    assert len(chunks[0].content_hash) == 64
    assert chunks[0].document_id == chunks[1].document_id
    assert chunks[0].chunk_id != chunks[1].chunk_id


def test_chunker_keeps_paragraph_overlap() -> None:
    chunker = DocumentChunker(target_chars=16, overlap_chars=6, max_paragraph_chars=30)
    text = "가나다라\n\n마바사아\n\n자차카타\n\n파하거너"

    chunks = chunker.chunk(text, title="문서", source_url="https://notion.site/page")

    assert len(chunks) == 2
    assert chunks[0].text.endswith("자차카타")
    assert chunks[1].text.startswith("자차카타")


def test_chunker_splits_a_long_paragraph() -> None:
    chunker = DocumentChunker(target_chars=20, overlap_chars=0, max_paragraph_chars=20)
    text = "가" * 45

    chunks = chunker.chunk(text, title="문서", source_url="https://notion.site/page")

    assert [chunk.char_count for chunk in chunks] == [20, 20, 5]
    assert "".join(chunk.text for chunk in chunks) == text


def test_chunker_is_deterministic() -> None:
    chunker = DocumentChunker()
    arguments = {
        "text": "첫 문단\n\n둘째 문단",
        "title": "문서",
        "source_url": "https://notion.site/page",
    }

    first = chunker.chunk(**arguments)
    second = chunker.chunk(**arguments)

    assert first == second


def test_chunker_returns_empty_list_for_empty_text() -> None:
    assert DocumentChunker().chunk("  ", title="문서", source_url="url") == []
