from pathlib import Path

p = Path("app/templates/article_v3.html")
s = p.read_text(encoding="utf-8")

addition = '''
<div class="share-card-overlay" id="share-card-overlay" hidden>
    <div class="share-card-dialog" role="dialog" aria-modal="true" aria-labelledby="share-card-title">
        <div class="share-card-head">
            <b id="share-card-title">{{ 'بطاقة مشاركة' if ar else 'Share card' }}</b>
            <button type="button" class="share-card-close" data-share-card-close
                aria-label="{{ 'إغلاق' if ar else 'Close' }}">&times;</button>
        </div>
        <canvas id="share-card-canvas" width="1080" height="1350"
            aria-label="{{ 'بطاقة مشاركة للقصة' if ar else 'Story share card' }}"></canvas>
        <div class="share-card-actions">
            <button type="button" class="btn btn-primary" data-share-card-download>
                {{ 'تنزيل الصورة' if ar else 'Download PNG' }}
            </button>
            <button type="button" class="btn btn-secondary" data-share-card-close>
                {{ 'إغلاق' if ar else 'Close' }}
            </button>
        </div>
        <p class="share-card-hint">{{ 'صورة جاهزة للنشر على واتساب أو لينكدإن أو إنستغرام. الرابط ورمز الاستجابة مضمنان.' if ar else 'Ready to post on WhatsApp, LinkedIn or Instagram. The link and QR code are included.' }}</p>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
window.SHARE_CARD = {
    title: {{ title | tojson }},
    summary: {{ (summary or '') | striptags | truncate(220) | tojson }},
    source: {{ (item.source or magazine_name) | tojson }},
    desk: {{ ((item.desk_ar if ar and item.desk_ar else item.desk_en) or '') | tojson }},
    url: {{ request.base_url | tojson }},
    qr: {{ url_for('share_qr_png', target=request.base_url, _external=True) | tojson }},
    brand: {{ magazine_name | tojson }},
    arabic: {{ ar | tojson }}
};
</script>
<script src="{{ url_for('static', filename='js/share-card.js') }}" defer></script>
{% endblock %}
'''

pos = s.rfind("{% endblock %}")
if pos == -1:
    raise SystemExit("endblock missing")
s = s[:pos] + addition
p.write_text(s, encoding="utf-8")
print("share card markup and scripts added")
