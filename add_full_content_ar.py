import sqlite3

def add_full_content_ar_column():
    db_path = "app/instance/local_dev.db"  # Flask instance folder
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(news_items)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'full_content_ar' not in columns:
            print("Adding 'full_content_ar' column...")
            cursor.execute("ALTER TABLE news_items ADD COLUMN full_content_ar TEXT")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'full_content_ar' column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_full_content_ar_column()
