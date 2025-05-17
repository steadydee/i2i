#!/usr/bin/env python3
"""
Re-embed every task_manifest row using:  title + " " + " ".join(phrase_examples)
Updates the existing `embedding` column in place.

.env needs:
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_SERVICE_KEY=service-role-key
  OPENAI_API_KEY=sk-...
"""
import os, sys, json, time
from supabase import create_client      # pip install supabase
import openai                           # pip install openai
from dotenv import load_dotenv          # pip install python-dotenv

MODEL  = "text-embedding-3-small"
BATCH  = 50

# ── env -----------------------------------------------------------------------
load_dotenv()

url  = os.getenv("SUPABASE_URL")
key  = os.getenv("SUPABASE_SERVICE_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

missing = [k for k,v in {
    "SUPABASE_URL": url,
    "SUPABASE_SERVICE_KEY": key,
    "OPENAI_API_KEY": openai.api_key,
}.items() if not v]

if missing:
    sys.exit(f"❌ Missing env vars: {', '.join(missing)}")

sb = create_client(url, key)

# ── helpers -------------------------------------------------------------------
def embed(text: str) -> list[float]:
    return openai.embeddings.create(model=MODEL, input=text).data[0].embedding

# ── main ----------------------------------------------------------------------
def run():
    total = sb.table("task_manifest").select("count=exact").execute().count
    offset = 0
    while offset < total:
        rows = (
            sb.table("task_manifest")
              .select("task,title,phrase_examples")
              .range(offset, offset + BATCH - 1)
              .execute().data
        )
        if not rows: break

        for r in rows:
            title   = r["title"] or ""
            phrases = " ".join(r.get("phrase_examples") or [])
            txt     = f"{title} {phrases}".strip()
            if not txt:
                print(f"⚠️  {r['task']} has no text — skipping"); continue

            try:
                vec = embed(txt)
            except Exception as e:
                print(f"❌  {r['task']} embedding failed: {e}"); continue

            sb.table("task_manifest")\
              .update({"embedding": json.dumps(vec)})\
              .eq("task", r["task"]).execute()
            print(f"✔  {r['task']} updated")
            time.sleep(0.4)   # gentle pacing

        offset += BATCH
    print("🎉  Re-embedding complete.")

if __name__ == "__main__":
    try: run()
    except KeyboardInterrupt: sys.exit("\nInterrupted")
