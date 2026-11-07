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
    page.screenshot(path=f"{OUT}/login_1440.png", full_page=True)

    page.fill("#username", "nasser")
    page.fill("#password", "Goo@allmona_22")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    print("after login:", page.url)

    for name, path, full in [
        ("dashboard_1440", "/admin", True),
        ("settings_1440", "/settings", False),
        ("newsroom_1440", "/", True),
        ("subscribers_1440", "/subscribers", True),
        ("desk_world_1440", "/desk/world", False),
    ]:
        page.goto(BASE + path, wait_until="networkidle")
        page.wait_for_timeout(600)
        m = page.evaluate("""() => ({
            h: document.documentElement.scrollHeight,
            sw: document.documentElement.scrollWidth,
            cw: document.documentElement.clientWidth,
            title: document.title,
            sidebar: !!document.querySelector('.admin-sidebar'),
            panels: document.querySelectorAll('.settings-panel').length,
            navicons: document.querySelectorAll('.settings-nav .nav-icon').length
        })""")
        print(name, m, "errors:", errors[-3:])
        page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
        if name == "settings_1440":
            page.screenshot(path=f"{OUT}/settings_1440_top.png", full_page=False)

    ctx.close()

    # mobile settings
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill("#username", "nasser")
    page.fill("#password", "Goo@allmona_22")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.goto(BASE + "/settings", wait_until="networkidle")
    page.wait_for_timeout(500)
    print("mobile settings", page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,h:document.documentElement.scrollHeight})"))
    page.screenshot(path=f"{OUT}/settings_390.png", full_page=False)
    ctx.close()
    b.close()
