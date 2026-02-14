import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def check_db():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        print("Existing tables:")
        for table in tables:
            print(f"- {table[0]}")
            
        cur.execute("SELECT count(*) FROM businesses")
        print(f"Business count: {cur.fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    check_db()
