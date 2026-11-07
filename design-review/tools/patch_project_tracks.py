from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# 1) track column on the model
old = """    area = db.Column(db.String(30), default='agents')
    difficulty = db.Column(db.String(20), default='intermediate')"""
new = """    area = db.Column(db.String(30), default='agents')
    track = db.Column(db.String(20), default='final_year')
    difficulty = db.Column(db.String(20), default='intermediate')"""
if old in s:
    s = s.replace(old, new, 1)
    print("track column added")
else:
    print("track column anchor missing")

# 2) to_dict fields
old = """            'area_ar': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[1],
            'difficulty': self.difficulty or 'intermediate',"""
new = """            'area_ar': PROJECT_AREAS.get(self.area, ('Other', 'أخرى'))[1],
            'track': self.track or 'final_year',
            'track_en': PROJECT_TRACKS.get(self.track, ('Final-year project', 'مشروع التخرج'))[0],
            'track_ar': PROJECT_TRACKS.get(self.track, ('Final-year project', 'مشروع التخرج'))[1],
            'difficulty': self.difficulty or 'intermediate',"""
if old in s:
    s = s.replace(old, new, 1)
    print("track to_dict added")
else:
    print("track to_dict anchor missing")

# 3) track labels beside the area labels
anchor = "PROJECT_AREAS = {"
block = """PROJECT_TRACKS = {
    'final_year': ('Final-year project', 'مشروع التخرج'),
    'research': ('Research idea', 'فكرة بحثية'),
    'competition': ('Competition / hackathon', 'مسابقة / هاكاثون'),
}

"""
if "PROJECT_TRACKS =" not in s:
    s = s.replace(anchor, block + anchor, 1)
    print("PROJECT_TRACKS inserted")
else:
    print("PROJECT_TRACKS exists")

p.write_text(s, encoding="utf-8")
