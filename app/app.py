import os
import sys
import importlib
import base64
import socket
import ipaddress
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Force UTF-8 stdio so emoji/status logging never crashes the process on
# Windows terminals that default to a legacy codepage (cp1252) instead of UTF-8.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import time
import uuid
import secrets
import datetime
import traceback
import csv
import io
from datetime import timedelta
import calendar
import json # Added for Gallery handling
from collections import defaultdict
from flask import Flask, abort, render_template, request, redirect, url_for, flash, jsonify
from admin_i18n import admin_text
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv


# Load env variables
load_dotenv(override=True)  # .env is the source of truth (managed via Settings -> API Keys) — never
# let a stale OS-level environment variable of the same name silently win.

print(">>> RELOAD DEBUG: app.py loaded V10 <<<")

# Import Skills
# 1. News Fetcher
try:
    from agent.skills.news_fetcher import actions as news_fetcher
except ImportError as e:
    print(f"❌ News Fetcher Import Error: {e}")
    news_fetcher = None

# 2. Media Handler
try:
    from agent.skills.media_handler import actions as media_handler
except ImportError as e:
    print(f"❌ Media Handler Import Error: {e}")
    media_handler = None

# 3. Content Processor (OpenAI)
try:
    from agent.skills.content_processor import actions as content_processor
except ImportError as e:
    print(f"❌ Content Processor Import Error: {e}")
    content_processor = None

# 3b. Newsletter Mailer (SMTP)
try:
    from agent.skills.newsletter import actions as newsletter_mailer
except ImportError as e:
    print(f"❌ Newsletter Mailer Import Error: {e}")
    newsletter_mailer = None

# 4. Translator (Legacy/Fallback)
try:
    from agent.skills.translator import actions as translator
except ImportError as e:
    print(f"❌ Translator Import Error: {e}")
    translator = None

# Define a simple Config class for demonstration purposes, as it's referenced in the diff
# In a real application, this would likely be in a separate config.py file.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-nasser-news')
    # Handle multiple DB URL formats
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///local_dev.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app = Flask(
    __name__,
    instance_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"),
)
app.config.from_object(Config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Behind Nginx the app can live under a subpath such as /ainews/.
# Nginx sends X-Forwarded-Prefix; ProxyFix turns it into SCRIPT_NAME so url_for()
# and static URLs include the prefix.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['SESSION_COOKIE_PATH'] = os.environ.get('SESSION_COOKIE_PATH', '/')

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB limit
# print(f">>> DEBUG CHECK: MAX_CONTENT_LENGTH set to {app.config['MAX_CONTENT_LENGTH']} <<<")

# Ensure upload dirs exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'images'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'docs'), exist_ok=True)

print(f">>> SERVER STARTUP: CONFIG UPDATED V6 - Max Upload: {app.config['MAX_CONTENT_LENGTH']} <<<") 

db = SQLAlchemy(app)

# --- Database Model ---

class MagazineSettings(db.Model):
    __tablename__ = 'magazine_settings'
    id = db.Column(db.Integer, primary_key=True)
    magazine_title = db.Column(db.String(200), default="Nasser AI News")
    logo_path = db.Column(db.String(500), default="") # Empty means use text or default
    version = db.Column(db.String(50), default="Vol. 1 - 2026")
    
    # Author / Editor Profile
    author_name = db.Column(db.String(200), default="Editor in Chief")
    author_bio = db.Column(db.Text, default="AI Enthusiast & Curator")
    author_name_ar = db.Column(db.String(200), default="")
    author_bio_ar = db.Column(db.Text, default="")
    author_image = db.Column(db.String(500), default="")
    author_phone = db.Column(db.String(50), default="")
    author_email = db.Column(db.String(100), default="")
    author_address = db.Column(db.String(200), default="")
    author_workplace = db.Column(db.String(200), default="")
    
    # Social Media
    social_twitter = db.Column(db.String(200), default="")
    social_linkedin = db.Column(db.String(200), default="")
    social_facebook = db.Column(db.String(200), default="")
    social_instagram = db.Column(db.String(200), default="")
    
    # Enhanced Profile
    author_intro = db.Column(db.Text, default="")         # Rich text intro
    author_intro_ar = db.Column(db.Text, default="")      # Rich text intro (Arabic)
    author_cv = db.Column(db.String(500), default="")     # Path to CV file
    author_gallery = db.Column(db.Text, default="[]")     # JSON list of image paths
    
    @property
    def gallery_list(self):
        try:
            if self.author_gallery:
                items = json.loads(self.author_gallery)
                normalized = []
                for item in items:
                    if isinstance(item, str):
                        normalized.append({'path': item, 'title': '', 'desc': ''})
                    elif isinstance(item, dict):
                        normalized.append(item)
                return normalized
            return []
        except:
            return []
    
    # Appearance
    language_mode = db.Column(db.String(20), default="bilingual") # 'bilingual', 'en', 'ar'
    theme = db.Column(db.String(20), default="slate") # 'slate', 'light', 'midnight', 'sepia'
    magazine_template = db.Column(db.String(30), default="slate") # 'slate', 'broadsheet', 'wire', 'quarterly'
    
    # Custom Overrides
    custom_text_color = db.Column(db.String(20), nullable=True)
    custom_accent_color = db.Column(db.String(20), nullable=True)
    
    # Tag-Specific Colors
    color_h1 = db.Column(db.String(20), nullable=True)
    color_h2 = db.Column(db.String(20), nullable=True)
    color_h3 = db.Column(db.String(20), nullable=True)
    color_h4 = db.Column(db.String(20), nullable=True)
    color_h5 = db.Column(db.String(20), nullable=True)
    color_h6 = db.Column(db.String(20), nullable=True)
    color_p  = db.Column(db.String(20), nullable=True)
    color_li = db.Column(db.String(20), nullable=True)
    
    # Section Titles (Customizable)
    section_title_top = db.Column(db.String(100), default="Top Story")
    section_title_latest = db.Column(db.String(100), default="Latest News")
    section_title_trending = db.Column(db.String(100), default="Trending / Updates")
    section_title_archives = db.Column(db.String(100), default="Archives")
    section_title_ads = db.Column(db.String(100), default="Sponsored")
    # Section Titles — Arabic (falls back to a sensible built-in translation if blank)
    section_title_top_ar = db.Column(db.String(100), default="")
    section_title_latest_ar = db.Column(db.String(100), default="")
    section_title_trending_ar = db.Column(db.String(100), default="")
    section_title_archives_ar = db.Column(db.String(100), default="")
    section_title_ads_ar = db.Column(db.String(100), default="")
    # Curated Reels section
    reels_enabled = db.Column(db.Boolean, default=True)
    section_title_reels = db.Column(db.String(100), default="Worth Watching")
    section_title_reels_ar = db.Column(db.String(100), default="")
    reels_display_limit = db.Column(db.Integer, default=4)

    # Names of extra (non-predefined) API keys added via the API Keys settings
    # tab — the actual secret values live only in .env, never in the database.
    custom_api_key_names = db.Column(db.Text, default="[]")

    # Editor-chosen covers. Blank means the issue picks for itself.
    cover_world_id = db.Column(db.String(36), default="")
    cover_campus_id = db.Column(db.String(36), default="")
    # Comma-separated campus topic keys. Blank keeps the built-in order.
    campus_kind_order = db.Column(db.Text, default="")

    @property
    def custom_api_key_names_list(self):
        try:
            return json.loads(self.custom_api_key_names) if self.custom_api_key_names else []
        except Exception:
            return []

    @staticmethod
    def get_settings():
        settings = MagazineSettings.query.first()
        if not settings:
            settings = MagazineSettings()
            db.session.add(settings)
            db.session.commit()
        return settings

class NewsItem(db.Model):
    __tablename__ = 'news_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # English Fields
    title = db.Column(db.String(500), nullable=False)
    summary = db.Column(db.Text)
    full_content = db.Column(db.Text)
    
    headline_display_mode = db.Column(db.String(20), default='default') # 'en', 'ar', 'default'

    # Arabic Fields
    title_ar = db.Column(db.String(500))
    summary_ar = db.Column(db.Text)
    full_content_ar = db.Column(db.Text)
    
    # Meta
    source = db.Column(db.String(200))
    url = db.Column(db.Text)
    image = db.Column(db.String(500))
    attachment = db.Column(db.String(500))
    category = db.Column(db.String(50), default='sidebar')
    is_published = db.Column(db.Boolean, default=True) # New visibility toggle
    display_order = db.Column(db.Integer, default=0)
    show_details = db.Column(db.Boolean, default=False) # New: Show full content in magazine
    article_type = db.Column(db.String(20), default='manual') # 'manual' or 'external'
    
    # YouTube / Video Specific
    video_id = db.Column(db.String(50))
    content_format = db.Column(db.String(20), default='article') # 'article', 'video'

    # Popularity
    views = db.Column(db.Integer, default=0)

    # Editorial desk (ai, software, security, ...). Blank means "classify from the headline".
    topic = db.Column(db.String(30), default="")

    # When the original report was published. Blank falls back to the time it entered the magazine.
    published_at = db.Column(db.DateTime)

    # world = companies and the daily wire. research = labs, journals, universities.
    # campus = Dhofar University and the Computer Science department. Never auto-imported.
    wing = db.Column(db.String(20), default="world")
    campus_kind = db.Column(db.String(20), default="")  # notice, work, forum
    event_on = db.Column(db.Date)
    place = db.Column(db.String(160), default="")
    course = db.Column(db.String(120), default="")

    # Classroom bridge for students. Grounded in the story; blank until written.
    lesson_why = db.Column(db.Text, default="")
    lesson_why_ar = db.Column(db.Text, default="")
    lesson_term = db.Column(db.String(160), default="")
    lesson_term_ar = db.Column(db.String(160), default="")
    lesson_gloss = db.Column(db.Text, default="")
    lesson_gloss_ar = db.Column(db.Text, default="")
    lesson_ask = db.Column(db.Text, default="")
    lesson_ask_ar = db.Column(db.Text, default="")

    # Relationship
    comments = db.relationship('Comment', backref='news_item', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "title": self.title,
            "summary": self.summary,
            "full_content": self.full_content,
            "title_ar": self.title_ar,
            "summary_ar": self.summary_ar,
            "full_content_ar": self.full_content_ar,
            "video_id": self.video_id,
            "content_format": self.content_format,
            "source": self.source,
            "url": self.url,
            "image": self.image,
            "attachment": self.attachment,
            "category": self.category,
            "is_published": self.is_published if self.is_published is not None else True,
            "display_order": self.display_order,
            "show_details": self.show_details,
            "article_type": self.article_type,
            "headline_display_mode": self.headline_display_mode,
            "views": self.views or 0,
            "topic": self.topic or "",
            "published_at": self.published_at.isoformat() if self.published_at else "",
            "wing": self.wing or "world",
            "campus_kind": self.campus_kind or "",
            "event_on": self.event_on.isoformat() if self.event_on else "",
            "place": self.place or "",
            "course": self.course or "",
            "lesson_why": self.lesson_why or "",
            "lesson_why_ar": self.lesson_why_ar or "",
            "lesson_term": self.lesson_term or "",
            "lesson_term_ar": self.lesson_term_ar or "",
            "lesson_gloss": self.lesson_gloss or "",
            "lesson_gloss_ar": self.lesson_gloss_ar or "",
            "lesson_ask": self.lesson_ask or "",
            "lesson_ask_ar": self.lesson_ask_ar or "",
            "comments": [c.to_dict() for c in self.comments]
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    news_item_id = db.Column(db.String(36), db.ForeignKey('news_items.id'), nullable=False)
    author = db.Column(db.String(100), default="Guest")
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "author": self.author,
            "content": self.content,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M')
        }

class Subscriber(db.Model):
    """Newsletter sign-ups — the audience for the weekly/daily AI briefing."""
    __tablename__ = 'subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120))
    language_pref = db.Column(db.String(10), default='both')  # 'en', 'ar', 'both'
    source = db.Column(db.String(50), default='web')  # 'web', 'qr'
    is_active = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(64), unique=True, default=lambda: secrets.token_urlsafe(24))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "language_pref": self.language_pref,
            "source": self.source,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ""
        }

class CuratedReel(db.Model):
    """
    A pointer to an external short-form video (Instagram Reel, etc.) — NOT the
    video itself. We only ever store a title, creator attribution, a small
    preview thumbnail, a link back to the original post, and an original
    editorial summary. The source video/transcript never gets hosted or
    reproduced here; this is a curated "worth watching" card that sends
    readers to the original creator.
    """
    __tablename__ = 'curated_reels'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    title_ar = db.Column(db.String(300))
    creator_name = db.Column(db.String(150))       # e.g. "Shirin Khosravi Jam"
    creator_handle = db.Column(db.String(100))      # e.g. "jam.with.ai"
    platform = db.Column(db.String(30), default='instagram')  # instagram, tiktok, youtube_short...
    source_url = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.String(500))
    summary_en = db.Column(db.Text)
    summary_ar = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)  # legacy — superseded by `status`, kept for the migration
    status = db.Column(db.String(20), default='published')  # 'draft' | 'published' | 'archived'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "title_ar": self.title_ar,
            "creator_name": self.creator_name,
            "creator_handle": self.creator_handle,
            "platform": self.platform,
            "source_url": self.source_url,
            "thumbnail": self.thumbnail,
            "summary_en": self.summary_en,
            "summary_ar": self.summary_ar,
            "display_order": self.display_order,
            "status": self.status or 'published',
            "created_at": self.created_at.strftime('%Y-%m-%d') if self.created_at else ""
        }

TOOL_CATEGORIES = [
    ('chatbot', '💬 Chatbot / Assistant'),
    ('coding', '💻 Coding Assistant'),
    ('image', '🎨 Image Generation'),
    ('video', '🎬 Video Generation'),
    ('video_edit', '🎞️ Video Editing'),
    ('writing', '✍️ Writing & Content'),
    ('research', '🔬 Research & Analysis'),
    ('presentations', '📊 Presentations'),
    ('productivity', '⚡ Productivity'),
    ('voice', '🎙️ Audio & Voice'),
    ('design', '🧩 Design & UI'),
    ('education', '🎓 Learning'),
    ('agents', '🤖 Agents & Automation'),
    ('platforms', '🧱 Models & GPUs'),
    ('other', '🧩 Other'),
]
TOOL_CATEGORY_LABELS = dict(TOOL_CATEGORIES)

PROJECT_TRACKS = {
    'final_year': ('Final-year project', 'مشروع التخرج'),
    'research': ('Research idea', 'فكرة بحثية'),
    'competition': ('Competition / hackathon', 'مسابقة / هاكاثون'),
}

PROJECT_AREAS = {
    'agents': ('Agents & automation', 'الوكلاء والأتمتة'),
    'rag': ('Search & RAG', 'البحث وRAG'),
    'arabic': ('Arabic AI', 'الذكاء الاصطناعي العربي'),
    'education': ('Learning & teaching', 'التعلم والتعليم'),
    'vision': ('Vision & imaging', 'الرؤية والصور'),
    'audio': ('Speech & audio', 'الصوت والكلام'),
    'security': ('Safety & security', 'الأمان والحماية'),
    'sustainability': ('Sustainability', 'الاستدامة'),
    'data': ('Data & recommendation', 'البيانات والتوصية'),
    'accessibility': ('Accessibility', 'الوصول'),
}

LLMWARE_PICKS = [
    {'name': 'Dragon Mistral 7B', 'repo': 'llmware/dragon-mistral-7b-v0', 'size': '7B',
     'downloads': 1315, 'likes': 112,
     'use_en': 'RAG answers over long documents',
     'use_ar': 'إجابات RAG على مستندات طويلة',
     'url': 'https://huggingface.co/llmware/dragon-mistral-7b-v0'},
    {'name': 'Dragon Yi 6B', 'repo': 'llmware/dragon-yi-6b-v0', 'size': '6B',
     'downloads': 534, 'likes': 61,
     'use_en': 'RAG with a smaller memory footprint',
     'use_ar': 'RAG بذاكرة أصغر',
     'url': 'https://huggingface.co/llmware/dragon-yi-6b-v0'},
    {'name': 'SLIM Sentiment Tool', 'repo': 'llmware/slim-sentiment-tool', 'size': 'small',
     'downloads': 4776, 'likes': 5,
     'use_en': 'Fast sentiment labels for feedback',
     'use_ar': 'تصنيف مشاعر سريع للملاحظات',
     'url': 'https://huggingface.co/llmware/slim-sentiment-tool'},
    {'name': 'SLIM SQL 1B', 'repo': 'llmware/slim-sql-1b-v0', 'size': '1B',
     'downloads': 233, 'likes': 10,
     'use_en': 'Natural language to SQL',
     'use_ar': 'تحويل اللغة الطبيعية إلى SQL',
     'url': 'https://huggingface.co/llmware/slim-sql-1b-v0'},
]

TOOL_PRICING_LABELS = {
    'free': ('Free', 'مجاني'),
    'freemium': ('Free tier', 'خطة مجانية'),
    'paid': ('Paid', 'مدفوع'),
}

class AITool(db.Model):
    """
    A curated entry in the "AI Tools & Platforms Directory" — an evergreen
    reference (ChatGPT, Claude, coding assistants, image generators, etc.)
    separate from the news feed, so readers can learn the AI landscape itself
    rather than just following headlines. Each tool can link back to the
    magazine's own past coverage that mentions it.
    """
    __tablename__ = 'ai_tools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    name_ar = db.Column(db.String(150))
    category = db.Column(db.String(30), default='other')
    description_en = db.Column(db.Text)
    description_ar = db.Column(db.Text)
    tagline_en = db.Column(db.String(200), default='')
    tagline_ar = db.Column(db.String(200), default='')
    official_url = db.Column(db.Text)
    logo = db.Column(db.String(500))
    pricing = db.Column(db.String(20), default='freemium')  # free | freemium | paid
    free_tier = db.Column(db.Boolean, default=True)
    arabic_support = db.Column(db.Boolean, default=False)
    platforms = db.Column(db.String(200), default='Web')
    best_for = db.Column(db.String(200), default='')
    featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    last_checked = db.Column(db.Date)
    rating = db.Column(db.Float, default=0)
    rating_note = db.Column(db.String(300), default='')
    rating_source = db.Column(db.String(300), default='')
    is_published = db.Column(db.Boolean, default=True)
    related_article_ids = db.Column(db.Text, default='[]')  # JSON list of NewsItem ids
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    @property
    def related_article_ids_list(self):
        try:
            return json.loads(self.related_article_ids) if self.related_article_ids else []
        except Exception:
            return []

    def to_dict(self):
        pricing = self.pricing or 'freemium'
        price_en, price_ar = TOOL_PRICING_LABELS.get(pricing, ('Free tier', 'خطة مجانية'))
        return {
            "id": self.id,
            "name": self.name,
            "name_ar": self.name_ar,
            "category": self.category or 'other',
            "category_label": TOOL_CATEGORY_LABELS.get(self.category, '🧩 Other'),
            "tagline_en": self.tagline_en or '',
            "tagline_ar": self.tagline_ar or '',
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "official_url": self.official_url,
            "logo": self.logo,
            "pricing": pricing,
            "pricing_label_en": price_en,
            "pricing_label_ar": price_ar,
            "free_tier": bool(self.free_tier),
            "arabic_support": bool(self.arabic_support),
            "platforms": [p.strip() for p in (self.platforms or 'Web').split(',') if p.strip()],
            "best_for": self.best_for or '',
            "featured": bool(self.featured),
            "sort_order": self.sort_order or 0,
            "rating": round(float(self.rating or 0), 1),
            "rating_note": self.rating_note or '',
            "rating_source": self.rating_source or '',
            "last_checked": self.last_checked.isoformat() if self.last_checked else '',
            "is_published": self.is_published if self.is_published is not None else True,
            "related_article_ids": self.related_article_ids_list,
            "created_at": self.created_at.strftime('%Y-%m-%d') if self.created_at else ""
        }


class LLMModel(db.Model):
    """A snapshot of the most-downloaded open language models on Hugging Face.

    Downloads are a popularity signal, not a quality score; the model card and
    licence link are the reference readers should follow.
    """
    __tablename__ = 'llm_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    org = db.Column(db.String(100), default='')
    params = db.Column(db.String(40), default='')
    licence = db.Column(db.String(80), default='')
    downloads = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    pipeline = db.Column(db.String(80), default='text-generation')
    url = db.Column(db.Text)
    note_en = db.Column(db.Text, default='')
    note_ar = db.Column(db.Text, default='')
    checked_at = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'org': self.org,
            'params': self.params,
            'licence': self.licence,
            'downloads': self.downloads or 0,
            'likes': self.likes or 0,
            'pipeline': self.pipeline,
            'url': self.url,
            'note_en': self.note_en,
            'note_ar': self.note_ar,
            'checked_at': self.checked_at.isoformat() if self.checked_at else '',
        }


class ProjectIdea(db.Model):
    """A final-year project idea for Computer Science students, with a reference."""
    __tablename__ = 'project_ideas'
    id = db.Column(db.Integer, primary_key=True)
    title_en = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), default='')
    summary_en = db.Column(db.String(300), default='')
    summary_ar = db.Column(db.String(300), default='')
    body_en = db.Column(db.Text, default='')
    body_ar = db.Column(db.Text, default='')
    area = db.Column(db.String(30), default='agents')
    track = db.Column(db.String(20), default='final_year')
    difficulty = db.Column(db.String(20), default='intermediate')
    skills = db.Column(db.String(200), default='')
    tools = db.Column(db.String(200), default='')
    reference_title = db.Column(db.String(200), default='')
    reference_url = db.Column(db.Text)
    reference_note_en = db.Column(db.String(300), default='')
    reference_note_ar = db.Column(db.String(300), default='')
    featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title_en': self.title_en,
            'title_ar': self.title_ar,
            'summary_en': self.summary_en,
            'summary_ar': self.summary_ar,
            'body_en': self.body_en,
            'body_ar': self.body_ar,
            'area': self.area or 'agents',
            'area_en': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[0],
            'area_ar': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[1],
            'track': self.track or 'final_year',
            'track_en': PROJECT_TRACKS.get(self.track, ('Final-year project', 'مشروع التخرج'))[0],
            'track_ar': PROJECT_TRACKS.get(self.track, ('Final-year project', 'مشروع التخرج'))[1],
            'difficulty': self.difficulty or 'intermediate',
            'skills': [s.strip() for s in (self.skills or '').split(',') if s.strip()],
            'tools': [t.strip() for t in (self.tools or '').split(',') if t.strip()],
            'reference_title': self.reference_title or '',
            'reference_url': self.reference_url or '',
            'reference_note_en': self.reference_note_en or '',
            'reference_note_ar': self.reference_note_ar or '',
            'featured': bool(self.featured),
            'sort_order': self.sort_order or 0,
            'is_published': bool(self.is_published),
        }


class OccasionAlbum(db.Model):
    """One department occasion: a semester, a name, a date, and its pictures."""
    __tablename__ = 'occasion_albums'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    term = db.Column(db.String(10), nullable=False, default='fall')  # fall | spring
    year = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), default='')
    title_ar = db.Column(db.String(200), default='')
    event_date = db.Column(db.Date)
    note = db.Column(db.Text, default='')
    note_ar = db.Column(db.Text, default='')
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    photos = db.relationship(
        'OccasionPhoto',
        backref='album',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='OccasionPhoto.display_order',
    )


class OccasionPhoto(db.Model):
    __tablename__ = 'occasion_photos'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    album_id = db.Column(db.String(36), db.ForeignKey('occasion_albums.id'), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), default='')
    title_ar = db.Column(db.String(200), default='')
    caption = db.Column(db.Text, default='')
    caption_ar = db.Column(db.Text, default='')
    display_order = db.Column(db.Integer, default=0)


class NewsPhoto(db.Model):
    """A news picture added by hand, beside the photos taken from saved stories."""
    __tablename__ = 'news_photos'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), default='')
    title_ar = db.Column(db.String(200), default='')
    caption = db.Column(db.Text, default='')
    caption_ar = db.Column(db.Text, default='')
    source_url = db.Column(db.Text, default='')
    topic = db.Column(db.String(30), default='ai')
    event_date = db.Column(db.Date)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class YouTubePick(db.Model):
    """One chosen YouTube clip on the news shelf or the education shelf."""
    __tablename__ = 'youtube_picks'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = db.Column(db.String(20), nullable=False)
    lane = db.Column(db.String(20), nullable=False)  # news | education
    language = db.Column(db.String(5), nullable=False)  # en | ar
    title = db.Column(db.String(300), default='')
    summary = db.Column(db.Text, default='')
    channel = db.Column(db.String(180), default='')
    image = db.Column(db.String(500), default='')
    url = db.Column(db.Text, default='')
    published_at = db.Column(db.DateTime)
    view_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer, default=0)
    display_order = db.Column(db.Integer, default=0)
    fetched_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# --- Utils ---
LANG_COOKIE = 'lang_pref'
LANG_CHOICES = ('en', 'ar', 'both')

# Reader-facing sections. First match wins, so a security story that mentions
# "AI" still lands on the security desk. Blank `topic` means "infer".
NEWS_DESKS = (
    ("security", "Cybersecurity", "الأمن السيبراني", (
        "security", "cyber", "hack", "breach", "malware", "ransomware", "privacy",
        "vulnerability", "phishing", "prompt injection", "exploit", "injection",
        "أمن", "اختراق", "حقن", "استغلال", "ثغرة",
    )),
    ("robotics", "Robotics", "الروبوتات", (
        "robot", "robotics", "drone", "humanoid", "روبوت",
    )),
    ("hardware", "Chips & Devices", "الرقائق والأجهزة", (
        "chip", "semiconductor", "nvidia", "gpu", "cpu", "iphone", "hardware",
        "processor", "tsmc", "intel", "amd", "معالج", "شريحة", "رقائق",
    )),
    ("ai", "Artificial Intelligence", "الذكاء الاصطناعي", (
        "artificial intelligence", "machine learning", "deep learning", "llm",
        "gpt", "chatgpt", "openai", "claude", "gemini", "neural", "generative",
        "transformer", "copilot", "anthropic", "agent", "agentic", "clawdbot",
        "moltbot", "ذكاء", "وكيل",
    )),
    ("data", "Data & Cloud", "البيانات والسحابة", (
        "cloud", "database", "data center", "aws", "azure", "kubernetes", "بيانات", "سحاب",
    )),
    ("software", "Software", "البرمجيات", (
        "software", "programming", "developer", "github", "python", "javascript",
        "open source", "linux", "coding", "vps", "برمجة", "تثبيت",
    )),
    ("science", "Science", "العلوم", (
        "quantum", "nasa", "physics", "biology", "climate", "scientist", "فضاء", "كموم",
    )),
    ("business", "Tech & Business", "التقنية والأعمال", (
        "startup", "funding", "acquisition", "ipo", "regulation", "investment",
        "استثمار", "تمويل",
    )),
)
BRIEFING_DESK = ("briefing", "The Brief", "مختارات", ())
DESK_BY_KEY = {d[0]: d for d in NEWS_DESKS}
DESK_BY_KEY[BRIEFING_DESK[0]] = BRIEFING_DESK
ARABIC_WEEKDAYS = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
ARABIC_MONTHS = ["", "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                 "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def get_lang_pref():
    """The reader's language: saved choice, then ?lang=, then the browser.

    The old first-visit gate blocked every shared link (and every crawler) behind a
    cookie. Public content now always renders; the choice is remembered when made.
    """
    val = request.cookies.get(LANG_COOKIE)
    if val in LANG_CHOICES:
        return val
    asked = (request.args.get('lang') or '').strip().lower()
    if asked in LANG_CHOICES:
        return asked
    best = request.accept_languages.best_match(['ar', 'en'])
    return best or 'en'

ADMIN_LANG_COOKIE = 'admin_lang'

def get_admin_lang():
    """Editor language. Separate from the public reader, so a supervisor can work in Arabic."""
    return 'ar' if request.cookies.get(ADMIN_LANG_COOKIE) == 'ar' else 'en'

def _render_language_gate():
    """
    The first thing a reader ever sees (e.g. right after scanning the door
    QR code). Leads with today's actual top story and the author's own
    byline — proving there's something real and credible here before asking
    for a single click — rather than a bare language-choice form.
    """
    settings = MagazineSettings.get_settings()
    top_story = NewsItem.query.filter_by(is_published=True) \
        .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc()).first()
    return render_template('language_gate.html', settings=settings,
                           next=request.full_path.rstrip('?'),
                           top_story=top_story.to_dict() if top_story else None)

