
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

try:
    from agent.skills.news_fetcher.actions import fetch_news, search_youtube_videos
    print("Import successful.")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print("--- Testing Video Fetch via actions.fetch_news ---")
results = fetch_news("AI", content_type='video')
print(f"fetch_news results count: {len(results)}")
for r in results:
    print(f" - {r.get('title')} ({r.get('source')})")

print("\n--- Testing Direct search_youtube_videos ---")
try:
    direct_results = search_youtube_videos("AI", max_results=5)
    print(f"Direct results count: {len(direct_results)}")
except Exception as e:
    print(f"Direct call failed: {e}")
