"""Progress saved under an old id shows up under the new one (RENAMED in assets/common.js)."""
import json

from playwright.sync_api import sync_playwright


def test_old_progress_migrates(base_url):
    old = {"stars": ["shaf", "kteb"], "weights": {"shaf|pres|1": 3, "chaf|pres|2": 2, "mine|shems|0": 4, "c|8|khaf|men": 5}}
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.goto(f"{base_url}/index.html")
        page.evaluate("s => localStorage.setItem('darija:test', s)", json.dumps(old))
        got = page.evaluate("async () => { const m = await import('./assets/common.js'); const d = m.load('test', {}); return { stars: d.stars, weights: d.weights }; }")
        b.close()
    assert got["stars"] == ["chaf", "kteb"]
    assert got["weights"] == {"chaf|pres|1": 3, "chaf|pres|2": 2, "mine|chems|0": 4, "c|8|khaf|mn": 5}
