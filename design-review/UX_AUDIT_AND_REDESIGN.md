# Nasser AI News — UX/UI Audit & Audience Growth Plan

- **Prepared:** 6 November 2026
- **Scope:** the public (reader-facing) magazine: `/magazine`, the article page, department, watch, tools, photos, subscribe, and the shared layout/design system.
- **Method:** full read of the Flask routes, all 39 templates and 124 KB of CSS; a scripted visual audit of the running app (Edge/Playwright) at 1440 px and 390 px, in English and Arabic, including print media; live data from `app/instance/local_dev.db`; and a rebuilt prototype of the front page and article page.

> Everything below is measured from the app as it runs today, not from the design intent in `BUILD_NASSER_NEWS.md`. Where the two disagree (for example, the brief mandates a dark theme; the saved setting is light), this audit describes what readers actually see.

---

## 1. The short version

The magazine does not have an attention problem. It has a **focus problem, a depth problem, and a distribution problem**.

- **Focus:** the front page is **13,755 px tall on a laptop and 32,212 px on a phone** — about 38 phone screens — carrying 69 images and roughly 60 story cards with no hierarchy beyond "cover, then everything". A reader cannot tell what to read first, so most read nothing.
- **Depth:** **69 of 71 published stories have no article body.** The "article" page renders a single ~30-word summary in bold and then a large button that sends the reader to the publisher. The magazine is currently a link blog wearing a newspaper costume.
- **Distribution:** every public content URL returns a **language gate with HTTP 200** to anyone without a cookie, so search engines, WhatsApp previews, and first-time readers all see the same choice screen instead of the story. There is no sitemap, no RSS, no canonical URL, no public search, no public archive, no analytics. In this database: **32 total article views, 0 subscribers, 1 comment.**

The good news: the raw material is unusually strong. The two-desk idea (department life vs. the world), the bilingual edition, the source-first attribution, the "why this belongs in class" bridge, the photo archive, and the AI reading companion are genuinely distinctive. The redesign is not about throwing that away. It is about **giving it an order, a depth, and a reason to come back**.

The proposal in one sentence:

> **One weekly issue of about 20 stories, opened by a 90-second brief, led by one story worth five minutes, and finished with a class layer that turns the news into revision — on a paper-calm design system that works on a 3G phone in Arabic first.**

![Front page: current vs proposed](shots/compare_front_1440.jpg)

*Left: today. Right: the proposed front page, built as a working prototype with the real stories and images. Same content, one third of the length.*

---

## 2. What the audit measured

| Measure | Today | Notes |
|---|---|---|
| Front page height, 1440 px | **13,755 px** | 69 images, ~60 cards |
| Front page height, 390 px | **32,212 px** | ≈ 38 screens; nav clipped |
| Article page height, 1440 px | **7,919 px** | its sidebar carries a 71-story archive list |
| Article body length | **median 171 characters** | 69/71 stories have no `full_content` |
| Published stories | 71 | 4 campus, 13 research, 56 world |
| Stories with images | 66 | 62 are hotlinked from publishers |
| Images lazy-loaded | **1** | and it is on the editor's CV page |
| CSS shipped | **116 KB**, 3 files | plus 83 KB inline in templates |
| Fonts per page | **5 families / 10 weights** | plus a render-blocking `@import` |
| Public search | **none** | `/search` is admin-only |
| Public archive | **none** | `/archive` is admin-only |
| Analytics / consent | **none** | `views += 1` on article GET only |
| Subscribers | **0** | no double opt-in, no confirmation |
| Total article views | **32** | 61 of 71 published stories have never been opened |
| Accessibility | no `<main>`, no skip link, 8 unlabelled images, 3 modals without dialog semantics | see §5 |

**Caveat:** this is the local development database. Production numbers may differ, but every structural finding below is in the code, not in the data.

---

## 3. What readers actually experience

### 3.1 The front page asks for too much before it gives anything

The current front page opens with: a masthead, two "desk doors" that look like a table row, a pink YouTube strip, two competing covers, a four-image rail with four different aspect ratios, an opening spread, a photo wall, a three-room department block, a course band, a classroom bridge, desk chips, and finally the story grid — then a "back of the book".

