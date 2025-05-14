from dotenv import load_dotenv
load_dotenv()  # pulls vars from .env

import os
from supabase import create_client, Client

_SUPA_URL = os.environ["SUPABASE_URL"]
_SUPA_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_KEY")
    or os.environ["SUPABASE_SERVICE_KEY"]         # matches your .env
)

supabase: Client = create_client(_SUPA_URL, _SUPA_KEY)
sb = supabase  # legacy alias
