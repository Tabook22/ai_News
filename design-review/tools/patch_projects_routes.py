from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# 1) pass featured projects into the department page
old = """        week_label_ar=f"{start.day} {ARABIC_MONTHS[start.month]}",
        settings=MagazineSettings.get_settings(),
    )"""
new = """        week_label_ar=f"{start.day} {ARABIC_MONTHS[start.month]}",
        featured_projects=[i.to_dict() for i in ProjectIdea.query.filter_by(
            is_published=True, featured=True).order_by(ProjectIdea.sort_order.asc()).limit(3).all()],
        project_total=ProjectIdea.query.filter_by(is_published=True).count(),
        settings=MagazineSettings.get_settings(),
    )"""
if old in s:
    s = s.replace(old, new, 1)
    print("campus return patched")
else:
    print("campus return anchor missing")

# 2) add the public projects route
anchor = "def _department_desk():"
route = '''@app.route('/campus/projects')
def campus_projects():
    """Recommended final-year project ideas for Computer Science students."""
    q = (request.args.get('q') or '').strip()
    area = request.args.get('area', 'all')
    difficulty = request.args.get('difficulty', 'all')

    query = ProjectIdea.query.filter_by(is_published=True)
    if area != 'all':
        query = query.filter_by(area=area)
    if difficulty != 'all':
        query = query.filter_by(difficulty=difficulty)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            ProjectIdea.title_en.ilike(like), ProjectIdea.title_ar.ilike(like),
            ProjectIdea.summary_en.ilike(like), ProjectIdea.summary_ar.ilike(like),
            ProjectIdea.body_en.ilike(like), ProjectIdea.body_ar.ilike(like),
            ProjectIdea.skills.ilike(like), ProjectIdea.tools.ilike(like),
        ))
    ideas = query.order_by(ProjectIdea.featured.desc(), ProjectIdea.sort_order.asc(), ProjectIdea.title_en.asc()).all()

    counts = {'all': ProjectIdea.query.filter_by(is_published=True).count()}
    for key in PROJECT_AREAS:
        counts[key] = ProjectIdea.query.filter_by(area=key, is_published=True).count()

    return render_template('campus_projects_v3.html',
                           ideas=[i.to_dict() for i in ideas],
                           counts=counts, areas=PROJECT_AREAS,
                           q=q, area=area, difficulty=difficulty,
                           total=counts['all'],
                           settings=MagazineSettings.get_settings(),
                           date=datetime.datetime.now().strftime("%Y-%m-%d"))


'''
if "def campus_projects()" not in s:
    s = s.replace(anchor, route + anchor, 1)
    print("campus projects route inserted")
else:
    print("route already exists")

p.write_text(s, encoding="utf-8")