On a phone, the **first actual headline is about two screens down**, and the nav cuts off at "NEWS PHO…". The page never says *start here*.

Compounding it:

- The same department workshop appears **three times** on one page (cover, week board, "Department life").
- The world cover appears again under "Also from the world".
- Two covers compete for the same job, so neither wins.
- The picture rail numbers its items 02–05 because 01 is the cover — a numbering system only the editor can decode.
- The image on the campus cover **contains the headline**, which is then printed again underneath.

### 3.2 The article page has no article

`magazine_detail.html` prints the summary as body copy, bold, then shows a gradient card that says **"Read the Full Story"** and links off-site. In Arabic, the Arabic headline is printed twice and the Arabic body inherits Playfair Display — a Latin-only font — so the most important text on the page falls back to an arbitrary system serif.

Before the story begins, the reader scrolls past a 100 px logo, a 4.5 rem site title, "VOL. 1 / date / PREMIUM EDITION", an "Editor-in-Chief" pill, a breadcrumb that says only "← The department", and a meta line that includes the **raw source URL in uppercase**.

What is missing is exactly what a student needs: *what happened, why it matters, what to say in class*.

### 3.3 The magazine cannot be found or shared

Every public content route calls `_render_language_gate()` when the `lang_pref` cookie is absent and returns it with status 200. Consequences:

- Googlebot, LinkedIn, WhatsApp and X never set that cookie, so every shared link previews the gate — in English — regardless of the story.
- There is no `robots.txt`, `sitemap.xml`, RSS feed, canonical tag, `hreflang`, or `NewsArticle` structured data anywhere in the repo.
- Story titles average 68 characters (max 148) and non-article pages all share one title and one description.
- The share image for every non-article page is the 280 KB logo PNG; `twitter:image` is never set.

For a magazine whose entire growth plan is a QR code on a door, **the link is the product**, and the link is currently broken for anyone who is not already a returning reader.

### 3.4 Navigation promises rooms that are empty

The reader bar has **nine links plus three language toggles**. Three of those rooms are empty in this database (`/watch`: 0 reels, `/directory`: 0 tools, `/campus/photos`: 0 albums), `/campus` has 4 stories, and `/archive` — the one label readers will look for — is a login wall.

Naming is also inconsistent: `/department` is the admin desk while `/campus` is the public "Department"; `/tools` is admin while `/directory` is public; `/search` is admin-only.

### 3.5 Mobile is an afterthought

- The nav is a horizontal scroller with no fade, arrow, or hamburger; tap targets are **~28 px** (44 px is the minimum).
- The article sidebar becomes a **full archive tree of all 71 stories** after the article, on a single column.
- The fixed chat bubble, the sticky two-row header, the progress bar, and two modals compete for z-index and thumb space.
- `secondary-grid` uses `minmax(300px, 1fr)` inside a 320 px viewport with 2×0.9 rem padding — a guaranteed horizontal scroll on small phones.
- The modal close button on the video overlay sits at `top: -40px` inside `overflow: hidden`, i.e. partly invisible.

### 3.6 The visual system has no contract

There is a token *vocabulary* but no token *system*:

- 14 palette variables re-declared **12 times** (4 admin themes + 8 magazine templates).
- **294 hex literals**, 117 unique; **589 `!important`**; 12 breakpoints; 19 card surfaces; 56 font sizes, 36 of them below 12 px.
- The saved "custom accent colour" is injected at `:root` with `!important` — currently `#000000`, which turns every accent, chip and pill black and produces white-on-cyan pills at **2.14:1** contrast.
- Arabic body font is wrong (see 3.2), and `dir="rtl"` is used ~50 times with a `lang` attribute exactly once.
- **Printing is broken on dark themes**: `body { color: black }` is overridden by every `color: var(--text-main)`, so text prints light-on-white; gradient-clipped titles print blank; there is no `@page`, no link URLs, no page breaks.
- The admin dashboard hardcodes `#0f172a` headings, so the moment someone switches the site theme away from light, the admin becomes unreadable (1:1 contrast).

None of this is visible to a reader as "bad CSS". It shows up as the thing they actually feel: **the page looks like a link dump, not a publication**.

---

## 4. Who the readers are (and what they are hiring the magazine to do)

The magazine serves four audiences with different jobs:

