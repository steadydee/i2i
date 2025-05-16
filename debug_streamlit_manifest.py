from backend.supabase import fetch_manifest

def main():
    _, manifest = fetch_manifest("leave policy")
    print("DEBUG [Streamlit handoff]: About to pass manifest to workflow/state:", manifest)
    # Simulate your app’s next step (e.g., pass manifest to workflow, render UI, etc.)

if __name__ == "__main__":
    main()
