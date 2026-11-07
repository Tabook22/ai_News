from pathlib import Path

# ---------- public_v3 ----------
p = Path("app/templates/public_v3.html")
s = p.read_text(encoding="utf-8")

s = s.replace(
    '''<link rel="stylesheet" href="{{ url_for('static', filename='css/issue-v3.css') }}">''',
    '''<link rel="stylesheet" href="{{ url_for('static', filename='css/issue-v3.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/disclaimer.css') }}">''', 1)

s = s.replace(
    '''                <span>{{ 'صُنع في قسم علوم الحاسوب' if lang_pref == 'ar' else 'Made in the Department of Computer Science' }}</span>''',
    '''                <span>{{ 'صُنع في قسم علوم الحاسوب' if lang_pref == 'ar' else 'Made in the Department of Computer Science' }} · <button type="button" class="footer-disclaimer" data-disclaimer-open>{{ 'إخلاء المسؤولية' if lang_pref == 'ar' else 'Disclaimer' }}</button></span>''', 1)

s = s.replace(
    '''    <!-- search overlay -->''',
    '''    {% include '_disclaimer_modal.html' %}

    <!-- search overlay -->''', 1)

s = s.replace(
    '''    <script src="{{ url_for('static', filename='js/issue-v3.js') }}"></script>''',
    '''    <script src="{{ url_for('static', filename='js/disclaimer.js') }}" defer></script>
    <script src="{{ url_for('static', filename='js/issue-v3.js') }}"></script>''', 1)

p.write_text(s, encoding="utf-8")
print("public_v3 patched")

# ---------- public.html (classic pages) ----------
p = Path("app/templates/public.html")
s = p.read_text(encoding="utf-8")

s = s.replace(
    '''<link rel="stylesheet" href="{{ url_for('static', filename='css/issue.css') }}">''',
    '''<link rel="stylesheet" href="{{ url_for('static', filename='css/issue.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/disclaimer.css') }}">''', 1)

s = s.replace(
    '''                    <script>document.write(new Date().getFullYear())</script>
                </div>''',
    '''                    <script>document.write(new Date().getFullYear())</script>
                    <button type="button" class="footer-disclaimer" data-disclaimer-open style="margin-inline-start:8px;">{{ 'إخلاء المسؤولية' if lang_pref == 'ar' else 'Disclaimer' }}</button>
                </div>''', 1)

s = s.replace(
    '''    <!-- Global Source Modal''',
    '''    {% include '_disclaimer_modal.html' %}

    <!-- Global Source Modal''', 1)

s = s.replace(
    '''<script src="{{ url_for('static', filename='js/scripts.js') }}"></script>''',
    '''<script src="{{ url_for('static', filename='js/disclaimer.js') }}" defer></script>
<script src="{{ url_for('static', filename='js/scripts.js') }}"></script>''', 1)

p.write_text(s, encoding="utf-8")
print("public.html patched")
