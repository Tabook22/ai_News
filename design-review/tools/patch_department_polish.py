from pathlib import Path

p = Path("app/templates/department.html")
s = p.read_text(encoding="utf-8")

s = s.replace("{{ A('dept_intro') }}",
              "{{ t('Publish notices, manage topics, curate the photo archive, and add project ideas for students.', 'انشر الإعلانات، وأدر المواضيع، ونسّق أرشيف الصور، وأضف أفكار مشاريع للطلبة.') }}", 1)

old = '''        <div class="dept-albums">
            {% for album in albums %}
            <a class="dept-album" href="{{ url_for('photo_archive_admin') }}#album-{{ album.id }}">
                <span class="dept-album-cover">
                    {% if album.photos %}
                    <img src="{{ album.photos[0].image }}" alt="" loading="lazy">
                    {% else %}
                    <svg class="icon" aria-hidden="true"><use href="#i-image"></use></svg>
                    {% endif %}
                </span>
                <span class="dept-album-copy">
                    <b>{{ (album.title_ar or album.title) if admin_ar else album.title }}</b>
                    <small>{{ album.photos|length }} {{ t('photos', 'صورة') }} · {{ album.term }} {{ album.year }}</small>
                </span>
                <svg class="icon" aria-hidden="true"><use href="#i-arrow"></use></svg>
            </a>
            {% else %}
            <p class="dept-empty">{{ t('No albums yet. Add the first one.', 'لا توجد ألبومات بعد. أضف الأول.') }}</p>
            {% endfor %}
        </div>'''
new = '''        {% if albums %}
        <div class="dept-albums">
            {% for album in albums %}
            <a class="dept-album" href="{{ url_for('photo_archive_admin') }}#album-{{ album.id }}">
                <span class="dept-album-cover">
                    {% if album.photos %}
                    <img src="{{ album.photos[0].image }}" alt="" loading="lazy">
                    {% else %}
                    <svg class="icon" aria-hidden="true"><use href="#i-image"></use></svg>
                    {% endif %}
                </span>
                <span class="dept-album-copy">
                    <b>{{ (album.title_ar or album.title) if admin_ar else album.title }}</b>
                    <small>{{ album.photos|length }} {{ t('photos', 'صورة') }} · {{ album.term }} {{ album.year }}</small>
                </span>
                <svg class="icon" aria-hidden="true"><use href="#i-arrow"></use></svg>
            </a>
            {% endfor %}
        </div>
        {% else %}
        <div class="dept-empty-state">
            <span class="dept-empty-icon"><svg class="icon" aria-hidden="true"><use href="#i-image"></use></svg></span>
            <h3>{{ t('No photo albums yet', 'لا توجد ألبومات صور بعد') }}</h3>
            <p>{{ t('Create an occasion album, drop the photos, and publish it. It will appear on the public department page automatically.', 'أنشئ ألبوم مناسبة، وأفلت الصور، وانشره. سيظهر تلقائيًا في صفحة القسم العامة.') }}</p>
            <a class="btn btn-primary" href="{{ url_for('photo_archive_admin') }}">
                <svg class="icon" aria-hidden="true"><use href="#i-plus"></use></svg>
                {{ t('Create the first album', 'أنشئ الألبوم الأول') }}
            </a>
        </div>
        {% endif %}'''
if old in s:
    s = s.replace(old, new, 1)
    print("photos empty state patched")
else:
    print("photos anchor missing")

p.write_text(s, encoding="utf-8")
