from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

constant = '''EVENT_TYPES = [
    ('national', 'National', 'وطني'),
    ('religious', 'Religious', 'ديني'),
    ('campus', 'Campus', 'جامعي'),
    ('cultural', 'Cultural', 'ثقافي'),
]

'''
if "EVENT_TYPES" not in s:
    s = s.replace("RESOURCE_CATEGORIES = [", constant + "RESOURCE_CATEGORIES = [", 1)
    print("event types added")

model = '''

class NationalEvent(db.Model):
    """A national, religious or campus moment shown only after editor approval."""
    __tablename__ = 'national_events'
    id = db.Column(db.Integer, primary_key=True)
    title_en = db.Column(db.String(240), nullable=False)
    title_ar = db.Column(db.String(240), default='')
    kicker_en = db.Column(db.String(120), default='')
    kicker_ar = db.Column(db.String(120), default='')
    description_en = db.Column(db.Text, default='')
    description_ar = db.Column(db.Text, default='')
    event_type = db.Column(db.String(20), default='national')
    event_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date)
    location_en = db.Column(db.String(180), default='')
    location_ar = db.Column(db.String(180), default='')
    image = db.Column(db.String(500), default='')
    link_url = db.Column(db.Text, default='')
    link_label_en = db.Column(db.String(100), default='')
    link_label_ar = db.Column(db.String(100), default='')
    accent = db.Column(db.String(20), default='#0f766e')
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        today = datetime.date.today()
        start = self.event_date
        end = self.end_date or self.event_date
        if start and start > today:
            status = 'upcoming'
            days = (start - today).days
        elif end and end < today:
            status = 'past'
            days = 0
        else:
            status = 'live'
            days = 0
        return {
            'id': self.id,
            'title_en': self.title_en or '',
            'title_ar': self.title_ar or '',
            'kicker_en': self.kicker_en or '',
            'kicker_ar': self.kicker_ar or '',
            'description_en': self.description_en or '',
            'description_ar': self.description_ar or '',
            'event_type': self.event_type or 'national',
            'event_date': self.event_date,
            'end_date': self.end_date,
            'location_en': self.location_en or '',
            'location_ar': self.location_ar or '',
            'image': self.image or '',
            'link_url': self.link_url or '',
            'link_label_en': self.link_label_en or '',
            'link_label_ar': self.link_label_ar or '',
            'accent': self.accent or '#0f766e',
            'is_approved': bool(self.is_approved),
            'is_featured': bool(self.is_featured),
            'display_order': self.display_order or 0,
            'status': status,
            'days_until': days,
        }

'''
if "class NationalEvent" not in s:
    s = s.replace("class DailyQuestion(db.Model):", model + "class DailyQuestion(db.Model):", 1)
    print("event model added")

p.write_text(s, encoding="utf-8")
