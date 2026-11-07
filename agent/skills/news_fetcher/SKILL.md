---
name: News Fetcher
description: Fetches, parses, and filters high-quality AI news from RSS feeds and web sources.
---

# Skill Description
Fetches, parses, and filters high-quality AI news from RSS feeds and web sources. This skill is used to collect recent AI developments, with priority given to Agentic AI topics, for the Nasser AI News magazine.

## Inputs
- Source URLs (RSS feeds or web pages)
- Time window: last 7 days
- Keywords related to Agentic AI (e.g., autonomous agents, tool use, workflows)

## Steps / Instructions

### Source Evaluation
1. If the provided URL contains a standard RSS feed, execute `fetch_rss` from `actions.py`.
2. If the source is a dynamic web page without RSS, execute `scrape_web` from `actions.py`.

### Content Filtering
1. Apply the ranking philosophy defined in `ranking.md`.
2. Prioritize articles containing Agentic AI–related keywords such as:
   - Autonomous Agents
   - Tool Use
   - Agentic Workflows
3. Discard promotional content, repetitive announcements, or marketing hype.

### Freshness Check
- Ensure all retrieved articles are published within the last 7 days.

### Data Storage
- Store the filtered results in JSON format at: `storage/raw_news/latest.json`
- Include headline, summary, publication date, and source URL.

## Output
A structured JSON file (`latest.json`) containing:
- Relevant AI news articles
- Clean summaries
- Verified source URLs
- Ready for downstream processing (summarization, translation, publishing)