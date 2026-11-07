import feedparser
from datetime import datetime

def fetch_from_rss(url):
    """
    Muscle A: Parses standard RSS feeds.
    Returns a list of dictionaries with title, summary, url, and source.
    """
    try:
        feed = feedparser.parse(url)
        results = []
        # Get top 5 from each source to avoid noise
        if not feed.entries:
            print(f"Warning: No entries found for {url}")
            return []
            
        for entry in feed.entries[:5]:
            results.append({
                "title": entry.title,
                "summary": entry.get('summary', 'No summary available.'),
                "url": entry.link,
                "source": url,
                "fetched_at": datetime.now().isoformat()
            })
        return results
    except Exception as e:
        print(f"Error fetching RSS {url}: {e}")
        return []
