"""
Pick the day's most important global AI stories.

The list is built from newsrooms, the big technology companies, university
labs, and scientific outlets. Each run returns at most five stories, spread
across different publishers, and only from the last few days.
"""
import socket
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import feedparser

# name, feed url, trust weight, whether every item is already about AI
FEEDS = [
    ("OpenAI", "https://openai.com/news/rss.xml", 10, True),
    ("Google", "https://blog.google/technology/ai/rss/", 9, True),
    ("DeepMind", "https://deepmind.google/blog/rss.xml", 9, True),
    ("Microsoft", "https://blogs.microsoft.com/feed/", 8, False),
    ("Apple", "https://www.apple.com/newsroom/rss-feed.rss", 8, False),
    ("NVIDIA", "https://blogs.nvidia.com/feed/", 8, False),
    ("MIT News", "https://news.mit.edu/rss/topic/artificial-intelligence2", 9, True),
    ("MIT Technology Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed", 9, True),
    ("Nature", "https://www.nature.com/subjects/machine-learning.rss", 9, True),
    ("ScienceDaily", "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", 7, True),
    ("TechCrunch", "https://techcrunch.com/category/artificial-intelligence/feed/", 7, True),
    ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", 7, True),
    ("Wired", "https://www.wired.com/feed/tag/ai/latest/rss", 7, True),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab", 6, False),
    ("BBC", "https://feeds.bbci.co.uk/news/technology/rss.xml", 8, False),
    ("The Guardian", "https://www.theguardian.com/technology/artificialintelligenceai/rss", 8, True),
    ("New York Times", "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml", 8, False),
]

AI_TERMS = (
    "artificial intelligence", "machine learning", "generative ai", "large language",
    "llm", "chatgpt", "openai", "gemini", "claude", "copilot", "deepmind",
    "anthropic", "neural", "gpt-4", "gpt-5", "apple intelligence", " ai ",
    "a.i.", "ذكاء اصطناعي",
)

LANDMARKS = (
    ("breakthrough", 3), ("announces", 2), ("announce", 2), ("launches", 2),
    ("launch", 2), ("unveils", 2), ("open-source", 2), ("open source", 2),
    ("regulation", 2), ("regulators", 2), ("acquisition", 2), ("acquires", 2),
    ("billion", 1), ("researchers", 1), ("university", 1), ("paper", 1),
)


def _plain(html):
    if not html:
        return ""
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    except Exception:
        return str(html)


def lookup_published_at(url):
    """Read the report's own publish time from its page. Returns naive UTC, or None."""
    if not url:
        return None
    try:
        import requests
        from bs4 import BeautifulSoup
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; NasserAINews/1.0)"},
            timeout=8,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as exc:
        print(f"Daily brief: no publish time for {url} ({exc})")
        return None

    candidates = []
    for attrs in (
        {"property": "article:published_time"},
        {"property": "og:published_time"},
        {"name": "pubdate"},
        {"name": "publishdate"},
        {"name": "date"},
        {"itemprop": "datePublished"},
    ):
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            candidates.append(tag["content"])
    clock = soup.find("time")
    if clock is not None and clock.get("datetime"):
        candidates.append(clock["datetime"])

    for raw in candidates:
        when = _parse_when(raw)
        if when is not None:
            return when.astimezone(timezone.utc).replace(tzinfo=None)
    return _date_from_url(url)


def _date_from_url(url):
    """Some publishers put the day in the address and hide the clock from scrapers."""
    import re
    match = re.search(r"/(20\d{2})/(\d{2})/(\d{2})(?:/|$)", url or "")
    if not match:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def _parse_when(raw):
    text = (raw or "").strip()
    if not text:
        return None
    try:
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            when = parsedate_to_datetime(text)
        except Exception:
            return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when


