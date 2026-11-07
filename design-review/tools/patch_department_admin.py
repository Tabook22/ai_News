from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# 1) enrich the department admin data
old = """    return render_template('department.html', groups=groups)"""
new = """    albums = (OccasionAlbum.query
              .order_by(OccasionAlbum.year.desc(), OccasionAlbum.event_date.desc()).all())
    projects = (ProjectIdea.query
                .order_by(ProjectIdea.featured.desc(), ProjectIdea.sort_order.asc()).all())
    stats = {
        'published': sum(1 for s in stories if s.get('is_published')),
        'hidden': sum(1 for s in stories if not s.get('is_published')),
        'photos': sum(len(a.photos) for a in albums),
        'albums': len(albums),
        'projects': len(projects),
        'research': sum(1 for p in projects if (p.track or 'final_year') == 'research'),
        'competitions': sum(1 for p in projects if (p.track or 'final_year') == 'competition'),
    }
    return render_template('department.html', groups=groups, stats=stats,
                           albums=albums[:4], projects=[p.to_dict() for p in projects])"""
if old in s:
    s = s.replace(old, new, 1)
    print("department data patched")
else:
    print("department data anchor missing")

# 2) project CRUD routes
anchor = "@app.route('/api/department/reorder', methods=['POST'])"
routes = '''def _apply_project_form(idea):
    idea.title_en = (request.form.get('title_en') or '').strip()[:200]
    idea.title_ar = (request.form.get('title_ar') or '').strip()[:200]
    idea.summary_en = (request.form.get('summary_en') or '').strip()[:300]
    idea.summary_ar = (request.form.get('summary_ar') or '').strip()[:300]
    idea.body_en = (request.form.get('body_en') or '').strip()
    idea.body_ar = (request.form.get('body_ar') or '').strip()
    idea.area = request.form.get('area', 'agents')
    idea.track = request.form.get('track', 'final_year')
    idea.difficulty = request.form.get('difficulty', 'intermediate')
    idea.skills = request.form.get('skills', '')
    idea.tools = request.form.get('tools', '')
    idea.reference_title = request.form.get('reference_title', '')[:200]
    idea.reference_url = (request.form.get('reference_url') or '').strip()
    idea.reference_note_en = request.form.get('reference_note_en', '')[:300]
    idea.reference_note_ar = request.form.get('reference_note_ar', '')[:300]
    idea.featured = bool(request.form.get('featured'))
    idea.is_published = bool(request.form.get('is_published'))
    try:
        idea.sort_order = int(request.form.get('sort_order') or 0)
    except ValueError:
        idea.sort_order = 0


@app.route('/department/projects/new', methods=['GET', 'POST'])
@login_required
def add_project_idea():
    if request.method == 'POST':
        idea = ProjectIdea(title_en=(request.form.get('title_en') or '').strip()[:200])
        if not idea.title_en:
            flash('An English title is required.', 'error')
            return redirect(request.url)
        _apply_project_form(idea)
        db.session.add(idea)
        db.session.commit()
        flash('Project idea added.', 'success')
        return redirect(url_for('department_admin', _anchor='projects'))
    return render_template('project_idea_form.html', idea=None,
                           areas=PROJECT_AREAS, tracks=PROJECT_TRACKS)


@app.route('/department/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project_idea(project_id):
    idea = ProjectIdea.query.get_or_404(project_id)
    if request.method == 'POST':
        _apply_project_form(idea)
        db.session.commit()
        flash('Project idea updated.', 'success')
        return redirect(url_for('department_admin', _anchor='projects'))
    return render_template('project_idea_form.html', idea=idea.to_dict(),
                           areas=PROJECT_AREAS, tracks=PROJECT_TRACKS)


@app.route('/department/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project_idea(project_id):
    idea = ProjectIdea.query.get_or_404(project_id)
    db.session.delete(idea)
    db.session.commit()
    flash('Project idea removed.', 'success')
    return redirect(url_for('department_admin', _anchor='projects'))


'''
if "def add_project_idea()" not in s:
    s = s.replace(anchor, routes + anchor, 1)
    print("project CRUD inserted")
else:
    print("project CRUD already exists")

p.write_text(s, encoding="utf-8")
