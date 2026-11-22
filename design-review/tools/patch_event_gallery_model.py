from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# Gallery relationship on event
old = """    photos = db.relationship('EventPhoto', backref='event', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='EventPhoto.display_order, EventPhoto.id')"""
new = """    gallery = db.relationship('EventGallery', backref='event', uselist=False,
                              cascade='all, delete-orphan')
    photos = db.relationship('EventPhoto', backref='event', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='EventPhoto.display_order, EventPhoto.id')"""
if "gallery = db.relationship('EventGallery'" not in s:
    s = s.replace(old, new, 1)
    print("event gallery relationship added")

# Gallery id on a photo
old = """    event_id = db.Column(db.Integer, db.ForeignKey('national_events.id'), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=False)"""
new = """    event_id = db.Column(db.Integer, db.ForeignKey('national_events.id'), nullable=False, index=True)
    gallery_id = db.Column(db.Integer, db.ForeignKey('event_galleries.id'), index=True)
    image = db.Column(db.String(500), nullable=False)"""
if "gallery_id = db.Column" not in s:
    s = s.replace(old, new, 1)
    print("event photo gallery_id added")

gallery_model = '''

class EventGallery(db.Model):
    """One titled, separate gallery per event."""
    __tablename__ = 'event_galleries'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('national_events.id'),
                         nullable=False, unique=True, index=True)
    title_en = db.Column(db.String(240), default='')
    title_ar = db.Column(db.String(240), default='')
    description_en = db.Column(db.Text, default='')
    description_ar = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    photos = db.relationship('EventPhoto', backref='gallery', lazy=True,
                             order_by='EventPhoto.display_order, EventPhoto.id')

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'title_en': self.title_en or '',
            'title_ar': self.title_ar or '',
            'description_en': self.description_en or '',
            'description_ar': self.description_ar or '',
            'photo_count': len(self.photos or []),
        }

'''
if "class EventGallery" not in s:
    anchor = "class EventPhoto(db.Model):"
    s = s.replace(anchor, gallery_model + anchor, 1)
    print("event gallery model added")

p.write_text(s, encoding="utf-8")