@app.context_processor
def inject_global_vars():
    try:
        from flask import session as flask_session
        is_logged = bool(flask_session.get('logged_in'))
        try:
            reels_count = CuratedReel.query.filter_by(status='published').count()
            tools_count = AITool.query.filter_by(is_published=True).count()
            subscriber_count = Subscriber.query.filter_by(is_active=True).count() if is_logged else 0
        except Exception:
            reels_count = tools_count = subscriber_count = 0
        return {
            'settings': MagazineSettings.get_settings(),
            'lang_pref': get_lang_pref(),
            'news_desks': NEWS_DESKS,
            'campus_kind_choices': ordered_campus_kind_choices(),
            'logged_in': is_logged,
            'admin_desk': _admin_desk(),
            'admin_lang': get_admin_lang(),
            'admin_ar': get_admin_lang() == 'ar',
            'now_year': datetime.datetime.now().year,
            'reels_count': reels_count,
            'tools_count': tools_count,
            'subscriber_count': subscriber_count,
        }
    except Exception:
        # DB might not be init yet
        return {'settings': None, 'lang_pref': get_lang_pref(), 'news_desks': NEWS_DESKS, 'campus_kind_choices': CAMPUS_KIND_CHOICES, 'admin_desk': 'newsroom', 'admin_lang': 'en', 'admin_ar': False, 'now_year': datetime.datetime.now().year, 'reels_count': 0, 'tools_count': 0, 'subscriber_count': 0}


@app.template_global('A')
def admin_label(key):
    return admin_text(get_admin_lang(), key)


@app.route('/admin_language')
def set_admin_language():
    lang = 'ar' if request.args.get('lang') == 'ar' else 'en'
    next_url = _safe_next(request.args.get('next'), url_for('newsroom'))
    resp = redirect(next_url)
    resp.set_cookie(ADMIN_LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return resp


def _admin_desk():
    """Which editing room the admin nav should show. The two content desks never share a list."""
    ep = request.endpoint or ''
    if ep in (
        'department_admin', 'add_campus_post', 'toggle_campus_post', 'remove_campus_post',
        'photo_archive_admin', 'add_occasion_photos', 'add_photos_to_album',
        'update_occasion_photo', 'remove_occasion_photo', 'remove_occasion_album',
        'toggle_occasion_album',
    ):
        return 'campus'
    if ep == 'archive_page':
        return 'campus' if request.args.get('desk') == 'campus' else 'world'
    if ep == 'edit_news':
        item = NewsItem.query.get((request.view_args or {}).get('item_id'))
        if item and (item.wing or '') == 'campus':
            return 'campus'
        return 'world'
    if ep in (
        'dashboard', 'search_page', 'add_news', 'classroom_note', 'run_daily_brief',
        'news_photos_admin', 'add_news_photo', 'remove_news_photo',
        'refresh_youtube_desk',
        'reels_list', 'reels_archive', 'add_reel', 'edit_reel',
        'tools_list', 'add_tool', 'edit_tool',
    ):
        return 'world'
    return 'newsroom'

@app.route('/favicon.ico')
def favicon():
    """Some browsers/crawlers request this path directly regardless of the
    <link rel="icon"> tag. Point them at the magazine logo if set, else the
    default icon."""
    settings = MagazineSettings.get_settings()
    if settings and settings.logo_path:
        return redirect(settings.logo_path)
    return redirect(url_for('static', filename='favicon.svg'))

def _safe_next(url, default):
    """Same-site relative paths only. '//evil.com' and '/\\evil.com' look relative but
    browsers treat them as off-site, so they are rejected too."""
    if url and url.startswith('/') and not url.startswith('//') and '\\' not in url:
        return url
    return default

_public_hits = defaultdict(list)  # (bucket, ip) -> recent request timestamps

def _public_rate_limited(bucket, max_hits, window_seconds):
    """Counts this request against the caller's IP; True means over the limit."""
    key = (bucket, request.remote_addr or 'unknown')
    now = time.time()
    recent = [t for t in _public_hits[key] if now - t < window_seconds]
    if len(recent) >= max_hits:
        _public_hits[key] = recent
        return True
    recent.append(now)
    _public_hits[key] = recent
    return False

@app.route('/set_language')
def set_language():
    """Sets (or changes) the reader's language cookie, then bounces back to
    wherever they came from. Read once, remembered for a year — no re-asking."""
    lang = request.args.get('lang', 'both')
    if lang not in LANG_CHOICES:
        lang = 'both'
    next_url = _safe_next(request.args.get('next'), url_for('magazine_view'))
    resp = redirect(next_url)
    resp.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite='Lax')
    return resp

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# --- API Key Management (.env-backed) ---
# Predefined third-party providers the app can actually use. "fields" lists the
# .env variable name(s) each card manages; a provider may need more than one
# (e.g. Google Search needs both an API key and a Search Engine ID).
API_KEY_PROVIDERS = [
    {
        'id': 'openai', 'label': 'OpenAI', 'icon': '🧠',
        'help': 'Powers AI summaries, translations, and the Reels AI-assist.',
        'fields': [{'name': 'OPENAI_API_KEY', 'label': 'API Key', 'placeholder': 'sk-...'}],
    },
    {
        'id': 'anthropic', 'label': 'Anthropic (Claude)', 'icon': '🟣',
        'help': 'Reserved for future Claude-powered features.',
        'fields': [{'name': 'ANTHROPIC_API_KEY', 'label': 'API Key', 'placeholder': 'sk-ant-...'}],
    },
    {
        'id': 'grok', 'label': 'Grok (xAI)', 'icon': '⚡',
        'help': 'Reserved for future Grok-powered features.',
        'fields': [{'name': 'XAI_API_KEY', 'label': 'API Key', 'placeholder': 'xai-...'}],
    },
    {
        'id': 'google_search', 'label': 'Google Search', 'icon': '🔍',
        'help': 'Powers live news search — needs both a Custom Search API key and a Search Engine ID.',
        'fields': [
            {'name': 'GOOGLE_API_KEY', 'label': 'API Key', 'placeholder': 'AIza...'},
            {'name': 'SEARCH_ENGINE_ID', 'label': 'Search Engine ID', 'placeholder': 'e.g. a1b2c3d4e5f6g7h8i'},
        ],
    },
    {
        'id': 'youtube', 'label': 'YouTube Data API', 'icon': '📺',
        'help': 'Powers video search and link verification.',
        'fields': [{'name': 'YOUTUBE_API_KEY', 'label': 'API Key', 'placeholder': 'AIza...'}],
    },
    {
        'id': 'smtp', 'label': 'Email (SMTP)', 'icon': '📧',
        'help': 'Powers the subscriber newsletter digest. Works with Gmail (use an App Password), Outlook, or any SMTP provider.',
        'fields': [
            {'name': 'SMTP_HOST', 'label': 'SMTP Host', 'placeholder': 'smtp.gmail.com'},
            {'name': 'SMTP_PORT', 'label': 'Port', 'placeholder': '587'},
            {'name': 'SMTP_USERNAME', 'label': 'Username', 'placeholder': 'you@gmail.com'},
            {'name': 'SMTP_PASSWORD', 'label': 'Password / App Password', 'placeholder': '••••••••'},
            {'name': 'SMTP_FROM_EMAIL', 'label': 'From Email (optional)', 'placeholder': 'you@gmail.com', 'optional': True},
            {'name': 'SMTP_FROM_NAME', 'label': 'From Name (optional)', 'placeholder': 'Nasser AI News', 'optional': True},
        ],
    },
]

# Core app secrets this UI will never read or write, even if a custom key name collides.
_RESERVED_ENV_NAMES = {
    'SECRET_KEY', 'DATABASE_URL', 'ADMIN_USERNAME', 'ADMIN_PASSWORD',
    'ADMIN_PASSWORD_HASH', 'FLASK_DEBUG', 'FLASK_ENV', 'FLASK_APP',
}

_ENV_NAME_RE = re.compile(r'^[A-Z][A-Z0-9_]{1,60}$')
ENV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')

def _mask_secret(value):
    if not value:
        return ''
    value = value.strip()
    if len(value) <= 8:
        return '•' * len(value)
    return f"{value[:4]}{'•' * 6}{value[-4:]}"

def _read_env_lines():
    if not os.path.exists(ENV_FILE_PATH):
        return []
    with open(ENV_FILE_PATH, 'r', encoding='utf-8') as f:
        return f.readlines()

def set_env_var(name, value):
    """Writes/updates one KEY=VALUE line in .env and applies it to the live process immediately."""
    lines = _read_env_lines()
    new_lines = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key == name:
                new_lines.append(f"{name}={value}\n")
                found = True
                continue
        new_lines.append(line)
    if not found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines.append(f"{name}={value}\n")
    with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    os.environ[name] = value

