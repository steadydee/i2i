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

# Template ID stored once here; change when you upload a new version
_TEMPLATE_ID = "tpl_sow_v1"

_renderer = DocxRender(template_id=_TEMPLATE_ID)


def generate(**fields):
    """
    Forward all user-supplied fields to DocxRender and return
    its standard `{"ui_event": "download_link", "url": ...}` dict.
    """
    return _renderer.invoke(fields)
