from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# 1) public downloads routes before the admin department helper
anchor = "def _department_desk():"
routes = '''RESOURCE_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip'}


@app.route('/campus/downloads')
def campus_downloads():
    """The department's public file shelf: notes, syllabi, policies and forms."""
    q = (request.args.get('q') or '').strip()
    category = request.args.get('category', 'all')

    query = DepartmentResource.query.filter_by(is_published=True)
    if category != 'all':
        query = query.filter_by(category=category)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(
            DepartmentResource.title.ilike(like), DepartmentResource.title_ar.ilike(like),
            DepartmentResource.description.ilike(like), DepartmentResource.description_ar.ilike(like),
            DepartmentResource.course.ilike(like), DepartmentResource.course_ar.ilike(like),
        ))
    resources = query.order_by(DepartmentResource.featured.desc(),
                               DepartmentResource.sort_order.asc(),
                               DepartmentResource.uploaded_at.desc()).all()
    counts = {'all': DepartmentResource.query.filter_by(is_published=True).count()}
    for key, _en, _ar in RESOURCE_CATEGORIES:
        counts[key] = DepartmentResource.query.filter_by(category=key, is_published=True).count()

    return render_template('resources_v3.html', resources=[r.to_dict() for r in resources],
                           categories=RESOURCE_CATEGORIES, counts=counts,
                           q=q, category=category, total=counts['all'],
                           settings=MagazineSettings.get_settings(),
                           date=datetime.datetime.now().strftime('%Y-%m-%d'))


@app.route('/campus/downloads/<int:resource_id>/file')
def download_department_resource(resource_id):
    from flask import send_from_directory
    resource = DepartmentResource.query.get_or_404(resource_id)
    if not resource.is_published:
        abort(404)
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'resources')
    path = os.path.join(folder, resource.file_name)
    if not os.path.isfile(path):
        abort(404)
    resource.download_count = (resource.download_count or 0) + 1
    db.session.commit()
    return send_from_directory(folder, resource.file_name, as_attachment=True,
                               download_name=resource.original_name or resource.file_name)


def _save_resource_file(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, RESOURCE_EXTENSIONS):
        return None
    original = file.filename[:300]
    cleaned = secure_filename(file.filename) or ('resource.' + file.filename.rsplit('.', 1)[-1].lower())
    stored = f"resource_{uuid.uuid4().hex}_{cleaned}"
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'resources')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, stored)
    file.save(path)
    ext = stored.rsplit('.', 1)[-1].lower() if '.' in stored else ''
    return stored, original, os.path.getsize(path), ext


def _apply_resource_form(resource, new_file):
    resource.title = (request.form.get('title') or '').strip()[:200]
    resource.title_ar = (request.form.get('title_ar') or '').strip()[:200]
    resource.description = (request.form.get('description') or '').strip()
    resource.description_ar = (request.form.get('description_ar') or '').strip()
    resource.course = (request.form.get('course') or '').strip()[:120]
    resource.course_ar = (request.form.get('course_ar') or '').strip()[:120]
    resource.category = request.form.get('category', 'notes')
    resource.is_published = bool(request.form.get('is_published'))
    resource.featured = bool(request.form.get('featured'))
    try:
        resource.sort_order = int(request.form.get('sort_order') or 0)
    except ValueError:
        resource.sort_order = 0
    if new_file:
        resource.file_name, resource.original_name, resource.file_size, resource.file_type = new_file


@app.route('/department/resources')
@login_required
def resources_admin():
    resources = (DepartmentResource.query
                 .order_by(DepartmentResource.featured.desc(),
                           DepartmentResource.sort_order.asc(),
                           DepartmentResource.uploaded_at.desc()).all())
    counts = {'all': len(resources)}
    for key, _en, _ar in RESOURCE_CATEGORIES:
        counts[key] = sum(1 for r in resources if r.category == key)
    return render_template('resources_admin.html', resources=resources,
                           categories=RESOURCE_CATEGORIES, counts=counts)


@app.route('/department/resources/new', methods=['GET', 'POST'])
@login_required
def add_department_resource():
    if request.method == 'POST':
        new_file = _save_resource_file(request.files.get('file'))
        if not new_file:
            flash('Choose a PDF, Word, PowerPoint, Excel, text or ZIP file.', 'error')
            return redirect(request.url)
        title = (request.form.get('title') or '').strip()
        if not title:
            flash('A title is required.', 'error')
            return redirect(request.url)
        resource = DepartmentResource(title=title, file_name=new_file[0])
        _apply_resource_form(resource, new_file)
        db.session.add(resource)
        db.session.commit()
        flash('File added to the department downloads.', 'success')
        return redirect(url_for('resources_admin'))
    return render_template('resource_form.html', resource=None, categories=RESOURCE_CATEGORIES)


@app.route('/department/resources/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department_resource(resource_id):
    resource = DepartmentResource.query.get_or_404(resource_id)
    if request.method == 'POST':
        new_file = _save_resource_file(request.files.get('file'))
        old_file = resource.file_name
        _apply_resource_form(resource, new_file)
        if not resource.title:
            flash('A title is required.', 'error')
            return redirect(request.url)
        db.session.commit()
        if new_file and old_file:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'resources', old_file))
            except OSError:
                pass
        flash('Download updated.', 'success')
        return redirect(url_for('resources_admin'))
    return render_template('resource_form.html', resource=resource, categories=RESOURCE_CATEGORIES)


@app.route('/department/resources/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete_department_resource(resource_id):
    resource = DepartmentResource.query.get_or_404(resource_id)
    old_file = resource.file_name
    db.session.delete(resource)
    db.session.commit()
    if old_file:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'resources', old_file))
        except OSError:
            pass
    flash('Download removed.', 'success')
    return redirect(url_for('resources_admin'))


'''
if "def campus_downloads()" not in s:
    s = s.replace(anchor, routes + anchor, 1)
    print("resource routes inserted")
else:
    print("resource routes already exist")

# 2) include downloads in the department page
old = """        featured_projects=[i.to_dict() for i in ProjectIdea.query.filter_by(
            is_published=True, featured=True).order_by(ProjectIdea.sort_order.asc()).limit(3).all()],
        project_total=ProjectIdea.query.filter_by(is_published=True).count(),"""
new = """        featured_projects=[i.to_dict() for i in ProjectIdea.query.filter_by(
            is_published=True, featured=True).order_by(ProjectIdea.sort_order.asc()).limit(3).all()],
        project_total=ProjectIdea.query.filter_by(is_published=True).count(),
        resources=[r.to_dict() for r in DepartmentResource.query.filter_by(is_published=True)
                   .order_by(DepartmentResource.featured.desc(), DepartmentResource.sort_order.asc(),
                             DepartmentResource.uploaded_at.desc()).limit(6).all()],
        resource_total=DepartmentResource.query.filter_by(is_published=True).count(),"""
if old in s:
    s = s.replace(old, new, 1)
    print("campus resources passed")
else:
    print("campus resources anchor missing")

# 3) extra stats for the department hub
old = """        'projects': len(projects),
        'research': sum(1 for p in projects if (p.track or 'final_year') == 'research'),"""
new = """        'projects': len(projects),
        'resources': DepartmentResource.query.count(),
        'research': sum(1 for p in projects if (p.track or 'final_year') == 'research'),"""
if old in s:
    s = s.replace(old, new, 1)
    print("department resource stat added")

p.write_text(s, encoding="utf-8")
