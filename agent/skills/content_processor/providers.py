"""
AI providers, saved models, and which model handles each magazine task.

API keys stay in .env. The choices (which models are enabled, and which
provider/model serves each task) live in data/ai_routing.json.
"""
import json
import os
import re

from openai import OpenAI

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ROUTING_PATH = os.path.join(ROOT, "data", "ai_routing.json")

# OpenAI-compatible chat endpoints. Gemini, Anthropic, xAI, Zhipu, and Qwen
# all accept the same chat call the magazine already uses.
PROVIDERS = [
    {
        "id": "openai",
        "label": "OpenAI",
        "icon": "🧠",
        "key_env": "OPENAI_API_KEY",
        "base_url": "",
        "placeholder": "sk-...",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o4-mini"],
    },
    {
        "id": "gemini",
        "label": "Google Gemini",
        "icon": "✦",
        "key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "placeholder": "AIza...",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "icon": "🟣",
        "key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1/",
        "placeholder": "sk-ant-...",
        "models": ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-1"],
    },
    {
        "id": "xai",
        "label": "xAI (Grok)",
        "icon": "⚡",
        "key_env": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "placeholder": "xai-...",
        "models": ["grok-4", "grok-3", "grok-3-mini"],
    },
    {
        "id": "zhipu",
        "label": "Zhipu AI (GLM)",
        "icon": "🧪",
        "key_env": "ZHIPU_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "placeholder": "your Zhipu key",
        "models": ["glm-4.5", "glm-4.5-air", "glm-4-flash"],
    },
    {
        "id": "qwen",
        "label": "Qwen",
        "icon": "🌐",
        "key_env": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "placeholder": "sk-...",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
    },
]

TASKS = [
    {
        "id": "gather",
        "label": "Searching and gathering news",
        "help": "Turns a fetched headline into the bilingual title and summary saved in the magazine.",
    },
    {
        "id": "analyze",
        "label": "Discussing and analyzing news",
        "help": "Answers a reader who asks the magazine about its stories.",
    },
    {
        "id": "summarize",
        "label": "Summarizing news articles",
        "help": "Drafts video blurbs, tool descriptions, and the newsletter introduction.",
    },
    {
        "id": "comments",
        "label": "Analyzing reader comments",
        "help": "Reads the comments on a story and reports sentiment, opinions, and themes.",
    },
    {
        "id": "other",
        "label": "Other AI tasks",
        "help": "Translations of titles and full articles.",
    },
]

_SLUG = re.compile(r"[^a-z0-9]+")


def _defaults():
    tasks = {task["id"]: {"provider": "openai", "model": "gpt-4o-mini"} for task in TASKS}
    models = {provider["id"]: list(provider["models"][:2]) for provider in PROVIDERS}
    return {"models": models, "tasks": tasks, "custom": []}


def load_routing():
    data = _defaults()
    try:
        with open(ROUTING_PATH, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return data
    if isinstance(saved, dict):
        if isinstance(saved.get("models"), dict):
            data["models"].update(saved["models"])
        if isinstance(saved.get("tasks"), dict):
            data["tasks"].update({k: v for k, v in saved["tasks"].items() if isinstance(v, dict)})
        if isinstance(saved.get("custom"), list):
            data["custom"] = [row for row in saved["custom"] if isinstance(row, dict) and row.get("id")]
    return data


def save_routing(data):
    os.makedirs(os.path.dirname(ROUTING_PATH), exist_ok=True)
    with open(ROUTING_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _mask(value):
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "•" * len(value)
    return f"{value[:4]}{'•' * 6}{value[-4:]}"


def all_providers(routing=None):
    """Built-in providers plus any custom endpoint the editor added."""
    routing = routing or load_routing()
    rows = []
    for provider in PROVIDERS:
        rows.append({**provider, "custom": False})
    for row in routing.get("custom") or []:
        rows.append({
            "id": row["id"],
            "label": row.get("label") or row["id"],
            "icon": "🧩",
            "key_env": row.get("key_env") or "",
            "base_url": row.get("base_url") or "",
            "placeholder": "API key",
            "models": row.get("models") or [],
            "custom": True,
        })
    return rows


def public_status():
    """What the settings page may show. Keys are masked."""
    routing = load_routing()
    selected = routing.get("models") or {}
    providers = []
    for provider in all_providers(routing):
        secret = os.environ.get(provider["key_env"], "") if provider["key_env"] else ""
        chosen = selected.get(provider["id"]) or []
        if not chosen and not provider["custom"]:
            chosen = provider["models"][:1]
        providers.append({
            "id": provider["id"],
            "label": provider["label"],
            "icon": provider["icon"],
            "placeholder": provider["placeholder"],
            "base_url": provider["base_url"],
            "catalog": provider["models"],
            "selected": chosen,
            "configured": bool(secret.strip()),
            "masked": _mask(secret),
            "custom": provider["custom"],
        })
    tasks = []
    for task in TASKS:
        choice = routing["tasks"].get(task["id"]) or {"provider": "openai", "model": "gpt-4o-mini"}
        tasks.append({**task, "provider": choice.get("provider") or "openai", "model": choice.get("model") or ""})
    return {"providers": providers, "tasks": tasks}


def client_for(task):
    """Return (OpenAI-compatible client, model name) for a task, or (None, None)."""
    routing = load_routing()
    choice = (routing.get("tasks") or {}).get(task) or {}
    provider_id = choice.get("provider") or "openai"
    model = (choice.get("model") or "").strip()
    provider = next((row for row in all_providers(routing) if row["id"] == provider_id), None)
    if provider is None:
        provider = all_providers(routing)[0]
    if not model:
        chosen = (routing.get("models") or {}).get(provider["id"]) or provider["models"]
        model = chosen[0] if chosen else ""
    api_key = os.environ.get(provider["key_env"], "").strip() if provider.get("key_env") else ""
    if not api_key or not model:
        return None, None
    kwargs = {"api_key": api_key}
    if provider.get("base_url"):
        kwargs["base_url"] = provider["base_url"]
    return OpenAI(**kwargs), model


def complete(task, messages, temperature=0.3, json_mode=False):
    """One chat completion for a task. Returns None when that task has no key."""
    client, model = client_for(task)
    if client is None:
        return None
    kwargs = {"model": model, "messages": messages, "temperature": temperature}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        return client.chat.completions.create(**kwargs)
    except Exception:
        if not json_mode:
            raise
        kwargs.pop("response_format", None)
        return client.chat.completions.create(**kwargs)


def slug_id(label):
    slug = _SLUG.sub("-", (label or "").strip().lower()).strip("-")[:24]
    return f"custom-{slug or 'provider'}"
