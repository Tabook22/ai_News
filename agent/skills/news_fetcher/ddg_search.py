try:
    # `duckduckgo_search` was renamed to `ddgs` — prefer the maintained package.
    # The two packages use different keyword-argument names for the same call,
    # so we track which one loaded and call it accordingly.
    from ddgs import DDGS
    _QUERY_PARAM = 'query'
except ImportError:
    from duckduckgo_search import DDGS
    _QUERY_PARAM = 'keywords'

def search_duckduckgo_news(query: str, lang: str = 'all', time_limit: str = 'w', errors=None) -> list[dict]:
    """
    Searches DuckDuckGo News.

    Args:
        query: Search term
        lang: 'ar' for Arabic Only, 'all' for everything.
        time_limit: 'd' (day), 'w' (week), 'm' (month).
        errors: optional list to collect human-readable failure reasons into.

    Returns:
        List of dicts: title, link, summary, published.
    """

    # Map our internal time codes to DDG time codes
    # Our app uses: 'today', 'week', 'month', 'year', 'all'
    # DDG uses: 'd', 'w', 'm', 'y'
    ddg_time = 'w' # Default
    if time_limit == 'today': ddg_time = 'd'
    elif time_limit == 'week': ddg_time = 'w'
    elif time_limit == 'month': ddg_time = 'm'
    elif time_limit == 'year': ddg_time = 'y'
    elif time_limit == 'all': ddg_time = None

    # Region/Language handling
    # DDG uses region codes like 'wt-wt' (world) or 'sa-ar' (Saudi/Arabic)
    # If lang='ar', we force Arabic region to get better results
    region = "wt-wt"
    if lang == 'ar':
        region = "sa-ar"

    print(f"DDG Search: '{query}' [Region: {region}, Time: {ddg_time}]")

    results = []
    try:
        with DDGS() as ddgs:
            # DDG .news() returns a list/generator of dicts
            ddg_results = ddgs.news(**{
                _QUERY_PARAM: query,
                'region': region,
                'safesearch': 'off',
                'timelimit': ddg_time,
                'max_results': 10,
            })

            if ddg_results:
                for r in ddg_results:
                    # Normalize to our app's format
                    results.append({
                        "title": r.get('title', 'No Title'),
                        "url": r.get('url', r.get('link', '#')),
                        "image": r.get('image'), # DDG provides images!
                        "source": r.get('source', 'DuckDuckGo'),
                        "summary": r.get('body', r.get('excerpt', '')),
                        "snippet": r.get('body', r.get('excerpt', '')), # Dual keys for compat
                        "published": r.get('date', ''),
                        "fetched_at": r.get('date', '') # For consistency
                    })
            else:
                print("DDG returned no results.")

    except Exception as e:
        msg = str(e)
        hint = ""
        if 'ratelimit' in msg.lower() or '202' in msg:
            hint = " -> DuckDuckGo is temporarily rate-limiting this server; wait a few minutes and try again."
        full_msg = f"DuckDuckGo search failed: {msg}{hint}"
        print(f"DDG Error: {full_msg}")
        if errors is not None:
            errors.append(full_msg)

    return results
