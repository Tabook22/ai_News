# BUILD_NASSER_NEWS.md — Nasser AI News (Master Instruction File)
Purpose:
This file is the single source of truth that programs an AI agent to generate the entire "Nasser AI News" codebase.
Follow steps in order. Do not skip. Do not invent features.

Project:
Nasser AI News — Bilingual (English/Arabic) AI News Magazine

Stack:
- Backend: Python + Flask
- Database: PostgreSQL (mandatory, no JSON storage)
- ORM: SQLAlchemy (Flask-SQLAlchemy)
- Frontend: Jinja templates + Vanilla JS
- Config: python-dotenv (.env)

========================================================
0) TARGET FOLDER STRUCTURE (MUST MATCH EXACTLY)
========================================================
nasser_ai_news/
├── agent/
│   ├── identity.md
│   ├── rules.md
│   ├── workflows.md
│   └── skills/
│       ├── news_fetcher/
│       │   ├── SKILL.md
│       │   ├── actions.py
│       │   ├── google_search.py
│       │   └── ddg_search.py
│       ├── translator/
│       │   ├── SKILL.md
│       │   ├── actions.py
│       │   └── translation_api.py
│       └── media_handler/
│           ├── SKILL.md
│           ├── actions.py
│           └── image_extractor.py
├── app/
│   ├── app.py
│   ├── utils.py
│   ├── models.py
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css
│   │   ├── js/
│   │   │   └── scripts.js
│   │   └── uploads/
│   │       ├── images/
│   │       └── docs/
│   └── templates/
│       ├── layout.html
│       ├── dashboard.html
│       ├── search.html
│       └── magazine_view.html
├── migrations/                 (optional future: Alembic/Flask-Migrate)
├── .env
├── requirements.txt
└── README.md

========================================================
1) GLOBAL PRODUCT RULES (NON-NEGOTIABLE)
========================================================
UI Rules:
- Dark theme is mandatory. Base background: #0f172a
- Unified Top Navigation must exist in layout.html
- Do NOT create "Go Back" buttons anywhere.
- Bilingual display is side-by-side: English (left) + Arabic (right)
- Arabic column must be RTL (direction: rtl) but the whole page is not RTL.

Upload Rules:
- When sending files/images from the browser to Flask, ALWAYS use FormData.
- No JSON upload payloads for files.

Code Rules:
- Keep functions small and testable.
- Skills must be runnable independently from Flask (CLI testable).
- No breaking changes to file paths or naming.
- No secrets in code. Use .env.

========================================================
2) DATABASE RULES (MANDATORY)
========================================================
- PostgreSQL is the only persistence layer.
- JSON files must NOT be used for storage.
- Use SQLAlchemy ORM only (no raw SQL unless necessary).
- All database models must live in app/models.py.
- DB credentials MUST be loaded from .env.
- URL must be UNIQUE to prevent duplicates.
- Add indexes for commonly queried fields (published_at, source).

Environment variable:
DATABASE_URL=postgresql://user:password@localhost:5432/nasser_ai_news

========================================================
3) PHASE 1 — SETUP (FOUNDATION)
========================================================
Step 1: Create all folders exactly as specified (including empty placeholder folders).
Step 2: Create Python virtual environment and install dependencies.
Step 3: Create requirements.txt with at least:
- Flask
- requests
- python-dotenv
- Flask-SQLAlchemy
- psycopg2-binary
Optional if needed:
- beautifulsoup4

Step 4: Create PostgreSQL database locally:
- Database name: nasser_ai_news

Step 5: Create .env with at least:
- DATABASE_URL=postgresql://user:password@localhost:5432/nasser_ai_news
Optional (if used later):
- GOOGLE_API_KEY=...
- GOOGLE_CSE_ID=...
- TRANSLATION_API_KEY=...

========================================================
4) PHASE 2 — DEFINE THE BRAIN (agent/)
========================================================
Create agent/identity.md:
- Persona: Expert Full-Stack Flask developer + UI designer
- Mission: Build bilingual AI news magazine for students
- Output standards: clean code, predictable structure, minimal dependencies

Create agent/rules.md:
- Repeat UI rules (dark theme, top nav, no go-back)
- Repeat FormData rule
- Never hardcode secrets; use .env
- Always keep bilingual output side-by-side (EN then AR)
- PostgreSQL only; no JSON persistence

Create agent/workflows.md with SOPs:

Workflow A: Daily Aggregation Loop
1) Search sources (Google/DDG)
2) Filter: last 24h + relevance + credibility
3) Normalize metadata: title, url, source, published date, snippet
4) Translate key fields (title + snippet/summary) to Arabic
5) Extract OG image or use placeholder
6) Save to PostgreSQL (dedupe by URL)
7) Render Magazine view

Workflow B: Manual Search UI Flow
1) User enters query
2) Call news_fetcher skill
3) Preview results
4) User selects items to save
5) Saved items appear in dashboard
6) Magazine reads from DB

