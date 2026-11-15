from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# Appearance presets used by the admin settings page and the public shell.
if "MAGAZINE_THEMES" not in s:
    s = s.replace(
        "MAGAZINE_TEMPLATES = {'slate', 'broadsheet', 'wire', 'quarterly', 'bloom', 'circuit', 'mission', 'halo', 'digital'}",
        "MAGAZINE_TEMPLATES = {'slate', 'broadsheet', 'wire', 'quarterly', 'bloom', 'circuit', 'mission', 'halo', 'digital'}\n\n"
        "MAGAZINE_THEMES = [\n"
        "    ('paper', 'Paper', 'Warm editorial paper', '#fbfaf7', '#0b4f6c'),\n"
        "    ('ocean', 'Ocean', 'Cool blue, calm and clear', '#f2f8fb', '#075985'),\n"
        "    ('forest', 'Forest', 'Earthy green on cream', '#f4f7ef', '#1f5a3d'),\n"
        "    ('sunset', 'Sunset', 'Warm sand and terracotta', '#fdf5ef', '#9a3412'),\n"
        "    ('lilac', 'Lilac', 'Soft violet, modern', '#f7f4fb', '#6d4aa3'),\n"
        "]\n\n"
        "MAGAZINE_BACKGROUNDS = [\n"
        "    ('paper', 'Paper', 'A quiet paper texture'),\n"
        "    ('wash', 'Colour wash', 'Soft fields of colour behind the page'),\n"
        "    ('grid', 'Grid', 'Fine editorial grid lines'),\n"
        "    ('dots', 'Dots', 'A subtle dot matrix'),\n"
        "    ('aurora', 'Aurora', 'A bolder colour gradient'),\n"
        "    ('solid', 'Solid colour', 'One clean background colour'),\n"
        "    ('custom', 'Your image', 'Upload a photo as the page background'),\n"
        "]\n",
        1,
    )
    print("appearance presets added")

# Model columns
old = """    magazine_template = db.Column(db.String(30), default=\"slate\") # 'slate', 'broadsheet', 'wire', 'quarterly'"""
new = """    magazine_template = db.Column(db.String(30), default=\"slate\") # 'slate', 'broadsheet', 'wire', 'quarterly'

    # Public magazine appearance (the admin chrome has its own `theme` above).
    public_theme = db.Column(db.String(30), default=\"paper\")
    background_style = db.Column(db.String(30), default=\"wash\")
    background_image = db.Column(db.String(500), default=\"\")
    background_color = db.Column(db.String(20), default=\"#fbfaf7\")
    background_fixed = db.Column(db.Boolean, default=False)"""
if "public_theme = db.Column" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("model columns added")
    else:
        print("MODEL ANCHOR MISSING")
else:
    print("model columns already exist")

# Migration columns for existing SQLite databases
old = """                'cover_world_id': "VARCHAR(36) DEFAULT ''",
                'cover_campus_id': "VARCHAR(36) DEFAULT ''",
                'campus_kind_order': "TEXT DEFAULT ''","""
new = """                'cover_world_id': "VARCHAR(36) DEFAULT ''",
                'cover_campus_id': "VARCHAR(36) DEFAULT ''",
                'campus_kind_order': "TEXT DEFAULT ''",
                'public_theme': "VARCHAR(30) DEFAULT 'paper'",
                'background_style': "VARCHAR(30) DEFAULT 'wash'",
                'background_image': "VARCHAR(500) DEFAULT ''",
                'background_color': "VARCHAR(20) DEFAULT '#fbfaf7'",
                'background_fixed': "BOOLEAN DEFAULT 0","""
if "public_theme" not in s[s.find("new_cols = {"):s.find("new_cols = {")+3000]:
    if old in s:
        s = s.replace(old, new, 1)
        print("migration columns added")
    else:
        print("MIGRATION ANCHOR MISSING")
else:
    print("migration columns already exist")

# Save fields
old = """            settings.theme = request.form.get('theme') # Theme Setting"""
new = """            settings.theme = request.form.get('theme') # Admin theme
            public_theme = request.form.get('public_theme', 'paper')
            if public_theme not in {key for key, _label, _desc, _bg, _accent in MAGAZINE_THEMES}:
                public_theme = 'paper'
            background_style = request.form.get('background_style', 'wash')
            if background_style not in {key for key, _label, _desc in MAGAZINE_BACKGROUNDS}:
                background_style = 'wash'
            settings.public_theme = public_theme
            settings.background_style = background_style
            settings.background_fixed = bool(request.form.get('background_fixed'))
            bg_color = (request.form.get('background_color') or '').strip()
            settings.background_color = bg_color if __import__('re').match(r'^#[0-9a-fA-F]{6}$', bg_color) else '#fbfaf7'

            bg_file = request.files.get('background_image')
            if bg_file and bg_file.filename and allowed_file(bg_file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
                bg_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'backgrounds')
                os.makedirs(bg_dir, exist_ok=True)
                bg_name = secure_filename(f"bg_{uuid.uuid4().hex}_{bg_file.filename}")
                bg_file.save(os.path.join(bg_dir, bg_name))
                old_bg = settings.background_image
                settings.background_image = f"/static/uploads/images/backgrounds/{bg_name}"
                if old_bg and old_bg.startswith('/static/uploads/images/backgrounds/'):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_bg.replace('/static/uploads/', '', 1)))
                    except OSError:
                        pass
            if request.form.get('remove_background'):
                old_bg = settings.background_image
                settings.background_image = ''
                if old_bg and old_bg.startswith('/static/uploads/images/backgrounds/'):
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_bg.replace('/static/uploads/', '', 1)))
                    except OSError:
                        pass"""
if "background_style = request.form.get" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("save fields added")
    else:
        print("SAVE ANCHOR MISSING")
else:
    print("save fields already exist")

# Pass presets to the settings template
old = """    return render_template('settings.html', settings=settings,
                           api_providers=providers_status, custom_api_keys=custom_api_keys,
                           ai_desk=public_status(),"""
new = """    return render_template('settings.html', settings=settings,
                           api_providers=providers_status, custom_api_keys=custom_api_keys,
                           ai_desk=public_status(), magazine_themes=MAGAZINE_THEMES,
                           magazine_backgrounds=MAGAZINE_BACKGROUNDS,"""
if "magazine_themes=" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("settings context added")
    else:
        print("CONTEXT ANCHOR MISSING")
else:
    print("settings context already exists")

p.write_text(s, encoding="utf-8")
