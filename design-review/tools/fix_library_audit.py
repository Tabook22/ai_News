from pathlib import Path
import shutil, sys, datetime

# 1) Fix admin page titles for the library
p = Path("app/templates/layout.html")
s = p.read_text(encoding="utf-8")
old = "    'template_picker': A('look'),\n    'author_info': t('Author profile', 'ملف المؤلف')"
new = ("    'template_picker': A('look'),\n"
       "    'library_admin': A('lib_title'),\n"
       "    'add_library_reference': A('lib_add'),\n"
       "    'edit_library_reference': A('lib_edit'),\n"
       "    'author_info': t('Author profile', 'ملف المؤلف')")
if "library_admin" not in s:
    s = s.replace(old, new, 1)
    print("titles fixed")
p.write_text(s, encoding="utf-8")

# 2) New references should not default to appearing in the magazine
p = Path("app/templates/library_form.html")
s = p.read_text(encoding="utf-8")
old = "{% set on_issue = ('in_issue' in f) if f else (item.in_issue if item else True) %}"
new = "{% set on_issue = ('in_issue' in f) if f else (item.in_issue if item else False) %}"
if old in s:
    s = s.replace(old, new, 1)
    print("new-reference issue default fixed")
p.write_text(s, encoding="utf-8")

# 3) Remove duplicate library rows caused by repeated discovery runs
sys.path.insert(0, "app")
import app as m
from collections import defaultdict

with m.app.app_context():
    db_path = m.app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    if db_path and not db_path.startswith("sqlite:"):
        backup = db_path + ".bak-before-library-dedupe"
        shutil.copy2(db_path, backup)
        print("backup", backup)

    groups = defaultdict(list)
    for row in m.LibraryReference.query.order_by(m.LibraryReference.id).all():
        groups[(row.url or "").strip().lower()].append(row)
    removed = 0
    for rows in groups.values():
        if len(rows) < 2:
            continue
        keep = rows[0]
        if any(r.in_issue for r in rows):
            keep.in_issue = True
        for row in rows[1:]:
            m.db.session.delete(row)
            removed += 1
    if removed:
        m.db.session.commit()
    print("duplicates removed", removed, "remaining", m.LibraryReference.query.count())
