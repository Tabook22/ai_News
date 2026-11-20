from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

models = '''

class DailyQuestion(db.Model):
    """One AI-science question tied to a reading, with a model answer."""
    __tablename__ = 'daily_questions'
    id = db.Column(db.Integer, primary_key=True)
    question_date = db.Column(db.Date, nullable=False, index=True)
    question_en = db.Column(db.Text, nullable=False)
    question_ar = db.Column(db.Text, default='')
    reading_title = db.Column(db.String(300), default='')
    reading_url = db.Column(db.Text, default='')
    reading_source = db.Column(db.String(160), default='')
    hint_en = db.Column(db.Text, default='')
    hint_ar = db.Column(db.Text, default='')
    answer_en = db.Column(db.Text, default='')
    answer_ar = db.Column(db.Text, default='')
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    answers = db.relationship('QuestionAnswer', backref='question', lazy=True,
                              cascade='all, delete-orphan',
                              order_by='QuestionAnswer.created_at.desc()')

    def to_dict(self):
        return {
            'id': self.id,
            'question_date': self.question_date.isoformat() if self.question_date else '',
            'question_en': self.question_en or '',
            'question_ar': self.question_ar or '',
            'reading_title': self.reading_title or '',
            'reading_url': self.reading_url or '',
            'reading_source': self.reading_source or '',
            'hint_en': self.hint_en or '',
            'hint_ar': self.hint_ar or '',
            'answer_en': self.answer_en or '',
            'answer_ar': self.answer_ar or '',
            'is_published': bool(self.is_published),
        }


class QuestionAnswer(db.Model):
    """A student's short answer. Public display is opt-in through approval."""
    __tablename__ = 'question_answers'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('daily_questions.id'), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=False)
    display_name = db.Column(db.String(80), default='')
    year = db.Column(db.String(40), default='')
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'answer_text': self.answer_text or '',
            'display_name': self.display_name or '',
            'year': self.year or '',
            'is_approved': bool(self.is_approved),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
        }

'''
if "class DailyQuestion" not in s:
    s = s.replace("class OccasionAlbum(db.Model):", models + "class OccasionAlbum(db.Model):", 1)
    print("question models added")
p.write_text(s, encoding="utf-8")
