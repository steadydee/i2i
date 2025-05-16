import os
import psycopg2

def get_prompt(name, version=None):
    # Connect using DATABASE_URL from environment
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    if version:
        cur.execute(
            "SELECT text FROM prompts WHERE name=%s AND version=%s ORDER BY updated_at DESC LIMIT 1",
            (name, version)
        )
    else:
        cur.execute(
            "SELECT text FROM prompts WHERE name=%s ORDER BY version DESC, updated_at DESC LIMIT 1",
            (name,)
        )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    else:
        raise ValueError(f"Prompt '{name}' not found in DB.")

# Test Harness
if __name__ == "__main__":
    try:
        print(get_prompt("policy_qa"))
    except Exception as e:
        print("Error fetching prompt:", e)
