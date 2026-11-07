import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load keys
load_dotenv(override=True)  # .env is the source of truth — never let a stale OS-level env var win

def search_google_news(query, time_filter=None, lang='all', errors=None):
    """
    Searches using Google Custom Search API.
    time_filter: 'today', 'week', 'month', 'year', or None
    lang: 'all', 'ar' (Arabic)
    errors: optional list — if given, human-readable failure reasons are appended
            to it so the caller (the Flask app) can show the admin *why* a search
            came back empty instead of failing silently.
    """
    def _fail(msg):
        print(msg)
        if errors is not None:
            errors.append(msg)

    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("SEARCH_ENGINE_ID")

    if not api_key or not cx:
        _fail("Google Search is not configured: GOOGLE_API_KEY / SEARCH_ENGINE_ID missing in .env.")
        return []

    # Map time_filter to dateRestrict values
    date_restrict = None
    if time_filter == 'today':
        date_restrict = 'd1'
    elif time_filter == 'week':
        date_restrict = 'w1'
    elif time_filter == 'month':
        date_restrict = 'm1'
    elif time_filter == 'year':
        date_restrict = 'y1'

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cx,
        "key": api_key,
        "num": 10,
        "sort": "date" 
    }
    
    if date_restrict:
        params["dateRestrict"] = date_restrict
        
    if lang == 'ar':
        params["lr"] = "lang_ar"

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "error" in data:
            api_msg = data['error']['message']
            hint = ""
            if "Custom Search JSON API" in api_msg or "has not been used" in api_msg or "it is disabled" in api_msg:
                tail = api_key[-4:] if api_key else ""
                hint = (f" -> The key ending in {tail} belongs to a Google project where Custom Search is still off. "
                        "Enabling it on MyHermes does not change this key. Create an API key inside MyHermes "
                        "after Custom Search API shows Enabled, paste that new key into Settings → API Keys → "
                        "Google Search (a blank box keeps the old key), and click Save on that card.")
            elif "API key not valid" in api_msg:
                hint = " -> Fix: check GOOGLE_API_KEY in .env."
            _fail(f"Google Search API error: {api_msg}{hint}")
            return []

        results = []
        for item in data.get('items', []):
            title = item.get('title')
            link = item.get('link')
            snippet = item.get('snippet')
            
            # Image Extraction (The Reference Way)
            image_url = None
            pagemap = item.get('pagemap', {})
            if 'cse_image' in pagemap and len(pagemap['cse_image']) > 0:
                image_url = pagemap['cse_image'][0].get('src')
            
            # Extract Source from "metatags" if possible or domain
            source = item.get('displayLink', 'Google Search')
            
            # Parse Date if available in snippet or metatags
            # CSE allows "dateRestrict" in query but returns loose dates in snippet
            # We'll default to now if not found easily
            pub_date = datetime.now().isoformat()

            results.append({
                "title": title,
                "summary": snippet,
                "url": link,
                "image": image_url,
                "source": source,
                "fetched_at": pub_date
            })
            
        return results

    except Exception as e:
        _fail(f"Google Search request failed: {e}")
        return []
