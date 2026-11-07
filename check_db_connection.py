import os
import sys
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def check_connection():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ Error: DATABASE_URL is missing in .env file.")
        return

    print(f"Checking connection to: {db_url}")
    
    try:
        # Parse URL to display clearer info (masking password)
        result = urlparse(db_url)
        print(f"  - Host: {result.hostname}")
        print(f"  - Port: {result.port or 5432}")
        print(f"  - User: {result.username}")
        print(f"  - Database: {result.path.lstrip('/')}")
        
        # Attempt connection
        conn = psycopg2.connect(db_url)
        conn.close()
        print("\n✅ SUCCESS! Connection to PostgreSQL established.")
        print("You can now run the application with: python -m flask run")
        
    except psycopg2.OperationalError as e:
        print("\n❌ CONNECTION FAILED")
        print("---------------------------------------------------")
        print(f"Error details: {e}")
        print("---------------------------------------------------")
        print("Troubleshooting steps:")
        print("1. Is PostgreSQL installed and running?")
        print("2. Does the database 'nasser_news' exist? (Create it via pgAdmin or psql)")
        print("3. Is the password in .env correct?")
        print("4. Is the username 'postgres' correct?")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    check_connection()
