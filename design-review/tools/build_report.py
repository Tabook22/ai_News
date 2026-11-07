"""Rebuild design-review/UX_AUDIT_AND_REDESIGN.pdf from the markdown source.

Run from the repository root:
    venv\\Scripts\\python.exe design-review/tools/build_report.py
"""
import re

import markdown
from playwright.sync_api import sync_playwright

MD = "design-review/UX_AUDIT_AND_REDESIGN.md"
HTML = "design-review/UX_AUDIT_AND_REDESIGN.html"
PDF = "design-review/UX_AUDIT_AND_REDESIGN.pdf"

text = open(MD, encoding="utf-8").read()
text = re.sub(r"^# .*\n", "", text, count=1)

md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"])
body = md.convert(text)

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { margin: 0; color: #1b1d22; background: #fff;
  font-family: "Source Serif 4", Georgia, serif; font-size: 10.2pt; line-height: 1.62; }
.cover { min-height: 250mm; display: flex; flex-direction: column; justify-content: space-between;
  padding: 6mm 0 0; page-break-after: always; }
.cover .kicker { font-family: Inter, sans-serif; font-size: 8.5pt; letter-spacing: .18em; text-transform: uppercase; color: #0b4f6c; }
.cover h1 { font-family: "Playfair Display", Georgia, serif; font-size: 34pt; line-height: 1.03; margin: 14mm 0 6mm; letter-spacing: -.02em; }
.cover .sub { font-size: 13pt; color: #444; max-width: 125mm; line-height: 1.5; }
.cover img { width: 100%; margin-top: 12mm; border-radius: 2mm; }
.cover .meta { font-family: Inter, sans-serif; font-size: 8.5pt; color: #666; border-top: 1px solid #d8d3c6; padding-top: 4mm; margin-top: 8mm; }
h1, h2, h3, h4 { font-family: "Playfair Display", Georgia, serif; color: #14161a; line-height: 1.15; page-break-after: avoid; }
h2 { font-size: 20pt; margin: 12mm 0 3mm; border-top: 2px solid #14161a; padding-top: 4mm; }
h3 { font-size: 13.5pt; margin: 7mm 0 2mm; }
h4 { font-size: 11pt; margin: 5mm 0 1.5mm; }
p { margin: 0 0 3.2mm; }
a { color: #0b4f6c; text-decoration: none; }
ul, ol { margin: 0 0 3.5mm; padding-inline-start: 5mm; }
li { margin-bottom: 1.4mm; }
strong { font-weight: 600; }
hr { border: 0; border-top: 1px solid #ddd8ca; margin: 7mm 0; }
blockquote { margin: 5mm 0; padding: 3mm 0 3mm 5mm; border-left: 3px solid #b45309; font-size: 12pt; color: #222; }
blockquote p { margin: 0; }
table { width: 100%; border-collapse: collapse; margin: 3mm 0 6mm; font-family: Inter, sans-serif; font-size: 8.4pt; line-height: 1.42; }
th, td { text-align: start; vertical-align: top; padding: 2mm 2.2mm; border-bottom: 1px solid #e2ddcf; }
th { background: #f4f1e8; font-weight: 600; color: #222; border-bottom: 1px solid #b9b2a0; }
tr:nth-child(even) td { background: #fbfaf6; }
img { max-width: 100%; height: auto; display: block; margin: 3mm 0 2mm; }
p img { margin: 0; }
em { color: #555; }
code { font-family: "JetBrains Mono", Consolas, monospace; font-size: 8.6pt; background: #f4f1e8; padding: .4mm 1mm; border-radius: 1mm; }
pre { background: #f6f3ea; border: 1px solid #e2ddcf; padding: 3mm 3.5mm; overflow: hidden; font-size: 7.8pt; line-height: 1.45; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
h2 + p, h3 + p { margin-top: 1mm; }
table { page-break-inside: auto; }
tr { page-break-inside: avoid; }
"""

cover = """
<div class="cover">
  <div>
    <div class="kicker">Nasser AI News · Dhofar University · Computer Science</div>
    <h1>UX/UI Audit &amp;<br>Audience Growth Plan</h1>
    <p class="sub">Why the magazine is hard to read, and how to make students, faculty and
    first-time visitors actually open it — a redesign blueprint, a working prototype, and a
    90-day plan.</p>
    <img src="shots/compare_front_1440.jpg" alt="Before and after">
  </div>
  <div class="meta">
    Prepared 6 November 2026 &nbsp;·&nbsp; Scope: public reader experience
    &nbsp;·&nbsp; Evidence: 39 templates, 124 KB CSS, live page metrics, and a rebuilt prototype
  </div>
</div>
"""

html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Nasser AI News — UX/UI Audit &amp; Audience Growth Plan</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
{cover}
{body}
</body></html>
"""

open(HTML, "w", encoding="utf-8").write(html)
print("html written", len(html))

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto("file:///C:/Users/nmtab/OneDrive/Desktop/myProjects/nasser_ai_news/"
              + HTML.replace("\\", "/"), wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(2500)
    page.pdf(path=PDF, format="A4", print_background=True,
             display_header_footer=True,
             header_template="<div style='font-family:Inter,sans-serif;font-size:7pt;color:#888;width:100%;padding:0 14mm;'>Nasser AI News — UX/UI Audit</div>",
             footer_template="<div style='font-family:Inter,sans-serif;font-size:7pt;color:#888;width:100%;padding:0 14mm;text-align:right;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>",
             margin={"top": "20mm", "bottom": "18mm", "left": "0mm", "right": "0mm"})
    browser.close()
print("pdf written")