def remove_env_var(name):
    """Deletes a KEY=VALUE line from .env and clears it from the live process."""
    lines = _read_env_lines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key == name:
                continue
        new_lines.append(line)
    with open(ENV_FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    os.environ.pop(name, None)

def estimate_reading_time(html_content, words_per_minute=200):
    """Rough '3 min read' estimate from an HTML body — strips tags, counts words."""
    if not html_content:
        return 1
    try:
        text = BeautifulSoup(html_content, 'html.parser').get_text(' ')
        word_count = len(text.split())
        return max(1, round(word_count / words_per_minute))
    except Exception:
        return 1

def infer_topic(title, summary="", source=""):
    """Best-effort desk for a story that was saved without an explicit section."""
    blob = f"{title or ''} {summary or ''} {source or ''}".lower()
    for key, _en, _ar, words in NEWS_DESKS:
        for word in words:
            if word in blob:
                return key
    return BRIEFING_DESK[0]

_SOURCE_KIND_LABELS = {
    "lab": ("Lab", "مختبر",
            "A university, journal, or research laboratory.",
            "جامعة أو مجلة علمية أو مختبر بحثي."),
    "newsroom": ("Newsroom", "غرفة أخبار",
                 "An established news organisation with editorial oversight.",
                 "مؤسسة إخبارية معروفة لديها تحرير ومراجعة."),
    "company": ("Company", "شركة",
                "The company's own announcement — useful, but it is also marketing.",
                "إعلان الشركة نفسها — مفيد، لكنه تسويق أيضًا."),
    "video": ("Video", "فيديو",
              "A video or channel; check who made it and why.",
              "مقطع أو قناة؛ تحقّق من صانعه وهدفه."),
    "other": ("Source", "مصدر",
              "The original publisher of the story.",
              "الناشر الأصلي للقصة."),
}

_LAB_SOURCES = {
    "mit news", "mit technology review", "nature", "sciencedaily", "deepmind",
    "science", "arxiv", "cell", "the lancet", "ieee", "acm",
}
_COMPANY_SOURCES = {
    "openai", "nvidia", "google", "meta", "microsoft", "anthropic", "apple",
    "amazon", "wiz", "trak.in", "intel", "amd", "ibm", "samsung", "huawei",
}
_NEWSROOM_SOURCES = {
    "the guardian", "the verge", "bbc", "new york times", "wired", "techcrunch",
    "reuters", "associated press", "bloomberg", "financial times", "cnbc",
    "cnn", "al jazeera", "the economist", "washington post", "axios",
}


def classify_source_kind(source, url="", content_format="", video_id=""):
    """What kind of source is this? Shown to readers as an evidence label."""
    name = (source or "").strip().lower()
    link = (url or "").strip().lower()
    if content_format == "video" or video_id or "youtube.com" in link or "youtu.be" in link:
        return "video"
    if name in _LAB_SOURCES:
        return "lab"
    if name in _NEWSROOM_SOURCES:
        return "newsroom"
    if name in _COMPANY_SOURCES:
        return "company"
    if "news" in name or "times" in name or "post" in name or "journal" in name:
        return "newsroom"
    return "other"


def assign_desk(story):
    """Attach the desk label, reading time, and source type onto a story dict."""
    stored = (story.get("topic") or "").strip()
    desk = stored if stored in DESK_BY_KEY else infer_topic(
        story.get("title"), story.get("summary"), story.get("source"))
    meta = DESK_BY_KEY[desk]
    story["desk"] = desk
    story["desk_en"] = meta[1]
    story["desk_ar"] = meta[2]
    story["reading_minutes"] = estimate_reading_time(story.get("full_content") or story.get("summary") or "")
    published_en, published_ar = published_labels(story.get("published_at") or story.get("timestamp"))
    story["published_en"] = published_en
    story["published_ar"] = published_ar
    kind = classify_source_kind(story.get("source"), story.get("url"),
                                story.get("content_format"), story.get("video_id"))
    labels = _SOURCE_KIND_LABELS[kind]
    story["source_kind"] = kind
    story["source_kind_en"] = labels[0]
    story["source_kind_ar"] = labels[1]
    story["source_kind_note_en"] = labels[2]
    story["source_kind_note_ar"] = labels[3]
    return story

def published_labels(value):
    """Date and time of a report, shown in Gulf time (UTC+4)."""
    local = _as_gulf_time(value)
    if local is None:
        return "", ""
    # Midnight UTC means the publisher gave a day but not a clock.
    if local.hour == 4 and local.minute == 0 and local.second == 0:
        en = f"{local.day} {local.strftime('%b')} {local.year}"
        ar = f"{local.day} {ARABIC_MONTHS[local.month]} {local.year}"
        return en, ar
    hour = local.hour % 12 or 12
    minute = f"{local.minute:02d}"
    en = f"{local.day} {local.strftime('%b')} {local.year} · {hour}:{minute} {'AM' if local.hour < 12 else 'PM'}"
    ar = f"{local.day} {ARABIC_MONTHS[local.month]} {local.year} · {hour}:{minute} {'ص' if local.hour < 12 else 'م'}"
    return en, ar

def _as_gulf_time(value):
    if isinstance(value, datetime.datetime):
        when = value
    elif isinstance(value, str) and value.strip():
        try:
            when = datetime.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when.astimezone(datetime.timezone(datetime.timedelta(hours=4)))

def edition_context(stories):
    now = datetime.datetime.now()
    minutes = sum((s.get("reading_minutes") or 1) for s in stories)
    return {
        "edition_count": len(stories),
        "edition_minutes": minutes or 1,
        "edition_weekday_en": now.strftime("%A"),
        "edition_weekday_ar": ARABIC_WEEKDAYS[now.weekday()],
        "edition_date_en": now.strftime("%B %d, %Y"),
        "edition_date_ar": f"{now.day} {ARABIC_MONTHS[now.month]} {now.year}",
    }

# Labs, journals, and university research desks. Company blogs stay on the world wire.
RESEARCH_SOURCES = {
    "mit news", "mit technology review", "nature", "sciencedaily", "deepmind",
}
CAMPUS_KIND_CHOICES = (
    ("exam", "Exam time", "موعد اختبار"),
    ("summary", "Study summary", "ملخص تعليمي"),
    ("video", "Teaching video", "فيديو تعليمي"),
    ("occasion", "Occasion", "مناسبة"),
    ("workshop", "Training workshops", "ورش تدريبية"),
    ("conference", "Conferences", "مؤتمرات"),
    ("meeting", "Student meetings", "اجتماعات طلبة"),
    ("notice", "University notice", "إعلان الجامعة"),
    ("work", "Department work", "عمل القسم"),
    ("forum", "Forum", "المنتدى"),
)
CAMPUS_KINDS = tuple(row[0] for row in CAMPUS_KIND_CHOICES)
CAMPUS_KIND_LABELS = {key: (en, ar) for key, en, ar in CAMPUS_KIND_CHOICES}


def ordered_campus_kind_choices():
    """Topic order chosen on the department desk. New topics stay at the end."""
    saved = []
    try:
        raw = MagazineSettings.get_settings().campus_kind_order or ""
        for part in raw.split(","):
            key = part.strip()
            if key in CAMPUS_KINDS and key not in saved:
                saved.append(key)
    except Exception:
        saved = []
    for key, _en, _ar in CAMPUS_KIND_CHOICES:
        if key not in saved:
            saved.append(key)
    return tuple((key, CAMPUS_KIND_LABELS[key][0], CAMPUS_KIND_LABELS[key][1]) for key in saved)


def _kind_rank():
    return {key: index for index, (key, _en, _ar) in enumerate(ordered_campus_kind_choices())}


def _clip(value, limit):
    return (value or "").strip()[:limit]


@app.template_filter("plain_dek")
def plain_dek(value):
    """Drop pasted links from a summary so a cover line reads as a sentence."""
    text = re.sub(r"https?://\S+", "", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


@app.template_filter("reader_line")
def reader_line(value):
    """Hide the untranslated marker so a failed Arabic line is not printed as a headline."""
    text = plain_dek(value)
    if text.startswith("[AR]"):
        text = text[4:].strip()
    return text


@app.template_filter("month_short")
def month_short(value, ar=False):
    """A compact month label for date chips: OCT / أكتوبر."""
    when = _as_gulf_time(value)
    if when is None:
        try:
            day = datetime.date.fromisoformat(str(value)[:10])
            when = datetime.datetime(day.year, day.month, day.day)
        except Exception:
            return ""
    if ar:
        return ARABIC_MONTHS[when.month]
    return when.strftime("%b").upper()


app.jinja_env.globals['month_short'] = month_short


def _first_sentence(value, limit=170):
    text = reader_line(value)
    if not text:
        return ""
    for mark in (". ", "۔ ", "! ", "? "):
        if mark in text:
            text = text.split(mark, 1)[0].strip()
            break
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return text


def _picture_brief(story):
    """Who, what changed, and the classroom line already stored on the story."""
    story["lead_what_en"] = _first_sentence(story.get("summary"))
    story["lead_what_ar"] = _first_sentence(story.get("summary_ar")) or story["lead_what_en"]
    why_en = reader_line(story.get("lesson_why") or story.get("lesson_ask") or "")
    why_ar = reader_line(story.get("lesson_why_ar") or story.get("lesson_ask_ar") or "")
    story["lead_why_en"] = why_en
    story["lead_why_ar"] = why_ar or why_en
    return story


def _daily_file(stories):
    """The latest five world stories, with the first one filed that day in front."""
    latest = sorted(stories, key=lambda story: story.get("timestamp") or "", reverse=True)[:5]
    latest.sort(key=lambda story: story.get("timestamp") or "")
    return latest


def _cover_story(stories, item_id):
    """The published story an editor pinned, or nothing if that pin is stale."""
    item_id = (item_id or "").strip()
    if not item_id:
        return None
    return next((story for story in stories if story.get("id") == item_id), None)


def classify_wing(source, title="", summary=""):
    """World wire, or the scientific community. Campus is chosen by the editor only."""
    if (source or "").strip().lower() in RESEARCH_SOURCES:
        return "research"
    blob = f"{title or ''} {summary or ''}".lower()
    for word in ("peer-reviewed", "preprint", "journal", "laboratory", "researchers at"):
        if word in blob:
            return "research"
    return "world"


def audience_from_form(form):
    wing = (form.get("wing") or "world").strip()
    if wing not in ("world", "research", "campus"):
        wing = "world"
    kind = (form.get("campus_kind") or "").strip()
    if wing != "campus" or kind not in CAMPUS_KINDS:
        kind = "work" if wing == "campus" else ""
    return wing, kind


def apply_campus_schedule(item, form):
    """Day, room, and course are set only when the form actually sends them."""
    if item.wing != "campus":
        return
    if "event_on" in form:
        item.event_on = _parse_day(form.get("event_on"))
    if "place" in form:
        item.place = _clip(form.get("place"), 160) or ""
    if "course" in form:
        item.course = _clip(form.get("course"), 120) or ""


def lesson_from_form(form):
    return {
        "lesson_why": _clip(form.get("lesson_why"), 700),
        "lesson_why_ar": _clip(form.get("lesson_why_ar"), 700),
        "lesson_term": _clip(form.get("lesson_term"), 160),
        "lesson_term_ar": _clip(form.get("lesson_term_ar"), 160),
        "lesson_gloss": _clip(form.get("lesson_gloss"), 400),
        "lesson_gloss_ar": _clip(form.get("lesson_gloss_ar"), 400),
        "lesson_ask": _clip(form.get("lesson_ask"), 400),
        "lesson_ask_ar": _clip(form.get("lesson_ask_ar"), 400),
    }


def apply_lesson(item, note):
    for key, value in note.items():
        setattr(item, key, value)


def draft_classroom_note(title, summary):
    """A student note drawn only from the story text. Returns None if the model is unavailable."""
    try:
        from agent.skills.content_processor import providers
    except Exception:
        return None
    system = (
        "You write a classroom note for computer-science undergraduates at Dhofar University. "
        "Use only the title and summary. Do not add events, numbers, names, causes, or advice that are not in that text. "
        "Do not tell the student how to run their own project. "
        "If the text is thin, say only what it actually says. "
        "Return JSON with keys why_en, why_ar, term_en, term_ar, gloss_en, gloss_ar, ask_en, ask_ar. "
        "why: at most two sentences on why a CS student should understand this. "
        "term: one technical term that appears in the story. gloss: one sentence defining that term. "
        "ask: one open question for the classroom, with no answer. Arabic fields are in Arabic."
    )
    try:
        response = providers.complete(
            "summarize",
            [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Title: {title}\nSummary: {summary or ''}"},
            ],
            temperature=0.2,
            json_mode=True,
        )
    except Exception as exc:
        print(f"Classroom note failed: {exc}")
        return None
    if response is None:
        return None
    raw = (response.choices[0].message.content or "").strip()
    try:
        data = json.loads(raw)
    except Exception:
        return None
    note = {
        "lesson_why": _clip(data.get("why_en"), 700),
        "lesson_why_ar": _clip(data.get("why_ar"), 700),
        "lesson_term": _clip(data.get("term_en"), 160),
        "lesson_term_ar": _clip(data.get("term_ar"), 160),
        "lesson_gloss": _clip(data.get("gloss_en"), 400),
        "lesson_gloss_ar": _clip(data.get("gloss_ar"), 400),
        "lesson_ask": _clip(data.get("ask_en"), 400),
        "lesson_ask_ar": _clip(data.get("ask_ar"), 400),
    }
    if not note["lesson_why"] or not note["lesson_ask"]:
        return None
    return note


def write_classroom_note(item):
    note = draft_classroom_note(item.title, item.summary)
    if not note:
        return False
    apply_lesson(item, note)
    return True


def pick_lesson(stories):
    noted = [s for s in stories if s.get("lesson_why") or s.get("lesson_ask")]
    if not noted:
        return None
    noted.sort(key=lambda s: s.get("timestamp") or "", reverse=True)
    return noted[0]


def youtube_watch_url(story):
    """Public YouTube address for a department video. Empty when the topic is not a video."""
    video_id = (story.get("video_id") or "").strip()
    url = (story.get("url") or "").strip()
    is_video = (
        story.get("content_format") == "video"
        or story.get("article_type") == "video"
        or story.get("campus_kind") == "video"
        or bool(video_id)
    )
    if not is_video:
        return ""
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def label_campus(stories):
    for story in stories:
        en, ar = CAMPUS_KIND_LABELS.get(story.get("campus_kind") or "work", ("Department", "القسم"))
        story["kind_en"] = en
        story["kind_ar"] = ar
        story["watch_url"] = youtube_watch_url(story)
    return stories


def campus_groups(stories):
    buckets = {key: [] for key in CAMPUS_KINDS}
    for story in stories:
        key = story.get("campus_kind") or "work"
        if key not in buckets:
            key = "work"
        buckets[key].append(story)
    groups = []
    for key, en, ar in ordered_campus_kind_choices():
        if buckets[key]:
            groups.append({"key": key, "label_en": en, "label_ar": ar, "stories": buckets[key]})
    return groups


CAMPUS_ROOMS = (
    ("study", "Study", "الدراسة", ("exam", "summary", "video")),
    ("life", "Department life", "حياة القسم", ("occasion", "workshop", "conference", "meeting")),
    ("board", "Notice board", "لوحة الإعلانات", ("notice", "work", "forum")),
)
_COVER_RANK = {
    "occasion": 0, "workshop": 1, "conference": 2, "meeting": 3,
    "exam": 4, "video": 5, "summary": 6, "notice": 7, "work": 8, "forum": 9,
}


def _parse_day(raw):
    text = (raw or "").strip()
    if not text:
        return None
    try:
        return datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None


def _story_day(story):
    day = _parse_day(story.get("event_on"))
    if day:
        return day
    return _parse_day(story.get("timestamp"))


def _stamp_campus(story):
    day = _story_day(story)
    if day:
        story["day_en"] = f"{day.strftime('%a')} {day.day} {day.strftime('%b')}"
        story["day_ar"] = f"{ARABIC_WEEKDAYS[day.weekday()]} {day.day} {ARABIC_MONTHS[day.month]}"
    else:
        story["day_en"] = ""
        story["day_ar"] = ""
    story["place_label"] = (story.get("place") or story.get("source") or "").strip()
    return story


def campus_rooms(stories):
    rank = _kind_rank()
    rooms = []
    for key, en, ar, kinds in CAMPUS_ROOMS:
        items = [story for story in stories if (story.get("campus_kind") or "work") in kinds]
        if not items:
            continue
        items.sort(key=lambda story: rank.get(story.get("campus_kind") or "work", 99))
        rooms.append({
            "key": key,
            "label_en": en,
            "label_ar": ar,
            "stories": items,
            "groups": campus_groups(items),
            "rank": min(rank.get(story.get("campus_kind") or "work", 99) for story in items),
        })
    rooms.sort(key=lambda room: room["rank"])
    return rooms


def campus_agenda(stories):
    """This Gulf week when the department dated it. Otherwise the latest study and life items."""
    today = datetime.date.today()
    start = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    end = start + datetime.timedelta(days=6)
    this_week = [story for story in stories if (day := _story_day(story)) and start <= day <= end]
    rank = _kind_rank()
    if this_week:
        this_week.sort(key=lambda story: (_story_day(story), rank.get(story.get("campus_kind"), 99)))
        return [_stamp_campus(story) for story in this_week[:5]], True
    preferred = [
        story for story in stories
        if (story.get("campus_kind") or "") in ("occasion", "workshop", "conference", "meeting", "exam", "video", "summary", "notice")
    ]
    preferred.sort(key=lambda story: story.get("timestamp") or "", reverse=True)
    preferred.sort(key=lambda story: rank.get(story.get("campus_kind"), 99))
    return [_stamp_campus(story) for story in preferred[:4]], False


def pick_campus_feature(stories):
    """An occasion, an exam, or a lesson leads the department side."""
    if not stories:
        return None
    ranked = sorted(stories, key=lambda story: story.get("timestamp") or "", reverse=True)
    ranked.sort(key=lambda story: (
        _COVER_RANK.get(story.get("campus_kind") or "work", 9),
        0 if story.get("image") else 1,
    ))
    return ranked[0]


def course_dossier(stories):
    """One course that currently has a summary, a lesson, or an exam."""
    buckets = {}
    for story in stories:
        name = (story.get("course") or "").strip()
        if not name or (story.get("campus_kind") or "") not in ("exam", "summary", "video"):
            continue
        buckets.setdefault(name, []).append(story)
    if not buckets:
        return None

    def weight(items):
        kinds = {item.get("campus_kind") for item in items}
        return (1 if "exam" in kinds else 0, len(kinds), len(items))

    name = max(buckets, key=lambda key: weight(buckets[key]))
    items = buckets[name]
    return {
        "name": name,
        "exam": next((item for item in items if item.get("campus_kind") == "exam"), None),
        "summary": next((item for item in items if item.get("campus_kind") == "summary"), None),
        "video": next((item for item in items if item.get("campus_kind") == "video"), None),
    }


def term_of(day):
    if day is None:
        return None
    if day.month >= 9 or day.month == 1:
        year = day.year if day.month >= 9 else day.year - 1
        return "fall", year
    return "spring", day.year


def campus_terms(stories):
    """Current semester first, then earlier ones."""
    buckets = {}
    for story in stories:
        key = term_of(_story_day(story))
        if key is None:
            continue
        buckets.setdefault(key, []).append(story)
    current = _current_term()
    ordered = sorted(buckets, key=lambda key: (key[1], 1 if key[0] == "fall" else 0), reverse=True)
    if current in ordered:
        ordered.remove(current)
        ordered.insert(0, current)
    terms = []
    for key in ordered:
        term, year = key
        terms.append({
            "key": f"{term}-{year}",
            "term": term,
            "year": year,
            "current": key == current,
            "stories": buckets[key],
        })
    return terms


def campus_slots_from(stories):
    ordered = sorted(stories, key=lambda s: s.get("timestamp") or "", reverse=True)
    slots = {kind: None for kind in CAMPUS_KINDS}
    for story in ordered:
        kind = story.get("campus_kind") or "work"
        if kind not in slots:
            kind = "work"
        if slots[kind] is None:
            slots[kind] = story
    return slots


def week_start_utc(now=None):
    now = now or datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=now.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0)

def _stored_topic(raw):
    value = (raw or "").strip()
    return value if value in DESK_BY_KEY else ""

_EMBED_PREFIXES = ('https://www.youtube.com/embed/', 'https://www.youtube-nocookie.com/embed/',
                   'https://player.vimeo.com/video/')

@app.template_filter('clean_html')
def clean_html(html_content):
    """Safe replacement for `|safe` on article bodies. Articles can contain pasted web
    content or AI output, so strip scripts, inline event handlers and javascript: links
    while keeping normal formatting, images and YouTube/Vimeo embeds."""
    from markupsafe import Markup
    if not html_content:
        return Markup('')
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup.find_all(['script', 'style', 'object', 'embed', 'link', 'meta', 'base', 'form']):
            tag.decompose()
        for tag in soup.find_all('iframe'):
            if not (tag.get('src') or '').startswith(_EMBED_PREFIXES):
                tag.decompose()
        for tag in soup.find_all(True):
            for attr in list(tag.attrs):
                if attr.lower().startswith('on') or attr.lower() == 'srcdoc':
                    del tag.attrs[attr]
                    continue
                value = tag.attrs[attr]
                if attr.lower() in ('href', 'src', 'xlink:href', 'action', 'formaction') and isinstance(value, str):
                    compact = re.sub(r'[\s\x00-\x1f]+', '', value).lower()
                    if compact.startswith(('javascript:', 'vbscript:')) or \
                            (compact.startswith('data:') and not compact.startswith('data:image/')):
                        del tag.attrs[attr]
        return Markup(str(soup))
    except Exception as e:
        print(f"⚠️ clean_html failed, escaping instead: {e}")
        from markupsafe import escape
        return escape(html_content)

def _editor_html(raw):
    """Drop an empty editor document so a blank page is not stored as the story."""
    text = (raw or "").strip()
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = plain.replace("&nbsp;", " ").replace("\xa0", " ").strip()
    return text if plain else ""


def process_content_images(html_content):
    """
    Parses HTML content, finds base64 images, saves them to disk,
    and replaces the 'src' with a local URL.
    """
    if not html_content:
        return html_content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        images = soup.find_all('img')
        
        modified = False
        for img in images:
            src = img.get('src')
            if src and src.startswith('data:image'):
                try:
                    # Format: data:image/png;base64,.....
                    # We accept jpg, jpeg, png, gif, webp
                    header, encoded = src.split(',', 1)
                    
                    file_ext = 'png' # default
                    if 'image/jpeg' in header: file_ext = 'jpg'
                    elif 'image/gif' in header: file_ext = 'gif'
                    elif 'image/webp' in header: file_ext = 'webp'
                    
                    data = base64.b64decode(encoded)
                    
                    # Add Timestamp to filename
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_name = f"embedded_{timestamp}_{uuid.uuid4().hex[:6]}.{file_ext}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', unique_name)
                    
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    
                    # Update src to server path
                    img['src'] = f"/static/uploads/images/{unique_name}"
                    modified = True
                    print(f"✅ Converted base64 image to {unique_name}")
                except Exception as e:
                    print(f"⚠️ Image conversion failed: {e}")
        
        return str(soup) if modified else html_content
    except Exception as e:
        print(f"❌ HTML Process Error: {e}")
        return html_content

# --- Auth ---
from functools import wraps
from flask import session
from werkzeug.security import check_password_hash

# Admin credentials are configurable via .env (ADMIN_USERNAME / ADMIN_PASSWORD or
# ADMIN_PASSWORD_HASH). Falls back to the original dev defaults so a fresh clone
# still boots, but logs a warning so it doesn't stay that way in production.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')

if not ADMIN_PASSWORD and not ADMIN_PASSWORD_HASH:
    ADMIN_PASSWORD = 'admin123'
    print("⚠️  Using default admin credentials (admin / admin123). "
          "Set ADMIN_USERNAME + ADMIN_PASSWORD (or ADMIN_PASSWORD_HASH) in .env before going live.")

def verify_admin_credentials(username, password):
    if not username or not password:
        return False
    if not secrets.compare_digest(username, ADMIN_USERNAME):
        return False
    if ADMIN_PASSWORD_HASH:
        return check_password_hash(ADMIN_PASSWORD_HASH, password)
    return secrets.compare_digest(password, ADMIN_PASSWORD)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # Send them back to THIS page after they log in, instead of always to the dashboard.
            return redirect(url_for('login', next=request.full_path.rstrip('?')))
        return f(*args, **kwargs)
    return decorated_function

# --- Basic brute-force protection on /login (in-memory, per-process) ---
_login_attempts = defaultdict(list)  # ip -> [timestamps of recent failed attempts]
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60

def _login_locked_out(ip):
    now = time.time()
    recent = [t for t in _login_attempts[ip] if now - t < LOGIN_LOCKOUT_SECONDS]
    _login_attempts[ip] = recent
    return len(recent) >= LOGIN_MAX_ATTEMPTS

def _record_failed_login(ip):
    _login_attempts[ip].append(time.time())

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = _safe_next(request.values.get('next'), '')

    if request.method == 'POST':
        ip = request.remote_addr or 'unknown'

        if _login_locked_out(ip):
            flash("Too many failed attempts. Please wait 15 minutes and try again.", "error")
            return render_template('login.html', next=next_url)

        username = request.form.get('username')
        password = request.form.get('password')
        if verify_admin_credentials(username, password):
            session.clear()  # avoid session fixation
            session['logged_in'] = True
            return redirect(next_url or url_for('admin_dashboard'))
        else:
            _record_failed_login(ip)
            flash("Invalid credentials.", "error")

    return render_template('login.html', next=next_url)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("Logged out.", "success")
    return redirect(url_for('login'))

@app.route('/debug_env')
@login_required
def debug_env():
    """Debug route to check environment from within Flask"""
    status = "<h1>Environment Debug</h1>"
    status += f"<p>Python: {sys.executable}</p>"
    status += f"<p>Path: {sys.path}</p>"
    
    try:
        import openai
        status += f"<p>✅ OpenAI: {openai.__file__}</p>"
        status += f"<p>Key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Missing'}</p>"
    except ImportError as e:
        status += f"<p>❌ OpenAI Error: {e}</p>"
        
    try:
        import duckduckgo_search
        status += f"<p>✅ DDG: {duckduckgo_search.__file__}</p>"
    except ImportError as e:
        status += f"<p>❌ DDG Error: {e}</p>"
        
    status += "<h2>Skills Status</h2>"
    status += f"<p>News Fetcher: {'✅ Loaded' if news_fetcher else '❌ None'}</p>"
    status += f"<p>Content Processor: {'✅ Loaded' if content_processor else '❌ None'}</p>"

    # DEBUG: DB Info
    status += f"<h2>Database Debug</h2>"
    status += f"<p>URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}</p>"
    
    try:
        # Check latest 5 items
        latest_items = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(5).all()
        if latest_items:
            status += "<h3>Latest 5 Items:</h3>"
            for item in latest_items:
                status += f"<div style='border:1px solid #ccc; margin:5px; padding:5px;'>"
                from markupsafe import escape
                status += f"<b>Title:</b> {escape(item.title)}<br>"
                status += f"<b>ID:</b> {escape(item.id)}<br>"
                status += f"<b>Source:</b> '{escape(item.source)}'<br>"
                status += f"<b>Content Len:</b> {len(item.full_content) if item.full_content else 0}<br>"
                status += f"<b>Summary Len:</b> {len(item.summary) if item.summary else 0}<br>"
                status += f"<b>Show Details:</b> {item.show_details}<br>"
                status += f"</div>"
        else:
            status += "<p>No items found in DB.</p>"
    except Exception as e:
        status += f"<p>DB Read Error: {e}</p>"

    return status

# --- Routes ---

@app.route('/admin')
@login_required
def admin_dashboard():
    """The editor's control room: what is published, what needs attention, and shortcuts."""
    published = NewsItem.query.filter(NewsItem.is_published.isnot(False)).count()
    drafts = NewsItem.query.filter(NewsItem.is_published.is_(False)).count()
    total_views = db.session.query(db.func.coalesce(db.func.sum(NewsItem.views), 0)).scalar() or 0
    subscribers = Subscriber.query.filter_by(is_active=True).count()
    comments = Comment.query.count()
    campus = NewsItem.query.filter(NewsItem.wing == 'campus',
                                   NewsItem.is_published.isnot(False)).count()
    world = max(0, published - campus)

    rows = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(8).all()
    recent = []
    for row in rows:
        story = row.to_dict()
        assign_desk(story)
        recent.append(story)

    days = []
    today = datetime.datetime.utcnow().date()
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        start = datetime.datetime.combine(day, datetime.time.min)
        end = start + timedelta(days=1)
        count = NewsItem.query.filter(NewsItem.timestamp >= start,
                                      NewsItem.timestamp < end).count()
        days.append({'label': day.strftime('%a'), 'count': count, 'iso': day.isoformat()})
    peak = max([d['count'] for d in days] + [1])

    missing_images = NewsItem.query.filter(
        NewsItem.is_published.isnot(False),
        db.or_(NewsItem.image.is_(None), NewsItem.image == '')).count()
    missing_arabic = NewsItem.query.filter(
        NewsItem.is_published.isnot(False),
        db.or_(NewsItem.title_ar.is_(None), NewsItem.title_ar == '')).count()
    summary_only = NewsItem.query.filter(
        NewsItem.is_published.isnot(False),
        db.or_(NewsItem.full_content.is_(None), NewsItem.full_content == '')).count()
    last_story = recent[0] if recent else None
    stale = True
    if last_story and last_story.get('timestamp'):
        try:
            last_dt = datetime.datetime.fromisoformat(last_story['timestamp'])
            stale = (datetime.datetime.utcnow() - last_dt).days >= 7
        except Exception:
            stale = False

    attention = []
    if drafts:
        attention.append({'label': 'Drafts waiting to publish', 'count': drafts,
                          'href': url_for('dashboard'), 'level': 'warn'})
    if summary_only:
        attention.append({'label': 'Published without a full article', 'count': summary_only,
                          'href': url_for('dashboard'), 'level': 'warn'})
    if missing_images:
        attention.append({'label': 'Stories missing an image', 'count': missing_images,
                          'href': url_for('dashboard'), 'level': 'warn'})
    if missing_arabic:
        attention.append({'label': 'Stories missing an Arabic title', 'count': missing_arabic,
                          'href': url_for('dashboard'), 'level': 'bad'})
    if not subscribers:
        attention.append({'label': 'No newsletter subscribers yet', 'count': 0,
                          'href': url_for('qr_page'), 'level': 'warn'})
    if stale:
        attention.append({'label': 'No new story in the last 7 days', 'count': 0,
                          'href': url_for('add_news'), 'level': 'bad'})
    if not attention:
        attention.append({'label': 'Everything is up to date', 'count': 0,
                          'href': url_for('magazine_view'), 'level': 'ok'})

    settings = MagazineSettings.get_settings()
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    health = {
        'database': 'SQLite (local file)' if db_uri.startswith('sqlite') else 'PostgreSQL',
        'ai_key': bool(os.environ.get('OPENAI_API_KEY')),
        'search_key': bool(os.environ.get('GOOGLE_API_KEY') or os.environ.get('SEARCH_ENGINE_ID')),
        'theme': settings.theme if settings else 'light',
        'template': settings.magazine_template if settings else 'slate',
        'last_publish': (last_story.get('published_en') if last_story else ''),
    }

    return render_template('admin_dashboard.html',
                           published=published, drafts=drafts, total_views=total_views,
                           subscribers=subscribers, comments=comments, campus=campus, world=world,
                           recent=recent, days=days, peak=peak, attention=attention,
                           health=health, last_story=last_story,
                           today=datetime.datetime.now())


@app.route('/healthz')
def healthz():
    return 'ok', 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/')
@login_required
def newsroom():
    """The door between the two desks. Nothing from one desk is listed on the other."""
    campus_q = NewsItem.query.filter_by(wing='campus')
    world_q = NewsItem.query.filter(NewsItem.wing != 'campus')
    published = (NewsItem.query.filter_by(is_published=True)
                 .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc())
                 .all())
    campus_items = []
    wire = []
    for row in published:
        story = assign_desk(row.to_dict())
        if (story.get('wing') or 'world') == 'campus':
            campus_items.append(story)
        else:
            wire.append(story)
    label_campus(campus_items)
    paste_campus = [
        {**group, 'stories': group['stories'][:3], 'total': len(group['stories'])}
        for group in campus_groups(campus_items)
    ]
    slot_names = {'top': 'Cover', 'second': 'Latest', 'sidebar': 'Sidebar', 'ads': 'Notice'}
    cover = next((story for story in wire if story.get('category') == 'top'), None)
    if cover is None and wire:
        cover = wire[0]
    if cover:
        cover = {**cover, 'slot': slot_names.get(cover.get('category'), 'Cover')}
    rest = [story for story in wire if not cover or story['id'] != cover['id']]
    rest.sort(key=lambda story: {'second': 0, 'sidebar': 1, 'top': 2, 'ads': 3}.get(story.get('category'), 4))
    paste_world = []
    for story in rest[:5]:
        paste_world.append({**story, 'slot': slot_names.get(story.get('category'), 'World')})

    campus_drafts = campus_q.filter_by(is_published=False).count()
    world_drafts = world_q.filter(NewsItem.is_published.is_(False)).count()
    campus_recent = _v3_dedupe(sorted(campus_items, key=lambda s: s.get('timestamp') or '', reverse=True))[:3]
    world_recent = _v3_dedupe(sorted(wire, key=lambda s: s.get('timestamp') or '', reverse=True))[:3]
    week_cut = (datetime.datetime.utcnow() - timedelta(days=7)).isoformat()
    campus_week = sum(1 for s in campus_items if (s.get('timestamp') or '') >= week_cut)
    world_week = sum(1 for s in wire if (s.get('timestamp') or '') >= week_cut)
    slots = {'top': 0, 'second': 0, 'sidebar': 0, 'ads': 0}
    for story in wire:
        key = story.get('category') or 'sidebar'
        if key in slots:
            slots[key] += 1
    missing_images = sum(1 for s in campus_items + wire if not s.get('image'))
    missing_arabic = sum(1 for s in campus_items + wire if not (s.get('title_ar') or '').strip())
    attention = []
    if campus_drafts:
        attention.append({'label': 'Department drafts waiting', 'count': campus_drafts,
                          'href': url_for('department_admin'), 'level': 'warn'})
    if world_drafts:
        attention.append({'label': 'World drafts waiting', 'count': world_drafts,
                          'href': url_for('dashboard'), 'level': 'warn'})
    if missing_images:
        attention.append({'label': 'Published stories missing an image', 'count': missing_images,
                          'href': url_for('dashboard'), 'level': 'bad'})
    if missing_arabic:
        attention.append({'label': 'Published stories missing an Arabic title', 'count': missing_arabic,
                          'href': url_for('dashboard'), 'level': 'bad'})
    if not campus_items:
        attention.append({'label': 'The department has no published stories', 'count': 0,
                          'href': url_for('department_admin'), 'level': 'warn'})
    if not cover:
        attention.append({'label': 'No cover story chosen for the world desk', 'count': 0,
                          'href': url_for('dashboard'), 'level': 'warn'})

    return render_template(
        'newsroom.html',
        campus_live=campus_q.filter_by(is_published=True).count(),
        campus_hidden=campus_q.filter_by(is_published=False).count(),
        world_live=world_q.filter(NewsItem.is_published.is_(True)).count(),
        world_hidden=world_q.filter(NewsItem.is_published.is_(False)).count(),
        reel_count=CuratedReel.query.filter_by(status='published').count(),
        tool_count=AITool.query.filter_by(is_published=True).count(),
        paste_campus=paste_campus,
        paste_cover=cover,
        paste_world=paste_world,
        campus_drafts=campus_drafts,
        world_drafts=world_drafts,
        campus_recent=campus_recent,
        world_recent=world_recent,
        campus_week=campus_week,
        world_week=world_week,
        slots=slots,
        attention=attention,
        cover=cover,
    )


@app.route('/desk/world')
@login_required
def dashboard():
    """World desk only. Department topics never appear in these slots."""
    try:
        items_query = (NewsItem.query
                       .filter(NewsItem.is_published.is_(True), NewsItem.wing != 'campus')
                       .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc())
                       .all())
        
        # Group items by category
        grouped_items = {
            'top': [],
            'second': [],
            'sidebar': [],
            'ads': []
        }
        
        for item in items_query:
            # Default to sidebar if category is missing or invalid
            cat = item.category if item.category in grouped_items else 'sidebar'
            grouped_items[cat].append(item.to_dict())
        
        # Count total ACTIVE items for display
        total_items = len(items_query)
        hidden_count = NewsItem.query.filter(NewsItem.is_published.is_(False), NewsItem.wing != 'campus').count()
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        return render_template('index.html',
                               grouped_items=grouped_items,
                               total=total_items,
                               hidden_count=hidden_count,
                               date=today)
    except Exception as e:
        print(f"DASHBOARD ERROR: {e}")
        traceback.print_exc()
        return f"Dashboard Error: {e}", 500

@app.route('/api/reorder_news', methods=['POST'])
@login_required
def reorder_news():
    try:
        data = request.json
        ordered_ids = data.get('ordered_ids', [])
        
        # Update order for each item
        for index, item_id in enumerate(ordered_ids):
            item = NewsItem.query.get(item_id)
            if item:
                item.display_order = index
        
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"REORDER ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/update_category', methods=['POST'])
@login_required
def update_category():
    try:
        data = request.json
        item_id = data.get('item_id')
        new_category = data.get('new_category')
        
        item = NewsItem.query.get(item_id)
        if item and (item.wing or '') == 'campus':
            return jsonify({"status": "error", "message": "Department topics stay on the department desk."}), 400
        if item:
            item.category = new_category
            db.session.commit()
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Item not found"}), 404
    except Exception as e:
        print(f"UPDATE CAT ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Protected Routes ---

@app.errorhandler(500)
def internal_error(error):
    return f"500 Error: {error}", 500


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'message': 'Not found'}), 404
    return render_template('not_found.html'), 404


@app.route('/robots.txt')
def robots_txt():
    from flask import Response
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /desk/",
        "Disallow: /settings",
        "Disallow: /subscribers",
        "Disallow: /search",
        "Disallow: /archive",
        "Disallow: /login",
        "",
        "Sitemap: %ssitemap.xml" % request.url_root.rstrip('/'),
    ]
    return Response("\n".join(lines) + "\n", mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    from flask import Response
    rows = NewsItem.query.filter(NewsItem.is_published.isnot(False)) \
        .order_by(NewsItem.timestamp.desc()).limit(2000).all()
    entries = ["<url><loc>%s</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"
               % url_for('magazine_view', _external=True)]
    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>"
                   % url_for('tools_directory', _external=True))
    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
                   % url_for('tools_ranked', _external=True))
    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
                   % url_for('models_directory', _external=True))
    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
                   % url_for('campus_projects', _external=True))
    for tool in AITool.query.filter_by(is_published=True).all():
        entries.append("<url><loc>%s</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>"
                       % url_for('tool_detail', tool_id=tool.id, _external=True))
    for row in rows:
        lastmod = row.timestamp.strftime('%Y-%m-%d') if row.timestamp else ''
        entries.append(
            "<url><loc>%s</loc>%s<changefreq>monthly</changefreq><priority>0.8</priority></url>"
            % (url_for('magazine_detail', item_id=row.id, _external=True),
               ("<lastmod>%s</lastmod>" % lastmod) if lastmod else "")
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + "".join(entries) + '</urlset>')
    return Response(xml, mimetype='application/xml')

@app.route('/search', methods=['GET'])
@login_required
def search_page():
    # Get parameters from URL (GET) for shareable searches
    query = request.args.get('q', '')
    mode = request.args.get('mode', 'live') if request.args.get('q') else 'archive' # Default to archive if no query, else live? Or explicit param?
    # User UI implies distinct forms. Live form -> /search_live? Archive form -> /search?
    # Let's align with the user's template actions. 
    # User template: 
    # Archive Form: action="/search" method="get"
    # Live Form: action="/search_live" method="get"
    # So I should split them or handle logic here if they map to same.
    # Actually, let's keep it simple and follow the user's template implied routes.
    # Determine Mode
    mode = request.args.get('mode', 'archive')
    
    # Common Results Container
    results = []
    
    if mode == 'live':
        # --- LIVE SEARCH LOGIC ---
        engine = request.args.get('engine', 'google')
        time_filter = request.args.get('t', 'week')
        content_type = request.args.get('type', 'mixed')
        
        search_warnings = []
        if query:
            try:
                results = news_fetcher.fetch_news(query, time_filter=time_filter, content_type=content_type,
                                                    warnings=search_warnings)
            except Exception as e:
                search_warnings.append(f"Live search crashed: {e}")

            # Surface *why* a source came back empty instead of failing silently —
            # even on a partial success (e.g. DDG worked but Google/YouTube didn't),
            # so it's obvious which sources need attention.
            if search_warnings:
                severity = "error" if not results else "warning"
                for w in search_warnings:
                    flash(w, severity)
            if not results and not search_warnings:
                flash("No results found for that search. Try a broader query or a wider time range.", "error")

        saved_ids = {}
        urls = [row.get('url') for row in results if isinstance(row, dict) and row.get('url')]
        if urls:
            for saved in NewsItem.query.filter(NewsItem.url.in_(urls)).all():
                saved_ids[saved.url] = saved.id

        # AJAX Partial Rendering for Live Search
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return render_template('components/search_results.html', results=results, query=query, is_live=True,
                                     search_warnings=search_warnings, saved_ids=saved_ids)

        # Render Full Page in Live Mode
        return render_template('search.html', results=results, query=query, is_live=True, mode='live',
                             engine=engine, time_filter=time_filter, content_type=content_type,
                             search_warnings=search_warnings, saved_ids=saved_ids)
                             
    else:
        # --- ARCHIVE SEARCH LOGIC (Default) ---
        time_filter = request.args.get('time', 'all')
        lang_filter = request.args.get('lang', 'all')
        
        query_obj = NewsItem.query.filter(NewsItem.wing != 'campus').order_by(NewsItem.timestamp.desc())

        # 1. Keyword Search
        if query:
            search_pattern = f'%{query}%'
            query_obj = query_obj.filter(
                (NewsItem.title.ilike(search_pattern)) | 
                (NewsItem.summary.ilike(search_pattern)) |
                (NewsItem.title_ar.ilike(search_pattern)) |
                (NewsItem.summary_ar.ilike(search_pattern))
            )
        
        # 2. Language Filter
        if lang_filter == 'ar':
            # Must have Arabic title to be considered "Arabic" content relevant
            query_obj = query_obj.filter(NewsItem.title_ar != None)
        
        # 3. Time Filter (Archive Specific)
        if time_filter and time_filter != 'all':
            now = datetime.datetime.now()
            start_date = None
            if time_filter == 'today': start_date = now - timedelta(days=1)
            elif time_filter == 'week': start_date = now - timedelta(weeks=1)
            elif time_filter == 'month': start_date = now - timedelta(days=30)
            elif time_filter == 'year': start_date = now - timedelta(days=365)
                
            if start_date:
                query_obj = query_obj.filter(NewsItem.timestamp >= start_date)
            
        items = query_obj.limit(50).all()
        results = [item.to_dict() for item in items]
        
        return render_template('search.html', results=results, query=query, is_live=False, mode='archive',
                             time_filter=time_filter, lang=lang_filter)

@app.route('/api/youtube/preview', methods=['POST'])
@login_required
def youtube_preview():
    """Fill the manual form from a YouTube link: title, channel, cover, description."""
    data = request.get_json(silent=True) or request.form
    url = (data.get('url') or '').strip()
    details = fetch_youtube_details(url)
    if not details or not details.get('title'):
        return jsonify({
            'status': 'error',
            'message': 'Paste a YouTube link. If the video is private, type the title yourself.',
        }), 400
    return jsonify({'status': 'success', **details})


