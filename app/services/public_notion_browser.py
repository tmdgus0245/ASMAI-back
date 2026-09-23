from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.services.document_cleaner import document_cleaner
from app.services.public_notion import PublicNotionError, extract_page_id

OPEN_TOGGLE_SELECTOR = '[role="button"][aria-label="열기"], [role="button"][aria-label="Open"]'


class PublicNotionBrowserService:
    def __init__(
        self,
        *,
        navigation_timeout_ms: int = 30_000,
        max_toggles: int = 500,
    ) -> None:
        self.navigation_timeout_ms = navigation_timeout_ms
        self.max_toggles = max_toggles

    async def fetch(self, url: str) -> dict[str, Any]:
        page_id = extract_page_id(url)

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                try:
                    page = await browser.new_page(locale="ko-KR")
                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.navigation_timeout_ms,
                    )
                    await page.locator("body").wait_for(
                        state="visible",
                        timeout=self.navigation_timeout_ms,
                    )
                    await page.wait_for_function(
                        "document.body && document.body.innerText.trim().length > 100",
                        timeout=self.navigation_timeout_ms,
                    )
                    await self._expand_all_toggles(page)

                    title = (await page.title()).strip() or "Untitled Notion page"
                    raw_text = await page.locator("body").inner_text()
                finally:
                    await browser.close()
        except PlaywrightTimeoutError as exc:
            raise PublicNotionError("공개 Notion 페이지 로딩 시간이 초과되었습니다.") from exc
        except PublicNotionError:
            raise
        except Exception as exc:
            raise PublicNotionError("브라우저에서 공개 Notion 페이지를 읽지 못했습니다.") from exc

        cleaned = document_cleaner.clean(raw_text, title=title)
        if not cleaned.text:
            raise PublicNotionError("공개 Notion 페이지에서 본문을 찾지 못했습니다.")

        return {
            "source_url": url,
            "page_id": page_id,
            "title": title,
            "text": cleaned.text,
            "block_count": cleaned.stats.cleaned_paragraph_count,
            "cleaning": cleaned.stats.to_dict(),
        }

    async def _expand_all_toggles(self, page: Any) -> None:
        expanded = 0
        while expanded < self.max_toggles:
            toggles = page.locator(OPEN_TOGGLE_SELECTOR)
            if await toggles.count() == 0:
                return

            await toggles.first.click(timeout=self.navigation_timeout_ms)
            expanded += 1

        if await page.locator(OPEN_TOGGLE_SELECTOR).count() > 0:
            raise PublicNotionError(f"페이지의 접힌 항목이 {self.max_toggles}개를 초과했습니다.")


public_notion_browser_service = PublicNotionBrowserService()
