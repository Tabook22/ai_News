"""Find the newest public references for each library shelf.

One click asks the open web for two new items on every shelf, from two
different sources. Already archived links are skipped, so the next click
continues down the list. Callers decide what is stored. Nothing here is
chosen for the magazine front.
"""

import html
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "NasserAINews/1.0 (educational reference library)"
_ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
_PER_SHELF = 2

_ESSAY_FEEDS = (
    "https://simonwillison.net/atom/everything/",
    "https://magazine.sebastianraschka.com/feed",
    "https://www.interconnects.ai/feed",
    "https://bair.berkeley.edu/blog/feed.xml",
    "https://thegradient.pub/rss/",
)
_ESSAY_NAMES = {
    "simonwillison.net": "Simon Willison",
    "magazine.sebastianraschka.com": "Sebastian Raschka",
    "interconnects.ai": "Interconnects",
    "bair.berkeley.edu": "BAIR",
    "thegradient.pub": "The Gradient",
}
_PODCAST_SHOWS = (
    "Lex Fridman Podcast",
    "Dwarkesh Podcast",
    "Latent Space",
    "TWIML AI Podcast",
    "No Priors",
    "Machine Learning Street Talk",
)
# Research explainers, then teaching channels. Two shelves of the same field.
_VIDEO_GROUPS = (
    ("TwoMinutePapers", "YannicKilcher"),
    ("3blue1brown", "statquest", "AndrejKarpathy"),
)


def canonical_url(url):
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw.lower()
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/")
    if "arxiv.org" in host:
        match = re.search(r"/(?:abs|pdf)/(\d{4}\.\d+)", path, re.I)
        if match:
            return "arxiv:" + match.group(1)
    if host in ("youtube.com", "m.youtube.com", "youtu.be"):
        if host == "youtu.be":
            video = path.strip("/").split("/")[0]
        else:
            video = (parse_qs(parts.query).get("v") or [""])[0]
        if video:
            return "yt:" + video
    return host + path.lower()


def canonical_title(title):
    text = re.sub(r"[^a-z0-9]+", " ", (title or "").lower())
    return re.sub(r"\s+", " ", text).strip()


_PROMO = re.compile(
    r"^(figure\b|check out|sign up|subscribe|http|❤️|❤|follow me|enroll)",
    re.I,
)
_ABOUT_AI = re.compile(
    r"\b(artificial intelligence|machine learning|deep learning|neural|llm|gpt|"
    r"chatgpt|generative|robots?|robotics|language model)\b|\bAI\b",
    re.I,
)


def _clean(text, limit=240):
    plain = re.sub(r"<[^>]+>", " ", text or "")
    plain = html.unescape(re.sub(r"\s+", " ", plain)).strip()
    if not plain:
        return ""
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        sentence = sentence.strip()
        if not sentence or _PROMO.match(sentence):
            continue
        if len(sentence) > limit:
            return sentence[: limit - 1].rstrip() + "…"
        return sentence
    return ""


def _about_ai(title, description=""):
    return bool(_ABOUT_AI.search(f"{title} {(description or '')[:500]}"))


def _get(url, **kwargs):
    try:
        response = _SESSION.get(url, timeout=12, **kwargs)
        if response.ok:
            return response
    except requests.RequestException:
        return None
    return None


def _arabic(text):
    raw = (text or "").strip()
    if not raw:
        return ""
    try:
        from agent.skills.translator.translation_api import translate
        done = translate(raw, target="ar", source="en")
    except Exception:
        return ""
    return (done or "").strip()[:500]


def _fresh(items, known_urls, known_titles):
    """Newest first, two items, two different sources, nothing already kept."""
    chosen = []
    sources = set()
    for item in items:
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()
        source = (item.get("source") or "").strip().lower()
        if not url.startswith(("http://", "https://")) or not title:
            continue
        if canonical_url(url) in known_urls or canonical_title(title) in known_titles:
            continue
        if source and source in sources:
            continue
        chosen.append(item)
        if source:
            sources.add(source)
        if len(chosen) == _PER_SHELF:
            break
    if len(chosen) < _PER_SHELF:
        for item in items:
            if item in chosen:
                continue
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            if not url.startswith(("http://", "https://")) or not title:
                continue
            if canonical_url(url) in known_urls or canonical_title(title) in known_titles:
                continue
            chosen.append(item)
            if len(chosen) == _PER_SHELF:
                break
    ready = []
    for item in chosen:
        why = item.get("why") or ""
        ready.append({
            "title": title_of(item)[:300],
            "authors": (item.get("authors") or "")[:300],
            "why": why[:800],
            "why_ar": _arabic(why),
            "url": item["url"].strip(),
            "source_label": (item.get("source_label") or "")[:160],
        })
    return ready


