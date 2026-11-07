"""
Choose the YouTube desk: five strong clips in each of four shelves.

News, English and Arabic. Education, English and Arabic.
News prefers the last two weeks and spreads across the big labs.
Education prefers clear lessons on local models, training, and building an app.
"""
import math
import os
import re
from datetime import datetime, timedelta, timezone

COMPANIES = (
    ("anthropic", ("anthropic", "claude", "أنثروبيك", "كلود")),
    ("openai", ("openai", "chatgpt", "gpt-4", "gpt-5", "أوبن إيه", "تشات جي")),
    ("gemini", ("gemini", "deepmind", "جيميناي", "جيمناي")),
    ("xai", ("xai", "x.ai", "grok", "غروك")),
    ("deepseek", ("deepseek", "ديب سيك", "ديبسيك", "الصين", "صيني", "chinese ai", "china ai")),
)

SKIP_WORDS = (
    "reaction", "reacts", "lyrics", "music video", "locomotive", "mustang",
    "رد فعل", "ريأكشن", "قتيل", "هجوم", "نشرة إخبارية",
)
AI_IN_TITLE = (
    " ai", "a.i", "artificial", "openai", "anthropic", "claude", "gemini", "gpt",
    "llm", "chatgpt", "deepseek", "grok", "neural", "machine learning", "deepmind",
    "ذكاء", "اصطناعي", "نموذج", "كلود", "جيميناي", "جيمناي", "ديب سيك", "ديبسيك",
    "أوبن", "غروك", "تشات",
)
LESSON_IN_TITLE = (
    "tutorial", "how to", "how ai", "learn", "course", "guide", "lesson", "build",
    "local", "fine-tun", "finetun", "ollama", "train", "explain",
    "شرح", "تدريب", "كيف", "محلي", "دليل", "للمبتد", "إنشاء", "بناء", "تشغيل",
)

NEWS_QUERIES = {
    "en": (
        "OpenAI Anthropic Gemini AI news",
        "xAI Grok DeepSeek AI news",
        "China artificial intelligence news",
        "latest AI news this week",
    ),
    "ar": (
        "أخبار الذكاء الاصطناعي",
        "أوبن إيه آي أنثروبيك جيميناي",
        "ديب سيك الذكاء الاصطناعي الصيني",
        "آخر أخبار الذكاء الاصطناعي",
        "بودكاست الذكاء الاصطناعي",
        "تحديث جيميناي كلود",
    ),
}

EDU_QUERIES = {
    "en": (
        "run a local AI Ollama tutorial",
        "how to fine tune an LLM",
        "build your own AI application tutorial",
        "how to train an AI model",
    ),
    "ar": (
        "تشغيل الذكاء الاصطناعي محليا شرح",
        "تدريب نموذج ذكاء اصطناعي",
        "إنشاء تطبيق بالذكاء الاصطناعي",
        "شرح الذكاء الاصطناعي للمبتدئين",
    ),
}


def _has_arabic(text):
    return any("\u0600" <= ch <= "\u06FF" for ch in (text or ""))


def _seconds(iso):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not match:
        return 0
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _company(blob):
    for key, words in COMPANIES:
        if any(word in blob for word in words):
            return key
    return ""


def _client():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("YouTube desk: YOUTUBE_API_KEY is missing.")
        return None
    from googleapiclient.discovery import build
    return build("youtube", "v3", developerKey=api_key)


def _search(youtube, query, language, published_after):
    found = []
    try:
        response = youtube.search().list(
            q=query,
            part="id,snippet",
            type="video",
            maxResults=8,
            order="viewCount",
            relevanceLanguage=language,
            publishedAfter=published_after,
            videoEmbeddable="true",
            safeSearch="moderate",
        ).execute()
    except Exception as exc:
        print(f"YouTube desk search failed for {query!r}: {exc.__class__.__name__}")
        return found
    for item in response.get("items") or []:
        video_id = ((item.get("id") or {}).get("videoId") or "").strip()
        snippet = item.get("snippet") or {}
        title = (snippet.get("title") or "").strip()
        if not video_id or not title:
            continue
        thumbs = snippet.get("thumbnails") or {}
        image = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url") or ""
        found.append({
            "video_id": video_id,
            "title": title[:300],
            "summary": (snippet.get("description") or "")[:500],
            "channel": (snippet.get("channelTitle") or "YouTube")[:180],
            "image": image[:500],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "published_raw": snippet.get("publishedAt") or "",
        })
    return found


def _hydrate(youtube, rows):
    details = {}
    ids = [row["video_id"] for row in rows]
    for start in range(0, len(ids), 40):
        chunk = ids[start:start + 40]
        try:
            response = youtube.videos().list(
                part="contentDetails,statistics,snippet",
                id=",".join(chunk),
            ).execute()
        except Exception as exc:
            print(f"YouTube desk details failed: {exc.__class__.__name__}")
            continue
        for item in response.get("items") or []:
            details[item.get("id")] = item
    ready = []
    for row in rows:
        item = details.get(row["video_id"])
        if not item:
            continue
        snippet = item.get("snippet") or {}
        stats = item.get("statistics") or {}
        try:
            views = int(stats.get("viewCount") or 0)
        except ValueError:
            views = 0
        published = _parse_when(row.get("published_raw") or snippet.get("publishedAt"))
        ready.append({
            **row,
            "title": (snippet.get("title") or row["title"])[:300],
            "summary": (snippet.get("description") or row["summary"])[:500],
            "channel": (snippet.get("channelTitle") or row["channel"])[:180],
            "views": views,
            "seconds": _seconds((item.get("contentDetails") or {}).get("duration")),
            "published_at": published,
        })
    return ready


