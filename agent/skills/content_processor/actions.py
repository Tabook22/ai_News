import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)  # .env is the source of truth — never let a stale OS-level env var win

def get_client():
    """Reads OPENAI_API_KEY fresh on every call so a key saved via the admin
    API Keys settings tab takes effect immediately, without restarting the app."""
    api_key = os.environ.get('OPENAI_API_KEY')
    return OpenAI(api_key=api_key) if api_key else None

def _reply(task, messages, temperature=0.3, json_mode=False):
    """Text from the provider/model assigned to this task, or None if unset."""
    from agent.skills.content_processor.providers import complete
    response = complete(task, messages, temperature=temperature, json_mode=json_mode)
    if response is None:
        return None
    return (response.choices[0].message.content or "").strip()

def process_news_item(title, snippet, url=None):
    """
    Takes raw news data and uses LLM to:
    1. Summarize/Polish English content
    2. Suggest a professional Arabic title
    3. Translate summary to Arabic
    """
    try:
        # Construct a rich prompt
        prompt = f"""
        You are an expert bilingual news editor for "Nasser AI News", a premium tech magazine.
        
        INPUT DATA:
        Title: {title}
        Context: {snippet}
        
        TASK:
        1. "summary_en": Write a 2-sentence executive summary in English. It must be engaging and professional.
        2. "title_ar": Write a professional, punchy Arabic headline for this news.
        3. "summary_ar": Write a 2-sentence Arabic summary. It must be in Modern Standard Arabic (Fusha), suitable for a tech magazine.
        
        OUTPUT FORMAT:
        Return ONLY valid JSON.
        {{
            "summary_en": "...",
            "title_ar": "...",
            "summary_ar": "..."
        }}
        """

        content = _reply("gather", [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": prompt},
        ], temperature=0.3, json_mode=True)
        if not content:
            print("⚠️ No model configured for gathering news. Using fallback processing.")
            return _fallback_processing(title, snippet)
        result = json.loads(content)
        
        print(f"✅ AI Processed: {title[:20]}...")
        return {
            "title_ar": result.get("title_ar", ""),
            "summary_en": result.get("summary_en", ""),
            "summary_ar": result.get("summary_ar", "")
        }

    except Exception as e:
        print(f"❌ OpenAI Processing Failed: {e}")
        return _fallback_processing(title, snippet)

def _fallback_processing(title, snippet):
    """Legacy deterministic fallback if no AI available"""
    return {
        "title_ar": "",
        "summary_en": snippet, # Keep original
        "summary_ar": ""
    }

def translate_html_to_arabic(html_content):
    """
    Translates a full HTML article body into Modern Standard Arabic while
    preserving all HTML tags/structure. This runs ONCE, at save time (when an
    admin adds/edits a story) — never per-reader — so Arabic readers are always
    served a pre-translated copy straight from the database.
    """
    return translate_html(html_content, 'ar')

def translate_html(html_content, target_lang='ar'):
    """
    Translates an HTML block (article body, a Summernote rich-text field, etc.)
    into the given language while preserving all HTML tags/structure.
    `target_lang` is 'ar' or 'en' — the language to translate INTO.
    Returns None (not a fake translation) when target_lang='en' and no AI
    client is configured, since there's no reliable AI-free path to English.
    """
    if not html_content or not html_content.strip():
        return ""

    try:
        lang_name = "Modern Standard Arabic (Fusha)" if target_lang == 'ar' else "English"
        prompt = f"""
        You are a professional bilingual translator/editor for "Nasser AI News", a bilingual tech magazine.

        Translate the HTML content below into {lang_name}.

        RULES:
        - Preserve every HTML tag exactly as-is (do not add, remove, or reorder tags/attributes).
        - Only translate the human-readable text content.
        - Keep brand names, product names, and technical model names as-is where that reads
          naturally (e.g. "GPT-4", "Google DeepMind").
        - Return ONLY the translated HTML — no markdown code fences, no commentary.

        HTML:
        {html_content}
        """

        translated = _reply("other", [
            {"role": "system", "content": "You translate HTML content between English and Arabic while preserving markup exactly. You output raw HTML only."},
            {"role": "user", "content": prompt},
        ], temperature=0.2)
        if not translated:
            if target_lang == 'ar':
                print("⚠️ No model configured for translation. Using fallback.")
                return _fallback_html_translation(html_content)
            return None
        translated = translated.strip()

        # Defensive cleanup in case the model wraps the output in a code fence anyway
        if translated.startswith("```"):
            translated = translated.strip("`")
            if translated[:4].lower() == "html":
                translated = translated[4:]
            translated = translated.strip()

        print(f"✅ AI Translated HTML content ({len(html_content)} -> {len(translated)} chars)")
        return translated or (_fallback_html_translation(html_content) if target_lang == 'ar' else None)

    except Exception as e:
        print(f"❌ OpenAI HTML Translation Failed: {e}")
        return _fallback_html_translation(html_content) if target_lang == 'ar' else None

