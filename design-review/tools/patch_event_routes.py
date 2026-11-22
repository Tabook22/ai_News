from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

public = '''

# ---------- National and seasonal events ----------

def _public_events(limit=None):
    rows = (NationalEvent.query.filter_by(is_approved=True)
            .order_by(NationalEvent.display_order.asc(),
                      NationalEvent.event_date.asc(), NationalEvent.id.asc()).all())
    items = [row.to_dict() for row in rows]
    active = [item for item in items if item['status'] != 'past']
    past = [item for item in items if item['status'] == 'past']
    active.sort(key=lambda item: (0 if item['is_featured'] else 1,
                                 item['event_date']))
    if limit:
        active = active[:limit]
    return active, past


@app.route('/events')
def events_page():
    ar = get_lang_pref() == 'ar'
    active, past = _public_events()
    return render_template('events.html', active=active, past=past, ar=ar,
                           today=_gulf_today())


@app.route('/events/<int:event_id>')
def event_detail(event_id):
    ar = get_lang_pref() == 'ar'
    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    return render_template('event_detail.html', event=event.to_dict(), ar=ar,
                           today=_gulf_today())


def _save_event_image(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
        return None
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'events')
    os.makedirs(folder, exist_ok=True)
    name = secure_filename(f"event_{uuid.uuid4().hex}_{file.filename}")
    file.save(os.path.join(folder, name))
    return f"/static/uploads/images/events/{name}"


def _apply_event_form(event):
    title = _question_clean(request.form.get('title_en'), 240)
    if not title:
        return 'The English title is required.'
    raw_date = (request.form.get('event_date') or '').strip()
    try:
        event_date = datetime.date.fromisoformat(raw_date)
    except ValueError:
        return 'Choose a valid event date.'
    end = None
    raw_end = (request.form.get('end_date') or '').strip()
    if raw_end:
        try:
            end = datetime.date.fromisoformat(raw_end)
        except ValueError:
            return 'Choose a valid end date.'
        if end < event_date:
            return 'The end date cannot be before the start date.'
    event_type = request.form.get('event_type', 'national')
    if event_type not in {key for key, _en, _ar in EVENT_TYPES}:
        event_type = 'national'
    link = (request.form.get('link_url') or '').strip()
    if link and not link.startswith(('/', 'http://', 'https://')):
        return 'The event link must be a site path or an http(s) URL.'
    accent = (request.form.get('accent') or '').strip()
    if not re.match(r'^#[0-9a-fA-F]{6}$', accent or ''):
        accent = '#0f766e'
    event.title_en = title
    event.title_ar = _question_clean(request.form.get('title_ar'), 240)
    event.kicker_en = _question_clean(request.form.get('kicker_en'), 120)
    event.kicker_ar = _question_clean(request.form.get('kicker_ar'), 120)
    event.description_en = _question_clean(request.form.get('description_en'), 1200)
    event.description_ar = _question_clean(request.form.get('description_ar'), 1200)
    event.event_type = event_type
    event.event_date = event_date
    event.end_date = end
    event.location_en = _question_clean(request.form.get('location_en'), 180)
    event.location_ar = _question_clean(request.form.get('location_ar'), 180)
    event.link_url = link
    event.link_label_en = _question_clean(request.form.get('link_label_en'), 100)
    event.link_label_ar = _question_clean(request.form.get('link_label_ar'), 100)
    event.accent = accent
    event.is_approved = bool(request.form.get('is_approved'))
    event.is_featured = bool(request.form.get('is_featured'))
    try:
        event.display_order = int(request.form.get('display_order') or 0)
    except ValueError:
        event.display_order = 0
    return None

'''
anchor = "@app.route('/library')\ndef reference_library():"
if "def events_page(" not in s:
    s = s.replace(anchor, public + anchor, 1)
    print("event public routes added")

admin = '''

@app.route('/desk/events')
@login_required
def events_admin():
    events = (NationalEvent.query
              .order_by(NationalEvent.event_date.desc(), NationalEvent.id.desc())
              .all())
    return render_template('events_admin.html', events=events)


@app.route('/desk/events/new', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        event = NationalEvent(title_en='', event_date=_gulf_today())
        error = _apply_event_form(event)
        image = _save_event_image(request.files.get('image'))
        if image:
            event.image = image
        if error:
            flash(error, 'error')
            return render_template('event_form.html', event=None, form=request.form,
                                   event_types=EVENT_TYPES, today=_gulf_today())
        db.session.add(event)
        db.session.commit()
        flash('Event saved. Tick “Approved” before it can appear on the magazine.', 'success')
        return redirect(url_for('events_admin'))
    return render_template('event_form.html', event=None, form=None,
                           event_types=EVENT_TYPES, today=_gulf_today())


@app.route('/desk/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    if request.method == 'POST':
        error = _apply_event_form(event)
        image = _save_event_image(request.files.get('image'))
        if image:
            old = event.image
            event.image = image
            if old:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                           old.replace('/static/uploads/', '', 1)))
                except OSError:
                    pass
        if request.form.get('remove_image'):
            old = event.image
            event.image = ''
            if old:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                           old.replace('/static/uploads/', '', 1)))
                except OSError:
                    pass
        if error:
            flash(error, 'error')
        else:
            db.session.commit()
            flash('Event updated.', 'success')
            return redirect(url_for('events_admin'))
    return render_template('event_form.html', event=event, form=None,
                           event_types=EVENT_TYPES, today=_gulf_today())


@app.route('/desk/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    image = event.image
    db.session.delete(event)
    db.session.commit()
    if image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                   image.replace('/static/uploads/', '', 1)))
        except OSError:
            pass
    flash('Event deleted.', 'success')
    return redirect(url_for('events_admin'))

'''
anchor2 = "@app.route('/desk/library')\n@login_required\ndef library_admin():"
if "def events_admin(" not in s:
    s = s.replace(anchor2, admin + anchor2, 1)
    print("event admin routes added")

# homepage data
s = s.replace("        daily_question=_question_for(),",
              "        daily_question=_question_for(),\n        national_events=_public_events(limit=3)[0],", 1)

p.write_text(s, encoding="utf-8")