========================================================
5) PHASE 3 — BUILD SKILLS (agent/skills/)  [CRUCIAL]
========================================================
All skills must follow this standard contract in SKILL.md:
- Title
- Description
- Inputs
- Steps
- Outputs (JSON schema if applicable)
- Errors
- CLI Test (how to run actions.py)

All skills must be runnable independently from Flask:
- Each skill’s actions.py acts as the single entry point.

A) Skill: news_fetcher
Files:
- SKILL.md
- actions.py
- google_search.py
- ddg_search.py

Functional goals:
- Inputs: query string, time_window_hours (default 24), max_results
- Output: list of normalized items:
  {
    "title": "...",
    "url": "...",
    "source": "...",
    "published": "ISO string or empty",
    "snippet": "..."
  }

actions.py responsibilities:
- Validate inputs
- Call ddg_search and/or google_search
- Merge + deduplicate by URL
- Filter to last 24h if possible (best-effort; do not break if date missing)
- Print JSON to stdout when run as CLI

B) Skill: translator
Files:
- SKILL.md
- actions.py
- translation_api.py

Functional goals:
- Inputs: English text (string) OR list of strings
- Output: Arabic text (string) OR list of strings

Rules:
- Arabic must be Modern Standard Arabic and easy for students.
- Keep critical technical terms in English in parentheses if needed.
- If no API key exists, provide a safe fallback that returns the input with a clear marker (so the pipeline still runs).

C) Skill: media_handler
Files:
- SKILL.md
- actions.py
- image_extractor.py

Functional goals:
- Input: article URL
- Output: best image URL (og:image) OR empty string

Rules:
- image_extractor fetches HTML and parses meta property="og:image"
- If missing, return empty string and UI must show a placeholder

========================================================
6) PHASE 4 — DATABASE DESIGN (PostgreSQL)
========================================================
Create app/models.py using Flask-SQLAlchemy.

Required table: NewsItem
Fields:
- id (PK, integer)
- title_en (text, required)
- title_ar (text, optional)
- summary_en (text, optional)
- summary_ar (text, optional)
- source (string, optional)
- url (string, required, UNIQUE)
- image_url (text, optional)
- published_at (datetime, optional)
- created_at (datetime, required, auto now)

Rules:
- URL is unique (dedupe key)
- Add indexes:
  - published_at
  - source
  - created_at

DB initialization approach (choose simplest):
- Use db.create_all() on app startup (development-friendly).
Optional future:
- Use Flask-Migrate/Alembic under migrations/

========================================================
7) PHASE 5 — BUILD THE BODY (Flask app/)
========================================================
A) app/app.py (Flask routes)
Required routes:
- GET /               -> redirect to /dashboard
- GET /dashboard      -> show saved items from PostgreSQL + simple stats
- GET /search         -> search page UI
- POST /search        -> run news_fetcher skill and show results preview
- POST /save          -> save selected item to PostgreSQL (dedupe by URL)
- GET /magazine       -> render magazine_view from DB

Implementation rules:
- Separate concerns: route handlers call small helpers in utils.py
- Use SQLAlchemy session via db (Flask-SQLAlchemy)
- Handle missing Arabic fields gracefully (still show English)

B) app/utils.py
Must include:
- normalize_item(raw_item) -> safe dict
- dedupe_by_url(items) -> list
- parse_datetime_best_effort(value) -> datetime|None
- db helpers:
  - get_recent_items(limit, sort)
  - save_item_if_new(item_dict)

C) UI templates
layout.html:
- unified top nav links: Dashboard | Search | Magazine
- include CSS and JS
- consistent container layout

dashboard.html:
- show saved news list (latest first)
- show basic stats: total items, items last 24h

search.html:
- search box
- show results cards
- each result has "Save" action (POST /save)
- include preview of bilingual fields if translator is applied

magazine_view.html:
- bilingual columns (EN left, AR right)
- Arabic column RTL only
- readable typography for Arabic and English
- minimal, clean layout

D) Static
styles.css:
- dark theme variables
- cards, nav, typography, spacing
- ensure good contrast on #0f172a background

scripts.js:
- If any uploads exist, use FormData
- simple client helpers only (no frameworks)

========================================================
8) TESTING CHECKLIST (MUST PASS)
========================================================
Skill tests (CLI):
- Run news_fetcher/actions.py with a sample query -> prints JSON list
- Run translator/actions.py on sample text -> prints Arabic or fallback output
- Run media_handler/actions.py on a URL -> prints image URL or empty

Database tests:
- App can connect to PostgreSQL via DATABASE_URL
- NewsItem table created successfully
- Saving same URL twice does not duplicate

App tests:
- Flask app starts
- /search returns results
- saving an item writes into PostgreSQL
- /dashboard shows saved items
- /magazine renders bilingual layout correctly

========================================================
9) README.md MINIMUM
========================================================
Include:
- What the project is
- How to install (venv + pip install -r requirements.txt)
- How to set up PostgreSQL + DATABASE_URL
- How to run Flask
- How to run each skill standalone (CLI)
- .env template keys

End of BUILD_NASSER_NEWS.md