def _fallback_html_translation(html_content):
    """
    No-AI fallback: walks the HTML text nodes and runs each through the mock
    translator so tags/images/links stay intact and it's obvious (via the
    "[AR]" marker) that this is a placeholder, not a real translation.
    """
    try:
        from bs4 import BeautifulSoup
        import sys, os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'translator'))
        import translation_api

        soup = BeautifulSoup(html_content, 'html.parser')
        for node in soup.find_all(string=True):
            text = str(node).strip()
            if text:
                node.replace_with(translation_api.translate(text))
        return str(soup)
    except Exception as e:
        print(f"⚠️ Fallback HTML translation failed, returning original: {e}")
        return html_content

def translate_title(text, target_lang='ar'):
    """
    Quick one-line title translation for the Reels admin form's live EN<->AR
    auto-fill. `target_lang` is 'ar' or 'en' — the language to translate INTO.
    Aims for a natural headline, not a literal word-for-word translation.
    """
    if not text or not text.strip():
        return ""

    try:
        lang_name = "Modern Standard Arabic (Fusha)" if target_lang == 'ar' else "English"
        prompt = f"""Translate this video title into {lang_name}. Keep it punchy and natural, the way a
        real headline would read — not a stiff word-for-word translation. Keep brand/product names
        (e.g. "GPT-4", "Instagram") as-is. Return ONLY the translated title, nothing else, no quotes.

        Title: {text}"""

        translated = _reply("other", [
            {"role": "system", "content": "You translate short titles/headlines naturally. Output only the translated text — no quotes, no commentary, no explanation."},
            {"role": "user", "content": prompt},
        ], temperature=0.3)
        if not translated:
            if target_lang == 'ar':
                return _mock_translate_to_ar(text)
            return None
        translated = translated.strip().strip('"').strip("'")
        return translated or text
    except Exception as e:
        print(f"❌ Title translation failed: {e}")
        if target_lang == 'ar':
            return _mock_translate_to_ar(text)
        return None

def _mock_translate_to_ar(text):
    """No-AI fallback for a short title — same mock translator used elsewhere."""
    try:
        from agent.skills.translator import translation_api
        return translation_api.translate(text)
    except Exception:
        return text

def draft_reel_summary(title, reference_notes, creator_name=None):
    """
    Drafts an ORIGINAL editorial summary (EN + AR) of a third-party short video,
    for use on a "worth watching" curation card that links out to the source.

    `reference_notes` is private background material (a transcript, a caption,
    rough notes) — it is read for context only and NEVER quoted at length or
    lightly reworded. The output must read as independent commentary describing
    what the clip covers, the way a journalist describes a talk they watched —
    not a rewrite of the source text. Callers should never display
    `reference_notes` itself on the site; it's an input to this function only.
    """
    if not reference_notes or not reference_notes.strip():
        return {"summary_en": "", "summary_ar": ""}

    try:
        prompt = f"""
        You are an editor for "Nasser AI News" writing a short curation blurb that links out
        to someone else's video. You are NOT transcribing, translating, or rewriting the
        source material — you are describing, in your own independent words, what the video
        is about, the way a journalist would describe a talk they attended.

        Video title: {title}
        Creator: {creator_name or "unknown"}

        Background notes (private reference only — a transcript/caption of the video; do not
        quote more than a few words of it verbatim, and never reproduce it as a whole):
        ---
        {reference_notes[:4000]}
        ---

        TASK:
        1. "summary_en": 2 sentences, in your own words, describing what the video covers and
           why it's worth watching. Do not closely paraphrase sentence-by-sentence — synthesize
           the gist instead.
        2. "summary_ar": the same idea, written natively in Modern Standard Arabic (not a
           translation of summary_en word-for-word, just convey the same gist).

        Return ONLY valid JSON: {{"summary_en": "...", "summary_ar": "..."}}
        """

        content = _reply("summarize", [
            {"role": "system", "content": "You write short, original, independent commentary about videos you're linking to. You never reproduce or closely paraphrase source text. You output JSON only."},
            {"role": "user", "content": prompt},
        ], temperature=0.4, json_mode=True)
        if not content:
            print("⚠️ No model configured for summarizing. Skipping AI summary draft.")
            return {"summary_en": "", "summary_ar": ""}
        result = json.loads(content)
        print(f"✅ AI drafted reel summary: {title[:30]}...")
        return {
            "summary_en": result.get("summary_en", ""),
            "summary_ar": result.get("summary_ar", "")
        }
    except Exception as e:
        print(f"❌ Reel summary draft failed: {e}")
        return {"summary_en": "", "summary_ar": ""}

