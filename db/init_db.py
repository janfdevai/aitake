import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def run_sql_file(filename):
    print(f"Running {filename}...")
    with open(filename, 'r') as f:
        sql = f.read()
    
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        # Split by semicolon for better error reporting, 
        # but be careful with functions/triggers. 
        # For this simple schema, executing as one block is fine.
        cur.execute(sql)
    conn.close()
    print(f"Finished {filename}")

if __name__ == "__main__":
    try:
        run_sql_file("schemas/schema.sql")
        run_sql_file("schemas/dummy_data.sql")
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error: {e}")
