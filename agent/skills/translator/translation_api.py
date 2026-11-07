"""English and Arabic for the magazine. Stored once, then shown by the reader's language."""
import json
import re
import time
import urllib.parse
import urllib.request

_ARABIC = re.compile(r"[\u0600-\u06FF]")
_LATIN = re.compile(r"[A-Za-z]")
_CACHE = {}


def has_arabic(text):
    return bool(_ARABIC.search(text or ""))


def needs_arabic(text):
    """True when the Arabic field is empty, a leftover marker, or still English."""
    raw = (text or "").strip()
    if not raw or raw.startswith("[AR]"):
        return True
    return bool(_LATIN.search(raw)) and not has_arabic(raw)


def strip_marker(text):
    raw = (text or "").strip()
    if raw.startswith("[AR]"):
        return raw[4:].strip()
    return raw


def translate(text, target="ar", source="en"):
    """Translate a string or a list. Already-Arabic text is left as it is."""
    if isinstance(text, list):
        return [translate(piece, target, source) for piece in text]
    raw = strip_marker(text)
    if not raw:
        return ""
    if target == "ar" and has_arabic(raw) and not (text or "").strip().startswith("[AR]"):
        return raw
    if target == "en" and not has_arabic(raw):
        return raw
    key = (source, target, raw)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    parts = _chunks(raw, 700)
    translated = []
    for index, part in enumerate(parts):
        translated.append(_one(part, source, target))
        if index + 1 < len(parts):
            time.sleep(0.15)
    result = " ".join(piece for piece in translated if piece).strip()
    if target == "ar" and not has_arabic(result):
        return raw
    _CACHE[key] = result
    return result


def translate_html(html, target="ar", source="en"):
    """Translate the words inside HTML and leave the tags in place."""
    if not html or not str(html).strip():
        return html or ""
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return translate(re.sub(r"<[^>]+>", " ", html), target, source)
    soup = BeautifulSoup(html, "html.parser")
    nodes = []
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in ("script", "style"):
            continue
        words = str(node)
        if words.strip() and (target != "ar" or needs_arabic(words) or words.strip().startswith("[AR]")):
            nodes.append(node)
    if not nodes:
        return str(soup)
    originals = [strip_marker(str(node)) for node in nodes]
    done = _translate_many(originals, target, source)
    for node, words in zip(nodes, done):
        node.replace_with(words)
    return str(soup)


def _chunks(text, limit):
    if len(text) <= limit:
        return [text]
    pieces = []
    rest = text
    while rest:
        if len(rest) <= limit:
            pieces.append(rest)
            break
        cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        pieces.append(rest[:cut])
        rest = rest[cut:].lstrip()
    return pieces


def _translate_many(texts, target, source):
    """One request for several short lines, then a line at a time if the join breaks."""
    marker = "\n⟦⟧\n"
    packed = marker.join(texts)
    if len(packed) <= 1800:
        try:
            block = _one(packed, source, target)
            parts = block.split("⟦⟧")
            if len(parts) == len(texts):
                return [part.strip() for part in parts]
        except Exception:
            pass
    return [translate(text, target, source) for text in texts]


def _one(text, source, target):
    query = urllib.parse.urlencode({
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": text,
    })
    url = "https://translate.googleapis.com/translate_a/single?" + query
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return "".join(piece[0] for piece in payload[0] if piece and piece[0])
