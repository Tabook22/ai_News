# Content Processor Skill

## Description
Uses OpenAI (GPT-4o or 3.5-turbo) to process raw news data into high-quality bilingual content.
It generates a concise English summary and a high-quality Arabic translation of the title and summary.

## Inputs
- `title`: Original English Title
- `snippet`: Raw snippet or content from search/url
- `url`: (Optional) source url

## Outputs
- `title_ar`: Arabic Title
- `summary_en`: Polished English Summary (2-3 sentences)
- `summary_ar`: Arabic translation of the summary

## Configuration
Requires `OPENAI_API_KEY` in .env.
Falls back to deterministic mock/translation if key is missing.
