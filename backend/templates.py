from __future__ import annotations
import re, io, os, uuid, zipfile, mimetypes
from typing import List

# ────────────────────────── placeholder regex ───────────────────────────
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+?)\s*\}\}")

# ────────────────────────── helper to strip XML tags ────────────────────
def _strip_xml(text: str) -> str:
    """Remove all <w:*> tags so placeholders that span runs join up."""
    return re.sub(r"<[^>]+>", "", text)

# ────────────────────────── public: extract_placeholders ────────────────
def extract_placeholders(file_bytes: bytes, ext: str) -> List[str]:
    """
    Return a sorted list of unique placeholder names (`{{name}}`)
    found in the uploaded template.
    Handles DOCX/PPTX (unzips and scans XML) as well as plain text/HTML/MD.
    """
    names: set[str] = set()

    if ext in {".docx", ".pptx"}:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            for member in zf.namelist():
                if member.endswith(".xml"):
                    xml = zf.read(member).decode("utf-8", errors="ignore")
                    plain = _strip_xml(xml)
                    names.update(_PLACEHOLDER_RE.findall(plain))
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        names.update(_PLACEHOLDER_RE.findall(text))

    return sorted(names)

# ────────────────────────── public: upload_template ─────────────────────
def upload_template(file_bytes: bytes, filename: str, tenant: str) -> str:
    """
    Uploads the template file to Supabase Storage `templates/<tenant>/...`
    and returns a `template_id` (uuid hex).
    """
    from supabase import create_client          # lazy import so tests pass
    _SB = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    bucket = "templates"

    ext = os.path.splitext(filename)[1].lower()
    template_id = uuid.uuid4().hex
    path = f"{tenant}/{template_id}{ext}"
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    # storage3 client: options dict values must be *strings*
    _SB.storage.from_(bucket).upload(
        path,
        file_bytes,
        {"contentType": mime, "upsert": "true"},
    )

    # optional: record in a templates metadata table (ignore if missing)
    try:
        _SB.table("templates").upsert({
            "template_id": template_id,
            "tenant_id": tenant,
            "path": path,
            "type": ext.lstrip("."),
        }).execute()
    except Exception:
        pass

    return template_id
