from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# Relationship on the event model
old = """    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):"""
new = """    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    photos = db.relationship('EventPhoto', backref='event', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='EventPhoto.display_order, EventPhoto.id')

    def to_dict(self):"""
if "photos = db.relationship('EventPhoto'" not in s:
    s = s.replace(old, new, 1)
    print("event photo relationship added")

photo_model = '''

class EventPhoto(db.Model):
    """One image in an event gallery, with a bilingual caption/comment."""
    __tablename__ = 'event_photos'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('national_events.id'), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=False)
    caption_en = db.Column(db.Text, default='')
    caption_ar = db.Column(db.Text, default='')
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'image': self.image,
            'caption_en': self.caption_en or '',
            'caption_ar': self.caption_ar or '',
            'display_order': self.display_order or 0,
        }

'''
if "class EventPhoto" not in s:
    anchor = "class DailyQuestion(db.Model):"
    s = s.replace(anchor, photo_model + anchor, 1)
    print("event photo model added")

p.write_text(s, encoding="utf-8")
