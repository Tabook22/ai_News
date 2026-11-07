import sqlite3

def add_show_details_column():
    db_path = "app/instance/local_dev.db"  # Flask instance folder
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(news_items)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'show_details' not in columns:
            print("Adding 'show_details' column...")
            cursor.execute("ALTER TABLE news_items ADD COLUMN show_details BOOLEAN DEFAULT 0")
            conn.commit()
            print("Column added successfully.")
        else:
            print("'show_details' column already exists.")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_show_details_column()
