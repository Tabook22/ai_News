from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

constant = '''RESOURCE_CATEGORIES = [
    ('notes', 'Course notes', 'ملاحظات المقرر'),
    ('syllabus', 'Syllabus', 'خطة المقرر'),
    ('policies', 'Policies & forms', 'السياسات والنماذج'),
    ('exams', 'Exams & revision', 'الاختبارات والمراجعة'),
    ('workshops', 'Workshop materials', 'مواد الورش'),
    ('other', 'Other', 'أخرى'),
]

'''
if "RESOURCE_CATEGORIES" not in s:
    s = s.replace("PROJECT_TRACKS = {", constant + "PROJECT_TRACKS = {", 1)
    print("resource categories added")

model = '''def _size_label(size):
    try:
        size = int(size or 0)
    except (TypeError, ValueError):
        size = 0
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


class DepartmentResource(db.Model):
    """A course note, policy, form or workshop file for department students."""
    __tablename__ = 'department_resources'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), default='')
    description = db.Column(db.Text, default='')
    description_ar = db.Column(db.Text, default='')
    course = db.Column(db.String(120), default='')
    course_ar = db.Column(db.String(120), default='')
    category = db.Column(db.String(30), default='notes')
    file_name = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(300), default='')
    file_size = db.Column(db.Integer, default=0)
    file_type = db.Column(db.String(20), default='')
    download_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        cat = dict((key, (en, ar)) for key, en, ar in RESOURCE_CATEGORIES).get(
            self.category, ('Other', 'أخرى'))
        ext = (self.file_type or self.original_name.rsplit('.', 1)[-1] if self.original_name else '').lower()
        return {
            'id': self.id,
            'title': self.title,
            'title_ar': self.title_ar,
            'description': self.description,
            'description_ar': self.description_ar,
            'course': self.course,
            'course_ar': self.course_ar,
            'category': self.category or 'other',
            'category_en': cat[0],
            'category_ar': cat[1],
            'original_name': self.original_name,
            'file_size': self.file_size or 0,
            'size_label': _size_label(self.file_size),
            'file_type': ext,
            'download_count': self.download_count or 0,
            'is_published': bool(self.is_published),
            'featured': bool(self.featured),
            'sort_order': self.sort_order or 0,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d') if self.uploaded_at else '',
        }


'''
if "class DepartmentResource" not in s:
    s = s.replace("class OccasionAlbum(db.Model):", model + "class OccasionAlbum(db.Model):", 1)
    print("resource model added")

p.write_text(s, encoding="utf-8")
