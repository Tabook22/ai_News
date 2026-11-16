# Nasser AI News

Bilingual (English/Arabic) AI News Magazine — curate stories, publish a magazine-style reader,
and grow an email newsletter you can promote with a printable QR code (e.g. on your door).

## Installation

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment:
   Copy `.env.example`-style keys below into your own `.env`:
   ```
   FLASK_APP=app/app.py
   FLASK_ENV=development
   SECRET_KEY=change_me_please
   DATABASE_URL=sqlite:///local_dev.db

   # Admin dashboard login — change these before putting the site online
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123

   # Optional AI/search integrations
   OPENAI_API_KEY=
   GOOGLE_API_KEY=
   SEARCH_ENGINE_ID=
   YOUTUBE_API_KEY=
   ```

For production, prefer setting `ADMIN_PASSWORD_HASH` (a `werkzeug.security.generate_password_hash`
   value) instead of a plaintext `ADMIN_PASSWORD`.

   **Never commit .env.** It is ignored by Git; use .env.example as the template.
   If a real .env is ever pushed, rotate the admin password and every API key.

## Deployment at /ainews/

See [deploy/DEPLOY.md](deploy/DEPLOY.md) for the VPS/Gunicorn/Nginx setup at
https://nasserdiary.com/ainews/, including SSL, .env, and update steps.

## Running the App

```bash
flask run
```
Access at `http://127.0.0.1:5000`.

### Public reader (v3)

The reader-facing magazine was rebuilt in November 2026: a 90-second brief, one cover
story, three world cards, the department week, a course band, editor's picks, and a
newsletter band — plus a new article page, public search, and a real department page.

- `/magazine` — the issue
- `/magazine/article/<id>` — a story
- `/campus` — the department
- `/campus/projects` — recommended final-year projects with references
- `/watch` — curated YouTube videos on AI news and technology
- `/find` — public search and every published story
- `/learn` — flashcards and a 10-question quiz on AI terms (progress is kept on the reader's own device)
- `/glossary` — the bilingual AI glossary: 49 starter terms, searchable, with a term of the day on the front page
- `/board` — the student board: questions, ideas, and useful links from students, published only after the editor approves them
- `/directory` — the AI tools directory (search, filters, 96 curated tools)
- `/directory/<id>` — one tool, with alternatives and related coverage
- `/directory/ranked` — the Nasser AI ranking, 30 scored tools with references
- `/directory/models` — most-downloaded open LLMs, a Hugging Face snapshot
- `/sitemap.xml`, `/robots.txt` — crawler basics

The previous design is still available: add `?classic=1` to `/magazine`, `/campus`, or an
article URL. See `design-review/IMPLEMENTATION.md` for what changed and
`design-review/UX_AUDIT_AND_REDESIGN.md` for the reasoning.

### Admin

- `/admin` — the editor's control room (login required)
- `/` — the newsroom landing page (login required)
- `/tools` — manage the AI tools directory
- `/desk/board` — review student posts: publish, reply, pin, decline, or delete (a badge in the sidebar shows how many are waiting)
- `/desk/glossary` — edit, hide, or add glossary terms (starter terms can be hidden but not deleted)
- `/settings` — magazine settings, with per-section help
- `/subscribe` — the public newsletter sign-up page (point your door QR code here)
- `/qr` — admin page to view/download/print the QR code for `/subscribe`
- `/subscribers` — admin list of everyone who signed up, with CSV export

## The Newsletter / QR Workflow

1. Open **QR Code** in the admin nav (`/qr`) while logged in.
2. Download the PNG and print it — at least 5×5 cm so phones can focus on it easily.
3. Stick it on your door, a flyer, or a business card. Anyone who scans it lands on
   `/subscribe` and can join in one tap (bilingual, no password needed).
4. Track everyone who joins on the **Subscribers** page (`/subscribers`); export the
   list as CSV any time to import into your email tool of choice.

## Running Skills Standalone

**News Fetcher:**
```bash
python agent/skills/news_fetcher/actions.py "Artificial Intelligence"
```

**Translator:**
```bash
python agent/skills/translator/actions.py "Hello World"
```

**Media Handler:**
```bash
python agent/skills/media_handler/actions.py "https://example.com"
```

## Notes / Recent Fixes

- Startup no longer crashes on Windows terminals using the legacy `cp1252` codepage
  (stdout/stderr are forced to UTF-8) — emoji status logging used to kill the process
  before the server could start.
- The "custom text/accent color" and per-tag color overrides in Settings were silently
  broken (malformed template syntax dumped literal Jinja text into the page `<style>`
  block); they now apply correctly.
- Admin login credentials moved out of source code and into `.env`.
# ai_News