| Audience | Job to be done | What they need from the page | What blocks them today |
|---|---|---|---|
| **CS students (Arabic-first)** | "Catch me up in 3 minutes; tell me what matters for my course." | Arabic headline first, a short brief, a class angle, phone-first speed | English-first gate, 38-screen scroll, machine-translated body, no class layer |
| **Students (English-first)** | "What happened in AI this week that I should know?" | A ranked brief, one deep story, sources | No hierarchy, no article body, broken search |
| **Faculty / department** | "What is happening in my department, and is this credible?" | Dates, events, student work, byline, standards | Admin-only archive, no editorial policy, no AI disclosure |
| **Prospective students / visitors (QR)** | "What is this place?" | A beautiful, fast first screen with one clear action | Language gate, no context, gate previews the wrong story |

The design implication is blunt: **the first screen must serve the 3-minute student**, and everything else must be one tap away. The current page serves the editor's mental model of a newspaper instead.

---

## 5. What to keep (do not redesign these away)

1. **The two desks.** Department vs. world is the magazine's identity. Keep it — but as two *sections in one ordered page*, not two competing covers.
2. **Bilingual parity.** Every story already has Arabic title and summary. That is rare and valuable.
3. **Source-first attribution.** The source link on every card and the original-article CTA are trust assets.
4. **"Why this belongs in class."** This is the single most differentiated idea in the product. It is currently one band near the bottom of a 13,000 px page.
5. **The editor's voice and photo archive.** A named editor with a face beats an anonymous aggregator.
6. **"Ask the Magazine."** A grounded, cited reading companion is a strong retention feature — if readers can find it.

---

## 6. The redesign

### 6.1 Five principles

1. **One issue, one path.** Every screen answers one question and offers one next step. The front page is a funnel, not an archive.
2. **Depth over volume.** 15–20 curated stories a week beat 71 dumped links. A story without a body, an image, and a "why" is a *brief*, not an article.
3. **Arabic is not a translation layer.** Design RTL and Arabic typography first, then mirror to English. One language switch, remembered.
4. **Paper calm, digital speed.** Hairlines, generous margins, two colours, real photography; no glassmorphism, no shadows on every card, no 12 breakpoints.
5. **The link is the product.** Every story has a clean URL, a share image, a title, and a WhatsApp message that works without a cookie.

### 6.2 New information architecture

```
The Issue        /                     front page (weekly)
Department       /department           campus life, events, photos, student board
Watch            /watch                reels + YouTube shelves, one permalink per clip
Tools            /tools                public AI tool directory
Search           /search               public full-text search
Archive          /archive              public, by issue/week
About            /about                editor, standards, corrections, AI disclosure
```

Header (desktop): wordmark · The Issue · Department · The World · Watch · Tools · search icon · EN | ع · Subscribe.
Mobile: brand + search + language in the bar; **five bottom tabs** (Issue, Department, World, Watch, Search).

Why: 9 links + 3 language buttons become 5 + 1. Empty rooms stop being advertised; they are merged (`/watch` + `/youtube`) or hidden until they have content.

### 6.3 Front page blueprint

```
┌──────────────────────────────────────────────────────────────┐
│ header: brand · sections · search · EN|ع · Subscribe         │
├──────────────────────────────────────────────────────────────┤
│ masthead: name · Issue 12 · Thu 6 Nov · 9 stories · PDF      │
├──────────────────────────────────────────────────────────────┤
│ THE 90-SECOND BRIEF        01 ─ 05 numbered lines            │
│ (label + 3 min read)       headline + source, two columns    │
├───────────────────────────────────────┬──────────────────────┤
│ LEAD STORY                            │ THIS WEEK IN THE     │
│ 16:9 image · kicker · H1 · dek        │ DEPARTMENT (3 dates) │
│ What happened / Why it matters /      │ TERM OF THE DAY      │
│ In class · byline · 4 min             │ PRINT ISSUE (A4 PDF) │
├───────────────────────────────────────┴──────────────────────┤
│ 02  THE WORLD, IN ORDER OF USEFULNESS      All 67 stories →  │
│ 3 cards + 5 one-line briefs                                  │
├──────────────────────────────────────────────────────────────┤
│ 01  INSIDE THE DEPARTMENT                  Department issue →│
│ 3 dated items + photo strip │ Coming up + student board      │
├──────────────────────────────────────────────────────────────┤
│ COURSE OF THE WEEK — dark band, 4 slots, quiz CTA            │
├──────────────────────────────────────────────────────────────┤
│ 03  EDITOR'S PICKS · 3 rows                                  │
│ SUBSCRIBE band                                               │
├──────────────────────────────────────────────────────────────┤
│ footer: sections · standards · corrections · RSS · contact    │
│ AI disclosure + privacy line                                 │
└──────────────────────────────────────────────────────────────┘
```

