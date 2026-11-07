
import sys
import os
from app.app import app, db, NewsItem

def check_latest_manual_items():
    with app.app_context():
        items = NewsItem.query.filter_by(article_type='manual').order_by(NewsItem.timestamp.desc()).limit(5).all()
        print(f"Found {len(items)} manual items.")
        for item in items:
            print(f"ID: {item.id}")
            print(f"Title: {item.title}")
            print(f"Summary: {item.summary}")
            print(f"Full Content Length: {len(item.full_content) if item.full_content else 0}")
            if item.full_content:
                print(f"Full Content Snippet: {item.full_content[:100]}...")
            else:
                print("Full Content is EMPTY or NONE")
            print("-" * 20)

if __name__ == "__main__":
    check_latest_manual_items()
