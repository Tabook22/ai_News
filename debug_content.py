
import sys
import os
from app.app import app, db, MagazineSettings, NewsItem

def debug_settings_and_content():
    with app.app_context():
        # Check Settings
        settings = MagazineSettings.get_settings()
        print(f"SETTINGS: Language Mode = '{settings.language_mode}'")
        
        # Check the specific item "The Agentic System"
        item = NewsItem.query.filter(NewsItem.title.like('%Agentic%')).first()
        if item:
            print("-" * 20)
            print(f"ITEM: {item.title}")
            print(f"Article Type: {item.article_type}")
            print(f"Full Content (English) Length: {len(item.full_content) if item.full_content else 0}")
            print(f"Full Content (Arabic) Length: {len(item.full_content_ar) if item.full_content_ar else 0}")
            print("-" * 20)
            if item.full_content:
                print(f"English Snippet: {item.full_content[:50]}...")
        else:
            print("Item 'The Agentic System' not found.")

if __name__ == "__main__":
    debug_settings_and_content()
