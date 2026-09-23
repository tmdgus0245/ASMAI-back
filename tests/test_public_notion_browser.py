from app.services.public_notion_browser import PublicNotionBrowserService


def test_browser_service_has_bounded_toggle_expansion() -> None:
    service = PublicNotionBrowserService(max_toggles=25)

    assert service.max_toggles == 25