@app.route('/add_manual_news', methods=['POST'])
@login_required
def add_manual_news():
    try:
        url = (request.form.get('url') or '').strip()
        title = (request.form.get('title') or '').strip()
        source = (request.form.get('source') or '').strip()
        summary_en = (request.form.get('summary_en') or '').strip()
        summary_ar = (request.form.get('summary_ar') or '').strip()
        image_url = (request.form.get('image_url') or '').strip()
        image_file = request.files.get('image_file')
        video_id, is_video = detect_youtube(url)

        if is_video:
            details = fetch_youtube_details(url) or {}
            title = title or details.get('title') or ''
            source = source or details.get('source') or 'YouTube'
            summary_en = summary_en or details.get('summary') or ''
            image_url = image_url or details.get('image') or ''
            video_id = details.get('video_id') or video_id
        if not title:
            message = 'Paste a YouTube link, or type a title for an article.'
            if is_video:
                message = 'Could not read that video. Check the link or type a title.'
            return jsonify({'status': 'error', 'message': message}), 400

        if image_file and image_file.filename:
            filename = f"manual_{uuid.uuid4().hex}_{secure_filename(image_file.filename)}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image_file.save(save_path)
            image_url = url_for('static', filename=f'uploads/images/{filename}')

        if url:
            existing = NewsItem.query.filter(NewsItem.url == url).first()
            if existing:
                return jsonify({
                    'status': 'success',
                    'already': True,
                    'message': 'Already in the magazine.',
                    'id': existing.id,
                    'edit_url': url_for('edit_news', item_id=existing.id),
                })

        full_en = process_content_images(_editor_html(request.form.get('full_content')))
        full_ar = process_content_images(_editor_html(request.form.get('full_content_ar')))
        title, title_ar, summary_en, summary_ar, full_en, full_ar = ensure_bilingual_content(
            title_en=title,
            summary_en=summary_en,
            full_content_html=full_en or None,
            summary_ar=summary_ar or None,
            full_content_ar=full_ar or None,
        )

        item = NewsItem(
            id=str(uuid.uuid4()),
            title=(title or '')[:490],
            title_ar=(title_ar or '')[:490],
            url=url or f"manual-{uuid.uuid4().hex}",
            source=(source or 'Manual Entry')[:190],
            summary=summary_en,
            summary_ar=summary_ar,
            full_content=full_en or None,
            full_content_ar=full_ar or None,
            image=image_url or '',
            article_type='external' if url else 'manual',
            content_format='video' if is_video else 'article',
            video_id=video_id if is_video else None,
            category='sidebar',
            is_published=True,
            show_details=bool(full_en or full_ar),
            headline_display_mode=request.form.get('headline_display_mode', 'default'),
        )

        db.session.add(item)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Saved.',
            'title': item.title,
            'id': item.id,
            'edit_url': url_for('edit_news', item_id=item.id),
        })

    except Exception as e:
        db.session.rollback()
        print(f"Manual Entry Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    try:
        data = request.get_json()
        print(f"Removing item with URL: {data.get('url')}")
        item = NewsItem.query.filter_by(url=data.get('url')).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/enrich_image')
@login_required
def enrich_image():
    url = request.args.get('url')
    if not url:
        return jsonify({'image': None})
        
    try:
        from agent.skills.news_fetcher.meta_extractor import extract_meta_image
        img_url = extract_meta_image(url)
        return jsonify({'image': img_url})
    except ImportError:
        print("Meta Extractor not found")
        return jsonify({'image': None})
    except Exception as e:
        print(f"Enrich Error: {e}")
        return jsonify({'image': None})

# --- "Ask the Magazine" — AI reader companion, grounded only in curated articles ---

_ask_attempts = defaultdict(list)  # ip -> [timestamps] — public unauthenticated AI endpoint, needs abuse protection
ASK_MAX_PER_HOUR = 20
ASK_WINDOW_SECONDS = 60 * 60

def _ask_rate_limited(ip):
    now = time.time()
    recent = [t for t in _ask_attempts[ip] if now - t < ASK_WINDOW_SECONDS]
    _ask_attempts[ip] = recent
    return len(recent) >= ASK_MAX_PER_HOUR

@app.route('/api/ask', methods=['POST'])
def ask_the_magazine():
    ip = request.remote_addr or 'unknown'
    if _ask_rate_limited(ip):
        return jsonify({'status': 'error',
                        'message': 'Too many questions for now — try again in a bit.'}), 429

    data = request.json or {}
    question = (data.get('question') or '').strip()
    lang = data.get('lang') if data.get('lang') in ('en', 'ar') else 'en'

    if not question:
        return jsonify({'status': 'error', 'message': 'Ask me something first!'}), 400
    if len(question) > 500:
        return jsonify({'status': 'error', 'message': 'That question is a bit long — try to keep it shorter.'}), 400

    if not content_processor or not hasattr(content_processor, 'answer_reader_question'):
        return jsonify({'status': 'error', 'message': 'The magazine assistant is not available right now.'}), 500

    _ask_attempts[ip].append(time.time())

    settings = MagazineSettings.get_settings()
    items = NewsItem.query.filter_by(is_published=True).order_by(NewsItem.timestamp.desc()).limit(60).all()
    articles = [{
        'id': idx,
        'title': (i.title_ar or i.title) if lang == 'ar' else i.title,
        'summary': (i.summary_ar or i.summary) if lang == 'ar' else i.summary,
        'url': url_for('magazine_detail', item_id=i.id, _external=False),
    } for idx, i in enumerate(items)]

    if not articles:
        msg = "لا توجد قصص في المجلة بعد لأجيب عن سؤالك." if lang == 'ar' else "There's nothing published in the magazine yet for me to draw from."
        return jsonify({'status': 'success', 'answer': msg, 'sources': []})

    result = content_processor.answer_reader_question(question, lang, articles, settings.magazine_title)
    if result is None:
        return jsonify({'status': 'error',
                        'message': 'The magazine assistant needs a working OpenAI key — ask the editor to add one in Settings → API Keys.'}), 500

    sources = [{'title': articles[i]['title'], 'url': articles[i]['url']}
               for i in result['used_ids'] if 0 <= i < len(articles)]

    return jsonify({'status': 'success', 'answer': result['answer'], 'sources': sources})

@app.route('/authorinfo')
def author_info():
    settings = MagazineSettings.get_settings()
    template = 'author_info.html' if request.args.get('classic') else 'about_v3.html'
    return render_template(template, settings=settings)

@app.route('/watch')
def watch_page():
    """Public 'worth watching' page — curated pointers to external short videos.
    Never hosts the videos themselves; every card links out to the original post."""
    lang_pref = get_lang_pref()
    if lang_pref is None:
        return _render_language_gate()

    settings = MagazineSettings.get_settings()
    reels = CuratedReel.query.filter_by(status='published') \
        .order_by(CuratedReel.display_order.asc(), CuratedReel.created_at.desc()).all()
    return render_template('watch.html', settings=settings, reels=[r.to_dict() for r in reels],
                            date=datetime.datetime.now().strftime("%Y-%m-%d"))

# --- Newsletter Subscription ---

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def _wants_json():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
           request.accept_mimetypes.best == 'application/json'

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Public newsletter sign-up. This is the page the door QR code should point to."""
    settings = MagazineSettings.get_settings()

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        name = (request.form.get('name') or '').strip()[:100]
        lang = request.form.get('language_pref', 'both')
        if lang not in LANG_CHOICES:
            lang = 'both'
        source = (request.form.get('source') or 'web').strip()[:30] or 'web'

        if _public_rate_limited('subscribe', 10, 60 * 60):
            msg, ok = "Too many sign-up attempts. Please try again later.", False
        elif not email or len(email) > 254 or not EMAIL_RE.match(email):
            msg, ok = "Please enter a valid email address.", False
        else:
            try:
                existing = Subscriber.query.filter_by(email=email).first()
                if existing:
                    if not existing.is_active:
                        existing.is_active = True
                        db.session.commit()
                    msg, ok = "You're already on the list — welcome back!", True
                else:
                    sub = Subscriber(email=email, name=name or None, language_pref=lang, source=source)
                    db.session.add(sub)
                    db.session.commit()
                    msg, ok = "Subscribed! You'll get the next AI briefing in your inbox.", True
            except Exception as e:
                db.session.rollback()
                print(f"Subscribe Error: {e}")
                msg, ok = "Something went wrong. Please try again.", False

        if _wants_json():
            return jsonify({'status': 'success' if ok else 'error', 'message': msg})

        if ok:
            # The page itself confirms the sign-up; no duplicate flash message.
            return redirect(url_for('subscribe', subscribed=1))
        flash(msg, "error")
        return redirect(url_for('subscribe', source=source))

    template = 'subscribe.html' if request.args.get('classic') else 'subscribe_v3.html'
    return render_template(template, settings=settings,
                           subscribed=request.args.get('subscribed'),
                           unsubscribed=False,
                           source_hint=request.args.get('source', 'web'))

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    settings = MagazineSettings.get_settings()
    sub = Subscriber.query.filter_by(unsubscribe_token=token).first()
    if sub and sub.is_active:
        sub.is_active = False
        db.session.commit()
    template = 'subscribe.html' if request.args.get('classic') else 'subscribe_v3.html'
    return render_template(template, settings=settings, unsubscribed=True,
                           subscribed=False, source_hint='email')

@app.route('/subscribers')
@login_required
def subscribers_page():
    """Admin view of the mailing list, with counts and CSV export."""
    subs = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
    active_subs = [s for s in subs if s.is_active]
    since_24h = sum(1 for s in active_subs if s.created_at and s.created_at >= datetime.datetime.utcnow() - timedelta(days=1))
    since_7d = sum(1 for s in active_subs if s.created_at and s.created_at >= datetime.datetime.utcnow() - timedelta(days=7))
    return render_template('subscribers.html', subscribers=subs, total=len(active_subs),
                            since_24h=since_24h, since_7d=since_7d)

@app.route('/subscribers/export.csv')
@login_required
def export_subscribers_csv():
    subs = Subscriber.query.filter_by(is_active=True).order_by(Subscriber.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['email', 'name', 'language_pref', 'source', 'subscribed_at'])
    for s in subs:
        writer.writerow([s.email, s.name or '', s.language_pref, s.source,
                          s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else ''])
    output = buf.getvalue()
    from flask import Response
    return Response(output, mimetype='text/csv',
                     headers={'Content-Disposition': 'attachment; filename=nasser_ai_news_subscribers.csv'})

@app.route('/subscribers/delete/<int:sub_id>', methods=['POST'])
@login_required
def delete_subscriber(sub_id):
    sub = Subscriber.query.get(sub_id)
    if sub:
        db.session.delete(sub)
        db.session.commit()
        flash("Subscriber removed.", "success")
    return redirect(url_for('subscribers_page'))

# --- Newsletter Digest (AI-written intro + this issue's stories, emailed to subscribers) ---

def _make_absolute(path):
    """Email clients fetch images/links from an external server, so relative
    /static/... paths need to become full URLs."""
    if not path:
        return None
    if path.startswith('http://') or path.startswith('https://'):
        return path
    return request.url_root.rstrip('/') + path

def _get_digest_articles(limit=6):
    items = NewsItem.query.filter_by(is_published=True).order_by(NewsItem.timestamp.desc()).limit(limit).all()
    articles = []
    for i in items:
        articles.append({
            'title': i.title,
            'title_ar': i.title_ar,
            'summary': i.summary,
            'summary_ar': i.summary_ar,
            'url': url_for('magazine_detail', item_id=i.id, _external=True),
            'image': _make_absolute(i.image),
        })
    return articles

def _build_digest_email(lang, settings, raw_articles, unsubscribe_token='preview'):
    """Renders the digest email HTML for one language ('en' or 'ar')."""
    articles = [{
        'title': (a['title_ar'] or a['title']) if lang == 'ar' else a['title'],
        'summary': (a['summary_ar'] or a['summary'] or '') if lang == 'ar' else (a['summary'] or ''),
        'url': a['url'],
        'image': a['image'],
    } for a in raw_articles]

    intro_text = ""
    if content_processor and hasattr(content_processor, 'draft_newsletter_intro'):
        intro_text = content_processor.draft_newsletter_intro(raw_articles, lang) or ""

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    subject = f"{settings.magazine_title} — {'نشرة الذكاء الاصطناعي الأسبوعية' if lang == 'ar' else 'Weekly AI Briefing'} ({date_str})"

    html = render_template('emails/digest.html',
                           lang=lang, subject=subject, settings=settings, date=date_str,
                           intro_text=intro_text, articles=articles,
                           logo_url=_make_absolute(settings.logo_path),
                           magazine_url=url_for('magazine_view', _external=True),
                           unsubscribe_url=url_for('unsubscribe', token=unsubscribe_token, _external=True))
    return subject, html

@app.route('/subscribers/digest')
@login_required
def digest_preview():
    settings = MagazineSettings.get_settings()
    raw_articles = _get_digest_articles()

    if not raw_articles:
        flash("No published stories to send yet — publish something first.", "error")
        return redirect(url_for('subscribers_page'))

    _, preview_en = _build_digest_email('en', settings, raw_articles)
    _, preview_ar = _build_digest_email('ar', settings, raw_articles)

    counts = {
        'en': Subscriber.query.filter_by(is_active=True, language_pref='en').count(),
        'ar': Subscriber.query.filter_by(is_active=True, language_pref='ar').count(),
        'both': Subscriber.query.filter_by(is_active=True, language_pref='both').count(),
    }
    counts['total'] = counts['en'] + counts['ar'] + counts['both']

    smtp_ready = bool(newsletter_mailer and newsletter_mailer.is_smtp_configured())

    return render_template('digest_preview.html', preview_en=preview_en, preview_ar=preview_ar,
                           counts=counts, smtp_ready=smtp_ready, article_count=len(raw_articles))

@app.route('/subscribers/digest/send', methods=['POST'])
@login_required
def digest_send():
    if not newsletter_mailer or not newsletter_mailer.is_smtp_configured():
        flash("Email isn't configured yet — add your SMTP details in Settings → API Keys first.", "error")
        return redirect(url_for('digest_preview'))

    settings = MagazineSettings.get_settings()
    raw_articles = _get_digest_articles()
    if not raw_articles:
        flash("No published stories to send yet.", "error")
        return redirect(url_for('subscribers_page'))

    # One rendered email per language, reused across every subscriber in that group
    # (only the unsubscribe link is personalized, patched in per-recipient below).
    subject_en, html_en = _build_digest_email('en', settings, raw_articles)
    subject_ar, html_ar = _build_digest_email('ar', settings, raw_articles)
    # "both" subscribers get the English version followed by the Arabic version in one email.
    subject_both = subject_en
    html_both = html_en + '<div style="height:2px;background:#334155;"></div>' + html_ar

    subscribers = Subscriber.query.filter_by(is_active=True).all()
    sent, failed = 0, []

    for sub in subscribers:
        if sub.language_pref == 'ar':
            subject, html = subject_ar, html_ar
        elif sub.language_pref == 'both':
            subject, html = subject_both, html_both
        else:
            subject, html = subject_en, html_en

        # Patch in this subscriber's own unsubscribe link.
        personal_unsub = url_for('unsubscribe', token=sub.unsubscribe_token, _external=True)
        html = html.replace(url_for('unsubscribe', token='preview', _external=True), personal_unsub)

        ok, err = newsletter_mailer.send_email(sub.email, subject, html)
        if ok:
            sent += 1
        else:
            failed.append((sub.email, err))

    if sent:
        flash(f"Digest sent to {sent} subscriber{'s' if sent != 1 else ''}.", "success")
    if failed:
        flash(f"{len(failed)} failed to send — first error: {failed[0][1]}", "error")
    if not sent and not failed:
        flash("No active subscribers to send to yet.", "warning")

    return redirect(url_for('subscribers_page'))

# --- Curated Reels (external short-video pointers — see CuratedReel model) ---

REEL_STATUSES = {'draft', 'published', 'archived'}

@app.route('/reels')
@login_required
def reels_list():
    """
    The working list — Published + Draft only. Archived reels are tucked away
    on their own page (see reels_archive()) organized by year/month, so this
    view stays focused on what's live or still being prepped.
    """
    status_filter = request.args.get('status', 'all')
    if status_filter == 'archived':
        return redirect(url_for('reels_archive'))
    sort_mode = request.args.get('sort', 'manual')

    query = CuratedReel.query.filter(CuratedReel.status != 'archived')
    if status_filter in ('published', 'draft'):
        query = query.filter_by(status=status_filter)

    if sort_mode == 'date':
        reels = query.order_by(CuratedReel.created_at.desc()).all()
    else:
        reels = query.order_by(CuratedReel.display_order.asc(), CuratedReel.created_at.desc()).all()

    counts = {
        'all': CuratedReel.query.filter(CuratedReel.status != 'archived').count(),
        'draft': CuratedReel.query.filter_by(status='draft').count(),
        'published': CuratedReel.query.filter_by(status='published').count(),
        'archived': CuratedReel.query.filter_by(status='archived').count(),
    }

    return render_template('reels_list.html', reels=reels, status_filter=status_filter,
                           sort_mode=sort_mode, counts=counts)

@app.route('/reels/archive')
@login_required
def reels_archive():
    """Archived reels only, grouped by year -> month -> date, newest first."""
    archived = CuratedReel.query.filter_by(status='archived').order_by(CuratedReel.created_at.desc()).all()

    archive_tree = defaultdict(lambda: defaultdict(list))
    for reel in archived:
        if reel.created_at:
            archive_tree[reel.created_at.year][reel.created_at.month].append(reel)

    archive_data = []
    for year in sorted(archive_tree.keys(), reverse=True):
        months_data = []
        year_total = 0
        for month_num in sorted(archive_tree[year].keys(), reverse=True):
            posts = sorted(archive_tree[year][month_num], key=lambda r: r.created_at, reverse=True)
            year_total += len(posts)
            months_data.append({
                'name': calendar.month_name[month_num],
                'posts': [p.to_dict() for p in posts],
                'count': len(posts)
            })
        archive_data.append({'year': year, 'months': months_data, 'count': year_total})

    return render_template('reels_archive.html', archive_data=archive_data, total=len(archived))

@app.route('/reels/add', methods=['GET', 'POST'])
@login_required
def add_reel():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            source_url = request.form.get('source_url')
            if not title or not source_url:
                flash("Title and source link are required.", "error")
                return redirect(request.url)

            thumbnail_path = ""
            file = request.files.get('thumbnail')
            if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
                filename = secure_filename(f"reel_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                thumbnail_path = f"/static/uploads/images/{filename}"
            else:
                fetched = (request.form.get('fetched_thumbnail') or '').strip()
                if fetched.startswith('/static/uploads/images/'):
                    thumbnail_path = fetched

            max_order = db.session.query(db.func.max(CuratedReel.display_order)).scalar() or 0
            status = request.form.get('status', 'published')
            if status not in REEL_STATUSES:
                status = 'published'

            reel = CuratedReel(
                title=title,
                title_ar=request.form.get('title_ar'),
                creator_name=request.form.get('creator_name'),
                creator_handle=request.form.get('creator_handle'),
                platform=request.form.get('platform', 'instagram'),
                source_url=source_url,
                thumbnail=thumbnail_path,
                summary_en=request.form.get('summary_en'),
                summary_ar=request.form.get('summary_ar'),
                display_order=max_order + 1,
                status=status,
                is_published=(status == 'published'),
            )
            db.session.add(reel)
            db.session.commit()
            flash("Reel added.", "success")
            return redirect(url_for('reels_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding reel: {e}", "error")
            return redirect(request.url)

    return render_template('reel_form.html', mode='add')

@app.route('/reels/edit/<int:reel_id>', methods=['GET', 'POST'])
@login_required
def edit_reel(reel_id):
    reel = CuratedReel.query.get_or_404(reel_id)
    if request.method == 'POST':
        try:
            reel.title = request.form.get('title')
            reel.title_ar = request.form.get('title_ar')
            reel.creator_name = request.form.get('creator_name')
            reel.creator_handle = request.form.get('creator_handle')
            reel.platform = request.form.get('platform', 'instagram')
            reel.source_url = request.form.get('source_url')
            reel.summary_en = request.form.get('summary_en')
            reel.summary_ar = request.form.get('summary_ar')

            status = request.form.get('status', reel.status or 'published')
            if status in REEL_STATUSES:
                reel.status = status
                reel.is_published = (status == 'published')

            file = request.files.get('thumbnail')
            if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
                filename = secure_filename(f"reel_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                reel.thumbnail = f"/static/uploads/images/{filename}"
            else:
                fetched = (request.form.get('fetched_thumbnail') or '').strip()
                if fetched.startswith('/static/uploads/images/'):
                    reel.thumbnail = fetched

            db.session.commit()
            flash("Reel updated.", "success")
            return redirect(url_for('reels_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Update failed: {e}", "error")

    return render_template('reel_form.html', mode='edit', item=reel.to_dict())

@app.route('/reels/delete/<int:reel_id>', methods=['POST'])
@login_required
def delete_reel(reel_id):
    reel = CuratedReel.query.get(reel_id)
    if reel:
        db.session.delete(reel)
        db.session.commit()
        flash("Reel removed.", "success")
    return redirect(url_for('reels_list'))

@app.route('/api/reels/reorder', methods=['POST'])
@login_required
def reorder_reels():
    try:
        data = request.json
        ordered_ids = data.get('ordered_ids', [])
        for index, reel_id in enumerate(ordered_ids):
            reel = CuratedReel.query.get(int(reel_id))
            if reel:
                reel.display_order = index
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reels/set_status/<int:reel_id>', methods=['POST'])
@login_required
def set_reel_status(reel_id):
    reel = CuratedReel.query.get(reel_id)
    if not reel:
        return jsonify({'status': 'error', 'message': 'Not found'}), 404

    new_status = (request.json or {}).get('status')
    if new_status not in REEL_STATUSES:
        return jsonify({'status': 'error', 'message': 'Invalid status.'}), 400

    reel.status = new_status
    reel.is_published = (new_status == 'published')
    db.session.commit()
    return jsonify({'status': 'success', 'new_status': reel.status})

_THUMB_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def _is_safe_public_url(url):
    """Basic SSRF guard: only plain http(s) links to a publicly-routable host."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            return False
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
        return True
    except Exception:
        return False

@app.route('/api/reels/fetch_thumbnail', methods=['POST'])
@login_required
def fetch_reel_thumbnail():
    """
    Finds a preview image and downloads a local copy. Social CDNs sign these
    image URLs with short-lived tokens, so we re-host locally instead of
    hotlinking. Two modes:
    - source_url: detect a preview from the reel's link (YouTube's public
      thumbnail endpoint, TikTok's oEmbed endpoint, or the page's
      og:image/twitter:image meta tag).
    - direct_image_url: skip detection entirely and just download this exact
      image URL — the fallback for links (Instagram, etc.) auto-detection
      can't reach.
    """
    data = request.json or {}
    source_url = (data.get('source_url') or '').strip()
    direct_image_url = (data.get('direct_image_url') or '').strip()

    try:
        if direct_image_url:
            if not _is_safe_public_url(direct_image_url):
                return jsonify({'status': 'error', 'message': 'Enter a valid, publicly-reachable image link.'}), 400
            image_url = direct_image_url
        else:
            if not source_url or not _is_safe_public_url(source_url):
                return jsonify({'status': 'error', 'message': 'Enter a valid, publicly-reachable link first.'}), 400

            image_url = None

            if 'tiktok.com' in source_url:
                r = requests.get('https://www.tiktok.com/oembed', params={'url': source_url},
                                  headers=_THUMB_HEADERS, timeout=8)
                if r.ok:
                    image_url = r.json().get('thumbnail_url')
            elif 'youtube.com' in source_url or 'youtu.be' in source_url:
                m = re.search(r'(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})', source_url)
                if m:
                    image_url = f"https://img.youtube.com/vi/{m.group(1)}/hqdefault.jpg"

            if not image_url:
                from agent.skills.news_fetcher.meta_extractor import extract_meta_image
                image_url = extract_meta_image(source_url)

            if not image_url or not _is_safe_public_url(image_url):
                return jsonify({'status': 'error',
                                 'message': 'Could not find a preview image at that link. Paste a direct image link or upload one instead.'}), 404

        img_resp = requests.get(image_url, headers=_THUMB_HEADERS, timeout=8, stream=True)
        img_resp.raise_for_status()

        content_type = img_resp.headers.get('Content-Type', '').split(';')[0].strip().lower()
        ext = {'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}.get(content_type)
        if not ext:
            return jsonify({'status': 'error', 'message': 'That link did not return a usable image.'}), 400

        max_bytes = 8 * 1024 * 1024
        buf = bytearray()
        for chunk in img_resp.iter_content(8192):
            buf.extend(chunk)
            if len(buf) > max_bytes:
                return jsonify({'status': 'error', 'message': 'Preview image was too large.'}), 400

        filename = secure_filename(f"reel_fetch_{uuid.uuid4().hex}.{ext}")
        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename), 'wb') as f:
            f.write(buf)

        return jsonify({'status': 'success', 'thumbnail_url': f"/static/uploads/images/{filename}"})
    except requests.RequestException:
        return jsonify({'status': 'error', 'message': 'Could not reach that link.'}), 502
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reels/draft_summary', methods=['POST'])
@login_required
def draft_reel_summary_api():
    """
    AI-assist for the Add/Edit Reel form: paste in a transcript/caption as
    private reference notes, get back an ORIGINAL summary — never the notes
    themselves, never a close paraphrase. The notes are not saved anywhere.
    """
    try:
        data = request.json or {}
        title = data.get('title', '')
        notes = data.get('reference_notes', '')
        creator = data.get('creator_name', '')

        if not content_processor or not hasattr(content_processor, 'draft_reel_summary'):
            return jsonify({'status': 'error', 'message': 'AI assistant not available.'}), 500

        result = content_processor.draft_reel_summary(title, notes, creator)
        if not result.get('summary_en') and not result.get('summary_ar'):
            return jsonify({'status': 'error', 'message': 'Could not draft a summary — check your OpenAI API key.'}), 500

        return jsonify({'status': 'success', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reels/translate_title', methods=['POST'])
@login_required
def translate_reel_title():
    """Live EN<->AR title auto-fill for the Add/Edit Reel form."""
    try:
        data = request.json or {}
        text = (data.get('text') or '').strip()
        target = data.get('target')

        if not text:
            return jsonify({'status': 'error', 'message': 'No text provided.'}), 400
        if target not in ('ar', 'en'):
            return jsonify({'status': 'error', 'message': 'Invalid target language.'}), 400
        if not content_processor or not hasattr(content_processor, 'translate_title'):
            return jsonify({'status': 'error', 'message': 'Translator not available.'}), 500

        translated = content_processor.translate_title(text, target)
        if not translated:
            return jsonify({'status': 'error',
                             'message': 'Translation needs a working OpenAI key — add one in Settings → API Keys.'}), 500

        return jsonify({'status': 'success', 'translated': translated})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/settings/translate_html', methods=['POST'])
@login_required
def translate_settings_html():
    """Live EN<->AR translation for rich-text fields (e.g. the Author Profile's
    Detailed Introduction) — preserves HTML formatting/tags."""
    try:
        data = request.json or {}
        html_content = data.get('html') or ''
        target = data.get('target')

        if not html_content.strip():
            return jsonify({'status': 'error', 'message': 'Nothing to translate yet.'}), 400
        if target not in ('ar', 'en'):
            return jsonify({'status': 'error', 'message': 'Invalid target language.'}), 400
        if not content_processor or not hasattr(content_processor, 'translate_html'):
            return jsonify({'status': 'error', 'message': 'Translator not available.'}), 500

        translated = content_processor.translate_html(html_content, target)
        if translated is None:
            return jsonify({'status': 'error',
                             'message': 'Translation needs a working OpenAI key — add one in Settings → API Keys.'}), 500

        return jsonify({'status': 'success', 'translated': translated})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- AI Tools & Platforms Directory ---

@app.route('/tools')
@login_required
def tools_list():
    category = request.args.get('category', 'all')
    q = (request.args.get('q') or '').strip()
    query = AITool.query
    if category != 'all':
        query = query.filter_by(category=category)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(AITool.name.ilike(like), AITool.name_ar.ilike(like),
                                    AITool.tagline_en.ilike(like), AITool.best_for.ilike(like)))
    tools = query.order_by(AITool.featured.desc(), AITool.sort_order.asc(), AITool.name.asc()).all()

    counts = {'all': AITool.query.count()}
    for key, _ in TOOL_CATEGORIES:
        counts[key] = AITool.query.filter_by(category=key).count()
    stats = {
        'free': AITool.query.filter(AITool.free_tier.is_(True)).count(),
        'arabic': AITool.query.filter(AITool.arabic_support.is_(True)).count(),
        'featured': AITool.query.filter(AITool.featured.is_(True)).count(),
    }

    return render_template('tools_list.html', tools=[t.to_dict() for t in tools], category=category,
                           categories=TOOL_CATEGORIES, counts=counts, q=q, stats=stats)

@app.route('/tools/add', methods=['GET', 'POST'])
@login_required
def add_tool():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            if not name:
                flash("Name is required.", "error")
                return redirect(request.url)

            logo_path = ""
            file = request.files.get('logo')
            if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
                filename = secure_filename(f"tool_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                logo_path = f"/static/uploads/images/{filename}"
            else:
                fetched = (request.form.get('fetched_logo') or '').strip()
                if fetched.startswith('/static/uploads/images/'):
                    logo_path = fetched

            tool = AITool(
                name=name,
                name_ar=request.form.get('name_ar'),
                category=request.form.get('category', 'other'),
                tagline_en=request.form.get('tagline_en', ''),
                tagline_ar=request.form.get('tagline_ar', ''),
                description_en=request.form.get('description_en'),
                description_ar=request.form.get('description_ar'),
                official_url=request.form.get('official_url'),
                logo=logo_path,
                pricing=request.form.get('pricing', 'freemium'),
                rating=float(request.form.get('rating') or 0),
                rating_note=request.form.get('rating_note', ''),
                rating_source=request.form.get('rating_source', ''),
                free_tier=bool(request.form.get('free_tier')),
                arabic_support=bool(request.form.get('arabic_support')),
                platforms=request.form.get('platforms', 'Web'),
                best_for=request.form.get('best_for', ''),
                featured=bool(request.form.get('featured')),
                sort_order=int(request.form.get('sort_order') or 0),
                last_checked=datetime.date.today(),
                is_published=bool(request.form.get('is_published')),
                related_article_ids=json.dumps(request.form.getlist('related_articles')),
            )
            db.session.add(tool)
            db.session.commit()
            flash("Tool added.", "success")
            return redirect(url_for('tools_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding tool: {e}", "error")
            return redirect(request.url)

    recent_articles = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(40).all()
    return render_template('tool_form.html', mode='add', categories=TOOL_CATEGORIES, recent_articles=recent_articles)

@app.route('/tools/edit/<int:tool_id>', methods=['GET', 'POST'])
@login_required
def edit_tool(tool_id):
    tool = AITool.query.get_or_404(tool_id)
    if request.method == 'POST':
        try:
            tool.name = request.form.get('name')
            tool.name_ar = request.form.get('name_ar')
            tool.category = request.form.get('category', 'other')
            tool.tagline_en = request.form.get('tagline_en', '')
            tool.tagline_ar = request.form.get('tagline_ar', '')
            tool.description_en = request.form.get('description_en')
            tool.description_ar = request.form.get('description_ar')
            tool.official_url = request.form.get('official_url')
            tool.pricing = request.form.get('pricing', 'freemium')
            tool.rating = float(request.form.get('rating') or 0)
            tool.rating_note = request.form.get('rating_note', '')
            tool.rating_source = request.form.get('rating_source', '')
            tool.free_tier = bool(request.form.get('free_tier'))
            tool.arabic_support = bool(request.form.get('arabic_support'))
            tool.platforms = request.form.get('platforms', 'Web')
            tool.best_for = request.form.get('best_for', '')
            tool.featured = bool(request.form.get('featured'))
            tool.sort_order = int(request.form.get('sort_order') or 0)
            tool.last_checked = datetime.date.today()
            tool.is_published = bool(request.form.get('is_published'))
            tool.related_article_ids = json.dumps(request.form.getlist('related_articles'))

            file = request.files.get('logo')
            if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
                filename = secure_filename(f"tool_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                tool.logo = f"/static/uploads/images/{filename}"
            else:
                fetched = (request.form.get('fetched_logo') or '').strip()
                if fetched.startswith('/static/uploads/images/'):
                    tool.logo = fetched

            db.session.commit()
            flash("Tool updated.", "success")
            return redirect(url_for('tools_list'))
        except Exception as e:
            db.session.rollback()
            flash(f"Update failed: {e}", "error")

    recent_articles = NewsItem.query.order_by(NewsItem.timestamp.desc()).limit(40).all()
    return render_template('tool_form.html', mode='edit', item=tool.to_dict(),
                           categories=TOOL_CATEGORIES, recent_articles=recent_articles)

@app.route('/tools/delete/<int:tool_id>', methods=['POST'])
@login_required
def delete_tool(tool_id):
    tool = AITool.query.get(tool_id)
    if tool:
        db.session.delete(tool)
        db.session.commit()
        flash("Tool removed.", "success")
    return redirect(url_for('tools_list'))

@app.route('/api/tools/draft_description', methods=['POST'])
@login_required
def draft_tool_description_api():
    try:
        data = request.json or {}
        name = data.get('name', '')
        category_key = data.get('category', 'other')
        notes = data.get('reference_notes', '')
        category_label = TOOL_CATEGORY_LABELS.get(category_key, 'Other')

        if not content_processor or not hasattr(content_processor, 'draft_tool_description'):
            return jsonify({'status': 'error', 'message': 'AI assistant not available.'}), 500

        result = content_processor.draft_tool_description(name, category_label, notes)
        if not result.get('description_en') and not result.get('description_ar'):
            return jsonify({'status': 'error', 'message': 'Could not draft a description — check your OpenAI API key.'}), 500

        return jsonify({'status': 'success', **result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/directory')
def tools_directory():
    lang_pref = get_lang_pref()
    settings = MagazineSettings.get_settings()
    q = (request.args.get('q') or '').strip()
    category = request.args.get('category', 'all')
    pricing = (request.args.get('pricing') or '').strip()
    free_only = request.args.get('free') == '1'
    arabic_only = request.args.get('arabic') == '1'
    sort = (request.args.get('sort') or 'featured').strip()

    query = AITool.query.filter_by(is_published=True)
    if category != 'all':
        query = query.filter_by(category=category)
    if pricing in ('free', 'freemium', 'paid'):
        query = query.filter(AITool.pricing == pricing)
    if free_only:
        query = query.filter(AITool.free_tier.is_(True))
    if arabic_only:
        query = query.filter(AITool.arabic_support.is_(True))
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            AITool.name.ilike(like), AITool.name_ar.ilike(like),
            AITool.tagline_en.ilike(like), AITool.tagline_ar.ilike(like),
            AITool.description_en.ilike(like), AITool.description_ar.ilike(like),
            AITool.best_for.ilike(like),
        ))

    tools = [t.to_dict() for t in query.all()]
    if sort == 'name':
        tools.sort(key=lambda t: (t.get('name') or '').lower())
    elif sort == 'newest':
        tools.sort(key=lambda t: t.get('created_at') or '', reverse=True)
    else:
        tools.sort(key=lambda t: (not t.get('featured'), t.get('sort_order') or 0, (t.get('name') or '').lower()))

    featured = [t.to_dict() for t in AITool.query.filter_by(is_published=True, featured=True)
                .order_by(AITool.sort_order.asc(), AITool.name.asc()).limit(3).all()]
    counts = {'all': AITool.query.filter_by(is_published=True).count()}
    for key, _ in TOOL_CATEGORIES:
        counts[key] = AITool.query.filter_by(category=key, is_published=True).count()

    template = 'directory.html' if request.args.get('classic') else 'directory_v3.html'
    return render_template(template, settings=settings, tools=tools, featured=featured,
                           category=category, categories=TOOL_CATEGORIES, counts=counts,
                           q=q, pricing=pricing, free_only=free_only, arabic_only=arabic_only,
                           sort=sort, total=counts['all'],
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))

@app.route('/directory/ranked')
def tools_ranked():
    settings = MagazineSettings.get_settings()
    tools = (AITool.query.filter(AITool.is_published.is_(True), AITool.rating > 0)
             .order_by(AITool.rating.desc(), AITool.name.asc()).all())
    return render_template('rankings_v3.html', settings=settings,
                           tools=[t.to_dict() for t in tools],
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))

@app.route('/directory/models')
def models_directory():
    settings = MagazineSettings.get_settings()
    models = LLMModel.query.order_by(LLMModel.downloads.desc()).all()
    return render_template('models_v3.html', settings=settings,
                           models=[m.to_dict() for m in models],
                           llmware_picks=LLMWARE_PICKS,
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))

@app.route('/directory/<int:tool_id>')
def tool_detail(tool_id):
    settings = MagazineSettings.get_settings()
    tool = AITool.query.filter_by(id=tool_id, is_published=True).first_or_404()
    related = NewsItem.query.filter(NewsItem.id.in_(tool.related_article_ids_list),
                                    NewsItem.is_published == True).order_by(NewsItem.timestamp.desc()).all()
    if not related:
        like = f'%{tool.name}%'
        related = (NewsItem.query.filter(NewsItem.is_published.isnot(False),
                                         db.or_(NewsItem.title.ilike(like), NewsItem.summary.ilike(like)))
                   .order_by(NewsItem.timestamp.desc()).limit(3).all())
    alternatives = (AITool.query.filter(AITool.is_published.is_(True),
                                        AITool.category == tool.category,
                                        AITool.id != tool.id)
                    .order_by(AITool.featured.desc(), AITool.name.asc()).limit(3).all())
    template = 'tool_detail.html' if request.args.get('classic') else 'tool_detail_v3.html'
    return render_template(template, settings=settings, tool=tool.to_dict(),
                           related=[r.to_dict() for r in related],
                           alternatives=[a.to_dict() for a in alternatives],
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))

# --- Magazine Design Templates ---

MAGAZINE_TEMPLATES = {'slate', 'broadsheet', 'wire', 'quarterly', 'bloom', 'circuit', 'mission', 'halo', 'digital'}

@app.route('/templates')
@login_required
def template_picker():
    settings = MagazineSettings.get_settings()
    return render_template('template_picker.html', settings=settings)

@app.route('/templates/select', methods=['POST'])
@login_required
def select_template():
    tpl = request.form.get('template')
    if tpl not in MAGAZINE_TEMPLATES:
        flash("Unknown template.", "error")
        return redirect(url_for('template_picker'))

    settings = MagazineSettings.get_settings()
    settings.magazine_template = tpl
    db.session.commit()
    flash(f"Magazine template switched — take a look at the live site!", "success")
    return redirect(url_for('template_picker'))

# --- QR Code (for print / door signage) ---

@app.route('/qr')
@login_required
def qr_page():
    settings = MagazineSettings.get_settings()
    target_url = request.args.get('target', url_for('subscribe', source='qr', _external=True))
    return render_template('qr_code.html', settings=settings, target_url=target_url)

@app.route('/qr.png')
@login_required
def qr_png():
    """Generates a downloadable/printable QR code PNG pointing at the given target
    (defaults to the public subscribe page)."""
    from flask import Response
    target_url = request.args.get('target') or url_for('subscribe', _external=True)
    try:
        import qrcode
        qr = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(target_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/png')
    except ImportError:
        return "QR code generation requires the 'qrcode' and 'pillow' packages. Run: pip install qrcode[pil]", 500
    except Exception as e:
        print(f"QR Generation Error: {e}")
        return f"QR generation failed: {e}", 500

@app.route('/api/upload_image', methods=['POST'])
@login_required
def upload_image_api():
    """
    Dedicated endpoint for async image uploads from the rich text editor.
    Saves file with timestamp and returns the URL.
    """
    file = request.files.get('image')
    if file is None and request.files:
        file = next(iter(request.files.values()))
    if file is None:
        return jsonify({'error': 'No image provided', 'errorMessage': 'No image provided'}), 400
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
            unique_name = f"upload_{timestamp}_{uuid.uuid4().hex[:6]}.{file_ext}"
            
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', unique_name)
            file.save(save_path)
            
            # Use url_for to ensure correct path generation relative to static folder
            # File is saved at: app/static/uploads/images/{unique_name}
            # url_for('static', filename='...') maps to app/static/...
            url = url_for('static', filename=f'uploads/images/{unique_name}')
            
            return jsonify({
                'url': url,
                'result': [{'url': url, 'name': unique_name, 'size': 0}],
            })
        except Exception as e:
            print(f"Upload API Error: {e}")
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

# Helper: YouTube Detection
def detect_youtube(url):
    """
    Analyzes URL for YouTube patterns.
    Returns (video_id, is_video_bool)
    """
    if not url: return None, False
    
    # Regex for standard watch, embed, short, and youtu.be
    import re
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    
    if match:
        return match.group(1), True
    short = re.search(r'(?:shorts/|live/)([A-Za-z0-9_-]{11})', url)
    if short:
        return short.group(1), True
    return None, False


def fetch_youtube_details(url):
    """Title, channel, cover, and description for a YouTube link. None if it is not a video."""
    video_id, is_video = detect_youtube(url)
    if not is_video:
        return None
    details = {
        "video_id": video_id,
        "title": "",
        "source": "YouTube",
        "summary": "",
        "image": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
    }
    watch = f"https://www.youtube.com/watch?v={video_id}"
    try:
        response = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": watch, "format": "json"},
            headers=_THUMB_HEADERS,
            timeout=8,
        )
        if response.ok:
            payload = response.json()
            details["title"] = (payload.get("title") or "").strip()[:490]
            details["source"] = (payload.get("author_name") or "YouTube").strip()[:190]
            if payload.get("thumbnail_url"):
                details["image"] = payload["thumbnail_url"]
    except Exception as exc:
        print(f"YouTube oEmbed skipped: {exc}")
    try:
        page = requests.get(watch, headers=_THUMB_HEADERS, timeout=8)
        if page.ok:
            soup = BeautifulSoup(page.text, "html.parser")
            tag = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            if tag and tag.get("content"):
                text = tag["content"].strip()
                generic = ("Enjoy the videos and music you love", "Share your videos with friends")
                if not any(phrase in text for phrase in generic):
                    details["summary"] = text[:700]
    except Exception as exc:
        print(f"YouTube description skipped: {exc}")
    if not details["summary"] and details["source"]:
        details["summary"] = f"YouTube video by {details['source']}."
    return details

def _plain_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    return text.replace("&nbsp;", " ").replace("\xa0", " ").strip()


def _translate_value(value, target, html=False):
    """Translate one field. A failed call keeps the original words."""
    from agent.skills.translator.translation_api import has_arabic, translate, translate_html
    raw = value or ""
    if not _plain_text(raw):
        return raw
    source = "ar" if target == "en" else "en"
    try:
        done = translate_html(raw, target=target, source=source) if html else translate(raw, target=target, source=source)
    except Exception as exc:
        print(f"Translation skipped: {exc}")
        return raw
    done = (done or "").strip() or raw
    plain = _plain_text(done)
    if target == "ar" and not has_arabic(plain):
        return raw
    if target == "en" and has_arabic(plain) and not re.search(r"[A-Za-z]", plain):
        return raw
    return done


def _pair_languages(english, arabic, html=False):
    """Fill the empty language from the one that was written.

    Arabic in the English box is translated into English. English with no Arabic
    copy is translated into Arabic. When both languages are already written,
    both are kept.
    """
    from agent.skills.translator.translation_api import has_arabic
    english = english or ""
    arabic = arabic or ""
    en_text = _plain_text(english)
    ar_text = _plain_text(arabic)
    en_has_ar = has_arabic(en_text)
    ar_has_ar = has_arabic(ar_text)
    if en_has_ar and not ar_has_ar:
        arabic = english
        english = _translate_value(arabic, "en", html)
    elif en_has_ar and ar_has_ar:
        english = _translate_value(english, "en", html)
    elif ar_has_ar and not en_text:
        english = _translate_value(arabic, "en", html)
    elif en_text and not en_has_ar and not ar_has_ar:
        arabic = _translate_value(english, "ar", html)
    return english, arabic


def ensure_bilingual_content(title_en, summary_en, full_content_html,
                              title_ar=None, summary_ar=None, full_content_ar=None):
    """Store both languages at save time.

    Returns (title_en, title_ar, summary_en, summary_ar, full_en, full_ar).
    """
    title_en, title_ar = _pair_languages(title_en, title_ar)
    summary_en, summary_ar = _pair_languages(summary_en, summary_ar)
    full_en, full_ar = _pair_languages(full_content_html, full_content_ar, html=True)
    if not _plain_text(summary_en) and not _plain_text(summary_ar):
        summary_en = "No summary provided."
        summary_ar = "لا يوجد ملخص."
    return title_en, title_ar, summary_en, summary_ar, full_en, full_ar

def import_daily_top_stories(limit=5):
    """
    Pull the day's most important global AI stories and file the new ones
    under Latest News. Stories already in the magazine are left alone.
    Returns the titles that were added.
    """
    from agent.skills.news_fetcher.daily_brief import gather_top_stories, normalize_url

    existing = {
        normalize_url(url)
        for (url,) in db.session.query(NewsItem.url).all()
        if url
    }
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=20)
    already_today = NewsItem.query.filter(
        NewsItem.timestamp >= cutoff,
        NewsItem.article_type == "external",
        NewsItem.category == "second",
    ).count()
    room = max(0, limit - already_today)
    if room == 0:
        return []

    added = []
    for story in gather_top_stories(limit=limit + 8):
        if len(added) >= room:
            break
        if story["url_key"] in existing:
            continue

        image = (story.get("image") or "")[:500]
        if not image and media_handler:
            try:
                image = (media_handler.get_image(story["url"]) or "")[:500]
            except Exception as exc:
                print(f"Daily brief image skipped: {exc}")
                image = ""

        _title, title_ar, summary_en, summary_ar, _body, _body_ar = ensure_bilingual_content(
            title_en=story["title"],
            summary_en=story["summary"],
            full_content_html=None,
        )
        published_at = story.get("published_at")
        if published_at is None:
            from agent.skills.news_fetcher.daily_brief import lookup_published_at
            published_at = lookup_published_at(story["url"])
        if isinstance(published_at, datetime.datetime) and published_at.tzinfo is not None:
            published_at = published_at.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        item = NewsItem(
            title=story["title"][:490],
            title_ar=(title_ar or "")[:490],
            summary=summary_en,
            summary_ar=summary_ar,
            source=(story.get("source") or "World press")[:190],
            url=story["url"],
            image=image or "",
            category="second",
            article_type="external",
            is_published=True,
            topic="",
            published_at=published_at,
            wing=classify_wing(story.get("source"), story["title"], summary_en),
        )
        if not added:
            write_classroom_note(item)
        db.session.add(item)
        existing.add(story["url_key"])
        added.append(story["title"])

    if added:
        db.session.commit()
    return added

