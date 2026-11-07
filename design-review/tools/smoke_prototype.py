from playwright.sync_api import sync_playwright
import pathlib

base = pathlib.Path("design-review/prototype").resolve().as_uri()
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    page = b.new_page(viewport={"width": 1280, "height": 900})
    errors = []
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

    page.goto(f"{base}/index.html", wait_until="networkidle")
    page.click("button[data-lang='ar']")
    page.wait_for_timeout(300)
    dir_after = page.evaluate("document.documentElement.dir")
    page.click("button[data-lang='en']")
    page.click("#search-open")
    page.fill("#search-input", "quantum")
    results = page.locator("#search-results a").count()
    page.keyboard.press("Escape")

    page.goto(f"{base}/article.html", wait_until="networkidle")
    page.check("input[name=q1][value=b]")
    page.check("input[name=q2][value=c]")
    page.check("input[name=q3][value=a]")
    page.click("#quiz-check")
    score = page.inner_text("#quiz-score")
    page.click("#save-story")
    saved = page.get_attribute("#save-story", "aria-pressed")

    print({"dir_ar": dir_after, "search_results": results, "quiz": score, "saved": saved, "errors": errors[:6]})
    b.close()
