from backend.supabase import fetch_manifest

def debug_entry():
    _, manifest = fetch_manifest("leave policy")
    print("DEBUG [App entry]: Manifest row handed to workflow:", manifest)
    # Simulate passing to the rest of your workflow or UI here...

if __name__ == "__main__":
    debug_entry()
