from backend.supabase import fetch_manifest

def run_workflow(prompt: str):
    _, manifest = fetch_manifest(prompt)
    print("DEBUG: Manifest returned from fetch_manifest:", manifest)
    return manifest

if __name__ == "__main__":
    run_workflow("leave policy")