def draft_tool_description(name, category_label, reference_notes=None):
    """
    Drafts an EN + AR description (2-3 sentences) for an entry in the
    "AI Tools & Platforms Directory" — plain-language, educational, aimed at
    a reader who may not know this tool yet: what it is, what it's for, what
    makes it notable. `reference_notes` is optional free-text context the
    admin typed (e.g. from the tool's own site or an article about it).
    """
    if not name or not name.strip():
        return {"description_en": "", "description_ar": ""}

    try:
        prompt = f"""You are writing an entry for an educational "AI Tools & Platforms Directory" aimed at
        readers (often students) who are still learning the AI landscape.

        Tool name: {name}
        Category: {category_label}
        {"Reference notes: " + reference_notes[:2000] if reference_notes and reference_notes.strip() else ""}

        Write a plain-language description (2-3 sentences) covering: what this tool/platform is, what you'd
        use it for, and anything notable about it — written for someone encountering it for the first time,
        not an existing expert. Avoid marketing fluff.

        TASK:
        1. "description_en": in English.
        2. "description_ar": the same idea, written natively in Modern Standard Arabic (not a literal
           translation, just convey the same meaning naturally).

        Return ONLY valid JSON: {{"description_en": "...", "description_ar": "..."}}
        """
        content = _reply("summarize", [
            {"role": "system", "content": "You write clear, educational descriptions of AI tools for newcomers. You output JSON only."},
            {"role": "user", "content": prompt},
        ], temperature=0.4, json_mode=True)
        if not content:
            print("⚠️ No model configured for summarizing. Skipping tool description draft.")
            return {"description_en": "", "description_ar": ""}
        result = json.loads(content)
        return {
            "description_en": result.get("description_en", ""),
            "description_ar": result.get("description_ar", ""),
        }
    except Exception as e:
        print(f"❌ Tool description draft failed: {e}")
        return {"description_en": "", "description_ar": ""}

def answer_reader_question(question, lang, articles, magazine_title="the magazine"):
    """
    "Ask the Magazine" — answers a reader's question using ONLY the curated
    articles passed in, never open-ended general knowledge. This keeps answers
    trustworthy and on-brand for a curated news magazine, and lets every answer
    link back to the real source articles it drew from.

    `articles` is a list of {"id": int, "title": str, "summary": str} dicts.
    Returns {"answer": str, "used_ids": [int, ...]} — used_ids is empty when
    the archive doesn't cover the question, in which case `answer` should say
    so honestly rather than guess.
    Returns None if no AI client is configured (caller should show a clear
    "not available" message rather than a fake answer).
    """
    if not question or not question.strip():
        return {"answer": "", "used_ids": []}

    try:
        lang_name = "Modern Standard Arabic (Fusha)" if lang == 'ar' else "English"
        catalog = "\n".join(
            f'[id={a["id"]}] {a["title"]} — {(a.get("summary") or "")[:220]}'
            for a in articles[:60]
        )
        prompt = f"""You are the AI reading companion for "{magazine_title}", a curated AI/tech news magazine.
        A reader asked you a question. Answer using ONLY the articles listed below — this magazine's own
        curated coverage, not your general knowledge. Never invent facts that aren't implied by these articles.

        Two kinds of questions:
        1. BROAD / overview questions ("what's the latest in AI?", "what's new this week?", "summarize
           recent news", "what's happening?") — these ARE answerable: synthesize across several of the
           articles below into a short roundup. This is the normal case, not an edge case — the articles
           below ARE "the latest," so use them.
        2. SPECIFIC questions about a topic, product, or event that these articles simply don't mention at
           all (e.g. sports scores, unrelated trivia, something not implied by any article below) — only
           for this case, say so honestly in {lang_name} (e.g. "I don't see coverage of that in the
           magazine yet") instead of guessing.

        When in doubt, prefer answering from the articles over refusing — refusing is only for genuinely
        unrelated questions.

        Keep the answer conversational and concise (2-5 sentences). Respond in {lang_name}.

        Articles:
        {catalog}

        Reader's question: "{question.strip()[:500]}"

        Return ONLY valid JSON: {{"answer": "...", "used_ids": [the numeric ids of articles you actually
        drew from, or an empty list only if truly nothing applies]}}
        """

        content = _reply("analyze", [
            {"role": "system", "content": "You answer reader questions using only the provided article catalog. You never use outside knowledge. You output JSON only."},
            {"role": "user", "content": prompt},
        ], temperature=0.3, json_mode=True)
        if not content:
            return None
        result = json.loads(content)
        return {
            "answer": result.get("answer", "").strip(),
            "used_ids": [i for i in result.get("used_ids", []) if isinstance(i, int)],
        }
    except Exception as e:
        print(f"❌ Ask-the-magazine failed: {e}")
        return None

