import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

try:
    from agent.skills.news_fetcher.actions import fetch_news
    print("✅ Module imported successfully.")
except ImportError as e:
    print(f"❌ Import Failed: {e}")
    sys.exit(1)

def test_video_filter():
    query = "SpaceX"
    print(f"\n--- Testing Video Only Filter for '{query}' ---")
    
    # 1. Mixed Mode (Default)
    print("\n1. Mixed Mode (Standard):")
    results_mixed = fetch_news(query, max_results=5, content_type='mixed')
    video_count = sum(1 for r in results_mixed if r.get('source') == 'YouTube')
    print(f"   Total: {len(results_mixed)}, Videos: {video_count}")
    
    # 2. Video Only Mode
    print("\n2. Video Only Mode:")
    results_video = fetch_news(query, max_results=10, content_type='video')
    video_count_v = sum(1 for r in results_video if r.get('source') == 'YouTube')
    text_count_v = len(results_video) - video_count_v
    
    print(f"   Total: {len(results_video)}")
    print(f"   Videos: {video_count_v}")
    print(f"   Text: {text_count_v}")
    
    for v in results_video[:3]:
        print(f"   - [Video] {v['title'][:40]}... ({v['url']})")

    if text_count_v == 0 and video_count_v > 0:
        print("\n✅ Verification PASSED: Only videos returned.")
    else:
        print("\n❌ Verification FAILED: Text results found or no videos.")

if __name__ == "__main__":
    test_video_filter()
