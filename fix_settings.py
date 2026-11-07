
import sys
import os
from app.app import app, db, MagazineSettings

def fix_settings():
    with app.app_context():
        settings = MagazineSettings.get_settings()
        print(f"Current Mode: {settings.language_mode}")
        if settings.language_mode != 'bilingual':
            settings.language_mode = 'bilingual'
            db.session.commit()
            print("✅ Fixed: Language Mode set to 'bilingual'.")
        else:
            print("Settings already correct.")

if __name__ == "__main__":
    fix_settings()
