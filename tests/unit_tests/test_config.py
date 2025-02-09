from react_agent.configuration import Configuration
from react_agent.database import SupabaseDB

def test_config():
    config = Configuration()
    print(f"URL from config: {config.supabase_url}")
    print(f"Key from config: {config.supabase_key}")

    db = SupabaseDB(config.supabase_url, config.supabase_key)
    print("Database initialized successfully")

if __name__ == "__main__":
    test_config()