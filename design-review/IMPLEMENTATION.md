# Implementation — the new public magazine (v3)

**Shipped:** 6 November 2026
This file records what changed in the running app, how to see it, how to roll back, and what is still open.

---

## 1. What you see now

Open the app and go to `/magazine`. The public magazine is now a **paper-calm, one-path issue**:

- a compact header (The Issue · Department · All stories · search · EN/ع · Subscribe) and five mobile tabs;
- a **90-second brief** with five numbered lines;
- one **cover story** with a 16:9 image, a standfirst, and — when the story has them — *what happened / why it matters / in class*;
- the department's week in the sidebar, with dates, the term of the day, and a one-tap print button;
- **The world** — three cards and five one-line briefs;
- **Inside the department** — dated items plus "coming up";
- a dark **course-of-the-week** band with four slots;
- **Editor's picks**, the newsletter band, and a footer with the AI-methods disclosure.

The article page is now: breadcrumb → kicker → **H1** → byline/date/read time/save → a 30-second brief → a 16:9 hero → body → *For class* → original-source box → share → related stories.

The old front page and article page are still available at **`/magazine?classic=1`** and **`/magazine/article/<id>?classic=1`**. Nothing was deleted.

### New public routes

| Route | What it is |
|---|---|
| `/magazine` | the new issue (v3) |
| `/magazine/article/<id>` | the new article page (v3) |
| `/campus` | the new department page (v3) |
| `/find` | public search and the full story browser |
| `/subscribe` | the newsletter page (v3 form, same backend) |
| `/authorinfo` | the editor / about page (v3) |
| `/robots.txt` | crawl rules + sitemap pointer |
| `/sitemap.xml` | every published story (72 URLs today) |
| 404 | a real page with the reader header instead of Flask's bare error |

`?classic=1` on `/magazine`, `/campus`, an article, `/subscribe` or `/authorinfo` brings back the previous design.

---

## 2. Files added

```
app/static/css/issue-v3.css      the public design system (tokens, components, RTL, print)
app/static/js/issue-v3.js        search overlay, ask panel, save, share, reading progress
app/templates/public_v3.html     public shell: header, mobile tabs, footer, search, ask, meta
app/templates/_v3_macros.html    media + title + desk macros
app/templates/issue_v3.html      the new front page
app/templates/article_v3.html    the new article page
app/templates/campus_v3.html     the new department page
app/templates/search_v3.html     public search results
app/templates/subscribe_v3.html  the newsletter page
app/templates/about_v3.html      the editor / about page
app/templates/not_found.html     404
```

Files touched:

```
app/app.py
  - get_lang_pref(): cookie -> ?lang= -> Accept-Language -> English. No gate on public routes.
  - context processor: now_year, reels_count, tools_count (nav adapts to empty shelves).
  - _v3_* helpers: story rows, dedupe, cover-image rules, text picker.
  - new: /find, /robots.txt, /sitemap.xml, 404 handler.
  - magazine_view(): renders issue_v3 unless ?classic=1 or a legacy filter is used.
  - magazine_detail(): renders article_v3 unless ?classic=1.
  - campus_weekly(): renders campus_v3 unless ?classic=1.
  - month_short() template filter/global for date chips.
```

---

## 3. Editorial behaviour built into the design

- **Dedupe.** Syndicated copies of the same headline are dropped before the page is built (the department workshop used to appear three times).
- **Cover choice.** A pinned cover (`Settings → cover`) wins. Otherwise: a `top` story with a real photograph from a newsroom, then any newsroom story with a photo, then any photo. Search-engine thumbnails and video stills are never a cover.
- **Limits.** One lead, five brief lines, three world cards, five world one-liners, three department items, three picks. Everything else lives in `/find`.
- **Honest briefs.** Stories without a body render as a **Brief**: summary as the body, a badge, and a clear link to the original. They do not pretend to be full articles.
- **Class layer.** If a story has `lesson_why`, `lesson_term`, `lesson_ask`, they render in the article and can promote the story to the course band. Today only one story in the database has them — this is the biggest editorial lever.
- **Language.** No more first-visit wall: the browser language decides, `?lang=ar` forces Arabic, the switch remembers the choice for a year. Arabic pages are RTL, with Amiri for reading and Cairo for UI.