def title_of(item):
    return re.sub(r"\s+", " ", (item.get("title") or "")).strip()


def _papers():
    found = []
    queries = ("cat:cs.LG", "cat:cs.CL", "cat:cs.AI")
    for query in queries:
        response = _get("https://export.arxiv.org/api/query", params={
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 8,
        })
        if response is None:
            continue
        try:
            root = ElementTree.fromstring(response.content)
        except ElementTree.ParseError:
            continue
        for entry in root.findall("a:entry", _ATOM):
            title = _clean(entry.findtext("a:title", "", _ATOM), 300)
            link = entry.findtext("a:id", "", _ATOM).strip()
            link = re.sub(r"v\d+$", "", link.replace("http://", "https://"))
            names = []
            for author in entry.findall("a:author", _ATOM):
                name = (author.findtext("a:name", "", _ATOM) or "").strip()
                if name:
                    names.append(name)
            category = ""
            primary = entry.find("arxiv:primary_category", _ATOM)
            if primary is not None:
                category = primary.attrib.get("term") or ""
            summary = _clean(entry.findtext("a:summary", "", _ATOM))
            if title and link:
                found.append({
                    "title": title,
                    "authors": ", ".join(names[:4]),
                    "why": summary or "A newly posted paper on arXiv.",
                    "url": link,
                    "source_label": "arXiv",
                    "source": category or query,
                })
    return found


def _books():
    response = _get("https://openlibrary.org/search.json", params={
        "q": "artificial intelligence",
        "sort": "new",
        "language": "eng",
        "limit": 30,
        "fields": "title,author_name,first_publish_year,key",
    })
    if response is None:
        return []
    try:
        docs = response.json().get("docs") or []
    except ValueError:
        return []
    year_now = datetime.now(timezone.utc).year
    found = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        year = doc.get("first_publish_year") or 0
        authors = []
        for name in doc.get("author_name") or []:
            name = (name or "").strip()
            if not name or _ABOUT_AI.fullmatch(name):
                continue
            authors.append(name)
        key = (doc.get("key") or "").strip()
        lowered = title.lower()
        if not title or not authors or not key.startswith("/works/"):
            continue
        if year < year_now - 1:
            continue
        if any(word in lowered for word in ("proceedings", "conference", "workshop", "digest")):
            continue
        found.append({
            "title": title,
            "authors": ", ".join(authors[:4]),
            "why": f"Published in {year}. A recent book on artificial intelligence.",
            "url": "https://openlibrary.org" + key,
            "source_label": "Open Library",
            "source": authors[0].lower(),
        })
    return found


