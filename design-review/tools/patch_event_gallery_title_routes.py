from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

helper = '''

def _gallery_for_event(event):
    """Return the event's one gallery, creating it for older events."""
    gallery = event.gallery
    if gallery is None:
        gallery = EventGallery(
            event_id=event.id,
            title_en=event.title_en or '',
            title_ar=event.title_ar or '',
        )
        db.session.add(gallery)
        db.session.flush()
    for photo in event.photos:
        if not photo.gallery_id:
            photo.gallery_id = gallery.id
    db.session.commit()
    return gallery


'''
anchor = "def event_gallery(event_id):"
if "def _gallery_for_event(" not in s:
    s = s.replace(anchor, helper + anchor, 1)
    print("gallery helper added")

old = '''def event_gallery(event_id):
    ar = get_lang_pref() == 'ar'
    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    photos = [photo.to_dict() for photo in event.photos]
    return render_template('event_gallery.html', event=event.to_dict(), photos=photos,
                           ar=ar, today=_gulf_today())'''
new = '''def event_gallery(event_id):
    ar = get_lang_pref() == 'ar'
    event = NationalEvent.query.get_or_404(event_id)
    if not event.is_approved:
        abort(404)
    gallery = _gallery_for_event(event)
    photos = sorted(gallery.photos, key=lambda photo: (photo.display_order or 0, photo.id))
    return render_template('event_gallery.html', event=event.to_dict(),
                           gallery=gallery.to_dict(),
                           photos=[photo.to_dict() for photo in photos],
                           ar=ar, today=_gulf_today())'''
if "gallery=gallery.to_dict()" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("public gallery route scoped")
    else:
        print("PUBLIC GALLERY ANCHOR MISSING")

old = '''def event_gallery_admin(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    photos = sorted(event.photos, key=lambda photo: (photo.display_order or 0, photo.id))
    return render_template('event_gallery_admin.html', event=event,
                           photos=photos)'''
new = '''def event_gallery_admin(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    gallery = _gallery_for_event(event)
    photos = sorted(gallery.photos, key=lambda photo: (photo.display_order or 0, photo.id))
    return render_template('event_gallery_admin.html', event=event,
                           gallery=gallery, photos=photos)'''
if "gallery=gallery, photos=photos" not in s:
    if old in s:
        s = s.replace(old, new, 1)
        print("admin gallery route scoped")
    else:
        print("ADMIN GALLERY ANCHOR MISSING")

old = '''def upload_event_photo(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    image = _save_event_photo(request.files.get('image'))'''
new = '''def upload_event_photo(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    gallery = _gallery_for_event(event)
    image = _save_event_photo(request.files.get('image'))'''
if "gallery = _gallery_for_event(event)\n    image = _save_event_photo" not in s:
    s = s.replace(old, new, 1)
    print("upload gallery scoped")

s = s.replace('''    db.session.add(EventPhoto(
        event_id=event.id,
        image=image,''','''    db.session.add(EventPhoto(
        event_id=event.id,
        gallery_id=gallery.id,
        image=image,''',1)

settings_route = '''

@app.route('/desk/events/<int:event_id>/gallery/settings', methods=['POST'])
@login_required
def edit_event_gallery(event_id):
    event = NationalEvent.query.get_or_404(event_id)
    gallery = _gallery_for_event(event)
    gallery.title_en = _question_clean(request.form.get('title_en'), 240)
    gallery.title_ar = _question_clean(request.form.get('title_ar'), 240)
    gallery.description_en = _question_clean(request.form.get('description_en'), 1000)
    gallery.description_ar = _question_clean(request.form.get('description_ar'), 1000)
    db.session.commit()
    flash('Gallery title updated.', 'success')
    return redirect(url_for('event_gallery_admin', event_id=event.id))

'''
anchor2 = "@app.route('/desk/events/<int:event_id>/gallery/upload', methods=['POST'])"
if "def edit_event_gallery(" not in s:
    s = s.replace(anchor2, settings_route + anchor2, 1)
    print("gallery settings route added")

p.write_text(s, encoding="utf-8")
