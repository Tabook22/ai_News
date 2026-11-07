from pathlib import Path

# anchor ids on project cards
p = Path("app/templates/campus_projects_v3.html")
s = p.read_text(encoding="utf-8")
s = s.replace('<article class="project-card project-area-{{ idea.area }}">',
              '<article id="idea-{{ idea.id }}" class="project-card project-area-{{ idea.area }}">', 1)
p.write_text(s, encoding="utf-8")

# campus page block + meta link
p = Path("app/templates/campus_v3.html")
s = p.read_text(encoding="utf-8")

meta_old = """            <a href="{{ url_for('campus_photos') }}">{{ 'أرشيف الصور' if ar else 'Photo archive' }}</a>
            {% endif %}"""
meta_new = """            <a href="{{ url_for('campus_photos') }}">{{ 'أرشيف الصور' if ar else 'Photo archive' }}</a>
            {% endif %}
            {% if project_total %}
            <span class="dot" aria-hidden="true"></span>
            <a href="{{ url_for('campus_projects') }}">{{ 'مشاريع مقترحة' if ar else 'Recommended projects' }}</a>
            {% endif %}"""
if meta_old in s:
    s = s.replace(meta_old, meta_new, 1)
    print("meta link added")
else:
    print("meta anchor missing")

block = """    {% if featured_projects %}
    <section class="section" aria-labelledby="projects-title">
        <header class="section-head">
            <span class="num" aria-hidden="true">04</span>
            <h2 id="projects-title">{{ 'مشاريع مقترحة' if ar else 'Recommended projects' }}</h2>
            <p>{{ 'أفكار لمشروع السنة الأخيرة، كل واحدة بوصف بسيط ومرجع لما بُنيت عليه.' if ar else 'Final-year project ideas, each with a short brief and a reference for where it comes from.' }}</p>
            <a class="more" href="{{ url_for('campus_projects') }}">{{ 'كل الأفكار' if ar else 'All ideas' }} ({{ project_total }}) →</a>
        </header>
        <div class="project-strip">
            {% for idea in featured_projects %}
            <a class="project-mini project-area-{{ idea.area }}" href="{{ url_for('campus_projects') }}#idea-{{ idea.id }}">
                <span class="project-area">{{ idea.area_ar if ar else idea.area_en }}</span>
                <b>{{ (idea.title_ar or idea.title_en) if ar else idea.title_en }}</b>
                <span class="project-mini-summary">{{ (idea.summary_ar or idea.summary_en) if ar else idea.summary_en }}</span>
                <span class="project-mini-ref">{{ 'المرجع' if ar else 'Reference' }}: {{ idea.reference_title }} ↗</span>
            </a>
            {% endfor %}
        </div>
    </section>
    {% endif %}

"""
anchor = '    <div class="subscribe" id="subscribe">'
if 'projects-title' not in s:
    s = s.replace(anchor, block + anchor, 1)
    print("campus section inserted")
else:
    print("section already exists")

p.write_text(s, encoding="utf-8")