Rules that make it work:

- **Hard limits.** 1 lead, 3 features, 5 briefs, 3 department items, 3 picks. Everything else lives in the archive. The `has_more` flag already exists in `app.py:3721`; use it.
- **No duplicates.** A story appears once on the front page; the brief links to the same URL but does not repeat the card.
- **Every section has a number and a one-line purpose.** The number is the reading order, not decoration.
- **The brief is the product.** Five lines, each a complete thought with a source, readable in 90 seconds on a phone.
- **The department has equal billing, earlier.** It is the reason a student at Dhofar University opens this instead of TechCrunch.

### 6.4 Article page blueprint

```
breadcrumb · kicker · H1 · dek
byline (photo, name, role) · date · read time · Save
┌ IN 30 SECONDS ──────────────────────────────┐
│ What happened · Why it matters · In class    │
└──────────────────────────────────────────────┘
hero 16:9 + caption + credit
body 60–70ch, drop cap, subheads, pull quote,
inline term definitions, source callout
┌ CHECK YOURSELF — 3 questions ───────────────┐
│ 3 MCQs, instant feedback, score              │
└──────────────────────────────────────────────┘
Original reporting + why we chose it · share/save
Read next (same desk) · prev/next
```

What changes vs. today:

- Headline becomes the `h1`; the masthead shrinks to a 40 px bar with breadcrumb.
- The raw URL disappears from the meta line.
- The summary becomes a **dek**, not a bold paragraph.
- The "Read the Full Story" card moves below the body, reframed as attribution, with an editor's note on why the story was chosen.
- Arabic and English are one switch, in place; no side-by-side wall on mobile.
- Every story carries a **class layer**: term, discussion question, and three quiz questions.

![Article: current vs proposed](shots/compare_article_1440.jpg)

*Left: the story starts third, after the masthead; body is one bold paragraph. Right: headline first, a 30-second brief, then a real body, then a quiz.*

### 6.5 Design system (the contract)

**Tokens, once.** One palette block with `light`, `dark`, and `print` variants. No per-template redefinition; templates become *layout variants* that consume the same tokens.

```css
:root{
  --paper:#fbfaf7; --surface:#fff; --ink:#14161a; --ink-2:#33373e;
  --muted:#6e7178; --rule:#e4e0d6; --rule-strong:#c9c3b4;
  --brand:#0b4f6c; --accent:#b45309;
  --campus:#0f766e; --world:#1e3a8a;
  --serif:"Playfair Display",Georgia,serif;
  --body:"Source Serif 4",Georgia,serif;
  --sans:"Inter",system-ui,sans-serif;
  --ar:"Amiri",serif; --ar-ui:"Cairo",sans-serif;
}
@media print{ :root{ --paper:#fff; --ink:#000; --muted:#333; --rule:#bbb; } }
```

**Type scale** (six sizes, not 56): 12 / 14 / 16 / 18 / 22 / 32 / 48 / 64; body 18 px / 1.7; measure 60–70 characters; Arabic 1.2 rem / 1.95.

**Spacing** 4/8/12/16/24/32/48/64. **Radius** 4 and 8 only. **Breakpoints** 1280 / 900 / 560 (three, not twelve).

**Components** (one of each, not nineteen cards): `Lead`, `StoryCard` (3 densities: lead / standard / row), `BriefRow`, `SectionHead`, `Panel`, `AgendaItem`, `DateChip`, `TermCard`, `Quiz`, `SubscribeBand`, `Footer`.

**Images**: fixed aspect ratios (16:9 lead, 4:3 department, 1:1 strip), `object-fit: cover`, explicit `width`/`height`, `loading="lazy"` below the fold, `fetchpriority="high"` on the LCP cover, `srcset` at 480/960/1440, and a designed fallback tile instead of a broken image or a scraped logo.

