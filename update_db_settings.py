import sqlite3
import os

db_paths = [
    'local_dev.db',
    'instance/local_dev.db',
    'app/local_dev.db',
    'app/instance/local_dev.db'
]

def add_column(cursor, table, col_name, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
        print(f"  - Added {col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"  - Column {col_name} already exists.")
        else:
            print(f"  - Error adding {col_name}: {e}")

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (File not found)")
        continue
        
    print(f"Migrating {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cols = ['color_h1', 'color_h2', 'color_h3', 'color_h4', 'color_h5', 'color_h6', 'color_p', 'color_li']
        for col in cols:
            add_column(cursor, 'magazine_settings', col, 'VARCHAR(20)')
            
        conn.commit()
        conn.close()
        print(f"  Completed {db_path}.\n")
    except Exception as e:
        print(f"  Failed {db_path}: {e}\n")
