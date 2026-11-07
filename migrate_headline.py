import sqlite3
import os

# List of potential DB paths identified
db_files = [
    'local_dev.db',
    'admin.db', 
    'instance/local_dev.db',
    'app/local_dev.db',
    'app/instance/local_dev.db'
]

print("Starting FORCE migration on all detected DB files...")

for db_path in db_files:
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (File not found)")
        continue
        
    print(f"\nProcessing {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        try:
            cursor.execute("SELECT headline_display_mode FROM news_items LIMIT 1")
            print(f"✅ Column already exists in {db_path}")
        except sqlite3.OperationalError:
            print(f"⚠️ Column missing in {db_path}. Adding it...")
            try:
                cursor.execute("ALTER TABLE news_items ADD COLUMN headline_display_mode VARCHAR(20) DEFAULT 'default'")
                conn.commit()
                print(f"✅ Successfully added column to {db_path}")
            except Exception as e:
                print(f"❌ Failed to add column to {db_path}: {e}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Could not connect to {db_path}: {e}")

print("\nMigration checks complete.")
