from backend.supabase import fetch_manifest
row = fetch_manifest("do employees get military leave")[1]
print("Manifest Row:", row)
