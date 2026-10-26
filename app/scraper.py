from typing import List

from playwright.async_api import Page, async_playwright


async def scrape_webpage(url: str, is_paginated: bool = False) -> List[str]:
    """
    Scrapes a webpage, handling pagination if requested.

    Args:
        url: The URL of the webpage to scrape.
        is_paginated: Whether to click through numbered pagination buttons
            and collect one HTML document per page.

    Returns:
        A list of HTML documents — one entry if is_paginated=False,
        one per page otherwise.
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=0)

        documents = (
            await _scrape_paginated(page) if is_paginated else [await _scrape_single_page(page)]
        )

        await browser.close()
        return documents


async def _scrape_single_page(page: Page) -> str:
    """Returns the fully rendered HTML of the current page."""
    return await page.content()


async def _scrape_paginated(page: Page) -> List[str]:
    """Clicks through numbered pagination buttons, collecting HTML per page."""
    documents = []
    page_number = 1
    while True:
        try:
            documents.append(await _scrape_single_page(page))
            await page.get_by_role("button", name=str(page_number + 1)).click()
            await page.wait_for_load_state(state="domcontentloaded", timeout=0)
            page_number += 1
        except Exception:
            # No more pages to click through — stop.
            break
    return documents
