from playwright.sync_api import sync_playwright
import os

BASE = "http://127.0.0.1:5000"
OUT = "design-review/shots/v3/colour"
os.makedirs(OUT, exist_ok=True)
ARTICLE = "/magazine/article/7951362a-3cf4-4eef-b2de-746a850eba09"

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for name, path, lang, w, h in [
        ("front_en_1440", "/magazine", "en", 1440, 900),
        ("front_en_390", "/magazine", "en", 390, 844),
        ("front_ar_1440", "/magazine", "ar", 1440, 900),
        ("article_en_1440", ARTICLE, "en", 1440, 900),
        ("article_ar_390", ARTICLE, "ar", 390, 844),
        ("campus_en_1440", "/campus", "en", 1440, 900),
    ]:
        ctx = b.new_context(viewport={"width": w, "height": h})
        ctx.add_cookies([{"name": "lang_pref", "value": lang, "url": BASE}])
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(BASE + path, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(500)
        metrics = page.evaluate("""() => ({
            sw: document.documentElement.scrollWidth,
            cw: document.documentElement.clientWidth,
            tags: document.querySelectorAll('.desk-tag').length,
            badges: document.querySelectorAll('.src-badge').length,
            listen: document.querySelectorAll('[data-listen]').length
        })""")
        print(name, metrics, "errors:", errors[:3])
        page.screenshot(path=f"{OUT}/{name}.png", full_page=True)
        if name == "article_en_1440":
            page.click("[data-listen]")
            page.wait_for_timeout(300)
            print("listen state:", page.get_attribute("[data-listen]", "aria-pressed"),
                  page.inner_text("[data-listen]"))
        ctx.close()
    b.close()
