from pathlib import Path

p = Path("app/app.py")
s = p.read_text(encoding="utf-8")

func = '''

def _ensure_event_galleries():
    """Create one gallery per event and attach any legacy photos to it."""
    try:
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        if 'event_photos' in tables:
            columns = [c['name'] for c in inspector.get_columns('event_photos')]
            if 'gallery_id' not in columns:
                print("⚠️  event_photos.gallery_id missing. Adding...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("ALTER TABLE event_photos ADD COLUMN gallery_id INTEGER"))
                    conn.commit()
        if 'event_galleries' not in tables:
            return
        for event in NationalEvent.query.all():
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
        print("✅ Event galleries checked/completed.")
    except Exception as exc:
        db.session.rollback()
        print(f"⚠️ Event gallery migration warning: {exc}")


'''
anchor = "# Initialize DB (Safe)"
if "_ensure_event_galleries" not in s:
    s = s.replace(anchor, func + anchor, 1)
    s = s.replace("        seed_reference_library()", "        _ensure_event_galleries()\n        seed_reference_library()", 1)
    print("gallery migration added")
p.write_text(s, encoding="utf-8")
