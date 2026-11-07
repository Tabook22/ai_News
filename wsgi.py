"""Gunicorn entry point for the VPS.

Run from the repository root:
    gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app

The app itself lives in app/app.py; the repository root is not a package.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "app"))

from app import app  # noqa: E402,F401