def _youtube_latest(handle):
    key = os.getenv("YOUTUBE_API_KEY") or ""
    if not key:
        return None
    channel = _get("https://www.googleapis.com/youtube/v3/channels", params={
        "part": "contentDetails,snippet",
        "forHandle": handle,
        "key": key,
    })
    if channel is None:
        return None
    try:
        rows = channel.json().get("items") or []
    except ValueError:
        return None
    if not rows:
        return None
    uploads = (((rows[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get("uploads"))
    name = ((rows[0].get("snippet") or {}).get("title") or handle).strip()
    if not uploads:
        return None
    playlist = _get("https://www.googleapis.com/youtube/v3/playlistItems", params={
        "part": "snippet",
        "playlistId": uploads,
        "maxResults": 5,
        "key": key,
    })
    if playlist is None:
        return None
    try:
        videos = playlist.json().get("items") or []
    except ValueError:
        return None
    for video in videos:
        snippet = video.get("snippet") or {}
        title = html.unescape(snippet.get("title") or "").strip()
        video_id = ((snippet.get("resourceId") or {}).get("videoId") or "").strip()
        if not title or not video_id or "delete" in title.lower():
            continue
        if "#shorts" in title.lower() or title.strip().lower() == "private video":
            continue
        if not _about_ai(title, snippet.get("description") or ""):
            continue
        return {
            "title": title,
            "authors": name,
            "why": _clean(snippet.get("description") or "") or f"A recent video from {name}.",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "source_label": "YouTube",
            "source": handle.lower(),
            "published": snippet.get("publishedAt") or "",
        }
    return None


def _videos():
    handles = [handle for group in _VIDEO_GROUPS for handle in group]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(_youtube_latest, handles))
    group_of = {}
    for index, group in enumerate(_VIDEO_GROUPS):
        for handle in group:
            group_of[handle.lower()] = index
    found = [row for row in rows if row]
    found.sort(key=lambda row: row.get("published") or "", reverse=True)
    # One research explainer and one teaching channel, not two from the same kind.
    for row in found:
        row["source"] = f"group-{group_of.get(row['source'], 0)}"
    return found


def _feed_entries(url):
    response = _get(url)
    if response is None:
        return []
    try:
        root = ElementTree.fromstring(response.content)
    except ElementTree.ParseError:
        return []
    rows = []
    entries = root.findall("a:entry", _ATOM) or root.findall(".//item")
    for entry in entries[:12]:
        title = _clean(entry.findtext("a:title", "", _ATOM) or entry.findtext("title") or "", 300)
        link = ""
        atom_link = entry.find("a:link", _ATOM)
        if atom_link is not None and atom_link.attrib.get("href"):
            link = atom_link.attrib["href"]
        if not link:
            link = (entry.findtext("link") or entry.findtext("a:id", "", _ATOM) or "").strip()
        when = (entry.findtext("a:updated", "", _ATOM) or entry.findtext("pubDate")
                or entry.findtext("a:published", "", _ATOM) or "")
        summary = _clean(entry.findtext("a:summary", "", _ATOM) or entry.findtext("description") or "")
        host = urlsplit(link).netloc.lower().removeprefix("www.") if link else ""
        if title and link.startswith("http"):
            rows.append({
                "title": title,
                "authors": _ESSAY_NAMES.get(host, host),
                "why": summary or "A recent essay from this shelf.",
                "url": link.split("?")[0],
                "source_label": host,
                "source": host,
                "published": when,
            })
    return rows


def _essays():
    found = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for batch in pool.map(_feed_entries, _ESSAY_FEEDS):
            found.extend(batch)
    found.sort(key=lambda row: row.get("published") or "", reverse=True)
    return found


def _show_episodes(show):
    response = _get("https://itunes.apple.com/search", params={
        "term": show,
        "entity": "podcastEpisode",
        "limit": 12,
    })
    if response is None:
        return []
    try:
        results = response.json().get("results") or []
    except ValueError:
        return []
    needle = show.lower()
    rows = []
    for item in results:
        collection = (item.get("collectionName") or "").strip()
        if needle.split()[0] not in collection.lower() and needle not in collection.lower():
            continue
        title = html.unescape(item.get("trackName") or "").strip()
        url = (item.get("trackViewUrl") or "").strip()
        when = item.get("releaseDate") or ""
        if not title or not url.startswith("http"):
            continue
        if not _about_ai(title, item.get("description") or ""):
            continue
        # Drop crossover clips that are years behind the show's own recent episodes.
        if when and when[:4].isdigit() and int(when[:4]) < datetime.now(timezone.utc).year - 1:
            continue
        rows.append({
            "title": title,
            "authors": collection or show,
            "why": _clean(item.get("description") or "") or f"A recent episode of {collection or show}.",
            "url": url.split("?")[0],
            "source_label": "Podcast",
            "source": (collection or show).lower(),
            "published": when,
        })
    rows.sort(key=lambda row: row.get("published") or "", reverse=True)
    return rows[:3]


def _podcasts():
    found = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for batch in pool.map(_show_episodes, _PODCAST_SHOWS):
            found.extend(batch)
    found.sort(key=lambda row: row.get("published") or "", reverse=True)
    return found


def discover_latest(known_urls, known_titles):
    """Return up to two new references for each shelf key."""
    urls = {canonical_url(url) for url in known_urls}
    titles = {canonical_title(title) for title in known_titles}
    fetchers = (
        ("book", _books),
        ("paper", _papers),
        ("video", _videos),
        ("essay", _essays),
        ("podcast", _podcasts),
    )
    found = {}
    for shelf, fetcher in fetchers:
        try:
            found[shelf] = _fresh(fetcher(), urls, titles)
        except Exception:
            found[shelf] = []
        for item in found[shelf]:
            urls.add(canonical_url(item["url"]))
            titles.add(canonical_title(item["title"]))
    return found