@app.route('/daily_brief', methods=['POST'])
@login_required
def run_daily_brief():
    try:
        added = import_daily_top_stories(limit=5)
    except Exception as exc:
        db.session.rollback()
        flash(f"Could not fetch today's AI briefing: {exc}", "error")
        return redirect(url_for('dashboard'))

    if added:
        flash(f"Added {len(added)} of today's most important AI stories to Latest News.", "success")
    else:
        flash("No new stories. Today's top AI headlines are already in the magazine.", "success")
    return redirect(url_for('dashboard'))


def _compact_views(count, arabic):
    count = count or 0
    if count >= 1000000:
        text = f"{count / 1000000:.1f}"
        return f"{text} مليون" if arabic else f"{text}M"
    if count >= 1000:
        text = f"{count / 1000:.0f}"
        return f"{text} ألف" if arabic else f"{text}K"
    return str(count) if count else ""


def _compact_minutes(seconds, arabic):
    minutes = max(1, round((seconds or 0) / 60)) if seconds else 0
    if not minutes:
        return ""
    return f"{minutes} د" if arabic else f"{minutes} min"


def import_youtube_desk():
    """Replace each YouTube shelf that returned fresh clips. Empty shelves stay as they were."""
    from agent.skills.news_fetcher.youtube_desk import gather_youtube_desk
    chosen = gather_youtube_desk()
    saved = {}
    for (lane, language), videos in chosen.items():
        if not videos:
            saved[(lane, language)] = 0
            continue
        YouTubePick.query.filter_by(lane=lane, language=language).delete()
        for order, video in enumerate(videos):
            db.session.add(YouTubePick(
                video_id=video["video_id"],
                lane=lane,
                language=language,
                title=video.get("title") or "",
                summary=(video.get("summary") or "")[:500],
                channel=video.get("channel") or "",
                image=video.get("image") or "",
                url=video.get("url") or "",
                published_at=video.get("published_at"),
                view_count=video.get("views") or 0,
                duration_seconds=video.get("seconds") or 0,
                display_order=order,
            ))
        saved[(lane, language)] = len(videos)
    if any(saved.values()):
        db.session.commit()
    return saved


def _youtube_shelves(arabic):
    rows = YouTubePick.query.order_by(YouTubePick.display_order.asc()).all()
    shelves = {}
    for row in rows:
        when = ""
        if row.published_at:
            if arabic:
                when = f"{row.published_at.day} {ARABIC_MONTHS[row.published_at.month]} {row.published_at.year}"
            else:
                when = row.published_at.strftime("%d %b %Y")
        shelves.setdefault((row.lane, row.language), []).append({
            "video_id": row.video_id,
            "title": row.title,
            "channel": row.channel,
            "image": row.image,
            "url": row.url,
            "when": when,
            "views": _compact_views(row.view_count, arabic),
            "minutes": _compact_minutes(row.duration_seconds, arabic),
        })
    return shelves


@app.route('/youtube')
def youtube_desk():
    """News clips and lessons, five in English and five in Arabic on each shelf."""
    if get_lang_pref() is None:
        return _render_language_gate()
    arabic = get_lang_pref() == 'ar'
    shelves = _youtube_shelves(arabic)
    return render_template(
        'youtube.html',
        news_en=shelves.get(('news', 'en'), []),
        news_ar=shelves.get(('news', 'ar'), []),
        edu_en=shelves.get(('education', 'en'), []),
        edu_ar=shelves.get(('education', 'ar'), []),
        settings=MagazineSettings.get_settings(),
    )


