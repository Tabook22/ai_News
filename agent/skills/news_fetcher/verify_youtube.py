import os
import sys

from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

try:
    from agent.skills.news_fetcher.youtube_search import search_youtube_videos
    print("✅ Module imported successfully.")
except ImportError as e:
    print(f"❌ Import Failed: {e}")
    sys.exit(1)

# Check for API Key
api_key = os.environ.get('YOUTUBE_API_KEY')
if not api_key:
    print("⚠️  YOUTUBE_API_KEY not found in environment.")
    print("   Verification will skip actual API call.")
else:
    print(f"🔑 API Key found: {api_key[:5]}...")
    
    print("\nAttempting search for 'Artificial Intelligence'...")
    results = search_youtube_videos("Artificial Intelligence", max_results=2)
    
    if results:
        print(f"✅ Found {len(results)} videos:")
        for v in results:
            print(f"   - {v['title']} ({v['source']})")
    else:
        print("⚠️  No results found (or API error).")
