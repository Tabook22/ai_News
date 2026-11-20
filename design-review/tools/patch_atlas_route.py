from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# Import the atlas data next to the library catalog.
if "from atlas_catalog import" not in s:
    s = s.replace(
        "from library_catalog import LIBRARY_SEED, LIBRARY_SHELVES",
        "from library_catalog import LIBRARY_SEED, LIBRARY_SHELVES\n"
        "from atlas_catalog import ATLAS_REGIONS, ATLAS_KINDS, ATLAS_SOURCES",
        1,
    )
    print("atlas import added")

route = '''

@app.route('/library/atlas')
def ai_atlas():
    """A curated reading map of AI publications, labs and regional hubs."""
    q = (request.args.get('q') or '').strip()
    region = request.args.get('region', 'all')
    kind = request.args.get('kind', 'all')
    valid_regions = {row[0] for row in ATLAS_REGIONS}
    valid_kinds = {row[0] for row in ATLAS_KINDS}
    if region not in valid_regions:
        region = 'all'
    if kind not in valid_kinds:
        kind = 'all'

    region_labels = {key: (en, ar) for key, en, ar, _dek_en, _dek_ar in ATLAS_REGIONS}
    kind_labels = {key: (en, ar) for key, en, ar in ATLAS_KINDS}

    def matches(item):
        if region != 'all' and item.get('region') != region:
            return False
        if kind != 'all' and item.get('kind') != kind:
            return False
        if q:
            haystack = ' '.join(str(item.get(key) or '') for key in
                                ('name', 'location', 'language', 'copy_en', 'copy_ar', 'why_en', 'why_ar'))
            if q.lower() not in haystack.lower():
                return False
        return True

    rows = []
    for item in ATLAS_SOURCES:
        if not matches(item):
            continue
        row = dict(item)
        row['region_en'], row['region_ar'] = region_labels.get(row.get('region'), ('Global', 'العالم'))
        row['kind_en'], row['kind_ar'] = kind_labels.get(row.get('kind'), ('Source', 'مصدر'))
        rows.append(row)

    sections = []
    for key, en, ar, dek_en, dek_ar in ATLAS_REGIONS:
        entries = [row for row in rows if row.get('region') == key]
        if entries:
            sections.append({
                'key': key, 'en': en, 'ar': ar,
                'dek_en': dek_en, 'dek_ar': dek_ar,
                'entries': entries,
            })

    counts = {'all': len(ATLAS_SOURCES)}
    for key, _en, _ar, _dek_en, _dek_ar in ATLAS_REGIONS:
        counts[key] = sum(1 for row in ATLAS_SOURCES if row.get('region') == key)
    kind_counts = {'all': len(ATLAS_SOURCES)}
    for key, _en, _ar in ATLAS_KINDS:
        kind_counts[key] = sum(1 for row in ATLAS_SOURCES if row.get('kind') == key)

    featured = [row for row in rows if row.get('featured')][:4]
    return render_template('atlas.html', sections=sections, rows=rows, featured=featured,
                           regions=ATLAS_REGIONS, kinds=ATLAS_KINDS, counts=counts,
                           kind_counts=kind_counts, region=region, kind=kind, q=q)


'''
if "def ai_atlas()" not in s:
    s = s.replace("def library_admin():", route + "def library_admin():", 1)
    print("atlas route added")

# Sitemap entry
old = '''    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
                   % url_for('campus_projects', _external=True))'''
new = '''    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
                   % url_for('campus_projects', _external=True))
    entries.append("<url><loc>%s</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>"
                   % url_for('ai_atlas', _external=True))'''
if "url_for('ai_atlas'" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("atlas sitemap added")
    else:
        print("SITEMAP ANCHOR MISSING")

p.write_text(s, encoding="utf-8")