---

## 4. Verification

Measured on 6 November 2026 against the local database.

| Check | Before | After |
|---|---|---|
| Front page height, 1440 px | 13,755 px | **4,360 px** |
| Front page height, 390 px | 32,212 px | **7,546 px** |
| Article page height, 1440 px | 7,919 px | **2,896 px** |
| Images on the front page | 69 | 8 |
| Public search | admin-only | `/find` (40 results per view) |
| Crawler view without cookie | language gate, HTTP 200 | the actual story, HTTP 200 |
| Horizontal scroll at 390 px | nav clipped, grid overflow | none on front, article, search, department |
| Canonical / og:image / JSON-LD | none | present |
| Print | light text on white for dark themes | 5-page A4, black on white |

Also checked: language switch persists, search overlay submits to `/find`, the Ask panel opens and still calls `/api/ask`, save-for-later toggles, `/magazine?classic=1` renders the old design, admin login and `/desk/world` still work.

Screenshots of the shipped pages are in `design-review/shots/v3/` (EN/AR, desktop/mobile, print).

---

## 5. How to run

```bash
venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'app'); import app as m; m.app.run(port=5000, debug=False)"
```

or, from the repository root:

```bash
flask --app app.app run --port 5000
```

Then open `http://127.0.0.1:5000/magazine`.

To preview a specific language: `?lang=ar`, `?lang=en`.

---

## 6. What is deliberately not done yet

1. **Article bodies.** 69 of 71 stories still have no `full_content`. The design now handles that honestly (a Brief), but the magazine only becomes a magazine when the lead and features get 150–250 words each. The fields and the editor already exist.
2. **Class Mode content.** The UI is ready; the data is not. Filling `lesson_why`, `lesson_term`, `lesson_ask` on 3–5 stories a week would turn the course band into the magazine's signature.
3. **Watch and Tools.** Both are hidden from the new nav while they have 0 published items. When content exists they appear, but they still use the old templates. They need v3 list pages next.
4. **Analytics and feedback.** Still none. A cookieless script plus a one-tap "Was this useful?" is the next measurement step.
5. **RSS / issue objects.** `/sitemap.xml` and `/robots.txt` shipped; RSS and a permanent `/issue/<n>` archive are next.
6. **Comments.** The old article comments were disabled on 69/71 stories; the new article page does not show them. Decide whether to revive them or replace them with "Ask about this story".
7. **Image hosting.** Most images are still hotlinked from publishers. Rehosting at three widths is the fix for broken images and Core Web Vitals.

---

## 7. Colour, evidence and listening (added later on 6 November)

Three changes were made after the first implementation, on request:

1. **A colour system, not random colour.** Every desk now has its own colour:
   Cybersecurity red, Robotics teal, Chips amber, AI indigo, Data cyan, Software blue,
   Science green, Business orange, Department teal. The colour appears as a tag in every
   kicker, a 4px rule above every card, the card hover colour, coloured brief numbers,
   section numbers, department rules, editor's-pick ranks, and the article drop cap.
   A six-colour strip sits under the masthead; the course band is an indigo-to-teal gradient
   with an amber edge; the newsletter and footer have colour edges.
2. **Evidence badges.** Every story is classified by its source (Lab, Newsroom, Company,
   Video) and the article explains the label: a lab is a university/journal, a newsroom has
   editorial oversight, a company announcement is also marketing. The classifier lives in
   app.py (classify_source_kind, _SOURCE_KIND_LABELS); the lists are easy to extend.
3. **Listen.** The article has a Listen button that reads the body aloud with the browser's
   speech synthesis, in English or Arabic, and toggles to Stop. It is hidden automatically
   when the browser has no speech support.

Screenshots: shots/v3/colour/ (front desktop/mobile, Arabic, article, department).
The print stylesheet turns the colour tags into black-on-white outlined labels and removes
the decorative strips, so the A4 edition stays readable.