**Bilingual**: one `EN | ع` switch; `dir` and `lang` set together; `lang="ar"` on every Arabic block; logical CSS properties (`margin-inline`, `inset-inline`) so RTL is not a patch layer; Arabic default when the browser language is `ar` or the reader chose it.

### 6.6 What the prototype demonstrates

A working prototype is included in [`prototype/index.html`](prototype/index.html) (front page) and [`prototype/article.html`](prototype/article.html) (article). It uses **the real stories, images and Arabic titles from the database**, and implements:

- the 90-second brief, lead, world, department, class band, editor's picks, subscribe band;
- the article TL;DR, pull quote, term callout, source box, save, share, related;
- an interactive 3-question quiz with scoring;
- one language switch that flips the entire page to RTL with Arabic typography;
- a public search overlay (Ctrl/⌘ K), mobile tab bar, skip link, focus styles, `aria-live` status, print stylesheet.

Open it with any static server (`python -m http.server`) or the path above. Screenshots: [`shots/`](shots/).

---

## 7. New ideas to make the magazine wanted

Ranked by impact on a student's decision to open it again. Effort is engineering + editorial, in days.

| # | Idea | Why it earns a return visit | Effort | Impact |
|---|---|---|---|---|
| 1 | **The 90-second brief** — five numbered lines at the top of every issue | Gives a reason to open the page even when there is no time to read | S | ★★★ |
| 2 | **Class Mode on every story** — term, why-it-matters, 3-question quiz, course tag | Turns reading into revision; a lecturer can assign it; students share it | M | ★★★ |
| 3 | **Public search + archive by issue** | The first thing a reader does after "I remember a story about…" | S | ★★★ |
| 4 | **WhatsApp-first sharing + channel** | WhatsApp is where Omani student groups actually live; one tap to the group | S | ★★★ |
| 5 | **Follow a desk + Sunday digest** | Converts a one-off visit into a weekly habit; the email becomes the product | M | ★★★ |
| 6 | **Save for later / continue reading** | Half-read stories are the strongest return trigger | S | ★★ |
| 7 | **Department calendar + .ics + reminders** | Utility no aggregator has: exams, workshops, deadlines | S | ★★ |
| 8 | **A real print edition (4-page A4 PDF)** | Corridor presence, QR back to the site, something to hand a visitor | M | ★★ |
| 9 | **Issue cover + poster generator** | A shareable object ("Issue 12") and a printable QR poster per issue | M | ★★ |
| 10 | **Student bylines, guest picks, photo submissions** | Belonging: students read what their classmates wrote | M | ★★ |
| 11 | **One-tap feedback + analytics** | Tells the editor what to publish; today there is zero signal | S | ★★ |
| 12 | **PWA: installable, offline last issue, push** | The magazine on the home screen, readable in a lab with no Wi-Fi | M | ★ |
| 13 | **Audio version (TTS) of the brief** | Listening while walking between classes | S | ★ |
| 14 | **Polls and quiz leaderboard** | Light gamification tied to courses, not vanity points | M | ★ |

### Three feature specs worth spelling out

**A. Class Mode (the differentiator).**
Every story gets four optional fields that already exist in the model (`lesson_why`, `lesson_term`, `lesson_gloss`, `lesson_ask`) plus a new `course` tag and a `quiz_json`. On the article page they render as a boxed "For class" section; on the front page, one story per issue is promoted into the dark "Course of the week" band. The quiz is 3 MCQs, instant feedback, no login, score kept in `localStorage`. Lecturers can project the question of the week; students can screenshot the term card. This is the feature that makes the magazine *useful* rather than merely interesting — and it is 80% built already.

**B. The weekly issue object.**
Give every week a number, a date, a cover image, and a permanent URL (`/issue/12`). The issue page is the current front page frozen at publication; the archive lists issues, not 71 loose stories. This makes sharing, printing, and "what did I miss?" trivial, and gives the editor a natural deadline: the issue closes on Sunday.

