from playwright.sync_api import sync_playwright
import os

BASE = "http://127.0.0.1:5000"
OUT = "design-review/shots/admin"
os.makedirs(OUT, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))

    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill("#username", "nasser")
    page.fill("#password", "Goo@allmona_22")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")

    page.goto(BASE + "/add", wait_until="networkidle")
    page.wait_for_timeout(1200)
    print("add status:", page.title())
    print("fields:", page.evaluate("document.querySelectorAll('#story-form [name]').length"))
    print("editors:", page.evaluate("Object.keys(window.storyEditors||{}).length"))
    print("overflow:", page.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"))
    page.screenshot(path=f"{OUT}/story_editor_new.png", full_page=True)
    page.screenshot(path=f"{OUT}/story_editor_fold.png")

    # fill headline to test live preview + checklist
    page.fill("#title_en", "Sultan Qaboos University opens a new AI lab")
    page.fill("#summary_en", "The lab will focus on Arabic language models and robotics.")
    page.wait_for_timeout(400)
    print("preview title:", page.inner_text("#mini-title"))
    print("checklist done:", page.eval_on_selector_all("#publish-checklist li.is-done", "els=>els.length"))
    page.screenshot(path=f"{OUT}/story_editor_preview.png")

    # mobile
    mob = b.new_context(viewport={"width": 390, "height": 844})
    m = mob.new_page()
    m.goto(BASE + "/login", wait_until="networkidle")
    m.fill("#username", "nasser")
    m.fill("#password", "Goo@allmona_22")
    m.click("button[type=submit]")
    m.wait_for_load_state("networkidle")
    m.goto(BASE + "/add", wait_until="networkidle")
    m.wait_for_timeout(900)
    print("mobile overflow:", m.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth"))
    m.screenshot(path=f"{OUT}/story_editor_mobile.png")

    print("errors:", errors[:8])
    b.close()
