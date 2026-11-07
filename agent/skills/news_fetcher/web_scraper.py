import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_hacker_news(url):
    """
    Muscle B: Scrapes websites without RSS feeds.
    Currently specialized for Hacker News structure.
    """
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Logic specific to Hacker News structure
        # Note: Selectors might need updating if HN changes layout
        links = soup.select('.titleline > a')
        
        for link in links[:5]:
            results.append({
                "title": link.text,
                "summary": "Check link for details (Scraped Content).",
                "url": link.get('href'),
                "source": "Hacker News",
                "fetched_at": datetime.now().isoformat()
            })
        return results
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []
