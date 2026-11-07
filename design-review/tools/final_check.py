"""Final check of the v3 reader: status, overflow, and screenshots of the secondary pages."""
import json
import os

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
OUT = "design-review/shots/v3"
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ("subscribe_en_1440", "/subscribe", "en", 1440, 900),
    ("subscribe_ar_390", "/subscribe", "ar", 390, 844),
    ("about_en_1440", "/authorinfo", "en", 1440, 900),
]

report = {}
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    for name, path, lang, width, height in PAGES:
        ctx = browser.new_context(viewport={"width": width, "height": height})
        ctx.add_cookies([{"name": "lang_pref", "value": lang, "url": BASE}])
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        resp = page.goto(BASE + path, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(400)
        metrics = page.evaluate("""() => ({
            h: document.documentElement.scrollHeight,
            w: document.documentElement.clientWidth,
            sw: document.documentElement.scrollWidth,
            dir: document.documentElement.dir,
        })""")
        metrics.update({"status": resp.status if resp else None, "errors": errors[:4]})
        report[name] = metrics
        page.screenshot(path=f"{OUT}/{name}.png", full_page=True)
        print(name, metrics)
        ctx.close()
    browser.close()

print(json.dumps(report, indent=1))