def normalize_url(url):
    if not url:
        return ""
    parts = urlparse(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    path = parts.path.rstrip("/") or "/"
    return urlunparse((parts.scheme.lower(), parts.netloc.lower(), path, "", urlencode(query), ""))


def _entry_image(entry):
    thumbs = entry.get("media_thumbnail") or []
    if thumbs and isinstance(thumbs, list):
        url = thumbs[0].get("url")
        if url:
            return url
    for link in entry.get("links") or []:
        if str(link.get("type", "")).startswith("image") and link.get("href"):
            return link["href"]
    return ""


def _entry_date(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        try:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    raw = entry.get("published") or entry.get("updated") or ""
    if raw:
        try:
            when = parsedate_to_datetime(raw)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            return when.astimezone(timezone.utc)
        except Exception:
            return None
    return None


def _is_about_ai(text):
    blob = f" {text.lower()} "
    return any(term in blob for term in AI_TERMS)


def _score(item, now):
    blob = f"{item['title']} {item['summary']}".lower()
    if not item["ai_only"] and not _is_about_ai(blob):
        return None
    points = item["weight"]
    when = item.get("published_at")
    if when is None:
        points += 1
        item["age_hours"] = None
    else:
        age = (now - when).total_seconds() / 3600
        item["age_hours"] = age
        if age < 0:
            age = 0
        if age <= 30:
            points += 6
        elif age <= 72:
            points += 3
        elif age <= 24 * 7:
            points += 0
        else:
            return None
    for word, bonus in LANDMARKS:
        if word in blob:
            points += bonus
    return points


def _from_feed(name, url, weight, ai_only):
    found = []
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(12)
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        print(f"Daily brief: {name} failed ({exc})")
        return found
    finally:
        socket.setdefaulttimeout(previous)
    print(f"Daily brief: {name} returned {len(feed.entries or [])} items")

    for entry in (feed.entries or [])[:8]:
        link = entry.get("link") or ""
        title = (entry.get("title") or "").strip()
        if not link or not title:
            continue
        summary = _plain(entry.get("summary") or entry.get("description") or "")[:700]
        found.append({
            "title": title[:490],
            "url": link,
            "summary": summary,
            "source": name,
            "image": _entry_image(entry),
            "weight": weight,
            "ai_only": ai_only,
            "published_at": _entry_date(entry),
        })
    return found


def _from_search():
    found = []
    try:
        try:
            from agent.skills.news_fetcher.ddg_search import search_duckduckgo_news
        except ImportError:
            from ddg_search import search_duckduckgo_news
        rows = search_duckduckgo_news("artificial intelligence", time_limit="today") or []
    except Exception as exc:
        print(f"Daily brief: news search failed ({exc})")
        return found

    for row in rows[:8]:
        title = (row.get("title") or "").strip()
        link = row.get("url") or ""
        if not title or not link:
            continue
        found.append({
            "title": title[:490],
            "url": link,
            "summary": _plain(row.get("summary") or "")[:700],
            "source": row.get("source") or "World press",
            "image": row.get("image") or "",
            "weight": 6,
            "ai_only": True,
            "published_at": None,
        })
    return found


def gather_top_stories(limit=5):
    """Return up to `limit` distinct, high-signal AI stories for today."""
    pool = []
    for name, url, weight, ai_only in FEEDS:
        pool.extend(_from_feed(name, url, weight, ai_only))
    pool.extend(_from_search())

    now = datetime.now(timezone.utc)
    seen = set()
    ranked = []
    for item in pool:
        key = normalize_url(item["url"])
        if not key or key in seen:
            continue
        seen.add(key)
        points = _score(item, now)
        if points is None:
            continue
        item["score"] = points
        item["url_key"] = key
        ranked.append(item)

    ranked.sort(key=lambda item: (item["score"], -(item["age_hours"] or 999)), reverse=True)

    # One story per publisher first, so the five are not all from one company.
    picked = []
    used_sources = set()
    overflow = []
    for item in ranked:
        source = (item["source"] or "").strip().lower()
        if source in used_sources:
            overflow.append(item)
            continue
        used_sources.add(source)
        picked.append(item)
        if len(picked) >= limit:
            return picked
    for item in overflow:
        picked.append(item)
        if len(picked) >= limit:
            break
    return picked
