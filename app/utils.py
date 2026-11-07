import json
import os

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'news_archive.json')

def load_archive():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_archive(items):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def append_item(item):
    items = load_archive()
    # Dedupe by URL
    for existing in items:
        if existing.get('url') == item.get('url'):
            return False
    items.append(item)
    save_archive(items)
    return True