@app.route('/desk/world/youtube', methods=['POST'])
@login_required
def refresh_youtube_desk():
    try:
        saved = import_youtube_desk()
    except Exception as exc:
        db.session.rollback()
        flash(admin_text(get_admin_lang(), 'yt_failed'), 'error')
        print(f"YouTube desk refresh failed: {exc.__class__.__name__}")
        return redirect(url_for('dashboard'))
    total = sum(saved.values())
    if total:
        flash(admin_text(get_admin_lang(), 'yt_saved'), 'success')
    else:
        flash(admin_text(get_admin_lang(), 'yt_empty'), 'error')
    return redirect(url_for('youtube_desk'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_news():
    if request.method == 'POST':
        try:
            # Form Data
            title_en = request.form.get('title_en')
            # Validation
            if not title_en:
                flash("English Title is required.", "error")
                return redirect(request.url)

            # File Handling
            image_path = ""
            file = request.files.get('cover_image')
            if file and file.filename and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                image_path = f"/static/uploads/images/{filename}"
            elif request.form.get('url'):
                 # Try fetch if not uploaded
                 image_path = media_handler.get_image(request.form.get('url'))

            attachment_path = ""
            doc = request.files.get('attachment')
            if doc and doc.filename and allowed_file(doc.filename, {'pdf', 'doc', 'docx', 'txt'}):
                docname = secure_filename(f"{uuid.uuid4().hex}_{doc.filename}")
                doc.save(os.path.join(app.config['UPLOAD_FOLDER'], 'docs', docname))
                attachment_path = f"/static/uploads/docs/{docname}"

            # Process Rich Text Content (Extract Images)
            full_content_processed = process_content_images(_editor_html(request.form.get('full_content')))
            written_ar = process_content_images(_editor_html(request.form.get('full_content_ar')))

            # Translate ONCE, right now, at save time — fills in whatever the
            # editor left blank so both languages are ready in the DB immediately.
            title_en, title_ar, summary_en, summary_ar, full_en, full_ar = ensure_bilingual_content(
                title_en=title_en,
                summary_en=request.form.get('summary_en'),
                full_content_html=full_content_processed,
                title_ar=request.form.get('title_ar'),
                summary_ar=request.form.get('summary_ar'),
                full_content_ar=written_ar or None,
            )

            # Create DB Object
            new_item = NewsItem(
                title=title_en,
                title_ar=title_ar,
                source=request.form.get('source'),
                url=request.form.get('url'),
                summary=summary_en,
                summary_ar=summary_ar,
                full_content=full_en,
                full_content_ar=full_ar,
                show_details=bool(request.form.get('show_details') or full_en or full_ar),
                image=image_path,
                attachment=attachment_path,
                category=request.form.get('category', 'sidebar'),
                headline_display_mode=request.form.get('headline_display_mode', 'default'),
                article_type=request.form.get('article_type', 'manual'),
                topic=_stored_topic(request.form.get('topic')),
            )
            new_item.wing, new_item.campus_kind = audience_from_form(request.form)
            apply_campus_schedule(new_item, request.form)
            apply_lesson(new_item, lesson_from_form(request.form))
            
            # YouTube Automatic Detection
            if new_item.article_type == 'external' and new_item.url:
                vid_id, is_yt = detect_youtube(new_item.url)
                if is_yt:
                    new_item.content_format = 'video'
                    new_item.video_id = vid_id
                    new_item.source = request.form.get('source') or 'YouTube'
                    
                    # Auto-Fetch Thumbnail if not provided
                    if not new_item.image:
                        new_item.image = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
            
            db.session.add(new_item)
            db.session.commit()
            
            flash("News item added successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            print(f"Add News Error: {e}")
            flash(f"Error adding news: {e}", "error")
            return redirect(request.url)

    settings = MagazineSettings.get_settings()
    return render_template('add_edit.html', mode="add", settings=settings)

@app.route('/add_comment/<item_id>', methods=['POST'])
def add_comment(item_id):
    try:
        content = (request.form.get('content') or '').strip()
        author = (request.form.get('author') or 'Guest').strip()[:60] or 'Guest'

        if not NewsItem.query.get(item_id):
            flash("That article no longer exists.", "error")
            return redirect(url_for('magazine_view'))

        if not content:
            flash("Comment cannot be empty.", "error")
            return redirect(url_for('magazine_detail', item_id=item_id))

        if len(content) > 1000:
            flash("Comment is too long (1000 characters max).", "error")
            return redirect(url_for('magazine_detail', item_id=item_id))

        if _public_rate_limited('comment', 5, 10 * 60):
            flash("You're commenting too fast — please wait a few minutes.", "error")
            return redirect(url_for('magazine_detail', item_id=item_id))

        new_comment = Comment(news_item_id=item_id, author=author, content=content)
        db.session.add(new_comment)
        db.session.commit()

        flash("Comment added.", "success")
        return redirect(url_for('magazine_detail', item_id=item_id)) # Stay on the item view
    except Exception as e:
        print(f"Comment Error: {e}")
        flash("Failed to add comment.", "error")
        return redirect(url_for('magazine_detail', item_id=item_id))

@app.route('/toggle_publish/<item_id>', methods=['POST'])
@login_required
def toggle_publish(item_id):
    try:
        item = NewsItem.query.get(item_id)
        if not item:
            return jsonify({'status': 'error', 'message': 'Item not found'}), 404
        
        # Toggle boolean (handle None as True default flip)
        current_status = item.is_published if item.is_published is not None else True
        item.is_published = not current_status
        db.session.commit()
        
        return jsonify({'status': 'success', 'new_state': item.is_published})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/edit/<item_id>', methods=['GET', 'POST'])
@login_required
def edit_news(item_id):
    item = NewsItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        try:
            old_full_content = item.full_content

            item.source = request.form.get('source')
            item.url = request.form.get('url')

            # Process Rich Text Content (Extract Images)
            written_en = process_content_images(_editor_html(request.form.get('full_content')))
            written_ar = process_content_images(_editor_html(request.form.get('full_content_ar')))

            # Translate once, at save time, in either direction. A language the
            # editor already wrote is kept. Force rebuilds the Arabic from the English.
            force_retranslate = bool(request.form.get('force_retranslate'))
            body_changed = written_en != old_full_content
            kept_ar = None if force_retranslate else (written_ar or (None if body_changed else (item.full_content_ar or None)))
            title_en, title_ar, summary_en, summary_ar, full_en, full_ar = ensure_bilingual_content(
                title_en=request.form.get('title_en'),
                summary_en=request.form.get('summary_en'),
                full_content_html=written_en,
                title_ar=None if force_retranslate else (request.form.get('title_ar') or None),
                summary_ar=None if force_retranslate else (request.form.get('summary_ar') or None),
                full_content_ar=kept_ar,
            )
            item.title = title_en
            item.title_ar = title_ar
            item.summary = summary_en
            item.summary_ar = summary_ar
            item.full_content = full_en
            item.full_content_ar = full_ar

            item.category = request.form.get('category')
            item.article_type = request.form.get('article_type', 'manual')
            item.headline_display_mode = request.form.get('headline_display_mode', 'default')
            item.topic = _stored_topic(request.form.get('topic'))
            item.wing, item.campus_kind = audience_from_form(request.form)
            apply_campus_schedule(item, request.form)
            apply_lesson(item, lesson_from_form(request.form))

            # YouTube Automatic Detection (Update)
            if item.article_type == 'external' and item.url:
                vid_id, is_yt = detect_youtube(item.url)
                if is_yt:
                    item.content_format = 'video'
                    item.video_id = vid_id
                    if not item.source: item.source = 'YouTube'
                    
                    # Auto-Update thumbnail only if missing or was previous auto-generated one
                    if not item.image or 'img.youtube.com' in item.image:
                        item.image = f"https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg"
                else:
                    # Reset if URL changed to non-video
                    item.content_format = 'article'
                    item.video_id = None
            else:
                 # If switched to manual, ensure format is article
                 if item.article_type == 'manual':
                     item.content_format = 'article'

            # Handle new files
            file = request.files.get('cover_image')
            if file and file.filename:
                filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                item.image = f"/static/uploads/images/{filename}"

            doc = request.files.get('attachment')
            if doc and doc.filename:
                docname = secure_filename(f"{uuid.uuid4().hex}_{doc.filename}")
                doc.save(os.path.join(app.config['UPLOAD_FOLDER'], 'docs', docname))
                item.attachment = f"/static/uploads/docs/{docname}"
            
            # Save Checkbox from form (returns 'on' if checked, None if not)
            item.show_details = bool(request.form.get('show_details') or item.full_content or item.full_content_ar)
            
            db.session.commit()
            flash(admin_text(get_admin_lang(), 'story_saved'), "success")
            return redirect(url_for('edit_news', item_id=item.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Update failed: {e}", "error")

    settings = MagazineSettings.get_settings()
    return render_template('add_edit.html', mode="edit", item=item.to_dict(), settings=settings)

@app.route('/archive_news/<item_id>', methods=['POST'])
@login_required
def archive_news(item_id):
    """Take a story off the live magazine without deleting it."""
    item = NewsItem.query.get(item_id)
    if not item:
        flash("Item not found.", "error")
    else:
        item.is_published = False
        db.session.commit()
        flash("Moved to the archive. It is off the live magazine and can be published again from Archive.", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete/<item_id>', methods=['POST'])
@login_required
def delete_news(item_id):
    item = NewsItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted.", "success")
    else:
        flash("Item not found.", "error")
    return redirect(url_for('dashboard'))

@app.route('/api/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_news():
    try:
        data = request.json
        item_ids = data.get('ids', [])
        
        if not item_ids:
            return jsonify({'status': 'error', 'message': 'No items selected'}), 400
            
        # Bulk delete
        deleted_count = 0
        for item_id in item_ids:
            item = NewsItem.query.get(item_id)
            if item:
                db.session.delete(item)
                deleted_count += 1
        
        db.session.commit()
        flash(f"{deleted_count} items deleted successfully.", "success")
        return jsonify({'status': 'success', 'count': deleted_count})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/magazine/article/<item_id>')
def magazine_detail(item_id):
    # First-visit language gate: ask once, remember via cookie, never again.
    lang_pref = get_lang_pref()
    if lang_pref is None:
        return _render_language_gate()

    # Fetch Specific Item
    item = NewsItem.query.get_or_404(item_id)
    if item.is_published is False:
        abort(404)

    # Count the read (best-effort; never let this break the page)
    try:
        item.views = (item.views or 0) + 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"View count update failed: {e}")

    # --- Sidebar/Context Logic (Reused) ---
    if not request.args.get('classic'):
        return _render_v3_article(item)

    all_items = NewsItem.query.order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc()).all()
    public_items = [i for i in all_items if i.is_published is not False]

    # Build Archive Tree from published stories only — drafts stay in the dashboard.
    archive_tree = defaultdict(lambda: defaultdict(list))
    for i in public_items:
        if i.timestamp:
            y = i.timestamp.year
            m = i.timestamp.month
            archive_tree[y][m].append(i)
            
    # Serialize Archive Data
    archive_data = []
    for year in sorted(archive_tree.keys(), reverse=True):
        months_data = []
        for month_num in sorted(archive_tree[year].keys(), reverse=True):
            month_items_dicts = [x.to_dict() for x in archive_tree[year][month_num]]
            months_data.append({
                'name': calendar.month_name[month_num],
                'posts': month_items_dicts
            })
        archive_data.append({
            'year': year,
            'months': months_data
        })
        
    settings = MagazineSettings.get_settings()
    
    # Sidebar & Ads Logic for Detail View
    # Use to_dict() versions if filtering by properties easily
    all_dicts = [a.to_dict() for a in public_items]
    published_items = all_dicts
    for story in published_items:
        assign_desk(story)

    item_dict = item.to_dict()
    assign_desk(item_dict)
    if (item_dict.get('wing') or '') == 'campus':
        label_campus([item_dict])

    sidebar = [i for i in published_items if i.get('category') == 'sidebar']
    ads = [i for i in published_items if i.get('category') == 'ads']
    most_viewed = sorted(published_items, key=lambda i: i.get('views') or 0, reverse=True)[:5]
    reading_time = item_dict.get('reading_minutes') or estimate_reading_time(item.full_content or item.summary)
    reels = [r.to_dict() for r in CuratedReel.query.filter_by(status='published')
             .order_by(CuratedReel.display_order.asc(), CuratedReel.created_at.desc())
             .limit(settings.reels_display_limit or 4).all()]

    # Related reads: same desk first (security with security), then anything recent.
    others = [i for i in published_items if i.get('id') != item.id and i.get('category') != 'ads']
    same_category = [i for i in others if i.get('desk') == item_dict.get('desk')]
    related = same_category[:3]
    if len(related) < 3:
        seen_ids = {r['id'] for r in related}
        for i in others:
            if len(related) >= 3:
                break
            if i.get('id') not in seen_ids:
                related.append(i)
                seen_ids.add(i.get('id'))

    return render_template('magazine_detail.html',
                           item=item_dict,
                           archive_data=archive_data,
                           sidebar=sidebar,
                           most_viewed=most_viewed,
                           related=related,
                           reels=reels,
                           ads=ads,
                           reading_time=reading_time,
                           settings=settings,
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))

# --- Public reader (v3) ---------------------------------------------------
# The reader-facing magazine was rebuilt as a paper-first issue: a 90-second brief,
# one lead, three features, five one-line briefs, the department, a class layer and
# editor's picks. The previous templates stay available with ?classic=1.

def _v3_story_rows():
    rows = NewsItem.query.filter(NewsItem.is_published.isnot(False)).all()
    stories = []
    for row in rows:
        story = row.to_dict()
        assign_desk(story)
        stories.append(story)
    stories.sort(key=lambda s: s.get("timestamp") or "", reverse=True)
    return stories


def _v3_text(story, ar, en_key, ar_key, fallback=""):
    if ar:
        return (story.get(ar_key) or story.get(en_key) or fallback)
    return (story.get(en_key) or story.get(ar_key) or fallback)


def _v3_dedupe(stories):
    """Drop syndicated copies of the same story so the issue never repeats itself."""
    seen = set()
    unique = []
    for story in stories:
        key = re.sub(r"\s+", " ", (story.get("title") or "").strip().lower())[:90]
        if key in seen:
            continue
        seen.add(key)
        unique.append(story)
    return unique


def _v3_good_image(story):
    """A cover needs a real photograph, not a search-engine thumbnail or a video still."""
    image = (story.get("image") or "").lower()
    if not image:
        return False
    bad = ("bing.com/th", "ytimg.com", "img.youtube.com", "googleusercontent", "data:image")
    return not any(marker in image for marker in bad)


_V3_COVER_SOURCES = (
    "the guardian", "the verge", "bbc", "new york times", "wired", "techcrunch",
    "mit news", "mit technology review", "nature", "sciencedaily", "reuters",
    "associated press", "financial times", "bloomberg",
)


def _v3_cover_worthy(story):
    """A photograph plus a newsroom behind it — the cover should not be a vendor blog."""
    if not _v3_good_image(story):
        return False
    source = (story.get("source") or "").strip().lower()
    return any(name in source for name in _V3_COVER_SOURCES)


def _render_v3_issue():
    settings = MagazineSettings.get_settings()
    ar = get_lang_pref() == 'ar'
    stories = _v3_dedupe(_v3_story_rows())
    world = [s for s in stories if (s.get('wing') or 'world') != 'campus' and s.get('category') != 'ads']
    campus = [s for s in stories if (s.get('wing') or '') == 'campus']

    lead = None
    pin = (settings.cover_world_id or '').strip()
    if pin:
        lead = next((s for s in world if s['id'] == pin), None)
    if lead is None:
        lead = next((s for s in world if s.get('category') == 'top' and _v3_cover_worthy(s)), None)
    if lead is None:
        lead = next((s for s in world if _v3_cover_worthy(s)), None)
    if lead is None:
        lead = next((s for s in world if s.get('category') == 'top' and _v3_good_image(s)), None)
    if lead is None:
        lead = next((s for s in world if _v3_good_image(s)), None)
    if lead is None:
        lead = next((s for s in world if s.get('image')), None)
    if lead is None and world:
        lead = world[0]

    used = {lead['id']} if lead else set()
    brief_items = [s for s in world if s['id'] not in used][:5]
    used.update(s['id'] for s in brief_items)

    features = [s for s in world if s['id'] not in used and _v3_good_image(s)][:3]
    if len(features) < 3:
        for story in world:
            if len(features) >= 3:
                break
            if story['id'] not in used and story not in features:
                features.append(story)
    used.update(s['id'] for s in features)

    brief_rows = [s for s in world if s['id'] not in used][:5]
    used.update(s['id'] for s in brief_rows)

    picks_pool = [s for s in world if s['id'] not in used]
    picks = sorted(picks_pool, key=lambda s: (s.get('views') or 0), reverse=True)[:3]
    if len(picks) < 3:
        picks += [s for s in picks_pool if s not in picks][:3 - len(picks)]

    label_campus(campus)
    for story in campus:
        _stamp_campus(story)
    campus.sort(key=lambda s: (s.get('event_on') or s.get('timestamp') or ''), reverse=True)
    campus_items = campus[:3]
    agenda = campus[:3]
    upcoming = sorted([s for s in campus if s.get('event_on')],
                      key=lambda s: s.get('event_on') or '')[:3]

    term_story = next((s for s in stories if s.get('lesson_term') or s.get('lesson_term_ar')), None)
    term = None
    if term_story:
        term = {
            'id': term_story['id'],
            'term': term_story.get('lesson_term') or term_story.get('lesson_term_ar') or '',
            'term_ar': term_story.get('lesson_term_ar') or '',
            'gloss': term_story.get('lesson_gloss') or '',
            'gloss_ar': term_story.get('lesson_gloss_ar') or '',
        }
    class_story = next((s for s in stories if s.get('lesson_why') or s.get('lesson_why_ar') or s.get('lesson_ask')), None)

    lead_what = lead_why = lead_ask = ""
    if lead:
        _picture_brief(lead)
        lead_what = lead.get('lead_what_ar') if ar else lead.get('lead_what_en')
        lead_why = lead.get('lead_why_ar') if ar else lead.get('lead_why_en')
        lead_ask = _v3_text(lead, ar, 'lesson_ask', 'lesson_ask_ar')
        if lead_ask and lead_ask == lead_why:
            lead_ask = ""
        if not (lead_why or lead_ask):
            # A plain story shows its standfirst; the three-line block is reserved
            # for stories with a written classroom layer.
            lead_what = ""

    now = datetime.datetime.now()
    week = now.isocalendar()[1]
    edition = edition_context(([lead] if lead else []) + brief_items)
    stats = {'total': len(stories), 'campus': len(campus), 'world': len(world)}

    return render_template(
        'issue_v3.html',
        lead=lead,
        brief_items=brief_items,
        features=features,
        brief_rows=brief_rows,
        campus_items=campus_items,
        agenda=agenda,
        upcoming=upcoming,
        term=term,
        class_story=class_story,
        picks=picks,
        lead_what=lead_what,
        lead_why=lead_why,
        lead_ask=lead_ask,
        stats=stats,
        issue_label=('العدد %s' % week) if ar else ('Issue %s' % week),
        now=now,
        **edition
    )


def _render_v3_article(item):
    ar = get_lang_pref() == 'ar'
    story = item.to_dict()
    assign_desk(story)
    if (story.get('wing') or '') == 'campus':
        label_campus([story])
        _stamp_campus(story)

    title = _v3_text(story, ar, 'title', 'title_ar')
    summary = _v3_text(story, ar, 'summary', 'summary_ar')
    full = story.get('full_content_ar') if ar else story.get('full_content')
    has_body = bool(full and str(full).strip())

    what = _first_sentence(summary, 220) if summary else ""
    if not has_body:
        # The summary is the body of a brief, so it is not printed twice.
        what = ""
    why = _v3_text(story, ar, 'lesson_why', 'lesson_why_ar')
    ask = _v3_text(story, ar, 'lesson_ask', 'lesson_ask_ar')
    term = _v3_text(story, ar, 'lesson_term', 'lesson_term_ar')
    gloss = _v3_text(story, ar, 'lesson_gloss', 'lesson_gloss_ar')

    related = []
    try:
        rows = NewsItem.query.filter(NewsItem.is_published.isnot(False)).all()
        others = []
        for row in rows:
            if row.id == item.id:
                continue
            other = row.to_dict()
            assign_desk(other)
            others.append(other)
        same = [o for o in others if o.get('desk') == story.get('desk') and o.get('category') != 'ads']
        related = same[:3]
        if len(related) < 3:
            seen = {r['id'] for r in related}
            for other in others:
                if len(related) >= 3:
                    break
                if other['id'] not in seen and other.get('category') != 'ads':
                    related.append(other)
                    seen.add(other['id'])
    except Exception as error:
        print(f"Related stories failed: {error}")

    return render_template(
        'article_v3.html',
        item=story,
        title=title,
        summary=summary,
        has_body=has_body,
        body=full if has_body else "",
        body_text=summary or "",
        what=what,
        why=why,
        ask=ask,
        term=term,
        gloss=gloss,
        related=related,
        reading_minutes=story.get('reading_minutes') or 1,
        published=story.get('published_ar') if ar else story.get('published_en'),
        published_iso=(story.get('published_at') or story.get('timestamp') or '')[:10],
    )


@app.route('/find')
def find_stories():
    """Public search and the browser for every published story."""
    q = (request.args.get('q') or '').strip()
    wing = (request.args.get('wing') or '').strip()
    desk = (request.args.get('desk') or '').strip()

    query = NewsItem.query.filter(NewsItem.is_published.isnot(False))
    if wing in ('world', 'research', 'campus'):
        query = query.filter(NewsItem.wing == wing)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(
            NewsItem.title.ilike(like),
            NewsItem.summary.ilike(like),
            NewsItem.title_ar.ilike(like),
            NewsItem.summary_ar.ilike(like),
            NewsItem.source.ilike(like),
        ))

    rows = query.order_by(NewsItem.timestamp.desc()).limit(40).all()
    stories = []
    for row in rows:
        story = row.to_dict()
        assign_desk(story)
        if desk and story.get('desk') != desk:
            continue
        stories.append(story)

    return render_template('search_v3.html', q=q, wing=wing, desk=desk,
                           stories=stories, total=len(stories))


@app.route('/magazine')
def magazine_view():
    legacy = (request.args.get('classic') or request.args.get('item_id') or
              request.args.get('year') or request.args.get('desk') or request.args.get('wing'))
    if not legacy:
        return _render_v3_issue()
    # First-visit language gate: ask once, remember via cookie, never again.
    lang_pref = get_lang_pref()
    if lang_pref is None:
        return _render_language_gate()

    # 1. Fetch ALL items for the Archive (Sidebar)
    # 1. Fetch ALL items for the Archive (Sidebar) - Sorted by Order
    all_items = NewsItem.query.order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc()).all()
    all_items_dicts = [i.to_dict() for i in all_items]
    
    # Published stories only. Drafts never reach the public paper or its archive.
    published_items = [i for i in all_items_dicts if i.get('is_published')]
    for story in published_items:
        assign_desk(story)

    public_objects = [i for i in all_items if i.is_published is not False]
    archive_tree = defaultdict(lambda: defaultdict(list))
    for i in public_objects:
        if i.timestamp:
            y = i.timestamp.year
            m = i.timestamp.month
            archive_tree[y][m].append(i)

    campus_items = [i for i in published_items if (i.get('wing') or 'world') == 'campus']
    wire_items = [i for i in published_items if (i.get('wing') or 'world') != 'campus']
    top_news = [i for i in wire_items if i.get('category') == 'top']
    sub_news = [i for i in wire_items if i.get('category') == 'second']
    sidebar = [i for i in wire_items if i.get('category') == 'sidebar']
    ads = [i for i in published_items if i.get('category') == 'ads']
    most_viewed = sorted(published_items, key=lambda i: i.get('views') or 0, reverse=True)[:5]

    settings = MagazineSettings.get_settings()
    reels = [r.to_dict() for r in CuratedReel.query.filter_by(status='published')
             .order_by(CuratedReel.display_order.asc(), CuratedReel.created_at.desc())
             .limit(settings.reels_display_limit or 4).all()]

    # Convert to sorted structure for template
    archive_data = []
    for year in sorted(archive_tree.keys(), reverse=True):
        months_data = []
        for month_num in sorted(archive_tree[year].keys(), reverse=True):
            month_items_dicts = [item.to_dict() for item in archive_tree[year][month_num]]
            months_data.append({
                'name': calendar.month_name[month_num],
                'posts': month_items_dicts
            })
        archive_data.append({
            'year': year,
            'months': months_data
        })
    
    # --- Content Logic ---
    # Default: Show PUBLISHED Only
    filtered_items = published_items 
    current_filter = None
    
    # A direct item link still opens inside the paper, but only if it is published.
    item_id = request.args.get('item_id')
    if item_id:
        filtered_items = [i for i in published_items if i['id'] == item_id]
        current_filter = current_filter or 'Story'

    year_param = request.args.get('year')
    if year_param and year_param.isdigit():
        filtered_items = [i for i in published_items if i.get('timestamp') and i.get('timestamp')[:4] == year_param]
        current_filter = year_param

    # Group every published story (except ads) into a desk so nothing the
    # editor published can vanish just because it wasn't placed in a layout slot.
    story_items = [i for i in wire_items if i.get('category') != 'ads']
    grouped = defaultdict(list)
    for story in story_items:
        grouped[story['desk']].append(story)

    desk_nav = []
    for key, en, ar, _words in list(NEWS_DESKS) + [BRIEFING_DESK]:
        bucket = grouped.get(key) or []
        if bucket:
            desk_nav.append({'key': key, 'label_en': en, 'label_ar': ar, 'count': len(bucket)})

    requested_desk = (request.args.get('desk') or '').strip()
    active_desk = requested_desk if requested_desk in grouped else None
    science_only = request.args.get('wing') == 'research' and not active_desk
    # Each half has one cover. A pin from Settings wins; otherwise the issue
    # leads with the best of today's five, and the department's own pick.
    world_cover = None
    picture_lead = None
    picture_rail = []
    world_cover_chosen = False
    if not active_desk and not science_only:
        daily_five = _daily_file(sub_news)
        for story in daily_five:
            _picture_brief(story)
        chosen_world = _cover_story(wire_items, settings.cover_world_id)
        if chosen_world:
            _picture_brief(chosen_world)
            picture_lead = chosen_world
            world_cover_chosen = True
            picture_rail = [story for story in daily_five if story.get("id") != chosen_world.get("id")][:4]
        elif daily_five:
            picture_lead = daily_five[0]
            picture_rail = daily_five[1:]
        if top_news and (not picture_lead or top_news[0].get("id") != picture_lead.get("id")):
            world_cover = top_news[0]
        elif not picture_lead:
            world_cover = story_items[0] if story_items else None
    hero_id = world_cover['id'] if world_cover else None
    # On the front page the Latest News slot owns these stories, so they are
    # not repeated inside the desks underneath.
    latest_ids = {story['id'] for story in sub_news} if not active_desk and not science_only else set()
    research_all = [s for s in wire_items if s.get('wing') == 'research' and s.get('category') != 'ads']
    research_band = [
        s for s in research_all
        if s['id'] != hero_id and s['id'] not in latest_ids
    ][:4]
    research_ids = {s['id'] for s in research_band} if not active_desk and not science_only else set()
    lesson_story = None if science_only or active_desk else pick_lesson(list(top_news) + list(sub_news))
    label_campus(campus_items)
    for story in campus_items:
        _stamp_campus(story)
    campus_slots = campus_slots_from(campus_items)
    campus_preview = campus_items[:3]
    campus_featured = pick_campus_feature(campus_items)
    week_board, week_is_current = campus_agenda(campus_items)
    campus_cover = None
    campus_cover_chosen = False
    if not active_desk and not science_only:
        chosen_campus = _cover_story(campus_items, settings.cover_campus_id)
        if chosen_campus:
            campus_cover = chosen_campus
            campus_cover_chosen = True
        else:
            campus_cover = campus_featured or (week_board[0] if week_board else None)
        if campus_cover:
            _picture_brief(campus_cover)
    campus_room_groups = [
        {**room, "stories": room["stories"][:4], "total": len(room["stories"])}
        for room in campus_rooms(campus_items)
    ]
    course_week = course_dossier(campus_items)
    if course_week and lesson_story:
        course_week["question"] = lesson_story
    recent_photos = (OccasionPhoto.query
                     .join(OccasionAlbum)
                     .filter(OccasionAlbum.is_published.is_(True))
                     .order_by(OccasionAlbum.event_date.desc(), OccasionPhoto.display_order.asc())
                     .limit(6)
                     .all())
    campus_front_groups = [
        {**group, 'stories': group['stories'][:4], 'total': len(group['stories'])}
        for group in campus_groups(campus_items)
    ]
    shown_on_lead = {story['id'] for story in picture_rail}
    if picture_lead:
        shown_on_lead.add(picture_lead['id'])
    if world_cover:
        shown_on_lead.add(world_cover['id'])
    if shown_on_lead:
        sub_news = [s for s in sub_news if s['id'] not in shown_on_lead]
    week_cut = week_start_utc().isoformat()
    campus_week_count = sum(1 for s in campus_items if (s.get('timestamp') or '') >= week_cut)
    tools_preview = [
        t.to_dict() for t in AITool.query.filter_by(is_published=True)
        .order_by(AITool.created_at.desc()).limit(4).all()
    ]

    desk_sections = []
    for entry in desk_nav:
        if active_desk and entry['key'] != active_desk:
            continue
        stories = [
            s for s in grouped[entry['key']]
            if s['id'] != hero_id and s['id'] not in latest_ids and s['id'] not in research_ids
        ]
        if not stories:
            continue
        desk_sections.append({
            **entry,
            'stories': stories if active_desk else stories[:4],
            'has_more': (not active_desk) and len(stories) > 4,
        })

    return render_template('magazine_view.html',
                           items=filtered_items,
                           top_news=top_news,
                           sub_news=sub_news,
                           sidebar=sidebar,
                           reels=reels,
                           ads=ads,
                           most_viewed=most_viewed,
                           settings=settings,
                           archive_data=archive_data,
                           current_filter=current_filter,
                           desk_nav=desk_nav,
                           desk_sections=desk_sections,
                           active_desk=active_desk,
                           science_only=science_only,
                           research_all=research_all,
                           research_band=research_band,
                           lesson_story=lesson_story,
                           campus_slots=campus_slots,
                           campus_preview=campus_preview,
                           campus_featured=campus_featured,
                           campus_front_groups=campus_front_groups,
                           week_board=week_board,
                           week_is_current=week_is_current,
                           campus_room_groups=campus_room_groups,
                           course_week=course_week,
                           recent_photos=recent_photos,
                           world_cover=world_cover,
                           picture_lead=picture_lead,
                           picture_rail=picture_rail,
                           campus_cover=campus_cover,
                           campus_cover_chosen=campus_cover_chosen,
                           world_cover_chosen=world_cover_chosen,
                           tools_preview=tools_preview,
                           campus_week_count=campus_week_count,
                           date=datetime.datetime.now().strftime("%Y-%m-%d"),
                           **edition_context(story_items))

@app.route('/campus')
def campus_weekly():
    """The department's week: university notices, student and faculty work, forums, and classroom questions."""
    lang_pref = get_lang_pref()
    if lang_pref is None:
        return _render_language_gate()

    rows = (NewsItem.query.filter_by(is_published=True, wing='campus')
            .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc()).all())
    campus_items = []
    for row in rows:
        story = assign_desk(row.to_dict())
        campus_items.append(story)
    campus_items = _v3_dedupe(campus_items)

    start = week_start_utc()
    questions = []
    noted = (NewsItem.query.filter(NewsItem.is_published.is_(True), NewsItem.timestamp >= start)
             .order_by(NewsItem.timestamp.desc()).all())
    for row in noted:
        if (row.wing or 'world') == 'campus':
            continue
        if not (row.lesson_ask or row.lesson_why):
            continue
        questions.append(assign_desk(row.to_dict()))

    label_campus(campus_items)
    for story in campus_items:
        _stamp_campus(story)
    week_board, week_is_current = campus_agenda(campus_items)
    rooms = campus_rooms(campus_items)
    course_week = course_dossier(campus_items)
    if course_week and questions:
        course_week["question"] = questions[0]
    term_sections = []
    for term in campus_terms(campus_items):
        term_sections.append({
            **term,
            "label_en": f"{_term_label(term['term'], False)} {term['year']}",
            "label_ar": f"فصل {_term_label(term['term'], True)} {term['year']}",
            "rooms": campus_rooms(term["stories"]) if term["current"] else [],
        })
    current_term, current_year = _current_term()
    current_rooms = next((term["rooms"] for term in term_sections if term["current"] and term["rooms"]), None)
    if current_rooms:
        rooms = current_rooms
        earlier_terms = [term for term in term_sections if not term["current"]]
    else:
        earlier_terms = []
        placed = False
        for term in term_sections:
            if term["current"]:
                term["rooms"] = rooms
                placed = True
        term_sections = [term for term in term_sections if term["current"]]
        if not placed:
            term_sections = [{
                "key": f"{current_term}-{current_year}",
                "current": True,
                "label_en": f"{_term_label(current_term, False)} {current_year}",
                "label_ar": f"فصل {_term_label(current_term, True)} {current_year}",
                "rooms": rooms,
                "stories": campus_items,
            }]
    recent_photos = (OccasionPhoto.query
                     .join(OccasionAlbum)
                     .filter(OccasionAlbum.is_published.is_(True))
                     .order_by(OccasionAlbum.event_date.desc(), OccasionPhoto.display_order.asc())
                     .limit(6)
                     .all())
    template = 'campus.html' if request.args.get('classic') else 'campus_v3.html'
    return render_template(
        template,
        campus_items=campus_items,
        campus_groups=campus_groups(campus_items),
        rooms=rooms,
        term_sections=term_sections,
        earlier_terms=earlier_terms,
        current_term_en=f"{_term_label(current_term, False)} {current_year}",
        current_term_ar=f"فصل {_term_label(current_term, True)} {current_year}",
        week_board=week_board,
        week_is_current=week_is_current,
        course_week=course_week,
        questions=questions[:7],
        recent_photos=recent_photos,
        week_label_en=start.strftime('%d %b'),
        week_label_ar=f"{start.day} {ARABIC_MONTHS[start.month]}",
        featured_projects=[i.to_dict() for i in ProjectIdea.query.filter_by(
            is_published=True, featured=True).order_by(ProjectIdea.sort_order.asc()).limit(3).all()],
        project_total=ProjectIdea.query.filter_by(is_published=True).count(),
        settings=MagazineSettings.get_settings(),
    )


@app.route('/campus/projects')
def campus_projects():
    """Recommended final-year project ideas for Computer Science students."""
    q = (request.args.get('q') or '').strip()
    area = request.args.get('area', 'all')
    difficulty = request.args.get('difficulty', 'all')
    track = request.args.get('track', 'all')

    query = ProjectIdea.query.filter_by(is_published=True)
    if area != 'all':
        query = query.filter_by(area=area)
    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)
    if track != 'all':
        query = query.filter_by(track=track)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            ProjectIdea.title_en.ilike(like), ProjectIdea.title_ar.ilike(like),
            ProjectIdea.summary_en.ilike(like), ProjectIdea.summary_ar.ilike(like),
            ProjectIdea.body_en.ilike(like), ProjectIdea.body_ar.ilike(like),
            ProjectIdea.skills.ilike(like), ProjectIdea.tools.ilike(like),
        ))
    ideas = query.order_by(ProjectIdea.featured.desc(), ProjectIdea.sort_order.asc(), ProjectIdea.title_en.asc()).all()

    counts = {'all': ProjectIdea.query.filter_by(is_published=True).count()}
    for key in PROJECT_AREAS:
        counts[key] = ProjectIdea.query.filter_by(area=key, is_published=True).count()
    track_counts = {'all': counts['all']}
    for key in PROJECT_TRACKS:
        track_counts[key] = ProjectIdea.query.filter_by(track=key, is_published=True).count()

    return render_template('campus_projects_v3.html',
                           ideas=[i.to_dict() for i in ideas],
                           counts=counts, areas=PROJECT_AREAS,
                           track_counts=track_counts, tracks=PROJECT_TRACKS, track=track,
                           q=q, area=area, difficulty=difficulty,
                           total=counts['all'],
                           settings=MagazineSettings.get_settings(),
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))