The idea backlog that came out of this round is in IDEAS.md.

---

## 8. Admin control panel (added 7 November)

The editor area was rebuilt as a control panel rather than a set of pages.

**Shell.** A fixed dark sidebar (258px) with grouped navigation and line icons: Overview,
Content, Audience, Design, Account. It shows live counts for reels, tools, and subscribers,
an editor card, and one-click access to the public issue. A white top bar carries the page
breadcrumb, search, language switch, "View issue", help, and the editor avatar. On mobile the
sidebar becomes a drawer with a backdrop.

**Control room (`/admin`).** The new landing page after login:
- four KPI cards: published stories (with campus/world split), drafts, article reads, subscribers;
- a seven-day publishing chart;
- a "Recently edited" table with status, reads, date, and an Edit button;
- "Needs attention": drafts, stories without a full article, missing images, missing Arabic
  titles, no subscribers, no story in seven days;
- six quick actions;
- a system-health panel (database, AI key, search keys, theme, last publish).

**Settings (`/settings`).** Same functionality, new surface:
- a searchable section rail with icon tiles and one-line descriptions;
- white section cards with an icon, description, and a per-section **Help** drawer that
  explains what the section controls and gives practical notes;
- a consistent 42px input system, switch-like checkboxes, colour swatches;
- a floating save bar that is always visible, and hides automatically on the AI models and
  API keys tabs, which save through their own forms;
- the AI/API panels keep their existing save endpoints.

**Login (`/login`).** A split card: the brand narrative on the left, a clean form on the
right, and a redirect straight to the control room after sign-in.

Files: `app/static/css/admin-v3.css`, `app/static/js/admin-v3.js`,
`app/templates/admin_dashboard.html`, `app/templates/auth_layout.html`; `layout.html` and
`login.html` were rewritten. Screenshots: `design-review/shots/admin/`.

Checked: settings save returns "Settings updated successfully", the help drawer opens,
the save bar hides on AI/API tabs, the mobile drawer works, and the settings page has no
horizontal overflow at 390px.

---

## 9. Story editor (added 7 November)

The new/edit story form was rebuilt from a single tall card into a two-column editor.

**Main column**
- **The story** — oversized English and Arabic headlines, a segmented control for which
  headline is displayed, and a one-line explanation.
- **Summary** — bilingual summaries side by side, with live character counts.
- **Full story** — the two rich-text editors are now behind an **English / العربية** tab
  switch instead of being stacked, which removes about 450px of scroll. Both still submit.
- **Cover and files** — a drag-and-drop cover zone with an instant thumbnail, attachment
  upload, and two switch rows (own article page, regenerate Arabic translation).

**Sidebar (sticky)**
- **Live preview** — a miniature story card that updates as the headline and summary are
  typed, including the cover image, desk label, and reading time.
- **Publishing** — article type, desk, placement, world desk, source, external link, and
  automatic YouTube detection, all in labelled groups.
- **For class** — the classroom fields, collapsed until needed.
- **Ready to publish?** — a live checklist for headline, summary, Arabic headline, and cover.

A floating save bar appears after scrolling; the header keeps Back / Preview / Save.
The form still posts every field the route expects; a test story was created, verified in
the database (`wing=world`, `category=sidebar`, `source=Test Source`, published), then removed.

Screenshots: `design-review/shots/admin/story_editor_*.png`.

---

## 10. Newsroom redesign (added 7 November, later)

The old newsroom was a landing page: two big cards of static bullet lists, a watermarked
index number, and a long paste-up underneath. It described the desks but did not show their
state or offer a next action.

The route now computes, per desk: published / draft / hidden counts, stories this week,
the three most recent stories, the world slot counts (cover, latest, sidebar, notice),
missing images, missing Arabic titles, and a cover story. Duplicate headlines are removed
from the recent lists.

The page is rebuilt around those numbers:
- **Header** with Find news / New story.
- **Four stat cards**: published (with this-week delta), drafts, department, world — each
  clickable and colour-coded (green, amber, teal, indigo).
