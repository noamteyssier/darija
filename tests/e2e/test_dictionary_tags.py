"""Word tags in the dictionary: weather is not a question word, calendar words get a second tag."""
import pytest
from playwright.sync_api import sync_playwright

# search term -> tags shown on the first hit
CASES = {"hot": ["weather"], "Monday": ["calendar", "week"], "next month": ["calendar", "month"], "winter": ["calendar", "season"], "why": ["question"]}


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.mark.parametrize("term", CASES)
def test_tags(browser, base_url, term):
    page = browser.new_page()
    page.route(lambda url: not url.startswith(base_url), lambda route: route.fulfill(status=200, body=""))
    page.goto(f"{base_url}/dictionary.html", wait_until="networkidle")
    page.click('[data-group="what"] [data-val="words"]')
    page.fill("#search", term)
    first = page.locator("#list .vitem").first
    tags = [t.lower() for t in first.locator(".badge").all_inner_texts()]
    assert tags == CASES[term], (term, tags)
