from dotenv import load_dotenv
load_dotenv()
import os
from supabase import create_client

_SB_URL = os.environ.get("SUPABASE_URL")
_SB_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(_SB_URL, _SB_KEY)

# Use an actual embedding from the DB (to get a match)
from backend.supabase import _SB

emb = _SB.table("task_manifest").select("embedding").eq("task", "policy_qna").execute().data[0]["embedding"]

rpc = client.rpc(
    "match_task_manifest_vec",
    {
        "q_vec": emb,
        "tenant": "default",
        "min_similarity": 0.0
    }
).execute()

print("Raw result:", rpc)
print("Data:", rpc.data)
if isinstance(rpc.data, list) and len(rpc.data):
    print("Keys of first row:", rpc.data[0].keys())
