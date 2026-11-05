"""After answering a quiz question, swiping left on the card goes to the next one (issue #50)."""
import pytest
from playwright.sync_api import sync_playwright

SWIPE = """([sel, x0, y0, x1, y1]) => {
  const el = document.querySelector(sel);
  const mk = (type, x, y) => {
    const t = new Touch({ identifier: 1, target: el, clientX: x, clientY: y });
    el.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: type === 'touchend' ? [] : [t], changedTouches: [t] }));
  };
  mk('touchstart', x0, y0); mk('touchend', x1, y1);
}"""


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def test_swipe_left_advances_only_after_answer(browser, base_url):
    page = browser.new_page(viewport={"width": 375, "height": 812}, has_touch=True)
    page.route(lambda url: not url.startswith(base_url), lambda route: route.fulfill(status=200, body=""))
    page.goto(f"{base_url}/numbers.html", wait_until="networkidle")
    word = lambda: page.locator('[data-q="word"]').inner_text() + page.locator('[data-q="ask"]').inner_text()
    first = word()
    page.evaluate(SWIPE, [".card", 300, 400, 100, 400])
    assert page.locator('[data-q="next"]').is_hidden() and word() == first, "swipe before answering must do nothing"
    page.locator(".opt").first.click()
    assert page.locator('[data-q="next"]').is_visible()
    page.evaluate(SWIPE, [".card", 300, 400, 300, 100])  # vertical: ignored
    assert page.locator('[data-q="next"]').is_visible()
    page.evaluate(SWIPE, [".card", 100, 400, 300, 400])  # right: ignored
    assert page.locator('[data-q="next"]').is_visible()
    page.evaluate(SWIPE, [".card", 300, 400, 100, 400])  # left: next
    assert page.locator('[data-q="next"]').is_hidden()
    assert page.locator(".opt:not([disabled])").count() > 0