- **Needs attention** strip: drafts waiting, missing images, missing Arabic, empty desk,
  no cover.
- **Two desk cards** with a coloured top rule, live count, one-line description,
  New post / Manage desk / Preview actions, the three most recent stories with thumbnails
  and edit links, and a footer of drafts / hidden / this-week (the world card also lists
  reels and tools and shows slot chips).
- **On the issue** preview: department groups and the world cover plus latest/sidebar/notice
  rows, each linking straight to the editor.
- **Quick actions**: new story, find news, reels, AI tools, news photos, digest, QR, settings.

All of it uses the admin design tokens and a desk colour system (teal for the department,
indigo for the world, amber for drafts, green for published). On mobile the stats become
2×2, the desk cards stack, the issue preview stacks, and quick actions become one column.

Checked at 1440 and 390 px: no horizontal overflow, no console errors. Screenshots:
`design-review/shots/admin/newsroom_final.png`, `newsroom_final_fold.png`,
`newsroom_v3_mobile.png`.

---

## 11. AI tools directory (added 7 November, later)

The old directory was a bare grid with no content: no tools were in the database, the
page had one category filter, and the detail page had no context.

**Catalogue.** The database now holds 96 curated tools across 15 categories: chatbots,
coding, image, video generation, video editing, writing, research, presentations,
productivity, audio/voice, design, learning, agents, models & GPUs, and other. Each entry
has English and Arabic name, one-line tagline in both languages, a short description in both
languages, official URL, pricing, free-tier flag, Arabic-support flag, platforms, “best for”,
featured flag, sort order, last-checked date, a 0–5 score, a one-line justification and a
reference URL. Re-run the catalogue with:

    venv\Scripts\python.exe design-review/tools/seed_tools.py
    venv\Scripts\python.exe design-review/tools/seed_tools_extra.py
    venv\Scripts\python.exe design-review/tools/seed_coding.py
    venv\Scripts\python.exe design-review/tools/seed_platforms.py
    venv\Scripts\python.exe design-review/tools/seed_ratings.py
    venv\Scripts\python.exe design-review/tools/seed_models.py

The scripts are idempotent: they match by name and update in place. The extra seed adds
video editing, audio and presentation tools; the coding seed adds 14 agentic coding tools;
the platforms seed adds Hugging Face, RunPod, Colab, Kaggle, Replicate, Modal, Vast.ai,
Lambda, Together AI, Groq, OpenRouter, Ollama, LM Studio, vLLM, models.dev and LLMWare; the
ratings seed attaches 30 editorial scores with references; the models seed loads 16 top
Hugging Face models.

**Public directory (`/directory`).** A paper-style hero with search, three tabs
(Directory / Rankings / Top models), a curated “Start with these” row, category chips with
counts, price filter, free-tier and Arabic-support toggles, and name/newest/featured sorting.
Each card carries a category colour, initial tile, English and Arabic name, tagline,
“best for”, price, rating and Arabic badges, and two actions: details or the official site.

**Ranking (`/directory/ranked`).** The Nasser AI ranking: 30 tools with an editor score out
of 5, a one-line reason, a source link and a score bar. The page says plainly that it is an
editor score, not a scraped star average, and explains the weights; top three get a podium.

**Models (`/directory/models`).** Hugging Face is the primary source: a dated API snapshot
of the most-downloaded text-generation models, with organisation, parameter count,
downloads, likes, licence and model-card links. The page also links each row to models.dev
for specs and shows four most-downloaded picks from the LLMWare catalogue (Dragon Mistral,
Dragon Yi, SLIM Sentiment, SLIM SQL) for small RAG work. Both secondary sources are linked
at the top, and the page says plainly that downloads are popularity, not quality. Includes
Qwen3, DeepSeek-V3.2/V4-Flash, gpt-oss, Llama 3.1 and SmolLM2.

**Tool page (`/directory/<id>`).** Breadcrumb, header with pricing/rating/Arabic/platform
badges, visit button, bilingual description with the other language behind a disclosure,
“best for” callout, at-a-glance facts, related magazine coverage, and a sidebar with
alternatives, a visit card and an editorial note.

