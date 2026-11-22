from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

# Detailed event route with gallery count
old = """    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    return render_template('event_detail.html', event=event.to_dict(), ar=ar,
                           today=_gulf_today())"""
new = """    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    data = event.to_dict()
    photos = list(event.photos)
    data['has_gallery'] = bool(photos)
    data['photo_count'] = len(photos)
    return render_template('event_detail.html', event=data, ar=ar,
                           today=_gulf_today())"""
if "data['has_gallery']" not in s:
    s = s.replace(old, new, 1)
    print("event detail gallery count added")

public = '''

@app.route('/events/<int:event_id>/gallery')
def event_gallery(event_id):
    ar = get_lang_pref() == 'ar'
    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    photos = [photo.to_dict() for photo in event.photos]
    return render_template('event_gallery.html', event=event.to_dict(), photos=photos,
                           ar=ar, today=_gulf_today())


def _save_event_photo(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'webp'}):
        return None
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'images', 'events')
    os.makedirs(folder, exist_ok=True)
    name = secure_filename(f"event_photo_{uuid.uuid4().hex}_{file.filename}")
    file.save(os.path.join(folder, name))
    return f"/static/uploads/images/events/{name}"


'''
anchor = "def _save_event_image(file):"
if "def event_gallery(" not in s:
    s = s.replace(anchor, public + anchor, 1)
    print("event gallery public route added")

admin = '''

@app.route('/desk/events/<int:event_id>/gallery')
@login_required
def event_gallery_admin(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    return render_template('event_gallery_admin.html', event=event,
                           photos=event.photos)


@app.route('/desk/events/<int:event_id>/gallery/upload', methods=['POST'])
@login_required
def upload_event_photo(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    image = _save_event_photo(request.files.get('image'))
    if not image:
        flash('Choose a JPG, PNG or WebP image.', 'error')
        return redirect(url_for('event_gallery_admin', event_id=event.id))
    try:
        order = int(request.form.get('display_order') or 0)
    except ValueError:
        order = 0
    db.session.add(EventPhoto(
        event_id=event.id,
        image=image,
        caption_en=_question_clean(request.form.get('caption_en'), 1000),
        caption_ar=_question_clean(request.form.get('caption_ar'), 1000),
        display_order=order,
    ))
    db.session.commit()
    flash('Image added to the gallery.', 'success')
    return redirect(url_for('event_gallery_admin', event_id=event.id))


@app.route('/desk/events/gallery/<int:photo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event_photo(photo_id):
    photo = EventPhoto.query.get_or_404(photo_id)
    event = photo.event
    if request.method == 'POST':
        photo.caption_en = _question_clean(request.form.get('caption_en'), 1000)
        photo.caption_ar = _question_clean(request.form.get('caption_ar'), 1000)
        try:
            photo.display_order = int(request.form.get('display_order') or 0)
        except ValueError:
            photo.display_order = 0
        new_image = _save_event_photo(request.files.get('image'))
        if new_image:
            old = photo.image
            photo.image = new_image
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       old.replace('/static/uploads/', '', 1)))
            except OSError:
                pass
        db.session.commit()
        flash('Gallery image updated.', 'success')
        return redirect(url_for('event_gallery_admin', event_id=event.id))
    return render_template('event_photo_form.html', photo=photo, event=event)


@app.route('/desk/events/gallery/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_event_photo(photo_id):
    photo = EventPhoto.query.get_or_404(photo_id)
    event_id = photo.event_id
    image = photo.image
    db.session.delete(photo)
    db.session.commit()
    if image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                   image.replace('/static/uploads/', '', 1)))
        except OSError:
            pass
    flash('Gallery image deleted.', 'success')
    return redirect(url_for('event_gallery_admin', event_id=event_id))

'''
anchor2 = "@app.route('/desk/library')\n@login_required\ndef library_admin():"
if "def event_gallery_admin(" not in s:
    s = s.replace(anchor2, admin + anchor2, 1)
    print("event gallery admin routes added")

# Clean gallery images when deleting an event
old_delete = """def delete_event(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    image = event.image
    db.session.delete(event)"""
new_delete = """def delete_event(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    image = event.image
    gallery_images = [photo.image for photo in event.photos]
    db.session.delete(event)"""
if "gallery_images = [photo.image for photo in event.photos]" not in s:
    s = s.replace(old_delete, new_delete, 1)
    old_after = """    if image:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                   image.replace('/static/uploads/', '', 1)))
        except OSError:
            pass
    flash('Event deleted.', 'success')"""
    new_after = """    for filename in ([image] if image else []) + gallery_images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                   filename.replace('/static/uploads/', '', 1)))
        except OSError:
            pass
    flash('Event deleted.', 'success')"""
    s = s.replace(old_after, new_after, 1)
    print("event gallery cleanup added")

p.write_text(s, encoding="utf-8")
