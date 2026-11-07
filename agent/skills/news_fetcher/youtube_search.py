from googleapiclient.discovery import build
import os
import isodate
import datetime

def search_youtube_videos(query, max_results=5, time_filter=None, errors=None):
    """
    Searches YouTube for videos related to the query.
    Requires YOUTUBE_API_KEY in environment variables.
    errors: optional list to collect human-readable failure reasons into.
    """
    def _fail(msg):
        print(msg)
        if errors is not None:
            errors.append(msg)

    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        _fail("YouTube search is not configured: YOUTUBE_API_KEY missing in .env.")
        return []

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Date Logic
        published_after = None
        now = datetime.datetime.utcnow()
        if time_filter == 'today':
            published_after = (now - datetime.timedelta(days=1)).isoformat("T") + "Z"
        elif time_filter == 'week':
            published_after = (now - datetime.timedelta(weeks=1)).isoformat("T") + "Z"
        elif time_filter == 'month':
            published_after = (now - datetime.timedelta(days=30)).isoformat("T") + "Z"
        elif time_filter == 'year':
            published_after = datetime.datetime(now.year, 1, 1).isoformat("T") + "Z"

        # 1. Search for videos
        search_args = {
            'q': query,
            'part': 'id,snippet',
            'maxResults': max_results,
            'type': 'video',
            'order': 'date'
        }
        if published_after:
            search_args['publishedAfter'] = published_after

        search_response = youtube.search().list(**search_args).execute()

        video_ids = []
        videos = []

        for item in search_response.get('items', []):
            if item['id']['kind'] == 'youtube#video':
                video_ids.append(item['id']['videoId'])
                videos.append({
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'source': 'YouTube'
                })

        # 2. Get Video Details (Duration) if needed
        # For now, we'll skip the extra call to get duration to save quota, 
        # unless strictly necessary. The snippet has enough for a card.
        
        # Format for our app
        results = []
        for vid in videos:
            # Parse Date
            try:
                # ISO 8601 format: 2023-10-25T12:00:00Z
                dt = datetime.datetime.strptime(vid['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                pub_date = dt.strftime("%Y-%m-%d")
            except:
                pub_date = vid['published_at']

            results.append({
                "title": vid['title'],
                "url": vid['url'],
                "image": vid['thumbnail'],
                "source": "YouTube", # Special designator
                "summary": vid['description'] or f"Video by {vid['channel']}",
                "published": pub_date,
                "content_format": "video",
                "video_id": vid['id']
            })

        return results

    except Exception as e:
        msg = str(e)
        hint = ""
        if 'quota' in msg.lower():
            hint = " -> Your YouTube Data API daily quota is exhausted; it resets at midnight Pacific time."
        elif '403' in msg:
            hint = " -> Check that the YouTube Data API v3 is enabled for the project that owns YOUTUBE_API_KEY."
        _fail(f"YouTube search failed: {msg}{hint}")
        return []
