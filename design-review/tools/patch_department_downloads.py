from pathlib import Path

p = Path("app/templates/department.html")
s = p.read_text(encoding="utf-8")

old = '''        <div class="dept-stat is-indigo">
            <b>{{ stats.projects }}</b>
            <span>{{ stats.research }} {{ t('research', 'بحثية') }} · {{ stats.competitions }} {{ t('competitions', 'مسابقات') }}</span>
        </div>'''
new = '''        <div class="dept-stat is-indigo">
            <b>{{ stats.projects }}</b>
            <span>{{ stats.research }} {{ t('research', 'بحثية') }} · {{ stats.competitions }} {{ t('competitions', 'مسابقات') }}</span>
        </div>
        <a class="dept-stat is-blue" href="{{ url_for('resources_admin') }}">
            <b>{{ stats.resources }}</b>
            <span>{{ t('Downloads', 'ملفات') }}</span>
        </a>'''
if old in s:
    s = s.replace(old, new, 1)
    print("stat added")
else:
    print("stat anchor missing")

old2 = '''                            <a href="{{ url_for('photo_archive_admin') }}">
                                <svg class="icon" aria-hidden="true"><use href="#i-image"></use></svg>
                                <span><b>{{ t('Add photos', 'أضف صورًا') }}</b><small>{{ stats.photos }} {{ t('photos in the archive', 'صورة في الأرشيف') }}</small></span>
                            </a>'''
new2 = old2 + '''
                            <a href="{{ url_for('resources_admin') }}">
                                <svg class="icon" aria-hidden="true"><use href="#i-folder"></use></svg>
                                <span><b>{{ t('Downloads', 'ملفات القسم') }}</b><small>{{ stats.resources }} {{ t('files for students', 'ملفًا للطلبة') }}</small></span>
                            </a>'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print("shortcut added")
else:
    print("shortcut anchor missing")

p.write_text(s, encoding="utf-8")
