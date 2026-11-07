
import sys
import os
from app.app import app, db, NewsItem

def check_latest_item():
    with app.app_context():
        # Get the very latest modified/added item
        # Since we don't have 'updated_at', we use 'timestamp' (or we could guess by ID if UUIDs are sequential? No)
        # We'll just grab the last 5 and print titles.
        items = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(5).all()
        print(f"Checking latest {len(items)} items:")
        for item in items:
            print(f"ID: {item.id} | Title: {item.title}")
            print(f"English Content Len: {len(item.full_content) if item.full_content else 0}")
            print(f"Arabic Content Len: {len(item.full_content_ar) if item.full_content_ar else 0}")
            if item.full_content and len(item.full_content) > 0:
                 print(f"Content Snippet: {item.full_content[:100]}...")
            print("-" * 10)

if __name__ == "__main__":
    check_latest_item()