**C. WhatsApp loop.**
Every article gets a `wa.me/?text=` share with a pre-written bilingual message (`📌 [Arabic headline] — [link]`), plus a WhatsApp Channel link in the header/footer. Every issue gets a QR poster (A4, cover image, "Issue 12", QR to the issue URL) generated by the existing `qrcode` dependency. The door QR stays, but it points at the *issue*, not only at a subscribe form.

---

## 8. Roadmap

### Week 1 — stop the bleeding (P0, ~2–3 days)

| Task | File / route |
|---|---|
| Remove the cookie gate from public routes; default language from `?lang=` then `Accept-Language`; keep the cookie as an override | `app.py:3449,3543,1984,2709,2726,3765,4219,4328` |
| Cap the front page: `sub_news[:8]` and per-desk 3 cards; link to archive | `app.py:3568`, `_issue_front.html:416` |
| Nav: 5 items + search + language; hide empty rooms | `public.html:57-72` |
| Lazy-load + `width`/`height` + `srcset` on every card image | `_cards.html:10`, `_issue_front.html` |
| Article: headline as `h1`, hero `alt`, remove raw URL, fix Arabic font (`--font-ar`) | `magazine_detail.html`, `styles.css` |
| Print token reset (`@media print :root`) and remove gradient text | `styles.css:542`, `templates.css` |
| Public search route (reuse the existing SQL, drop `@login_required`) | `app.py:1683` |
| 404 template with the reader bar | new |
| Add `robots.txt`, `sitemap.xml`, canonical, `og:image`/`twitter:image`, `NewsArticle` JSON-LD | new / `public.html` |
| Analytics (cookieless) + fix view counting (dedupe, bots, front page) | `public.html`, `app.py:3460` |

### Weeks 2–4 — the new shell (P1)

- New design tokens + base CSS; retire duplicated palettes and inline `<style>` blocks.
- New front page and article templates (port the prototype to Jinja).
- Mobile bottom tabs; 44 px targets; sticky header reduced to one row.
- Image proxy/cache: rehost hotlinked images at 3 widths (fixes CLS, broken images, publisher blocking).
- Subscribe: double opt-in, confirmation screen, privacy note, unsubscribe in every email.
- Editorial pages: About, Standards, Corrections, AI disclosure, contact.
- Arabic-first QA pass: every RTL block has `lang="ar"`, every Arabic body uses Amiri.

### Month 2 — the habits (P1–P2)

- Class Mode fields + quiz rendering; course tags; course-of-the-week automation.
- Issue object + public archive by issue.
- WhatsApp share + channel + QR poster generator.
- Digest automation (weekly send, not a manual button), per-desk follow preferences.
- Department calendar (`/department/calendar.ics`) and event reminders.

### Month 3 — growth (P2)

- PWA (manifest, service worker, offline last issue, optional push).
- Student contributions: guest picks, bylines, photo submission, polls.
- Print edition: a designed 4-page A4 PDF generated from the issue, not `window.print()`.
- A/B test front page order (brief-first vs lead-first) on subscribe conversion and 7-day return.

---

## 9. Measurement: how you will know it is working

Today the only signal is a naive `views` counter on article GETs: **32 views across 71 published stories, and 61 of them have never been opened.** The front page, section pages, search, subscribe and language choice are unmeasured.

Install a cookieless analytics tool (Plausible/Umami, ~1 KB) and track:

**Pageviews:** `/`, `/issue/:n`, `/magazine/article/:id`, `/department`, `/watch`, `/tools`, `/search`, `/subscribe`.

**Events (7):** `brief_click`, `article_reach` (scroll 75%), `quiz_start`, `quiz_complete`, `source_open` (outbound to publisher — the real engagement signal), `share` (network), `subscribe_submit` (already carries `source=qr|web|digest`).

**KPIs and targets for the first 90 days:**

| KPI | Today | 90-day target |
|---|---|---|
| Weekly unique readers | unknown | 150 |
| Brief → article click-through | n/a | 25% |
| Article reach rate (article views ÷ issue views) | n/a | 20% |
| Quiz starts per issue | 0 | 40 |
| Subscribe conversion (QR + web) | 0 subscribers | 60 subscribers |
| 7-day return rate | unknown | 30% |
| Arabic vs English mix | unknown | measured, and used to order the front page |

Also add a one-tap **"Was this useful?"** at the end of every article. Two buttons, no login. That single data point is worth more to an editor than a page-view chart.

