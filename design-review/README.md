# Design review — Nasser AI News

This folder contains the UX/UI audit, the design prototype, and the record of what shipped.

## Start here

- **[IMPLEMENTATION.md](IMPLEMENTATION.md)** — what changed in the running app, new routes, rollback, and what is still open.
- **[UX_AUDIT_AND_REDESIGN.md](UX_AUDIT_AND_REDESIGN.md)** — the full audit, redesign blueprint, feature ideas, roadmap and measurement plan.
- **[UX_AUDIT_AND_REDESIGN.pdf](UX_AUDIT_AND_REDESIGN.pdf)** — the same document as a printable PDF.

The app now ships the v3 reader (see `IMPLEMENTATION.md`). The prototype below remains the
design reference and the place to try changes before they are ported.

## Open the prototype

The prototype is static HTML with no build step. Either:

1. **Double-click** `prototype/index.html` (the language switch, search and quiz work when opened directly; the Google Fonts and publisher images need internet).
2. Or serve the folder, which is closer to the real thing:

```bash
cd design-review/prototype
python -m http.server 8080
# open http://127.0.0.1:8080/index.html
```

Pages:

- `index.html` — the proposed front page: 90-second brief, lead, world, department, course of the week, editor's picks, subscribe.
- `article.html` — the proposed article page: 30-second brief, body, glossary term, 3-question quiz, source box, related.

Both pages have a working **EN / ع** switch (full RTL with Arabic typography), a search overlay (`Ctrl/⌘ K`), a mobile tab bar, save-for-later, and a print stylesheet (`Ctrl/⌘ P`).

## Screenshots

`shots/` contains:

| File | What it shows |
|---|---|
| `compare_front_1440.jpg` | current vs. proposed front page, top of page, desktop |
| `compare_front_390.jpg` | current vs. proposed first phone screen |
| `compare_article_1440.jpg` | current vs. proposed article page |
| `proto_front_en_1440.png`, `proto_front_ar_1440.png` | proposed front page, full height, both languages |
| `proto_front_en_390.png`, `proto_front_ar_390.png` | proposed front page, mobile |
| `proto_article_en_1440.png`, `proto_article_ar_1440.png` | proposed article page |
| `current_*.png` | the app before the redesign, for reference |
| `v3/` | screenshots of the **shipped** pages (EN/AR, desktop/mobile, print) |

## The shipped pages

`shots/v3/` contains the app as it runs now:

| File | What it shows |
|---|---|
| `front_en_1440.png`, `front_ar_1440.png` | the new issue, full height |
| `front_en_390_fold.png`, `front_ar_390_fold.png` | the first phone screen |
| `article_en_1440.png`, `article_ar_1440.png` | the new article page |
| `campus_en_1440.png`, `campus_ar_390_fold.png` | the new department page |
| `find_en_1440.png`, `find_ar_390_fold.png` | public search |
| `print_page1.png` | the A4 print edition |
| `compare_real_front_1440.jpg`, `compare_real_front_390.jpg` | before/after of the running app |

## What the prototype is and is not

- **Is:** the design reference — a clickable model with the real stories, images and Arabic titles from `app/instance/local_dev.db`.
- **Was:** the source for the shipped v3 templates (`issue_v3.html`, `article_v3.html`, `issue-v3.css`). The app now runs this design; `?classic=1` brings back the old one.
- Sample editorial copy in the prototype (the "what happened / why it matters / in class" lines and the quiz) was written to demonstrate the format. The app only shows those blocks when the story actually has the data.