def _department_desk():
    return url_for('department_admin')


@app.route('/department')
@login_required
def department_admin():
    rows = (NewsItem.query.filter_by(wing='campus')
            .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc()).all())
    stories = label_campus([row.to_dict() for row in rows])
    buckets = {key: [] for key in CAMPUS_KINDS}
    for story in stories:
        key = story.get('campus_kind') or 'work'
        if key not in buckets:
            key = 'work'
        buckets[key].append(story)
    groups = [
        {'key': key, 'label_en': en, 'label_ar': ar, 'stories': buckets[key]}
        for key, en, ar in ordered_campus_kind_choices()
    ]
    albums = (OccasionAlbum.query
              .order_by(OccasionAlbum.year.desc(), OccasionAlbum.event_date.desc()).all())
    projects = (ProjectIdea.query
                .order_by(ProjectIdea.featured.desc(), ProjectIdea.sort_order.asc()).all())
    stats = {
        'published': sum(1 for s in stories if s.get('is_published')),
        'hidden': sum(1 for s in stories if not s.get('is_published')),
        'photos': sum(len(a.photos) for a in albums),
        'albums': len(albums),
        'projects': len(projects),
        'research': sum(1 for p in projects if (p.track or 'final_year') == 'research'),
        'competitions': sum(1 for p in projects if (p.track or 'final_year') == 'competition'),
    }
    return render_template('department.html', groups=groups, stats=stats,
                           albums=albums[:4], projects=[p.to_dict() for p in projects])


def _apply_project_form(idea):
    idea.title_en = (request.form.get('title_en') or '').strip()[:200]
    idea.title_ar = (request.form.get('title_ar') or '').strip()[:200]
    idea.summary_en = (request.form.get('summary_en') or '').strip()[:300]
    idea.summary_ar = (request.form.get('summary_ar') or '').strip()[:300]
    idea.body_en = (request.form.get('body_en') or '').strip()
    idea.body_ar = (request.form.get('body_ar') or '').strip()
    idea.area = request.form.get('area', 'agents')
    idea.track = request.form.get('track', 'final_year')
    idea.difficulty = request.form.get('difficulty', 'intermediate')
    idea.skills = request.form.get('skills', '')
    idea.tools = request.form.get('tools', '')
    idea.reference_title = request.form.get('reference_title', '')[:200]
    idea.reference_url = (request.form.get('reference_url') or '').strip()
    idea.reference_note_en = request.form.get('reference_note_en', '')[:300]
    idea.reference_note_ar = request.form.get('reference_note_ar', '')[:300]
    idea.featured = bool(request.form.get('featured'))
    idea.is_published = bool(request.form.get('is_published'))
    try:
        idea.sort_order = int(request.form.get('sort_order') or 0)
    except ValueError:
        idea.sort_order = 0


@app.route('/department/projects/new', methods=['GET', 'POST'])
@login_required
def add_project_idea():
    if request.method == 'POST':
        idea = ProjectIdea(title_en=(request.form.get('title_en') or '').strip()[:200])
        if not idea.title_en:
            flash('An English title is required.', 'error')
            return redirect(request.url)
        _apply_project_form(idea)
        db.session.add(idea)
        db.session.commit()
        flash('Project idea added.', 'success')
        return redirect(url_for('department_admin', _anchor='projects'))
    return render_template('project_idea_form.html', idea=None,
                           areas=PROJECT_AREAS, tracks=PROJECT_TRACKS)


@app.route('/department/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project_idea(project_id):
    idea = ProjectIdea.query.get_or_404(project_id)
    if request.method == 'POST':
        _apply_project_form(idea)
        db.session.commit()
        flash('Project idea updated.', 'success')
        return redirect(url_for('department_admin', _anchor='projects'))
    return render_template('project_idea_form.html', idea=idea.to_dict(),
                           areas=PROJECT_AREAS, tracks=PROJECT_TRACKS)


@app.route('/department/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project_idea(project_id):
    idea = ProjectIdea.query.get_or_404(project_id)
    db.session.delete(idea)
    db.session.commit()
    flash('Project idea removed.', 'success')
    return redirect(url_for('department_admin', _anchor='projects'))


@app.route('/api/department/reorder', methods=['POST'])
@login_required
def reorder_department():
    payload = request.get_json(silent=True) or {}
    groups = payload.get('groups') or {}
    order = 0
    for key, _en, _ar in ordered_campus_kind_choices():
        for item_id in groups.get(key) or []:
            item = NewsItem.query.get(item_id)
            if not item or (item.wing or '') != 'campus':
                continue
            item.campus_kind = key
            item.display_order = order
            order += 1
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/department/kind-order', methods=['POST'])
@login_required
def save_campus_kind_order():
    """The department desk decides which topic readers meet first."""
    payload = request.get_json(silent=True) or {}
    clean = []
    for key in payload.get('order') or []:
        if key in CAMPUS_KINDS and key not in clean:
            clean.append(key)
    for key in CAMPUS_KINDS:
        if key not in clean:
            clean.append(key)
    settings = MagazineSettings.get_settings()
    settings.campus_kind_order = ",".join(clean)
    db.session.commit()
    return jsonify({'status': 'success', 'order': clean})


@app.route('/campus/add', methods=['POST'])
@login_required
def add_campus_post():
    back = _department_desk()
    title = (request.form.get('title_en') or '').strip()
    kind = (request.form.get('campus_kind') or 'summary').strip()
    if kind not in CAMPUS_KINDS:
        kind = 'summary'
    summary = (request.form.get('summary_en') or '').strip()
    source = (request.form.get('source') or '').strip()
    url = _clip(request.form.get('url'), 500)
    image = ''
    video_id = None
    content_format = 'article'
    if url:
        found_id, is_video = detect_youtube(url)
        if is_video:
            details = fetch_youtube_details(url) or {}
            title = title or details.get('title') or ''
            summary = summary or details.get('summary') or ''
            source = source or details.get('source') or 'YouTube'
            image = details.get('image') or ''
            video_id = found_id
            content_format = 'video'
    if not title:
        flash('A title is required. A YouTube link can supply it.', 'error')
        return redirect(back)
    title, title_ar, summary_en, summary_ar, _body, _body_ar = ensure_bilingual_content(
        title_en=title,
        summary_en=summary,
        full_content_html=None,
        title_ar=(request.form.get('title_ar') or '').strip() or None,
    )
    shown = request.form.get('show') == '1' if request.form.get('show_choice') else True
    last = NewsItem.query.filter_by(wing='campus').order_by(NewsItem.display_order.desc()).first()
    db.session.add(NewsItem(
        title=title[:490],
        title_ar=(title_ar or '')[:490],
        summary=summary_en,
        summary_ar=summary_ar,
        source=_clip(source, 190),
        url=url,
        image=image,
        category='sidebar',
        article_type='external' if url else 'manual',
        content_format=content_format,
        video_id=video_id,
        is_published=shown,
        wing='campus',
        campus_kind=kind,
        event_on=_parse_day(request.form.get('event_on')),
        place=_clip(request.form.get('place'), 160) or '',
        course=_clip(request.form.get('course'), 120) or '',
        display_order=((last.display_order or 0) + 1) if last else 0,
    ))
    db.session.commit()
    flash('Added to the department week.' if shown else 'Saved, and kept off the department page.', 'success')
    return redirect(back)


@app.route('/campus/toggle/<item_id>', methods=['POST'])
@login_required
def toggle_campus_post(item_id):
    item = NewsItem.query.get_or_404(item_id)
    if (item.wing or '') != 'campus':
        abort(404)
    item.is_published = not bool(item.is_published)
    db.session.commit()
    flash('Shown on the department page.' if item.is_published else 'Hidden from the department page.', 'success')
    return redirect(_department_desk())


@app.route('/campus/remove/<item_id>', methods=['POST'])
@login_required
def remove_campus_post(item_id):
    item = NewsItem.query.get_or_404(item_id)
    if (item.wing or '') != 'campus':
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash('Removed from the department week.', 'success')
    return redirect(_department_desk())


PHOTO_TERMS = (('fall', 'Fall', 'الخريف'), ('spring', 'Spring', 'الربيع'))
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def _term_label(term, arabic):
    for key, en, ar in PHOTO_TERMS:
        if key == term:
            return ar if arabic else en
    return term


def _current_term():
    today = datetime.date.today()
    if today.month >= 9 or today.month == 1:
        year = today.year if today.month >= 9 else today.year - 1
        return 'fall', year
    return 'spring', today.year


def _photo_date_label(day, arabic):
    if not day:
        return ''
    if arabic:
        return f"{day.day} {ARABIC_MONTHS[day.month]} {day.year}"
    return day.strftime('%d %b %Y')


def _photo_semesters(albums, arabic):
    groups = {}
    for album in albums:
        key = f"{album.year}-{album.term}"
        groups.setdefault(key, {
            'key': key,
            'year': album.year,
            'term': album.term,
            'label': f"{_term_label(album.term, arabic)} {album.year}",
            'albums': [],
        })
        groups[key]['albums'].append(album)
    ordered = sorted(
        groups.values(),
        key=lambda group: (group['year'], 1 if group['term'] == 'fall' else 0),
        reverse=True,
    )
    for group in ordered:
        group['albums'].sort(key=lambda album: album.event_date or datetime.date.min, reverse=True)
    return ordered


def _save_occasion_image(file_storage, prefix='occasion'):
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in PHOTO_EXTS:
        return None
    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return url_for('static', filename=f'uploads/images/{filename}')


def _unlink_occasion_image(url_path):
    if not url_path or '/static/uploads/images/' not in url_path:
        return
    name = os.path.basename(url_path.split('?', 1)[0])
    if not (name.startswith('occasion_') or name.startswith('newsphoto_')):
        return
    path = os.path.join(app.config['UPLOAD_FOLDER'], 'images', name)
    if os.path.isfile(path):
        os.remove(path)


def _read_occasion_form():
    term = (request.form.get('term') or 'fall').strip()
    if term not in ('fall', 'spring'):
        term = 'fall'
    title = _clip(request.form.get('title'), 190)
    title_ar = _clip(request.form.get('title_ar'), 190)
    note = _clip(request.form.get('note'), 500)
    note_ar = _clip(request.form.get('note_ar'), 500)
    raw_date = (request.form.get('event_date') or '').strip()
    try:
        event_date = datetime.date.fromisoformat(raw_date)
    except ValueError:
        event_date = datetime.date.today()
    try:
        year = int(request.form.get('year') or event_date.year)
    except (TypeError, ValueError):
        year = event_date.year
    year = min(2100, max(2000, year))
    return term, year, title, title_ar, note, note_ar, event_date


def _attach_photos(album, start_order=0):
    files = [item for item in request.files.getlist('photos') if item and item.filename]
    titles = request.form.getlist('photo_title')
    titles_ar = request.form.getlist('photo_title_ar')
    captions = request.form.getlist('photo_caption')
    captions_ar = request.form.getlist('photo_caption_ar')
    saved = 0
    for index, upload in enumerate(files):
        path = _save_occasion_image(upload)
        if not path:
            continue
        db.session.add(OccasionPhoto(
            album_id=album.id,
            image=path,
            title=_clip(titles[index] if index < len(titles) else '', 180),
            title_ar=_clip(titles_ar[index] if index < len(titles_ar) else '', 180),
            caption=_clip(captions[index] if index < len(captions) else '', 400),
            caption_ar=_clip(captions_ar[index] if index < len(captions_ar) else '', 400),
            display_order=start_order + saved,
        ))
        saved += 1
    return saved


@app.route('/department/photos')
@login_required
def photo_archive_admin():
    albums = OccasionAlbum.query.order_by(OccasionAlbum.year.desc(), OccasionAlbum.event_date.desc()).all()
    term, year = _current_term()
    return render_template(
        'photos_admin.html',
        semesters=_photo_semesters(albums, get_admin_lang() == 'ar'),
        this_term=term,
        this_year=year,
        today=datetime.date.today().isoformat(),
    )


@app.route('/department/photos', methods=['POST'])
@login_required
def add_occasion_photos():
    term, year, title, title_ar, note, note_ar, event_date = _read_occasion_form()
    if not title and not title_ar:
        flash(admin_text(get_admin_lang(), 'ph_need_name'), 'error')
        return redirect(url_for('photo_archive_admin'))
    album = OccasionAlbum(
        term=term,
        year=year,
        title=title,
        title_ar=title_ar,
        note=note,
        note_ar=note_ar,
        event_date=event_date,
        is_published=request.form.get('show') == '1',
    )
    db.session.add(album)
    db.session.flush()
    saved = _attach_photos(album)
    if saved == 0:
        db.session.rollback()
        flash(admin_text(get_admin_lang(), 'ph_none'), 'error')
        return redirect(url_for('photo_archive_admin'))
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'ph_saved'), 'success')
    return redirect(url_for('photo_archive_admin'))


@app.route('/department/photos/<album_id>/add', methods=['POST'])
@login_required
def add_photos_to_album(album_id):
    album = OccasionAlbum.query.get_or_404(album_id)
    last = max((photo.display_order or 0) for photo in album.photos) if album.photos else -1
    saved = _attach_photos(album, start_order=last + 1)
    if saved == 0:
        flash(admin_text(get_admin_lang(), 'ph_none'), 'error')
    else:
        db.session.commit()
        flash(admin_text(get_admin_lang(), 'ph_saved'), 'success')
    return redirect(url_for('photo_archive_admin') + f'#album-{album.id}')


@app.route('/department/photos/photo/<photo_id>', methods=['POST'])
@login_required
def update_occasion_photo(photo_id):
    photo = OccasionPhoto.query.get_or_404(photo_id)
    photo.title = _clip(request.form.get('title'), 180)
    photo.title_ar = _clip(request.form.get('title_ar'), 180)
    photo.caption = _clip(request.form.get('caption'), 400)
    photo.caption_ar = _clip(request.form.get('caption_ar'), 400)
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'ph_saved'), 'success')
    return redirect(url_for('photo_archive_admin') + f'#album-{photo.album_id}')


@app.route('/department/photos/photo/<photo_id>/remove', methods=['POST'])
@login_required
def remove_occasion_photo(photo_id):
    photo = OccasionPhoto.query.get_or_404(photo_id)
    album_id = photo.album_id
    _unlink_occasion_image(photo.image)
    db.session.delete(photo)
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'ph_removed'), 'success')
    return redirect(url_for('photo_archive_admin') + f'#album-{album_id}')


@app.route('/department/photos/<album_id>/remove', methods=['POST'])
@login_required
def remove_occasion_album(album_id):
    album = OccasionAlbum.query.get_or_404(album_id)
    for photo in list(album.photos):
        _unlink_occasion_image(photo.image)
    db.session.delete(album)
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'ph_removed'), 'success')
    return redirect(url_for('photo_archive_admin'))


@app.route('/department/photos/<album_id>/toggle', methods=['POST'])
@login_required
def toggle_occasion_album(album_id):
    album = OccasionAlbum.query.get_or_404(album_id)
    album.is_published = not bool(album.is_published)
    db.session.commit()
    key = 'ph_now_shown' if album.is_published else 'ph_now_hidden'
    flash(admin_text(get_admin_lang(), key), 'success')
    return redirect(url_for('photo_archive_admin') + f'#album-{album.id}')


@app.route('/campus/photos')
def campus_photos():
    """The department photo archive: semester, then occasion, then the pictures."""
    if get_lang_pref() is None:
        return _render_language_gate()
    arabic = get_lang_pref() == 'ar'
    albums = (OccasionAlbum.query.filter_by(is_published=True)
              .order_by(OccasionAlbum.year.desc(), OccasionAlbum.event_date.desc())
              .all())
    albums = [album for album in albums if album.photos]
    return render_template(
        'photos.html',
        semesters=_photo_semesters(albums, arabic),
        settings=MagazineSettings.get_settings(),
    )


def _news_photo_frames(include_hidden=False):
    """Pictures already on saved world stories, plus pictures added by hand."""
    frames = []
    rows = (NewsItem.query.filter(
                NewsItem.wing != 'campus',
                NewsItem.is_published.is_(True),
                NewsItem.image.isnot(None),
                NewsItem.image != '',
            )
            .order_by(NewsItem.timestamp.desc())
            .all())
    for row in rows:
        story = assign_desk(row.to_dict())
        frames.append({
            'id': row.id,
            'kind': 'story',
            'image': row.image,
            'title': row.title or '',
            'title_ar': row.title_ar or '',
            'caption': plain_dek(row.summary or '')[:240],
            'caption_ar': plain_dek(row.summary_ar or '')[:240],
            'source_url': row.url or '',
            'story_url': url_for('magazine_detail', item_id=row.id),
            'when': row.published_at or row.timestamp,
            'topic': story['desk'],
            'topic_en': story['desk_en'],
            'topic_ar': story['desk_ar'],
            'hidden': False,
        })
    query = NewsPhoto.query
    if not include_hidden:
        query = query.filter_by(is_published=True)
    for photo in query.all():
        desk = DESK_BY_KEY.get(photo.topic or '', BRIEFING_DESK)
        when = None
        if photo.event_date:
            when = datetime.datetime.combine(photo.event_date, datetime.time())
        frames.append({
            'id': photo.id,
            'kind': 'added',
            'image': photo.image,
            'title': photo.title or '',
            'title_ar': photo.title_ar or '',
            'caption': photo.caption or '',
            'caption_ar': photo.caption_ar or '',
            'source_url': photo.source_url or '',
            'story_url': '',
            'when': when or photo.created_at,
            'topic': desk[0],
            'topic_en': desk[1],
            'topic_ar': desk[2],
            'hidden': not bool(photo.is_published),
        })
    frames.sort(key=lambda frame: frame['when'] or datetime.datetime.min, reverse=True)
    return frames


def _news_photo_desks(frames):
    counts = {}
    for frame in frames:
        counts[frame['topic']] = counts.get(frame['topic'], 0) + 1
    desks = []
    for key, en, ar, _words in list(NEWS_DESKS) + [BRIEFING_DESK]:
        if counts.get(key):
            desks.append({'key': key, 'en': en, 'ar': ar, 'count': counts[key]})
    return desks


def _group_news_photos(frames, arabic):
    groups = {}
    for frame in frames:
        when = frame['when']
        if when is None:
            key, label, sort = 'undated', ('بدون تاريخ' if arabic else 'Undated'), (0, 0)
        else:
            key = f'{when.year}-{when.month:02d}'
            label = f'{ARABIC_MONTHS[when.month]} {when.year}' if arabic else when.strftime('%B %Y')
            sort = (when.year, when.month)
        bucket = groups.setdefault(key, {'key': key, 'label': label, 'sort': sort, 'frames': []})
        bucket['frames'].append(frame)
    return sorted(groups.values(), key=lambda group: group['sort'], reverse=True)


def _filter_news_topic(frames):
    topic = (request.args.get('topic') or '').strip()
    if topic not in DESK_BY_KEY:
        topic = ''
    if topic:
        frames = [frame for frame in frames if frame['topic'] == topic]
    return frames, topic


@app.route('/news/photos')
def news_photos():
    """Pictures from the world news archive, browsed by date and by topic."""
    if get_lang_pref() is None:
        return _render_language_gate()
    arabic = get_lang_pref() == 'ar'
    frames = _news_photo_frames()
    desks = _news_photo_desks(frames)
    frames, topic = _filter_news_topic(frames)
    return render_template(
        'news_photos.html',
        months=_group_news_photos(frames, arabic),
        desks=desks,
        topic=topic,
        settings=MagazineSettings.get_settings(),
    )


@app.route('/desk/world/photos')
@login_required
def news_photos_admin():
    frames = _news_photo_frames(include_hidden=True)
    desks = _news_photo_desks(frames)
    frames, topic = _filter_news_topic(frames)
    return render_template(
        'news_photos_admin.html',
        months=_group_news_photos(frames, get_admin_lang() == 'ar'),
        desks=desks,
        topic=topic,
        today=datetime.date.today().isoformat(),
    )


@app.route('/desk/world/photos', methods=['POST'])
@login_required
def add_news_photo():
    title = _clip(request.form.get('title'), 190)
    title_ar = _clip(request.form.get('title_ar'), 190)
    upload = request.files.get('photo')
    image = _save_occasion_image(upload, prefix='newsphoto')
    if not image or not (title or title_ar):
        if image:
            _unlink_occasion_image(image)
        flash(admin_text(get_admin_lang(), 'np_need'), 'error')
        return redirect(url_for('news_photos_admin'))
    topic = (request.form.get('topic') or 'ai').strip()
    if topic not in DESK_BY_KEY:
        topic = 'ai'
    raw_date = (request.form.get('event_date') or '').strip()
    try:
        event_date = datetime.date.fromisoformat(raw_date)
    except ValueError:
        event_date = datetime.date.today()
    db.session.add(NewsPhoto(
        image=image,
        title=title,
        title_ar=title_ar,
        caption=_clip(request.form.get('caption'), 400),
        caption_ar=_clip(request.form.get('caption_ar'), 400),
        source_url=_clip(request.form.get('source_url'), 500),
        topic=topic,
        event_date=event_date,
        is_published=request.form.get('show') == '1',
    ))
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'np_saved'), 'success')
    return redirect(url_for('news_photos_admin'))


