"""Shared Supabase client singleton."""
from __future__ import annotations
import os

from dotenv import load_dotenv
from supabase import create_client, Client   # pip install python-dotenv supabase

load_dotenv()                                # pulls SUPABASE_* from .env

_SB: Client | None = None


def sb() -> Client:
    """Return a cached Supabase client, creating it on first use."""
    global _SB
    if _SB is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise RuntimeError("Set SUPABASE_URL + SUPABASE_SERVICE_KEY in .env")
        _SB = create_client(url, key)
    return _SB
