from pathlib import Path

p = Path("app/templates/department.html")
s = p.read_text(encoding="utf-8")

tab_anchor = '''            <span>{{ stats.projects }}</span>
        </button>
    </div>'''
tab_new = '''            <span>{{ stats.projects }}</span>
        </button>
        <button type="button" class="dept-tab" data-dept-tab="downloads" role="tab" aria-selected="false">
            <svg class="icon" aria-hidden="true"><use href="#i-folder"></use></svg>
            {{ t('Downloads', 'ملفات القسم') }}
            <span>{{ stats.resources }}</span>
        </button>
    </div>'''
if tab_anchor in s:
    s = s.replace(tab_anchor, tab_new, 1)
    print("downloads tab added")
else:
    print("tab anchor missing")

panel_anchor = '''    </section>
</div>

<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>'''
panel_new = '''    </section>

    <section class="dept-panel" data-dept-panel="downloads" hidden>
        <div class="dept-panel-head">
            <div>
                <h2>{{ t('Department downloads', 'ملفات القسم') }}</h2>
                <p>{{ t('Course notes, syllabi, policies, forms and workshop material for students.', 'ملاحظات المقررات والخطط والسياسات والنماذج ومواد الورش للطلبة.') }}</p>
            </div>
            <div class="dept-panel-actions">
                <a href="{{ url_for('resources_admin') }}" class="btn btn-secondary">{{ t('Manage all', 'إدارة الكل') }}</a>
                <a href="{{ url_for('add_department_resource') }}" class="btn btn-primary">
                    <svg class="icon" aria-hidden="true"><use href="#i-plus"></use></svg>
                    {{ t('Upload a file', 'رفع ملف') }}
                </a>
            </div>
        </div>

        {% if resources %}
        <div class="res-list">
            {% for item in resources %}
            <article class="res-row">
                <span class="file-type is-{{ item.file_type }}">{{ item.file_type|upper or 'FILE' }}</span>
                <div class="res-main">
                    <b>{{ (item.title_ar or item.title) if admin_ar else item.title }}</b>
                    <small>
                        {{ item.category_ar if admin_ar else item.category_en }}
                        {% if item.course %} · {{ item.course }}{% endif %}
                        · {{ item.size_label }}
                    </small>
                </div>
                <span class="res-downloads">{{ item.download_count }} ↓</span>
                <span class="res-status {{ 'is-live' if item.is_published else 'is-hidden' }}">{{ t('Published', 'منشور') if item.is_published else t('Hidden', 'مخفي') }}</span>
                <div class="res-actions">
                    <a href="{{ url_for('download_department_resource', resource_id=item.id) }}">{{ t('Open', 'فتح') }}</a>
                    <a href="{{ url_for('edit_department_resource', resource_id=item.id) }}">{{ t('Edit', 'تعديل') }}</a>
                    <form method="POST" action="{{ url_for('delete_department_resource', resource_id=item.id) }}" onsubmit="return confirm('{{ t('Remove this file?', 'إزالة هذا الملف؟') }}');">
                        <button type="submit" class="is-danger">{{ t('Delete', 'حذف') }}</button>
                    </form>
                </div>
            </article>
            {% endfor %}
        </div>
        {% else %}
        <div class="dept-empty-state">
            <span class="dept-empty-icon"><svg class="icon" aria-hidden="true"><use href="#i-folder"></use></svg></span>
            <h3>{{ t('No downloads yet', 'لا توجد ملفات بعد') }}</h3>
            <p>{{ t('Upload the first course note, syllabus or policy. It will appear on the public department page.', 'ارفع أول ملاحظة أو خطة أو سياسة، وستظهر في صفحة القسم العامة.') }}</p>
            <a class="btn btn-primary" href="{{ url_for('add_department_resource') }}">
                <svg class="icon" aria-hidden="true"><use href="#i-plus"></use></svg>
                {{ t('Upload the first file', 'ارفع الملف الأول') }}
            </a>
        </div>
        {% endif %}
    </section>
</div>

<script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>'''
if panel_anchor in s:
    s = s.replace(panel_anchor, panel_new, 1)
    print("downloads panel added")
else:
    print("panel anchor missing")

s = s.replace("['compose', 'posts', 'photos', 'projects']", "['compose', 'posts', 'photos', 'projects', 'downloads']", 1)
p.write_text(s, encoding="utf-8")
print("tab js updated")
