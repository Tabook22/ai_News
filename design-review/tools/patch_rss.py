from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

route = '''

@app.route('/rss.xml')
def rss_feed():
    """Public RSS feed for readers and news-reader apps."""
    from flask import Response
    from email.utils import format_datetime
    rows = (NewsItem.query
            .filter(NewsItem.is_published.isnot(False))
            .order_by(NewsItem.timestamp.desc())
            .limit(40).all())

    def when(value):
        if not value:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return format_datetime(value)

    body = render_template('rss.xml', rows=rows, when=when,
                           settings=MagazineSettings.get_settings())
    return Response(body, mimetype='application/rss+xml')

'''
if "def rss_feed()" not in s:
    anchor = "@app.route('/sitemap.xml')\ndef sitemap_xml():"
    if anchor in s:
        s = s.replace(anchor, route + anchor, 1)
        print("rss route added")
    else:
        print("RSS ANCHOR MISSING")
p.write_text(s, encoding="utf-8")