**Admin (`/tools`).** Stats for tools/free tier/Arabic/featured, search, category chips, and
a compact row per tool with its Arabic name, category, price, rating, featured star,
“best for”, Open / Edit / Delete. The add/edit form exposes taglines, pricing, rating, rating
note and reference, free tier, Arabic support, platforms, best-for, featured and sort order.

Checked: 96 cards render across 15 categories; rankings render 30 rows; models render 16
rows with comma-formatted counts; search and filters work; invalid category does not crash;
Arabic view switches category labels and copy; no horizontal overflow at 1440 or 390.

Screenshots: `design-review/shots/admin/tools_directory_final_fold.png`,
`tools_cards.png`, `tools_coding.png`, `tools_rankings.png`, `tools_models.png`,
`tools_detail_final.png`, `tools_detail_coding.png`, `tools_directory_mobile.png`,
`tools_directory_ar.png`, `tools_admin_final.png`.

---

## 12. Recommended projects for Computer Science (added 7 November, later)

A new public section gives final-year students starting points rather than assigned topics.

**Where it lives.** A featured block on `/campus` (“Recommended projects”, number 04) shows
three editor picks; the full page is `/campus/projects`. The department masthead also links
to it.

**What each idea contains.** Title and summary in English and Arabic, a 2–3 sentence brief,
the area (agents, RAG, Arabic AI, learning, vision, audio, security, sustainability, data,
accessibility), difficulty (starter / intermediate / advanced), skills, tools, and a
**reference**: a paper, dataset or shipped product with a one-line note explaining what it is
and what the student should add. Ideas include:

- a cited RAG assistant over the student handbook;
- an Arabic-first campus assistant evaluated against a general model;
- a lecture-to-study-pack pipeline with timestamps;
- a hint-first Python tutor;
- a lab-booking agent with human approval;
- a prompt-injection lab and defence dashboard;
- Arabic OCR for the department archive;
- semantic search over department photos with CLIP;
- accessible lecture captions and a technical glossary;
- an explainable elective recommender;
- a green-AI dashboard;
- a free-study-room forecast;
- an Arabic claim checker with evidence;
- an offline FAQ kiosk on a small model;
- a coding-agent evaluation harness;
- a disclosed AI-video promo;
- a dialect-robustness study of open Arabic models (research track);
- a hint-style learning study (research track);
- a campus accessibility mapping sprint (competition track);
- an LLM security CTF (competition track).

**Interface.** Tracks (Final-year / Research / Competition) and areas, search across titles,
descriptions, skills and tools; area chips with counts; a difficulty filter; clear-filter and
empty states; a “How to turn an idea into a project”
four-step guide (choose a user, read the reference, build a baseline, evaluate with users).
Each card links its reference externally and carries an anchor so the department block can
link straight to it.

**Data and seed.** `ProjectIdea` model (auto-created by `db.create_all`), seeded by
`design-review/tools/seed_projects.py` (16 ideas, idempotent by English title).

Checked: `/campus` shows 3 picks, `/campus/projects` renders 16 cards, area/difficulty/search
filters work, anchors resolve, Arabic view switches the copy, no horizontal overflow at 1440
or 390.

Screenshots: `design-review/shots/admin/campus_projects_block.png`,
`projects_page.png`.

---

## 13. Department admin hub (added 7 November, later)

The old `/department` page was one long form followed by a wall of topic cards. It was
hard to scan and there was no place to manage the photo archive or project ideas.

**New shape.** The page opens on a control header with four live stats (published posts,
hidden posts, photos/albums, project ideas) and four tabs:

- **Compose** — the post form split into The post, When and where, and Link and cover, with a
  sticky Publishing card (show/hide, Publish post) and shortcuts to photos, projects and the
  department archive. The YouTube preview still fills title, summary and cover.
- **Posts & topics** — the kanban board, rebuilt as compact topic lanes with story rows:
  thumbnail, title, source/status, Edit / Hide / Remove. Topic lanes and story cards remain
  SortableJS draggable; the existing reorder APIs are unchanged.
