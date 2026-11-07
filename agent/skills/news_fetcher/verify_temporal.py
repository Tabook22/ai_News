import os
import sys
import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

try:
    from agent.skills.news_fetcher.youtube_search import search_youtube_videos
    from agent.skills.news_fetcher.google_search import search_google_news
    print("✅ Modules imported successfully.")
except ImportError as e:
    print(f"❌ Import Failed: {e}")
    sys.exit(1)

def test_search(query, time_filter):
    print(f"\n--- Testing Filter: {query} [{time_filter}] ---")
    
    # YouTube Test
    print("YouTube:")
    yt_results = search_youtube_videos(query, max_results=2, time_filter=time_filter)
    for v in yt_results:
        print(f"  - [{v['published']}] {v['title'][:40]}...")
        
    if not yt_results: print("  (No YouTube results)")

    # Google Test
    print("Google:")
    g_results = search_google_news(query, time_filter=time_filter)
    for g in g_results[:2]:
         print(f"  - {g['title'][:40]}...")
    if not g_results: print("  (No Google results)")

if __name__ == "__main__":
    test_search("AI News", "today")
    test_search("AI News", "month")