def draft_newsletter_intro(articles, lang='en'):
    """
    Writes a short (2-4 sentence) editorial intro tying this batch of stories
    together for the newsletter digest — NOT a rewrite of any single article,
    just a cohesive "here's what mattered" framing. The actual per-story
    summaries below it in the email are the magazine's own already-written
    summaries (never regenerated here), so this never risks misrepresenting
    an article's content.
    `articles` is a list of {"title": ..., "summary": ...} dicts.
    Returns "" (safe, non-fatal) if no AI is configured — the digest still
    sends, just without the AI-written framing paragraph.
    """
    if not articles:
        return ""

    try:
        lang_name = "Modern Standard Arabic (Fusha)" if lang == 'ar' else "English"
        headlines = "\n".join(f"- {a.get('title', '')}" for a in articles[:8])
        prompt = f"""You are the editor of "Nasser AI News", a bilingual AI-focused magazine, writing the
        opening of this issue's email newsletter. Below are this issue's headlines.

        Write a short, warm, 2-4 sentence introduction in {lang_name} that ties these stories together
        thematically and makes the reader want to read on. Do NOT list the headlines back verbatim, do NOT
        use bullet points, and do NOT invent facts not implied by the headlines — describe the general
        shape of what's happening in AI this week. No greeting like "Dear reader" and no sign-off, just the
        introduction paragraph itself.

        Headlines:
        {headlines}
        """
        intro = _reply("summarize", [
            {"role": "system", "content": "You write short, engaging newsletter introductions. Output only the introduction paragraph, no preamble."},
            {"role": "user", "content": prompt},
        ], temperature=0.6)
        return intro or ""
    except Exception as e:
        print(f"❌ Newsletter intro draft failed: {e}")
        return ""

def analyze_comments(comments, article_title=""):
    """
    Read reader comments and report the overall sentiment, the main opinions,
    and the themes they share. Returns None when no model is assigned.
    """
    usable = [c for c in (comments or []) if (c.get("content") or "").strip()]
    if not usable:
        return {"summary": "No comments to analyze yet.", "sentiment": "none", "opinions": [], "themes": []}

    lines = "\n".join(
        f"- {(c.get('author') or 'Reader')}: {(c.get('content') or '')[:500]}"
        for c in usable[:40]
    )
    prompt = f"""You edit "Nasser AI News". Read the reader comments on this story and describe
    what the audience thinks. Do not invent comments that are not listed.

    Story: {article_title or "Untitled"}
    Comments:
    {lines}

    Return ONLY valid JSON:
    {{
      "summary": "2-3 sentences on the overall reaction",
      "sentiment": "one of: positive, mixed, negative, neutral",
      "opinions": ["distinct opinions readers expressed, up to 5"],
      "themes": ["short theme labels, up to 5"]
    }}
    """
    try:
        content = _reply("comments", [
            {"role": "system", "content": "You analyze reader comments. You output JSON only and never invent comments."},
            {"role": "user", "content": prompt},
        ], temperature=0.2, json_mode=True)
        if not content:
            return None
        result = json.loads(content)
        return {
            "summary": (result.get("summary") or "").strip(),
            "sentiment": (result.get("sentiment") or "mixed").strip(),
            "opinions": [str(item) for item in (result.get("opinions") or [])][:5],
            "themes": [str(item) for item in (result.get("themes") or [])][:5],
        }
    except Exception as exc:
        print(f"❌ Comment analysis failed: {exc}")
        return None

if __name__ == "__main__":
    # Test CLI execution
    print("Testing Content Processor...")
    test_title = "Google DeepMind unveils Gemini 1.5 Pro with 1M context window"
    test_snippet = "The new model can process typically an hour of video, 11 hours of audio, codebases with over 30,000 lines of code or over 700,000 words."
    
    res = process_news_item(test_title, test_snippet)
    print("\n--- Result ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))