---

## 10. Technical appendix

### 10.1 Highest-impact fixes, in order

1. **Public routes must not return the gate** (`app.py`), plus `robots.txt`/`sitemap.xml`/canonical/RSS. Without this, nothing else compounds.
2. **Cap and paginate the issue** (`sub_news`, per-desk). One line removes ~50 cards and ~4 MB.
3. **Images**: lazy, dimensions, `srcset`, rehost. Fixes CLS, LCP, broken hotlinks, and publisher blocking.
4. **Article page**: real `h1`, real body, Arabic font, no duplicated headline.
5. **Nav and mobile**: 5 items, 44 px targets, bottom tabs, no horizontal clipped links.
6. **Design tokens once**: one palette block with light/dark/print; delete 12 palettes and 589 `!important` over time.
7. **Print**: token reset, page size/margins, break rules, visible link URLs.
8. **Accessibility**: `<main>`, skip link, `aria-label` on 8 icon buttons, dialog semantics for 3 modals, `aria-live` for async status, labels on 5 inputs, `lang="ar"` on RTL blocks, focus-visible.
9. **Contrast**: replace white-on-cyan/pink pills (2.1–2.9:1); stop injecting custom colours with `!important`.
10. **Admin**: remove hardcoded `#0f172a` from `admin-desks.css` so the dashboard survives a theme change.

### 10.2 Content rules to enforce at publication

A story can be **published as a full article** only if it has:

- an image with a real subject (not a logo screenshot), or a designed fallback;
- a 25–40 word dek;
- a 150–250 word body: what happened, why it matters, what to watch;
- an Arabic title that has been read by a human (machine translation of proper nouns is currently producing errors such as "أ. بوم" for "A.I. Boom");
- a source link;
- optionally, the class layer (term, question, quiz).

Anything else is a **brief**: title + one line + source, no card, no article page. This single rule fixes the "article page has no article" problem better than any template change.

### 10.3 Checklist for the new front page

- [ ] first headline visible within one phone screen
- [ ] at most 20 stories, no duplicates
- [ ] every section numbered and capped
- [ ] one accent colour + two desk colours only
- [ ] every image has dimensions, alt, and a fallback
- [ ] language switch works without reload and remembers choice
- [ ] keyboard reachable; focus visible; skip link
- [ ] 320 px wide: no horizontal scroll
- [ ] print: black on white, 4 pages, no nav
- [ ] share preview: correct title, image, description, URL

### 10.4 Security hygiene (outside UX, but urgent)

- `.env` contains live OpenAI, Google and YouTube keys plus the admin password. Rotate them, add `.env` to `.gitignore`, and use `ADMIN_PASSWORD_HASH`.
- `/debug_env` is login-protected but still exposes paths and configuration; remove it from production.
- Set `SESSION_COOKIE_SECURE`/`HTTPONLY`/`SAMESITE` and run behind a WSGI server for production.

---

## 11. Files in this review

```
design-review/
├── UX_AUDIT_AND_REDESIGN.md      this document
├── README.md                     how to open the prototype and screenshots
├── prototype/
│   ├── index.html                redesigned front page (EN/AR, live data)
│   ├── article.html              redesigned article page + quiz
│   ├── proto.css                 design tokens + components
│   ├── proto.js                  language, search, save, quiz, progress
│   └── assets/                   logo, author photo, department images
└── shots/
    ├── compare_front_1440.jpg    before/after, desktop
    ├── compare_front_390.jpg    before/after, mobile
    ├── compare_article_1440.jpg before/after, article
    ├── proto_*.png              prototype screenshots (EN/AR, 1440/390)
    └── current_*.png            current app screenshots
```

---

## 12. Closing note

The instinct behind this magazine is right: a department deserves its own paper, in its own two languages, with its own editor. What it needs now is not more features or more stories. It needs **an order, a depth, and a front door that opens**.

If only three things are done this month:

1. **Open the front door** — remove the gate from public routes, fix titles/share images, and add a sitemap.
2. **Cut the issue in half and put a 90-second brief on top** — 20 stories, one lead, five lines.
3. **Give every story a body and a class layer** — 150 words and three questions.

Everything else in this document is detail on those three moves.
