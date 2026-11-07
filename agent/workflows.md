# Standard Operating Procedures (SOPs)

## Workflow A: Daily Aggregation Loop
**Goal**: Automated fetching, processing, and publishing of news.

1. **Search**: Query sources (Google / DuckDuckGo) for generic AI terms (e.g., "Artificial Intelligence news").
2. **Filter**: Apply strict filters:
   - Published within the last 24 hours.
   - High relevance score.
   - Credible sources only.
3. **Extract**: Parse metadata: Title, URL, Source Name, Published Date.
4. **Translate**: Convert key fields (Title + Snippet) from English to Modern Standard Arabic.
5. **Enrich**: Fetch `og:image` from the URL. If failed, assign a high-quality category placeholder.
6. **Archive**: Save normalized record into `data/news_archive.json`.
7. **Render**: Update the Magazine View to reflect new content.

## Workflow B: Manual Search UI Flow
**Goal**: User-driven content curation.

1. **Input**: User enters a specific topic string in the Search UI.
2. **Fetch**: System invokes the `news_fetcher` skill synchronously.
3. **Preview**: Results are displayed as cards with snippets (no translation yet).
4. **Selection**: User clicks "Save & Translate" on specific items.
5. **Process**:
   - Backend fetches image.
   - Backend translates text.
   - Backend saves to JSON.
6. **Feedback**: User is redirected to Dashboard to view the newly saved, bilingual item.