def _parse_when(raw):
    text = (raw or "").strip()
    if not text:
        return None
    try:
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when.astimezone(timezone.utc).replace(tzinfo=None)


def _score(row, lane, language, now):
    title = (row.get("title") or "").lower()
    blob = f"{title} {row['summary']} {row['channel']}".lower()
    if any(word in blob for word in SKIP_WORDS):
        return None
    if language == "ar" and not _has_arabic(row.get("title")):
        return None
    if not any(word in f" {title} " for word in AI_IN_TITLE):
        return None
    if lane == "education" and not any(word in title for word in LESSON_IN_TITLE):
        return None
    seconds = row.get("seconds") or 0
    if seconds and seconds < 90:
        return None
    if lane == "news" and seconds > 3 * 3600:
        return None
    if lane == "education" and seconds and seconds < 4 * 60:
        return None
    points = math.log10((row.get("views") or 0) + 10) * 2
    when = row.get("published_at")
    if when is not None:
        age_days = max(0, (now - when).total_seconds() / 86400)
        if lane == "news":
            if age_days <= 3:
                points += 4
            elif age_days <= 10:
                points += 2
        elif age_days <= 45:
            points += 1
    if lane == "news" and _company(blob):
        points += 2
    if language == "ar" and _has_arabic(row["title"]):
        points += 3
    if language == "en" and _has_arabic(row["title"]) and not _has_arabic(row["channel"]):
        points -= 1
    if lane == "education" and seconds >= 8 * 60:
        points += 1.5
    row["company"] = _company(blob)
    return points


def _pick(rows, lane, language, limit=5):
    now = datetime.utcnow()
    ranked = []
    seen = set()
    for row in rows:
        if row["video_id"] in seen:
            continue
        seen.add(row["video_id"])
        points = _score(row, lane, language, now)
        if points is None:
            continue
        row["score"] = points
        ranked.append(row)
    ranked.sort(key=lambda row: row["score"], reverse=True)

    picked = []
    used_channels = set()
    used_companies = set()
    if lane == "news":
        for company, _words in COMPANIES:
            choice = next((row for row in ranked if row.get("company") == company and row["channel"].lower() not in used_channels), None)
            if choice is None:
                continue
            picked.append(choice)
            used_channels.add(choice["channel"].lower())
            used_companies.add(company)
            if len(picked) >= limit:
                return picked
    for row in ranked:
        if row in picked:
            continue
        channel = row["channel"].lower()
        if channel in used_channels:
            continue
        picked.append(row)
        used_channels.add(channel)
        if len(picked) >= limit:
            return picked
    for row in ranked:
        if row in picked:
            continue
        picked.append(row)
        if len(picked) >= limit:
            break
    return picked


def gather_youtube_desk():
    """Return {(lane, language): [up to five videos]}."""
    youtube = _client()
    empty = {("news", "en"): [], ("news", "ar"): [], ("education", "en"): [], ("education", "ar"): []}
    if youtube is None:
        return empty
    now = datetime.now(timezone.utc)
    windows = {
        "news": (now - timedelta(days=21)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "education": (now - timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    queries = {"news": NEWS_QUERIES, "education": EDU_QUERIES}
    chosen = {}
    for lane in ("news", "education"):
        for language in ("en", "ar"):
            pool = []
            seen = set()
            for query in queries[lane][language]:
                for row in _search(youtube, query, language, windows[lane]):
                    if row["video_id"] in seen:
                        continue
                    seen.add(row["video_id"])
                    pool.append(row)
            print(f"YouTube desk: {lane}/{language} found {len(pool)}")
            hydrated = _hydrate(youtube, pool)
            picked = _pick(hydrated, lane, language, limit=5)
            if len(picked) < 5 and lane == "education":
                used = {item["video_id"] for item in picked}
                used_channels = {item["channel"].lower() for item in picked}
                extra = []
                for row in hydrated:
                    if row["video_id"] in used:
                        continue
                    seconds = row.get("seconds") or 0
                    if seconds and seconds < 90:
                        continue
                    blob = f"{row['title']} {row['summary']}".lower()
                    if any(word in blob for word in SKIP_WORDS):
                        continue
                    extra.append(row)
                extra.sort(key=lambda row: row.get("views") or 0, reverse=True)
                for row in extra:
                    title = (row.get("title") or "").lower()
                    if language == "ar" and not _has_arabic(row.get("title")):
                        continue
                    if not any(word in f" {title} " for word in AI_IN_TITLE):
                        continue
                    if not any(word in title for word in LESSON_IN_TITLE):
                        continue
                    channel = row["channel"].lower()
                    if channel in used_channels:
                        continue
                    picked.append(row)
                    used_channels.add(channel)
                    if len(picked) >= 5:
                        break
            chosen[(lane, language)] = picked
            print(f"YouTube desk: {lane}/{language} kept {len(picked)}")
    return chosen
