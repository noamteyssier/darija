"""Every page loads, renders its header, and raises no console errors or failed requests.

Run: uv run --with pytest --with playwright pytest tests/e2e
First time: uv run --with playwright playwright install chromium
"""
import pytest
from playwright.sync_api import sync_playwright

PAGES = ["index.html", "verbs.html", "match.html", "nouns.html", "dictionary.html", "rules.html"]
VIEWPORTS = {"desktop": {"width": 1280, "height": 800}, "mobile": {"width": 375, "height": 812}}


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.mark.parametrize("size", VIEWPORTS)
@pytest.mark.parametrize("name", PAGES)
def test_page_loads_clean(browser, base_url, name, size):
    page = browser.new_page(viewport=VIEWPORTS[size])
    problems = []
    page.on("console", lambda m: m.type == "error" and problems.append("console: " + m.text))
    page.on("pageerror", lambda e: problems.append("pageerror: " + str(e)))
    page.on("requestfailed", lambda r: problems.append("failed: " + r.url))
    page.on("response", lambda r: r.status >= 400 and problems.append(f"{r.status}: {r.url}"))
    # Keep the test offline: fonts are the only external requests.
    page.route(
        lambda url: not url.startswith(base_url),
        lambda route: route.fulfill(status=200, body=""),
    )

    page.goto(f"{base_url}/{name}", wait_until="networkidle")

    assert page.locator("#top .brand").count() == 1, "header did not render"
    assert page.locator('#top nav a[aria-current="page"]').count() == (0 if name == "index.html" else 1)
    overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    assert not overflow, "horizontal scroll"
    assert not problems, "\n".join(problems)
    page.close()
