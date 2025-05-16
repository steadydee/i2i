"""
backend.helpers.sow_draft
-------------------------
Helper that fills the SOW DOCX template and returns a signed
download link. Designed to be invoked via the Generic Function
Runner.

Expected kwargs (gathered from the form):
    client, application_name, duration, cost, application_type
"""
from backend.tools.docx_render import DocxRender

_TEMPLATE_ID = "sow_v1"  # Must match Supabase template name, no prefix

_renderer = DocxRender(template_id=_TEMPLATE_ID)

def generate(**fields):
    return _renderer.invoke(fields)
