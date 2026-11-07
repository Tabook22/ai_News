
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

print("DEBUG START")

# 1. Test Direct Import of youtube_search
print("\n[1] Testing Direct Import of youtube_search...")
try:
    from agent.skills.news_fetcher.youtube_search import search_youtube_videos
    print("SUCCESS: youtube_search imported.")
    
    # Test Function
    print("Running search_youtube_videos('AI', max_results=2)...")
    try:
        results = search_youtube_videos('AI', max_results=2)
        print(f"RESULT: Found {len(results)} videos.")
        for r in results:
            print(f" - {r.get('title')}")
    except Exception as e:
        print(f"FAILURE: search_youtube_videos raised {e}")
except ImportError as e:
    print(f"FAILURE: Could not import youtube_search directly: {e}")

# 2. Test Actions Integration
print("\n[2] Testing Actions Integration...")
try:
    from agent.skills.news_fetcher.actions import fetch_news
    print("SUCCESS: actions imported.")
    
    print("Running fetch_news('AI', content_type='video')...")
    results = fetch_news('AI', content_type='video')
    print(f"RESULT: Found {len(results)} items.")
    for r in results:
        print(f" - {r.get('title')} [{r.get('source')}]")
except ImportError as e:
    print(f"FAILURE: Could not import actions: {e}")

print("DEBUG END")
