import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")
with open("debug_log.txt", "a") as f:
    f.write(f"Supabase Client Config - URL: {url}, Key Length: {len(key)}\n")
supabase: Client = create_client(url, key)
