from pathlib import Path

# layout sidebar + title
p = Path("app/templates/layout.html")
s = p.read_text(encoding="utf-8")
anchor = '''                    <a href="{{ url_for('archive_page', desk='world') }}"'''
link = '''                    <a href="{{ url_for('resources_admin') }}"
                        class="{{ 'is-active' if request.endpoint in ['resources_admin', 'add_department_resource', 'edit_department_resource'] else '' }}">
                        <svg class="icon" aria-hidden="true"><use href="#i-folder"></use></svg>
                        {{ t('Downloads', 'ملفات القسم') }}
                    </a>
'''
if "url_for('resources_admin')" not in s:
    s = s.replace(anchor, link + anchor, 1)
    print("sidebar link added")
else:
    print("sidebar link exists")
s = s.replace("'edit_project_idea': 'Edit project idea'",
              "'edit_project_idea': 'Edit project idea', 'resources_admin': 'Downloads', 'add_department_resource': 'Upload a file', 'edit_department_resource': 'Edit download'", 1)
p.write_text(s, encoding="utf-8")

# public footer section link
p = Path("app/templates/public_v3.html")
s = p.read_text(encoding="utf-8")
old = '''                        <li><a href="{{ url_for('campus_weekly') }}">{{ 'القسم' if lang_pref == 'ar' else 'Department' }}</a></li>
                        <li><a href="{{ url_for('watch_page') }}">{{ 'مشاهدة' if lang_pref == 'ar' else 'Watch' }}</a></li>'''
new = '''                        <li><a href="{{ url_for('campus_weekly') }}">{{ 'القسم' if lang_pref == 'ar' else 'Department' }}</a></li>
                        <li><a href="{{ url_for('campus_downloads') }}">{{ 'ملفات القسم' if lang_pref == 'ar' else 'Downloads' }}</a></li>
                        <li><a href="{{ url_for('watch_page') }}">{{ 'مشاهدة' if lang_pref == 'ar' else 'Watch' }}</a></li>'''
if old in s:
    s = s.replace(old, new, 1)
    print("footer link added")
else:
    print("footer anchor missing")
p.write_text(s, encoding="utf-8")

# grammar public
p = Path("app/templates/resources_v3.html")
s = p.read_text(encoding="utf-8")
s = s.replace("<span><b>{{ total }}</b> {{ 'ملف' if ar else 'files' }}</span>",
              "<span><b>{{ total }}</b> {{ 'ملف' if ar else ('file' if total == 1 else 'files') }}</span>", 1)
p.write_text(s, encoding="utf-8")

# grammar admin
p = Path("app/templates/resources_admin.html")
s = p.read_text(encoding="utf-8")
s = s.replace("<div class=\"res-stat is-teal\"><b>{{ counts.all }}</b><span>{{ t('Files', 'ملف') }}</span></div>",
              "<div class=\"res-stat is-teal\"><b>{{ counts.all }}</b><span>{{ t('File', 'ملف') if counts.all == 1 else t('Files', 'ملفات') }}</span></div>", 1)
p.write_text(s, encoding="utf-8")
print("grammar patched")