- **Photo archive** — counts, a public-archive link, the latest albums (cover, title, photo
  count, term), and a large “Create the first album” empty state. Uploads stay in the
  existing `/department/photos` screen.
- **Project ideas** — all 20 ideas with track, area, difficulty and reference; Edit / Remove
  per row and New idea.

**Project CRUD.** `/department/projects/new` and `/department/projects/<id>/edit` use the
same card layout as the story editor, with track (final year / research / competition),
area, difficulty, skills, tools, reference title/URL/notes, featured and published switches.
Saving returns to `/department#projects`.

**Tracks.** `ProjectIdea.track` is migrated at startup; the public projects page now filters
by Final-year, Research and Competition. Four new entries were seeded: dialect robustness of
open Arabic models, a hint-style learning study, a campus accessibility sprint and an LLM
security CTF.

Checked: tabs switch without reload, counts are live, 20 project rows render, project
create/edit/delete works (test row created and removed), posts board still drags, photo
empty state renders, Arabic labels switch, no console errors.

Screenshots: `dept_compose.png`, `dept_posts.png`, `dept_photos.png`, `dept_projects.png`,
`dept_project_form.png`.

---

## 14. Worth Watching — curated YouTube page (added 7 November, later)

The page was empty: no `CuratedReel` rows, so `/watch` showed only the empty state.

**Content.** Five YouTube videos are now seeded, each with a thumbnail, creator, English
and Arabic title, English and Arabic editorial summary, and the original link:

- Two Minute Papers — OpenAI's Astra interpretability work;
- DW News — the AI investment boom and the market wobble;
- Fireship — a theoretical CS result explained quickly;
- The Next Signal — a weekly model/tool roundup;
- UpskillAI — practical ChatGPT/Gemini/Canva updates.

**Page.** A v3 “Worth watching” hero, one large editor's pick with the thumbnail and a
reason to watch, then a three-column grid for the rest. Every card opens the original
creator in a new tab; the page never re-hosts video. A “How we choose” note explains the
editorial rule, and the footer links to the issue, tools and project ideas.

**Data and admin.** `CuratedReel` holds the cards; `design-review/tools/seed_reels.py`
creates/updates them idempotently by YouTube URL. The existing `/reels` admin list and
`/reels/add` form can edit or add more; the homepage reels band and the Watch nav count
pick them up automatically.

Checked: `/watch` returns 5 items (1 feature + 4 cards), all thumbnails load from
`img.youtube.com`, no console errors, no horizontal overflow at 1440 or 390, Arabic copy
switches correctly.

Screenshots: `design-review/shots/admin/watch_page.png`, `watch_mobile.png`,
`watch_ar.png`.

---

## 15. Department downloads (added 8 November)

A department file shelf for course notes, syllabi, policies, forms and workshop material.

**Public.** `/campus/downloads` — search, category chips (notes, syllabus, policies, exams,
workshops, other), file-type badges (PDF, DOCX, PPTX, XLSX, TXT, ZIP), course, size, date,
download count, and a direct download. The department page gets a numbered **Downloads**
section with the latest six files, plus links in the masthead and footer.

**Admin.** `/department/resources` lists every file with category, course, size, download
count and published state; upload/edit/delete are separate simple routes. The department
hub has a **Downloads** stat and shortcut. Allowed types are PDF, Word, PowerPoint, Excel,
text and ZIP; files are served as attachments with a sanitized stored name, and the original
name is preserved for the download.

**Data.** `DepartmentResource` model (auto-created by `db.create_all`); files live in
`app/static/uploads/resources/` (ignored by Git). `RESOURCE_CATEGORIES` holds the labels.
Upload, download, edit and delete were tested end-to-end; a temporary test file was removed.

Checked: `/campus/downloads` renders and filters, the download endpoint returns the file,
the admin list/form work, and the department page shows the section only when files exist.

Screenshots: `design-review/shots/vps/downloads_public.png`, `downloads_admin.png`.
