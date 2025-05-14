"""
backend.tools.docx_render
Render a DOCX template stored in Supabase Storage and return a signed download URL.

Buckets
-------
templates   – contains your .docx templates  (object key = template_id + ".docx")
documents   – output bucket for generated files

Environment variables
---------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY      # access Storage via service role
SUPABASE_DOC_BUCKET=documents  # optional override
URL_EXPIRY_MIN=120             # signed URL lifetime
"""

import io, os, uuid, docx
from datetime import timedelta
from langchain_core.runnables import Runnable
from backend.db import sb  # your helper returns a supabase client

class DocxRender(Runnable):
    def __init__(self, template_id: str):
        self.template_id = template_id
        self.tpl_bucket  = "templates"
        self.out_bucket  = os.getenv("SUPABASE_DOC_BUCKET", "documents")
        self.expiry_min  = int(os.getenv("URL_EXPIRY_MIN", "120"))

    # ── helpers ──────────────────────────────────────────────────────────
    def _download_template(self) -> bytes:
        path = f"{self.template_id}.docx"
        resp = sb().storage.from_(self.tpl_bucket).download(path)
        if not resp:
            raise FileNotFoundError(f"Template {path} not found in bucket '{self.tpl_bucket}'")
        return resp

    def _upload_and_sign(self, buf: bytes) -> str:
        key = f"{self.template_id}/{uuid.uuid4()}.docx"
        storage = sb().storage.from_(self.out_bucket)
        storage.upload(key, buf, {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"})
        signed = storage.create_signed_url(key, self.expiry_min * 60)
        return signed["signedURL"]

    # ── Runnable.invoke ──────────────────────────────────────────────────
    def invoke(self, inputs: dict, **_) -> dict:
        tpl_bytes = self._download_template()
        doc = docx.Document(io.BytesIO(tpl_bytes))

        # simple merge-field replacement {{field}}
        for para in doc.paragraphs:
            for run in para.runs:
                for k, v in inputs.items():
                    run.text = run.text.replace(f"{{{{{k}}}}}", str(v))

        out_buf = io.BytesIO()
        doc.save(out_buf)
        out_buf.seek(0)

        url = self._upload_and_sign(out_buf.read())
        return {"url": url}
