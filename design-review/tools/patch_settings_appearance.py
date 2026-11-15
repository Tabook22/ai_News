from pathlib import Path

p = Path("app/templates/settings.html")
s = p.read_text(encoding="utf-8")

anchor = '''                </div>

                <details class="advanced-colors">'''
block = '''                </div>

                <div class="settings-subheader">Magazine theme</div>
                <p class="settings-hint" style="margin-top:0.35rem;">The public magazine keeps exactly the same layout. This changes the paper, ink and accent colours.</p>
                <div class="choice-cards">
                    {% for key, label, desc, swatch_bg, swatch_accent in magazine_themes %}
                    <label class="choice-card">
                        <input type="radio" name="public_theme" value="{{ key }}"
                            {{ 'checked' if settings.public_theme == key or (not settings.public_theme and key == 'paper') else '' }}>
                        <span class="choice-card-body">
                            <span class="swatch-row">
                                <span class="swatch-dot" style="background:{{ swatch_bg }}; border:1px solid rgba(15,23,42,.18);"></span>
                                <span class="swatch-dot" style="background:{{ swatch_accent }};"></span>
                            </span>
                            <span class="choice-card-label">{{ label }}</span>
                            <span style="font-size:0.78rem; color:var(--text-muted);">{{ desc }}</span>
                        </span>
                    </label>
                    {% endfor %}
                </div>

                <div class="settings-subheader">Magazine background</div>
                <p class="settings-hint" style="margin-top:0.35rem;">Pick a page canvas. This is behind the existing layout, never inside it.</p>
                <div class="background-cards">
                    {% for key, label, desc in magazine_backgrounds %}
                    <label class="background-card">
                        <input type="radio" name="background_style" value="{{ key }}"
                            {{ 'checked' if settings.background_style == key or (not settings.background_style and key == 'wash') else '' }}>
                        <span class="bg-preview is-{{ key }}" aria-hidden="true"></span>
                        <span class="bg-copy">
                            <b>{{ label }}</b>
                            <small>{{ desc }}</small>
                        </span>
                    </label>
                    {% endfor %}
                </div>

                <div class="field-grid" style="margin-top:1rem; align-items:end;">
                    <div class="color-swatch-input">
                        <label>Background colour</label>
                        <input type="color" name="background_color"
                            value="{{ settings.background_color or '#fbfaf7' }}">
                    </div>
                    <label class="check-line" style="margin:0 0 0.55rem;">
                        <input type="checkbox" name="background_fixed" {{ 'checked' if settings.background_fixed else '' }}>
                        Keep the image fixed while scrolling
                    </label>
                </div>

                <div class="settings-subheader" style="font-size:0.9rem; margin-top:1.4rem;">Your own background image</div>
                <div class="editor-field bg-upload-field">
                    <label for="background_image">Upload a background</label>
                    <input id="background_image" type="file" name="background_image" accept=".jpg,.jpeg,.png,.webp">
                    <p class="settings-hint">Used when <b>Your image</b> is selected above. JPG, PNG or WebP. A light paper wash is added automatically so the text stays readable.</p>
                    {% if settings.background_image %}
                    <div class="bg-current-preview">
                        <img src="{{ settings.background_image }}" alt="Current magazine background">
                        <label class="check-line">
                            <input type="checkbox" name="remove_background">
                            Remove this image
                        </label>
                    </div>
                    {% endif %}
                </div>

                <details class="advanced-colors">'''
if "Magazine background" not in s:
    if anchor in s:
        s = s.replace(anchor, block, 1)
        print("settings appearance added")
    else:
        print("SETTINGS ANCHOR MISSING")
else:
    print("settings appearance already exists")

p.write_text(s, encoding="utf-8")
