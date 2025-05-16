from dotenv import load_dotenv
load_dotenv()
import os
from supabase import create_client

_SB_URL = os.environ.get("SUPABASE_URL")
_SB_KEY = os.environ.get("SUPABASE_KEY")
client = create_client(_SB_URL, _SB_KEY)

# Use a valid embedding vector of the correct shape (e.g., [0.0]*1536 for test)
embedding = [0.0]*1536

result = client.rpc(
    "match_task_manifest_vec",
    {
        "q_vec": embedding,
        "tenant": "default",
        "min_similarity": 0.30
    }
)

print("Type:", type(result))
print("Dir:", dir(result))
print("Value:", result)
if hasattr(result, "data"):
    print("Has .data:", result.data)
if hasattr(result, "execute"):
    exec_result = result.execute()
    print("Has .execute() -- exec_result:", exec_result)
    if hasattr(exec_result, "data"):
        print("exec_result.data:", exec_result.data)
