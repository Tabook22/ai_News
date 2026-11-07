import sqlite3

def add_display_order_column():
    db_path = "app/instance/local_dev.db"  # CORRECTED PATH (Likely Flask Instance Folder)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(news_items)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'display_order' not in columns:
            print("Adding 'display_order' column...")
            cursor.execute("ALTER TABLE news_items ADD COLUMN display_order INTEGER DEFAULT 0")
            
            # Initialize order based on timestamp (newest first)
            print("Initializing order...")
            cursor.execute("SELECT id FROM news_items ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            for idx, (item_id,) in enumerate(rows):
                cursor.execute("UPDATE news_items SET display_order = ? WHERE id = ?", (idx, item_id))
            
            conn.commit()
            print("Column added and initialized successfully.")
        else:
            print("'display_order' column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_display_order_column()