@app.route('/desk/world/photos/<photo_id>/remove', methods=['POST'])
@login_required
def remove_news_photo(photo_id):
    photo = NewsPhoto.query.get_or_404(photo_id)
    _unlink_occasion_image(photo.image)
    db.session.delete(photo)
    db.session.commit()
    flash(admin_text(get_admin_lang(), 'np_removed'), 'success')
    return redirect(url_for('news_photos_admin'))


@app.route('/classroom_note', methods=['POST'])
@login_required
def classroom_note():
    """Write today's student note from the lead world story. Does not invent a news item."""
    lead = (NewsItem.query.filter(
                NewsItem.is_published.is_(True),
                NewsItem.wing != 'campus',
                NewsItem.category.in_(('top', 'second')),
            )
            .order_by(NewsItem.display_order.asc(), NewsItem.timestamp.desc())
            .first())
    if lead is None:
        flash('Publish a world story first.', 'error')
        return redirect(url_for('dashboard'))
    if write_classroom_note(lead):
        db.session.commit()
        flash(f'Classroom note written for: {lead.title}', 'success')
    else:
        flash('The classroom note could not be written. Check the AI model key.', 'error')
    return redirect(url_for('dashboard'))


@app.route('/archive')
@login_required
def archive_page():
    desk = request.args.get('desk', 'world')
    if desk not in ('world', 'campus'):
        desk = 'world'
    all_items = NewsItem.query.order_by(NewsItem.timestamp.desc()).all()
    if desk == 'campus':
        all_items = [i for i in all_items if (i.wing or '') == 'campus']
    else:
        all_items = [i for i in all_items if (i.wing or '') != 'campus']
    
    # Build Hierarchy: { Year: { Month: [Items] } }
    archive_tree = defaultdict(lambda: defaultdict(list))
    for i in all_items:
        if i.timestamp:
            y = i.timestamp.year
            m = i.timestamp.month
            archive_tree[y][m].append(i) # Keep DB objects for template logic
    
    # Format for template
    archive_data = []
    for year in sorted(archive_tree.keys(), reverse=True):
        months_data = []
        year_total = 0
        for month_num in sorted(archive_tree[year].keys(), reverse=True):
            posts = archive_tree[year][month_num]
            count = len(posts)
            year_total += count
            months_data.append({
                'name': calendar.month_name[month_num],
                'name_ar': ARABIC_MONTHS[month_num],
                'posts': posts,
                'count': count
            })
        archive_data.append({
            'year': year,
            'months': months_data,
            'count': year_total
        })
        
    return render_template('archive.html', archive_data=archive_data, desk=desk)

@app.route('/api/keys/save', methods=['POST'])
@login_required
def save_api_keys():
    try:
        data = request.json or {}
        fields = data.get('fields') or {}
        if not isinstance(fields, dict) or not fields:
            return jsonify({'status': 'error', 'message': 'No fields provided.'}), 400

        known_names = {f['name'] for p in API_KEY_PROVIDERS for f in p['fields']}
        settings = MagazineSettings.get_settings()
        custom_names = settings.custom_api_key_names_list
        saved = []

        for name, value in fields.items():
            name = (name or '').strip().upper()
            value = (value if isinstance(value, str) else '')
            if not _ENV_NAME_RE.match(name):
                return jsonify({'status': 'error', 'message': f'"{name}" is not a valid key name.'}), 400
            if name in _RESERVED_ENV_NAMES:
                return jsonify({'status': 'error', 'message': f'"{name}" is reserved and cannot be edited here.'}), 400
            if '\n' in value or '\r' in value:
                return jsonify({'status': 'error', 'message': 'Key value cannot contain line breaks.'}), 400
            if not value.strip():
                continue  # blank = leave unchanged

            set_env_var(name, value.strip())
            saved.append(name)

            if name not in known_names and name not in custom_names:
                custom_names.append(name)

        settings.custom_api_key_names = json.dumps(custom_names)
        db.session.commit()

        if not saved:
            return jsonify({'status': 'error', 'message': 'Nothing to save — all fields were blank.'}), 400
        return jsonify({'status': 'success', 'saved': saved})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/keys/remove', methods=['POST'])
@login_required
def remove_api_keys():
    try:
        data = request.json or {}
        names = data.get('names') or []
        if not isinstance(names, list) or not names:
            return jsonify({'status': 'error', 'message': 'No keys specified.'}), 400

        settings = MagazineSettings.get_settings()
        custom_names = settings.custom_api_key_names_list

        for name in names:
            name = (name or '').strip().upper()
            if not name or name in _RESERVED_ENV_NAMES:
                continue
            remove_env_var(name)
            if name in custom_names:
                custom_names.remove(name)

        settings.custom_api_key_names = json.dumps(custom_names)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/ai/routing', methods=['POST'])
@login_required
def save_ai_routing():
    """Save provider keys, chosen models, and which model handles each task."""
    from agent.skills.content_processor.providers import (
        PROVIDERS, TASKS, load_routing, save_routing, slug_id,
    )
    try:
        data = request.json or {}
        routing = load_routing()
        known = {provider["id"]: provider for provider in PROVIDERS}

        cleaned_models = {}
        for provider_id, names in (data.get("models") or {}).items():
            if not isinstance(names, list):
                continue
            chosen = []
            for name in names:
                name = (name or "").strip()
                if name and len(name) <= 80 and name not in chosen:
                    chosen.append(name)
            if chosen:
                cleaned_models[provider_id] = chosen[:12]

        task_ids = {task["id"] for task in TASKS}
        cleaned_tasks = {}
        for task_id, choice in (data.get("tasks") or {}).items():
            if task_id not in task_ids or not isinstance(choice, dict):
                continue
            provider_id = (choice.get("provider") or "").strip()
            model = (choice.get("model") or "").strip()[:80]
            if provider_id and model:
                cleaned_tasks[task_id] = {"provider": provider_id, "model": model}

        remove_ids = set(data.get("remove_custom") or [])
        custom = [row for row in (routing.get("custom") or []) if row.get("id") not in remove_ids]
        for row in data.get("custom") or []:
            if not isinstance(row, dict):
                continue
            label = (row.get("label") or "").strip()[:40]
            base_url = (row.get("base_url") or "").strip()
            if not label or not (base_url.startswith("https://") or base_url.startswith("http://")):
                continue
            custom_id = (row.get("id") or "").strip()
            if not custom_id.startswith("custom-"):
                custom_id = slug_id(label)
            key_env = f"CUSTOM_AI_{custom_id.upper().replace('-', '_')}_KEY"
            if key_env in _RESERVED_ENV_NAMES or not _ENV_NAME_RE.match(key_env):
                continue
            model_names = []
            for name in row.get("models") or []:
                name = (name or "").strip()
                if name and name not in model_names:
                    model_names.append(name[:80])
            entry = {
                "id": custom_id,
                "label": label,
                "base_url": base_url[:200],
                "key_env": key_env,
                "models": model_names[:12],
            }
            current = next((item for item in custom if item.get("id") == custom_id), None)
            if current:
                current.update(entry)
            else:
                custom.append(entry)
            secret = row.get("key") if isinstance(row.get("key"), str) else ""
            if secret.strip() and "\n" not in secret and "\r" not in secret:
                set_env_var(key_env, secret.strip())
            if model_names:
                cleaned_models[custom_id] = model_names[:12]

        for provider_id, provider in known.items():
            secret = (data.get("keys") or {}).get(provider_id)
            if isinstance(secret, str) and secret.strip() and "\n" not in secret and "\r" not in secret:
                set_env_var(provider["key_env"], secret.strip())

        routing["models"] = cleaned_models
        routing["tasks"] = cleaned_tasks
        routing["custom"] = custom
        save_routing(routing)
        return jsonify({"status": "success"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500

@app.route('/api/comments/analyze/<item_id>', methods=['POST'])
@login_required
def analyze_item_comments(item_id):
    item = NewsItem.query.get_or_404(item_id)
    if not content_processor or not hasattr(content_processor, "analyze_comments"):
        return jsonify({"status": "error", "message": "Comment analysis is not available."}), 500
    comments = [{"author": comment.author, "content": comment.content} for comment in item.comments]
    result = content_processor.analyze_comments(comments, item.title)
    if not result:
        return jsonify({
            "status": "error",
            "message": "Assign a model to comment analysis in Settings → AI Models, and save its API key.",
        }), 400
    return jsonify({"status": "success", "analysis": result})

def _accepted_cover_id(item_id, campus):
    """Keep a cover pin only when it is a published story from that half."""
    item_id = (item_id or "").strip()
    if not item_id:
        return ""
    item = NewsItem.query.get(item_id)
    if not item or not item.is_published:
        return ""
    is_campus = (item.wing or "") == "campus"
    if campus != is_campus:
        return ""
    return item.id


def _cover_choices(campus, selected_id):
    query = NewsItem.query.filter(NewsItem.is_published.is_(True))
    if campus:
        query = query.filter(NewsItem.wing == "campus")
    else:
        query = query.filter(NewsItem.wing != "campus")
    rows = query.order_by(NewsItem.timestamp.desc()).limit(24).all()
    if selected_id and all(row.id != selected_id for row in rows):
        extra = NewsItem.query.get(selected_id)
        if extra and extra.is_published:
            rows.insert(0, extra)
    return rows


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    settings = MagazineSettings.get_settings()

    if request.method == 'POST':
        try:
            settings.magazine_title = request.form.get('magazine_title') or settings.magazine_title
            settings.version = request.form.get('version', '')
            settings.language_mode = request.form.get('language_mode') # New Setting
            settings.theme = request.form.get('theme') # Theme Setting
            
            # Custom Colors Logic
            if request.form.get('reset_colors'):
                settings.custom_text_color = None
                settings.custom_accent_color = None
                
                # Reset Tag Colors
                settings.color_h1 = None
                settings.color_h2 = None
                settings.color_h3 = None
                settings.color_h4 = None
                settings.color_h5 = None
                settings.color_h6 = None
                settings.color_p = None
                settings.color_li = None
            else:
                t_color = request.form.get('custom_text_color')
                a_color = request.form.get('custom_accent_color')
                settings.custom_text_color = t_color
                settings.custom_accent_color = a_color
                
                # Save Tag Colors
                settings.color_h1 = request.form.get('color_h1')
                settings.color_h2 = request.form.get('color_h2')
                settings.color_h3 = request.form.get('color_h3')
                settings.color_h4 = request.form.get('color_h4')
                settings.color_h5 = request.form.get('color_h5')
                settings.color_h6 = request.form.get('color_h6')
                settings.color_p  = request.form.get('color_p')
                settings.color_li = request.form.get('color_li')

            # Section Titles
            settings.section_title_top = request.form.get('section_title_top', '')
            settings.section_title_latest = request.form.get('section_title_latest', '')
            settings.section_title_trending = request.form.get('section_title_trending', '')
            settings.section_title_archives = request.form.get('section_title_archives', '')
            settings.section_title_ads = request.form.get('section_title_ads', '')
            settings.section_title_top_ar = request.form.get('section_title_top_ar', '')
            settings.section_title_latest_ar = request.form.get('section_title_latest_ar', '')
            settings.section_title_trending_ar = request.form.get('section_title_trending_ar', '')
            settings.section_title_archives_ar = request.form.get('section_title_archives_ar', '')
            settings.section_title_ads_ar = request.form.get('section_title_ads_ar', '')
            settings.reels_enabled = bool(request.form.get('reels_enabled'))
            settings.section_title_reels = request.form.get('section_title_reels', '')
            settings.section_title_reels_ar = request.form.get('section_title_reels_ar', '')
            try:
                settings.reels_display_limit = max(1, min(12, int(request.form.get('reels_display_limit', 4))))
            except (TypeError, ValueError):
                settings.reels_display_limit = 4
            if "cover_world_id" in request.form:
                settings.cover_world_id = _accepted_cover_id(request.form.get("cover_world_id"), campus=False)
            if "cover_campus_id" in request.form:
                settings.cover_campus_id = _accepted_cover_id(request.form.get("cover_campus_id"), campus=True)

            settings.author_name = request.form.get('author_name', '')
            settings.author_bio = request.form.get('author_bio', '')
            settings.author_name_ar = request.form.get('author_name_ar', '')
            settings.author_bio_ar = request.form.get('author_bio_ar', '')
            settings.author_phone = request.form.get('author_phone', '')
            settings.author_email = request.form.get('author_email', '')
            settings.author_address = request.form.get('author_address', '')
            settings.author_workplace = request.form.get('author_workplace', '')

            settings.social_twitter = request.form.get('social_twitter', '')
            settings.social_linkedin = request.form.get('social_linkedin', '')
            settings.social_facebook = request.form.get('social_facebook', '')
            settings.social_instagram = request.form.get('social_instagram', '')
            
            # File Uploads (Logo)
            logo = request.files.get('logo')
            if logo and logo.filename and allowed_file(logo.filename, {'png', 'jpg', 'jpeg'}):
                filename = secure_filename(f"logo_{uuid.uuid4().hex}_{logo.filename}")
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                settings.logo_path = f"/static/uploads/images/{filename}"

            # File Uploads (Author Image)
            pfp = request.files.get('author_image')
            if pfp and pfp.filename and allowed_file(pfp.filename, {'png', 'jpg', 'jpeg'}):
                filename = secure_filename(f"author_{uuid.uuid4().hex}_{pfp.filename}")
                pfp.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                settings.author_image = f"/static/uploads/images/{filename}"

            # Enhanced: Author Intro
            settings.author_intro = request.form.get('author_intro', '')
            settings.author_intro_ar = request.form.get('author_intro_ar', '')

            # Enhanced: CV Upload
            cv_file = request.files.get('author_cv')
            if cv_file and cv_file.filename:
                # Ensure docs folder exists
                docs_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'docs')
                os.makedirs(docs_dir, exist_ok=True)
                
                ext = cv_file.filename.rsplit('.', 1)[1].lower()
                if ext in {'pdf', 'doc', 'docx'}:
                    filename = secure_filename(f"cv_{uuid.uuid4().hex}.{ext}")
                    cv_file.save(os.path.join(docs_dir, filename))
                    settings.author_cv = f"/static/uploads/docs/{filename}"

            # Enhanced: Gallery Logic (Update & Add)
            # 1. Process Existing Items
            new_gallery_list = []
            
            # Get lists from form (using getlist for multiple inputs with same name)
            existing_paths = request.form.getlist('existing_gallery_paths')
            titles = request.form.getlist('gallery_titles')
            descs = request.form.getlist('gallery_descs')
            deleted_items = request.form.getlist('delete_gallery_items') # check values
            
            # Reconstruct list from form data
            if existing_paths:
                for i, path in enumerate(existing_paths):
                    # Check if this specific item is marked for deletion
                    # The delete checkbox value should be the path itself or index
                    if path not in deleted_items:
                        title = titles[i] if i < len(titles) else ""
                        desc = descs[i] if i < len(descs) else ""
                        new_gallery_list.append({
                            'path': path, 
                            'title': title, 
                            'desc': desc
                        })

            # 2. Add New Uploads
            gallery_files = request.files.getlist('gallery_images')
            if gallery_files:
                for g_file in gallery_files:
                    if g_file and g_file.filename and allowed_file(g_file.filename, {'png', 'jpg', 'jpeg'}):
                        filename = secure_filename(f"gallery_{uuid.uuid4().hex}_{g_file.filename}")
                        g_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', filename))
                        # Append new item (empty title/desc initially)
                        new_gallery_list.append({
                            'path': f"/static/uploads/images/{filename}",
                            'title': '',
                            'desc': ''
                        })
            
            settings.author_gallery = json.dumps(new_gallery_list)

            db.session.commit()
            flash("Settings updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating settings: {e}", "error")
            
        return redirect(url_for('settings_page'))
        
    providers_status = []
    for p in API_KEY_PROVIDERS:
        field_status = []
        for f in p['fields']:
            val = os.environ.get(f['name'], '')
            field_status.append({**f, 'configured': bool(val.strip()), 'masked': _mask_secret(val)})
        providers_status.append({**p, 'fields': field_status,
                                 'all_configured': all(fs['configured'] for fs in field_status if not fs.get('optional'))})

    custom_api_keys = [
        {'name': n, 'configured': bool(os.environ.get(n, '').strip()), 'masked': _mask_secret(os.environ.get(n, ''))}
        for n in settings.custom_api_key_names_list
    ]

    from agent.skills.content_processor.providers import public_status
    return render_template('settings.html', settings=settings,
                           api_providers=providers_status, custom_api_keys=custom_api_keys,
                           ai_desk=public_status(),
                           cover_world=_cover_choices(False, settings.cover_world_id),
                           cover_campus=_cover_choices(True, settings.cover_campus_id))

@app.route('/save_search_result', methods=['POST'])
@login_required
def save_search_result():
    try:
        title = request.form.get('title')
        url = request.form.get('url')
        snippet = request.form.get('snippet')
        ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        def back_to_search():
            ref = request.referrer or ""
            parsed = urlparse(ref)
            same_host = not parsed.netloc or parsed.netloc == request.host
            if same_host and parsed.path.startswith("/search"):
                return ref
            return url_for("search_page")

        existing = NewsItem.query.filter(NewsItem.url == url).first() if url else None
        if existing:
            edit_url = url_for('edit_news', item_id=existing.id)
            if ajax:
                return jsonify({
                    'status': 'success', 'already': True,
                    'message': 'Already in the magazine.',
                    'id': existing.id, 'edit_url': edit_url,
                })
            flash(admin_text(get_admin_lang(), 'story_saved'), "success")
            return redirect(edit_url)

        # Translate ONCE, right now, at save time (title + summary; no full body
        # to translate yet since search results are just a headline + snippet —
        # readers click through to the original source for the full story).
        title, title_ar, summary_en, summary_ar, _en_body, _ar_body = ensure_bilingual_content(
            title_en=title,
            summary_en=snippet,
            full_content_html=None,
        )

        # Skill: Image (Fallback if not provided)
        image_url = request.form.get('image')
        if not image_url and media_handler:
            image_url = media_handler.get_image(url)

        # Video detection: trust what the search result already told us
        # (YouTube results carry content_format/video_id), and fall back to
        # sniffing the URL for anything that slipped through.
        content_format = request.form.get('content_format') or 'article'
        video_id = request.form.get('video_id') or None
        if content_format != 'video' or not video_id:
            detected_id, is_yt = detect_youtube(url)
            if is_yt:
                content_format = 'video'
                video_id = detected_id

        new_item = NewsItem(
            title=title,
            title_ar=title_ar,
            source=request.form.get('source'),
            url=url,
            summary=summary_en,
            summary_ar=summary_ar,
            full_content="",
            image=image_url,
            category="sidebar",
            article_type='external',  # always a real external link -> "visit source" CTA shows
            content_format=content_format,
            video_id=video_id,
        )

        db.session.add(new_item)
        db.session.commit()
        edit_url = url_for('edit_news', item_id=new_item.id)
        if ajax:
            return jsonify({'status': 'success', 'message': 'Added.', 'id': new_item.id, 'edit_url': edit_url})
        flash(admin_text(get_admin_lang(), 'story_saved'), "success")
        return redirect(edit_url)
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        flash(f"Error saving search result: {e}", "error")
        return redirect(url_for('search_page'))

# Initialize DB (Safe)
with app.app_context():
    try:
        db.create_all()
        # Migration: Check for article_type column
        try:
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('news_items')]
            if 'article_type' not in columns:
                print("⚠️  'article_type' column missing. Attempting migration...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE news_items ADD COLUMN article_type VARCHAR(20) DEFAULT 'manual'"))
                    conn.commit()
                print("✅ Migration successful: Added 'article_type' column.")
            if 'views' not in columns:
                print("⚠️  'views' column missing. Attempting migration...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE news_items ADD COLUMN views INTEGER DEFAULT 0"))
                    conn.commit()
                print("✅ Migration successful: Added 'views' column.")
            if 'topic' not in columns:
                print("⚠️  'topic' column missing. Attempting migration...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE news_items ADD COLUMN topic VARCHAR(30) DEFAULT ''"))
                    conn.commit()
                print("✅ Migration successful: Added 'topic' column.")
            if 'published_at' not in columns:
                print("⚠️  'published_at' column missing. Attempting migration...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE news_items ADD COLUMN published_at DATETIME"))
                    conn.commit()
                print("✅ Migration successful: Added 'published_at' column.")
            extra_news_columns = {
                'wing': "VARCHAR(20) DEFAULT 'world'",
                'campus_kind': "VARCHAR(20) DEFAULT ''",
                'lesson_why': "TEXT DEFAULT ''",
                'lesson_why_ar': "TEXT DEFAULT ''",
                'lesson_term': "VARCHAR(160) DEFAULT ''",
                'lesson_term_ar': "VARCHAR(160) DEFAULT ''",
                'lesson_gloss': "TEXT DEFAULT ''",
                'lesson_gloss_ar': "TEXT DEFAULT ''",
                'lesson_ask': "TEXT DEFAULT ''",
                'lesson_ask_ar': "TEXT DEFAULT ''",
                'event_on': "DATE",
                'place': "VARCHAR(160) DEFAULT ''",
                'course': "VARCHAR(120) DEFAULT ''",
            }
            for col, typedef in extra_news_columns.items():
                if col not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(db.text(f"ALTER TABLE news_items ADD COLUMN {col} {typedef}"))
                        conn.commit()
                    columns.append(col)
            for row in NewsItem.query.filter((NewsItem.wing.is_(None)) | (NewsItem.wing == '') | (NewsItem.wing == 'world')).all():
                if classify_wing(row.source, row.title, row.summary) == 'research':
                    row.wing = 'research'
            db.session.commit()
        except Exception as mig_e:
            print(f"⚠️ Migration warning (may be safe if new DB): {mig_e}")

        # Migration: Check for new Author Profile columns
        try:
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('magazine_settings')]
            new_cols = {
                'author_phone': "VARCHAR(50) DEFAULT ''",
                'author_email': "VARCHAR(100) DEFAULT ''",
                'author_address': "VARCHAR(200) DEFAULT ''",
                'author_workplace': "VARCHAR(200) DEFAULT ''",
                'social_twitter': "VARCHAR(200) DEFAULT ''",
                'social_linkedin': "VARCHAR(200) DEFAULT ''",
                'social_facebook': "VARCHAR(200) DEFAULT ''",
                'social_instagram': "VARCHAR(200) DEFAULT ''",
                'author_intro': "TEXT DEFAULT ''",
                'author_cv': "VARCHAR(500) DEFAULT ''",
                'author_gallery': "TEXT DEFAULT '[]'",
                'author_name_ar': "VARCHAR(200) DEFAULT ''",
                'author_bio_ar': "TEXT DEFAULT ''",
                'author_intro_ar': "TEXT DEFAULT ''",
                'magazine_template': "VARCHAR(30) DEFAULT 'slate'",
                'section_title_top_ar': "VARCHAR(100) DEFAULT ''",
                'section_title_latest_ar': "VARCHAR(100) DEFAULT ''",
                'section_title_trending_ar': "VARCHAR(100) DEFAULT ''",
                'section_title_archives_ar': "VARCHAR(100) DEFAULT ''",
                'section_title_ads_ar': "VARCHAR(100) DEFAULT ''",
                'reels_enabled': "BOOLEAN DEFAULT 1",
                'section_title_reels': "VARCHAR(100) DEFAULT 'Worth Watching'",
                'section_title_reels_ar': "VARCHAR(100) DEFAULT ''",
                'custom_api_key_names': "TEXT DEFAULT '[]'",
                'reels_display_limit': "INTEGER DEFAULT 4",
                'cover_world_id': "VARCHAR(36) DEFAULT ''",
                'cover_campus_id': "VARCHAR(36) DEFAULT ''",
                'campus_kind_order': "TEXT DEFAULT ''",
            }
            
            with db.engine.connect() as conn:
                for col, type_def in new_cols.items():
                    if col not in columns:
                        print(f"⚠️  '{col}' column missing. Adding...")
                        conn.execute(db.text(f"ALTER TABLE magazine_settings ADD COLUMN {col} {type_def}"))
                conn.commit()
            print("✅ Author Profile Migration checked/completed.")
        except Exception as e:
             print(f"⚠️ Author Info Migration warning: {e}")

        # Migration: CuratedReel draft/published/archived status (replaces the old is_published toggle)
        try:
            inspector = db.inspect(db.engine)
            reel_columns = [c['name'] for c in inspector.get_columns('curated_reels')]
            with db.engine.connect() as conn:
                if 'status' not in reel_columns:
                    print("⚠️  'status' column missing on curated_reels. Adding...")
                    conn.execute(db.text("ALTER TABLE curated_reels ADD COLUMN status VARCHAR(20) DEFAULT 'published'"))
                    conn.commit()
                    # Backfill from the old boolean so existing hidden reels become drafts.
                    conn.execute(db.text(
                        "UPDATE curated_reels SET status = CASE WHEN is_published = 0 THEN 'draft' ELSE 'published' END"
                    ))
                    conn.commit()
            print("✅ Curated Reel status migration checked/completed.")
        except Exception as e:
            print(f"⚠️ Curated Reel status migration warning: {e}")

        # Migration: richer AI tool directory fields
        try:
            inspector = db.inspect(db.engine)
            tool_columns = [c['name'] for c in inspector.get_columns('ai_tools')]
            extra_tool_columns = {
                'tagline_en': "VARCHAR(200) DEFAULT ''",
                'tagline_ar': "VARCHAR(200) DEFAULT ''",
                'pricing': "VARCHAR(20) DEFAULT 'freemium'",
                'free_tier': "BOOLEAN DEFAULT 1",
                'arabic_support': "BOOLEAN DEFAULT 0",
                'platforms': "VARCHAR(200) DEFAULT 'Web'",
                'best_for': "VARCHAR(200) DEFAULT ''",
                'featured': "BOOLEAN DEFAULT 0",
                'sort_order': "INTEGER DEFAULT 0",
                'last_checked': "DATE",
                'rating': "FLOAT DEFAULT 0",
                'rating_note': "VARCHAR(300) DEFAULT ''",
                'rating_source': "VARCHAR(300) DEFAULT ''",
            }
            with db.engine.connect() as conn:
                for col, type_def in extra_tool_columns.items():
                    if col not in tool_columns:
                        print(f"⚠️  ai_tools.{col} missing. Adding...")
                        conn.execute(db.text(f"ALTER TABLE ai_tools ADD COLUMN {col} {type_def}"))
                conn.commit()
            print("✅ AI tool directory migration checked/completed.")
        except Exception as e:
            print(f"⚠️ AI tool directory migration warning: {e}")

        # Migration: add the project track (final year / research / competition)
        try:
            inspector = db.inspect(db.engine)
            project_columns = [c['name'] for c in inspector.get_columns('project_ideas')]
            if 'track' not in project_columns:
                print("⚠️  project_ideas.track missing. Adding...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE project_ideas ADD COLUMN track VARCHAR(20) DEFAULT 'final_year'"))
                    conn.commit()
            print("✅ Project track migration checked/completed.")
        except Exception as e:
            print(f"⚠️ Project track migration warning: {e}")

        print("✅ Database tables created/verified.")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
