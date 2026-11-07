from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")
anchor = "class OccasionAlbum(db.Model):"
block = '''class ProjectIdea(db.Model):
    """A final-year project idea for Computer Science students, with a reference."""
    __tablename__ = 'project_ideas'
    id = db.Column(db.Integer, primary_key=True)
    title_en = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), default='')
    summary_en = db.Column(db.String(300), default='')
    summary_ar = db.Column(db.String(300), default='')
    body_en = db.Column(db.Text, default='')
    body_ar = db.Column(db.Text, default='')
    area = db.Column(db.String(30), default='agents')
    difficulty = db.Column(db.String(20), default='intermediate')
    skills = db.Column(db.String(200), default='')
    tools = db.Column(db.String(200), default='')
    reference_title = db.Column(db.String(200), default='')
    reference_url = db.Column(db.Text)
    reference_note_en = db.Column(db.String(300), default='')
    reference_note_ar = db.Column(db.String(300), default='')
    featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title_en': self.title_en,
            'title_ar': self.title_ar,
            'summary_en': self.summary_en,
            'summary_ar': self.summary_ar,
            'body_en': self.body_en,
            'body_ar': self.body_ar,
            'area': self.area or 'agents',
            'area_en': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[0],
            'area_ar': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[1],
            'difficulty': self.difficulty or 'intermediate',
            'skills': [s.strip() for s in (self.skills or '').split(',') if s.strip()],
            'tools': [t.strip() for t in (self.tools or '').split(',') if t.strip()],
            'reference_title': self.reference_title or '',
            'reference_url': self.reference_url or '',
            'reference_note_en': self.reference_note_en or '',
            'reference_note_ar': self.reference_note_ar or '',
            'featured': bool(self.featured),
            'sort_order': self.sort_order or 0,
            'is_published': bool(self.is_published),
        }


'''
if "class ProjectIdea" not in s:
    s = s.replace(anchor, block + anchor, 1)
    p.write_text(s, encoding="utf-8")
    print("inserted ProjectIdea")
else:
    print("ProjectIdea already exists")
