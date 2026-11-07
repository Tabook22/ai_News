"""Attach the editorial Nasser AI score and a reference link to key tools.

Run after the catalogue seeds:
    venv\\Scripts\\python.exe design-review/tools/seed_ratings.py
Scores are editorial (0–5), not a scraped star average. Each row links to a
public reference: official documentation, G2, or the product page.
"""
import sys

sys.path.insert(0, "app")
import app as m  # noqa: E402

RATINGS = [
    ("Hugging Face", 4.9, "The default place to find, compare and download open models.",
     "https://huggingface.co/models"),
    ("ChatGPT", 4.8, "The broadest general assistant, with a usable free plan.",
     "https://www.g2.com/products/chatgpt/reviews"),
    ("Claude", 4.7, "Best-in-class long-document reading and careful prose.",
     "https://www.g2.com/products/anthropic-claude/reviews"),
    ("Perplexity", 4.7, "The fastest route from a question to checkable sources.",
     "https://www.g2.com/products/perplexity-ai/reviews"),
    ("NotebookLM", 4.8, "Grounded study from your own PDFs and notes, with audio overviews.",
     "https://notebooklm.google.com"),
    ("Claude Code", 4.8, "A terminal agent that genuinely reads, edits and tests a repo.",
     "https://code.claude.com/docs/en/overview"),
    ("GitHub Copilot", 4.6, "Reliable in-editor completion with a free student route.",
     "https://www.g2.com/products/github-copilot/reviews"),
    ("Cursor", 4.7, "The most fluid agentic editor for multi-file changes.",
     "https://www.g2.com/products/cursor/reviews"),
    ("OpenAI Codex", 4.6, "Strong delegated coding tasks with a reviewable diff.",
     "https://openai.com/codex/"),
    ("Google Antigravity", 4.5, "A credible agent manager, still young as an IDE.",
     "https://antigravity.google/"),
    ("DeepSeek Harness", 4.4, "Open, plugin-first and free, with a learning curve.",
     "https://www.deepseek.com/en/harness/"),
    ("DaVinci Resolve", 4.7, "A professional editor, colour suite and DAW for free.",
     "https://www.g2.com/products/davinci-resolve/reviews"),
    ("Adobe Premiere Pro", 4.6, "The industry timeline, now with useful AI masks and text edits.",
     "https://www.g2.com/products/adobe-premiere-pro/reviews"),
    ("Descript", 4.6, "Transcript editing is the fastest way through a talking-head video.",
     "https://www.g2.com/products/descript/reviews"),
    ("CapCut", 4.5, "The quickest social edit; advanced features are increasingly paid.",
     "https://www.g2.com/products/capcut/reviews"),
    ("Runway", 4.5, "The strongest generative video editor for shot-level changes.",
     "https://www.g2.com/products/runwayml/reviews"),
    ("Midjourney", 4.6, "Still the style benchmark, but subscription-only.",
     "https://www.g2.com/products/midjourney/reviews"),
    ("ElevenLabs", 4.7, "Natural narration and cloning with a usable free tier.",
     "https://www.g2.com/products/elevenlabs/reviews"),
    ("Suno", 4.4, "Complete songs from a prompt; check the licence before publishing.",
     "https://www.g2.com/products/suno-ai/reviews"),
    ("Gamma", 4.6, "The fastest good-looking first draft of a deck.",
     "https://www.g2.com/products/gamma/reviews"),
    ("Canva Magic Studio", 4.5, "Templates plus AI, ideal for posters and social cards.",
     "https://www.g2.com/products/canva/reviews"),
    ("Adobe Firefly", 4.3, "Commercially safer image generation inside Adobe apps.",
     "https://www.g2.com/products/adobe-firefly/reviews"),
    ("Sora", 4.4, "Polished short clips, limited access and no free tier.",
     "https://openai.com/sora/"),
    ("Elicit", 4.4, "A useful first pass over a literature review.",
     "https://www.g2.com/products/elicit/reviews"),
    ("RunPod", 4.4, "Simple GPU pods with transparent hourly pricing.",
     "https://www.g2.com/products/runpod/reviews"),
    ("OpenClaw", 4.3, "A serious open personal agent if you can run and secure it.",
     "https://openclaw.ai/"),
    ("Hermes Agent", 4.2, "An open harness for learning how agents are assembled.",
     "https://hermes-agent.nousresearch.com/"),
    ("Fanar", 4.2, "The most Arabic-first assistant in the list.",
     "https://www.fanar.qa/en"),
    ("Gemini", 4.5, "Strong multimodal assistant if your work lives in Google Workspace.",
     "https://www.g2.com/products/google-gemini/reviews"),
    ("Microsoft Copilot", 4.3, "Best when Windows and Microsoft 365 are already your tools.",
     "https://www.g2.com/products/microsoft-copilot/reviews"),
]


def main():
    with m.app.app_context():
        updated = 0
        missing = []
        for name, score, note, source in RATINGS:
            tool = m.AITool.query.filter_by(name=name).first()
            if not tool:
                missing.append(name)
                continue
            tool.rating = score
            tool.rating_note = note
            tool.rating_source = source
            updated += 1
        m.db.session.commit()
        print(f"Ratings: {updated} tools updated; missing: {missing}")


if __name__ == "__main__":
    main()
