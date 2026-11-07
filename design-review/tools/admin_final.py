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
    page.screenshot(path=f"{OUT}/login_final.png", full_page=True)
    page.fill("#username", "nasser")
    page.fill("#password", "Goo@allmona_22")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    print("login ->", page.url)

    page.goto(BASE + "/admin", wait_until="networkidle")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{OUT}/dashboard_final.png", full_page=True)

    page.goto(BASE + "/settings", wait_until="networkidle")
    page.wait_for_timeout(500)
    page.screenshot(path=f"{OUT}/settings_final.png", full_page=True)

    # help drawer
    page.click(".settings-panel.active .panel-help")
    page.wait_for_timeout(300)
    print("help open:", page.locator("#help-drawer.open").count())
    page.screenshot(path=f"{OUT}/settings_help.png")
    page.click("#help-close")

    # AI tab hides the save bar
    page.click('.settings-nav-item[data-tab="aimodels"]')
    page.wait_for_timeout(400)
    print("savebar hidden on AI:", page.eval_on_selector(".settings-save-bar", "e=>e.classList.contains('is-hidden')"))
    page.screenshot(path=f"{OUT}/settings_ai.png")
    page.click('.settings-nav-item[data-tab="general"]')

    # page icon on an older page
    page.goto(BASE + "/subscribers", wait_until="networkidle")
    print("subscribers h1:", page.inner_text(".dashboard-header h1"), "| page icon:", page.locator(".dashboard-header .page-icon").count())
    page.screenshot(path=f"{OUT}/subscribers_final.png", full_page=True)

    # mobile: menu + settings
    mobile = b.new_context(viewport={"width": 390, "height": 844})
    mp = mobile.new_page()
    mp.goto(BASE + "/login", wait_until="networkidle")
    mp.fill("#username", "nasser")
    mp.fill("#password", "Goo@allmona_22")
    mp.click("button[type=submit]")
    mp.wait_for_load_state("networkidle")
    mp.goto(BASE + "/settings", wait_until="networkidle")
    mp.wait_for_timeout(400)
    mp.screenshot(path=f"{OUT}/settings_mobile_final.png")
    print("mobile settings overflow:", mp.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth"))
    mp.click("#admin-menu-btn")
    mp.wait_for_timeout(300)
    print("mobile nav open:", mp.locator("#admin-shell.nav-open").count())
    mp.screenshot(path=f"{OUT}/mobile_nav.png")
    mobile.close()

    print("errors:", errors[:6])
    b.close()
