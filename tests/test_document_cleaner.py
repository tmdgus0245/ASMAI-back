from app.services.document_cleaner import document_cleaner, normalize_line


def test_normalize_line_removes_invisible_characters_and_extra_spaces() -> None:
    assert normalize_line("  첫\u200b 번째\u00a0  문단  ") == "첫 번째 문단"


def test_clean_removes_notion_ui_title_and_consecutive_duplicates() -> None:
    raw_text = """
    콘텐츠로 건너뛰기
    Get Notion free
    테스트 페이지
    첫 번째 문단
    ​
    첫 번째 문단
    두 번째 문단
    갤러리 보기
    """

    result = document_cleaner.clean(raw_text, title="테스트 페이지")

    assert result.text == "첫 번째 문단\n\n두 번째 문단"
    assert result.stats.original_paragraph_count == 8
    assert result.stats.cleaned_paragraph_count == 2
    assert result.stats.removed_paragraph_count == 6


def test_clean_preserves_nonconsecutive_repeated_content() -> None:
    raw_text = "알약\n설명\n알약"

    result = document_cleaner.clean(raw_text)

    assert result.text == "알약\n\n설명\n\n알약"
