import json
import os
import sys

# Ensure we can import from project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Also ensure local directory is in path
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
if LOCAL_DIR not in sys.path:
    sys.path.append(LOCAL_DIR)

# Import Fetching Muscles
try:
    # Try importing as standard modules (if running from adjacent)
    from rss_fetch import fetch_from_rss
    from web_scraper import scrape_hacker_news
    from ddg_search import search_duckduckgo_news
    from google_search import search_google_news
    from youtube_search import search_youtube_videos
except ImportError:
    # Try importing via package path (if running from root)
    try:
        from agent.skills.news_fetcher.rss_fetch import fetch_from_rss
        from agent.skills.news_fetcher.web_scraper import scrape_hacker_news
        from agent.skills.news_fetcher.ddg_search import search_duckduckgo_news
        from agent.skills.news_fetcher.google_search import search_google_news
        from agent.skills.news_fetcher.youtube_search import search_youtube_videos
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"Warning: Module import error: {e}. Some functionality may be limited.")
        def fetch_from_rss(*args): return []
        def scrape_hacker_news(*args): return []
        def search_duckduckgo_news(*args, **kwargs): return []
        def search_google_news(*args, **kwargs): return []
        def search_youtube_videos(*args, **kwargs): return []

# Define your high-quality AI news sources
SOURCES = {
    "RSS": [
        "https://openai.com/news/rss.xml",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://blog.google/technology/ai/rss/"
    ],
    "WEB": [
        "https://news.ycombinator.com/show"
    ],
    "SEARCH_QUERIES": [
        "Artificial Intelligence News",
        "New AI Tools released this week",
        "LLM benchmarks latest",
        "ChatGPT updates",
        "Google Gemini news"
    ]
}

def fetch_news(query, max_results=10, time_filter='week', content_type='mixed', warnings=None):
    """
    Live Search Function used by the Flask App.
    Combines DuckDuckGo and Google Search (if configured).
    time_filter: 'today', 'week', 'month', 'year', 'all'
    content_type: 'mixed' (default), 'video'
    warnings: optional list — if given, human-readable reasons for any source
              coming back empty/failing are appended, so the UI can tell the
              admin *why* instead of just showing a blank results page.
    """
    if warnings is None:
        warnings = []
    results = []

    # If content_type is video, we skip text search and boost video results
    if content_type != 'video':
        # 1. DuckDuckGo Search (Primary, Free, no API key needed)
        try:
            ddg_results = search_duckduckgo_news(query, time_limit=time_filter, errors=warnings)
            results.extend(ddg_results)
        except Exception as e:
            print(f"DDG Search failed: {e}")
            warnings.append(f"DuckDuckGo search failed: {e}")

        # 2. Google Search (Secondary, API Key required)
        try:
            google_results = search_google_news(query, time_filter=time_filter, errors=warnings)
            # Deduplicate
            seen_links = {r['url'] for r in results}
            for gr in google_results:
                if gr['url'] not in seen_links:
                    results.append(gr)
        except Exception as e:
            print(f"Google Search failed: {e}")
            warnings.append(f"Google search failed: {e}")

    # 3. YouTube Search (Video News)
    try:
        # If video-only, fetch more results (e.g. 12)
        target_video_count = 12 if content_type == 'video' else 3

        yt_results = search_youtube_videos(query, max_results=target_video_count, time_filter=time_filter, errors=warnings)

        # Deduplicate (rare for video to overlap with text link but good practice)
        for yt in yt_results:
             results.append(yt)

    except Exception as e:
        print(f"YouTube Search failed: {e}")
        warnings.append(f"YouTube search failed: {e}")

    # If mixed, we might want to interleave or just append.
    # For now, append is fine.

    return results[:max_results if content_type != 'video' else 12]

def run_fetcher():
    """
    Batch Fetcher for Daily Aggregation Workflow (Background Job).
    """
    all_news = []
    
    print("Fetching news from RSS feeds...")
    for url in SOURCES["RSS"]:
        try:
            results = fetch_from_rss(url)
            all_news.extend(results)
        except Exception as e:
            print(f"Failed to fetch RSS {url}: {e}")
        
    print("Scraping Hacker News...")
    for url in SOURCES["WEB"]:
        try:
            results = scrape_hacker_news(url)
            all_news.extend(results)
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")

    print("Searching DuckDuckGo...")
    for query in SOURCES["SEARCH_QUERIES"]:
        try:
            results = search_duckduckgo_news(query, time_limit='d') 
            print(f"  - '{query}': Found {len(results)} items.")
            all_news.extend(results)
        except Exception as e:
            print(f"Failed to search {query}: {e}")
        
    # Save the raw findings
    output_dir = os.path.join(PROJECT_ROOT, 'data') # Use data dir from project root
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'latest_fetch.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=4)
    
    print(f"Success! {len(all_news)} news items fetched and saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(fetch_news(sys.argv[1]))
    else:
        run_fetcher()
