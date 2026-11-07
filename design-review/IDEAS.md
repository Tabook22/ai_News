# Ideas that would make the magazine more accepted, educational, and appealing

A practical list for this codebase (Flask + SQLite + Jinja, no build step, Arabic/English).
Each idea says **what**, **why a student would care**, **how to build it here**, and a rough
effort: **S** (a day), **M** (a week), **L** (a month).

Shipped already, as part of this round: the colour system (desk colours, colour strip,
coloured course band), **evidence badges** on every article (`Lab / Newsroom / Company / Video`),
and a **Listen** button that reads the article aloud in English or Arabic.

---

## 1. The educational layer — what makes it worth a lecturer's time

### 1.1 Class Mode on every article  *(M)*
Turn the four fields already in `NewsItem` (`lesson_why`, `lesson_term`, `lesson_gloss`,
`lesson_ask`) into a standard block: *Why it matters / Term / Discussion question / Course*.
Add a `course` tag and show a "Course of the week" band built from the story that has the
richest fields. The front page already has the band; it needs content, not code.

**Why:** a student can screenshot the term card before a tutorial, and a lecturer can point
the class at one link. This is the single strongest differentiator against TechCrunch.

### 1.2 A credibility / evidence label  *(shipped)*
Each story now says whether it comes from a lab, a newsroom, a company, or a video, with a
one-line explanation. Next step: add a "How to read this" mini-rubric on the article —
*Who made the claim? Is there a study? Is it a product announcement?* — three questions,
no new data.

**Why:** AI literacy is the most employable skill in the department. Teaching students to
read a vendor blog as a vendor blog is genuinely educational.

### 1.3 Three levels of the same story  *(M)*
One story, three tabs: **30 seconds** (the brief), **3 minutes** (the current article),
**deep dive** (the original source + glossary). Store the three lengths as fields, or derive
the 30-second one from the summary and the class line.

**Why:** different readers, different days. It also gives the editor a clear writing target.

### 1.4 Glossary + flashcards  *(M)*
Turn the existing "term of the day" into a searchable glossary page (`/glossary`) with
Arabic/English pairs, and a "flashcards" mode (10 terms, flip, self-score). Add an
"exam week" pack generated from the terms used in the last eight issues.

**Why:** revision utility. Students return for the glossary even when they skip the news.

### 1.5 Weekly quiz with a shareable result  *(M)*
Five multiple-choice questions from the issue, no login, score kept in `localStorage`.
Show the result as a small card: "4/5 on Issue 45 — can you beat me?" with a link.
A leaderboard is optional and should use a nickname, not a real name.

**Why:** the cheapest habit loop in education, and it gives readers a reason to open the
next issue. It also tells the editor what readers actually understood.

### 1.6 Lecture pack (one page, printable)  *(M)*
A "lecture worksheet" button on the issue: a single A4 with the brief, three questions,
the glossary terms, and the source links. Generate it from the current issue, not a screenshot.

**Why:** makes the magazine usable in a classroom in under a minute. Lecturers will ask for it.

### 1.7 Numbers and timelines  *(S/M)*
Two small blocks on the article: **the numbers that matter** (three figures with their source)
and **how we got here** (three dated events). Both can be typed by the editor, or drafted by
AI and approved.

**Why:** context is what students miss when they read a single headline.

### 1.8 "AI literacy" micro-lessons  *(M)*
A short series (one per issue) about reading AI claims: *benchmarks*, *cherry-picked demos*,
*"coming soon"*, *press release vs. paper*. Each is 200 words with a real example from that
week's stories.

**Why:** it is the department's subject, it is evergreen, and it can be reused in induction week.

---

## 2. Habit and belonging — why a student comes back

### 2.1 Follow a desk, reorder the issue  *(S)*
Let readers star the desks they care about; store in `localStorage`; move those sections up.
No accounts, no privacy questions.

**Why:** a cybersecurity student and a robotics student should not see the same order.

### 2.2 Save for later + "your reading list"  *(S)*
The article already has a Save button writing to `localStorage`. Add a `/saved` page that
lists those stories, plus a "continue reading" strip on the front page.

**Why:** half-read stories are the strongest return trigger.

### 2.3 Student of the week / project showcase  *(M)*
A named student, a photo, one project, three questions. Edited, not scraped.

**Why:** belonging. Students read what their classmates built, and prospective students see
what the department produces.

### 2.4 Poll of the week  *(S/M)*
One question (`NewsItem`-like `Poll` + `PollVote` table, or a JSON column), results shown next
issue. "Should the department keep using AI detectors?" is already a placeholder on the front page.

**Why:** participation is the cheapest form of loyalty, and the results are content.

### 2.5 Letters to the editor  *(M)*
Replace the half-disabled comments with a short "write to the editor" form, published as
selected letters next issue. Moderation built in.

**Why:** safer than open comments, more editorial, and it gives readers a voice.

### 2.6 Department calendar + .ics  *(S)*
Every dated campus item gets "Add to calendar" (a generated `.ics` file). A weekly "what's on"
email is a natural extension.

**Why:** utility. Students need the exam and workshop dates more than they need another feed.

### 2.7 Streaks and badges  *(M)*
A light streak (weeks in a row with a quiz) and a few badges (first quiz, 5 terms, 3 issues).
Nickname only, and never public by default.

**Why:** works on the same instinct as Duolingo, without turning the magazine into a game.

### 2.8 Alumni and careers corner  *(M)*
Where graduates work, one internship lead per issue, and "what this tool means for your CV".

**Why:** the question students actually ask in their final year.

---

## 3. Appeal and distribution — how it reaches people

### 3.1 The issue as an object  *(M)*
Give every week a number, a date, a cover image, and a permanent URL (`/issue/45`). The archive
lists issues, not loose stories. Share the issue, not only a story.

**Why:** "read Issue 45" is a stronger invitation than "read our website".

### 3.2 WhatsApp-first sharing  *(S/M)*
Every article already has a WhatsApp share. Add a **WhatsApp Channel** link, and a
"share this issue" message with the cover and one line in Arabic. Generate a 1080×1350
quote card per lead story with the QR (Pillow is already installed).

**Why:** WhatsApp is where Omani student groups actually live.

### 3.3 Audio brief  *(S/M)*
The article now has **Listen** (browser speech). Extend it to the 90-second brief and publish
a weekly audio file (record it, or TTS) with an RSS/podcast enclosure.

**Why:** listening between classes is a real use case, and audio is easy to produce.

### 3.4 A poster per issue  *(S)*
A4 PDF: cover image, three headlines, QR to the issue. Print it for the corridor and the lab.

**Why:** physical presence in the department, where the audience already is.

### 3.5 PWA + offline  *(M)*
Manifest, service worker, offline cache of the last issue, optional push for the weekly issue.

**Why:** the magazine on the home screen, readable in a lab with no Wi-Fi.

### 3.6 Reading modes  *(S)*
Paper / sepia / dark, plus text size (A− / A+), stored in `localStorage`. The CSS already uses
tokens, so this is one `[data-reading]` block.

**Why:** comfort, accessibility, and long reads at night.

### 3.7 Instagram / TikTok carousel  *(M)*
One lead story → five slides: hook, what happened, why it matters, term, QR. Generated from
the same fields as the article.

**Why:** meets students where they already scroll, and links back to the issue.

---

## 4. Trust and operations — why it lasts

### 4.1 "How this was made"  *(S — partially shipped)*
The footer already discloses AI assistance and human review. Add a per-story line:
*Summarised with AI, edited by [name], sources linked.* Plus a public corrections page.

**Why:** credibility. Readers forgive AI if you tell them.

### 4.2 A real analytics loop  *(S/M)*
Cookieless analytics + a one-tap "Was this useful?" on every article. An editor dashboard:
most-read, least-read, search terms with no results, subscribe conversion by source.

**Why:** today the only signal is a view counter. You cannot improve what you do not measure.

### 4.3 The weekly content pipeline  *(S — editorial)*
A fixed checklist per story: image, 25-word dek, 150-word body, Arabic title edited, source,
class fields. Use the existing AI helpers to draft, then edit. Publish 1 lead + 3 features +
5 briefs, and stop.

**Why:** the design is ready; the bottleneck is depth. This is the highest-impact "feature".

### 4.4 Image rehosting  *(M)*
Download publisher images once, resize to three widths, serve from `/static`. Stops broken
images and hotlink blocking, and fixes Core Web Vitals.

**Why:** the most common reason a magazine looks broken is a dead image.

### 4.5 RSS + JSON feed  *(S)*
`/feed.xml` and `/feed.json` for the issue. Some readers still use RSS, and it is a free
distribution channel.

**Why:** low effort, permanent.

---

## What I would do in the next 30 days

| Order | Idea | Effort | Why first |
|---|---|---|---|
| 1 | Fill the class fields on 3–5 stories a week (1.1) | editorial | turns the course band from placeholder to signature |
| 2 | Save + reading list + continue reading (2.2) | S | cheapest return loop |
| 3 | Follow desks / reorder + reading modes (2.1, 3.6) | S | personal and accessible |
| 4 | Weekly quiz (1.5) | M | habit + learning, measurable |
| 5 | Calendar `.ics` (2.6) | S | utility nobody else offers |
| 6 | Issue object + WhatsApp channel + quote card (3.1, 3.2) | M | distribution |
| 7 | Analytics + one-tap feedback (4.2) | S | know what works |
| 8 | Glossary + flashcards (1.4) | M | revision utility |

The rule I would hold to: **one new feature a week, one editorial improvement every issue**.
The magazine does not need more sections; it needs three or four things that are unmistakably
useful, repeated every week.
