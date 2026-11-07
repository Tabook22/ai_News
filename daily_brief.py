"""
Add today's five most important global AI stories to the magazine.

Run by hand:
    venv\\Scripts\\python.exe daily_brief.py

Or leave it to the daily scheduled task "Nasser AI News Daily Brief".
"""
import datetime
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))
LOG_PATH = os.path.join(ROOT, "logs", "daily_brief.log")


def _log(line):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"{stamp}  {line}"
    print(text)
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(text + "\n")

spec = importlib.util.spec_from_file_location("nasser_app", os.path.join(ROOT, "app", "app.py"))
module = importlib.util.module_from_spec(spec)
sys.modules["nasser_app"] = module
spec.loader.exec_module(module)

try:
    with module.app.app_context():
        added = module.import_daily_top_stories(limit=5)
except Exception as exc:
    _log(f"FAILED  {exc}")
    raise

if added:
    _log(f"Added {len(added)} stories to Latest News:")
    for title in added:
        _log(f"  - {title}")
else:
    _log("No new stories. Today's top AI headlines are already in the magazine.")

try:
    with module.app.app_context():
        shelves = module.import_youtube_desk()
    _log("YouTube shelves: " + ", ".join(f"{lane}/{lang} {count}" for (lane, lang), count in shelves.items()))
except Exception as exc:
    _log(f"YouTube desk failed: {exc.__class__.__name__}")
