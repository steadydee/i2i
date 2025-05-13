"""
backend/tools/docx_render.py
Fill a DOCX template using python-docx-template (`docxtpl`).
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict

from docxtpl import DocxTemplate


class DocxRender:
    """
    Parameters
    ----------
    template_id : str | dict
        Either "tpl_sow_v1" or a dict that contains it.
    """

    def __init__(self, template_id: str | Dict[str, Any], **_: Any) -> None:
        # Accept nested structures coming from the workflow state
        if isinstance(template_id, dict):
            template_id = (
                template_id.get("template_id")
                or (template_id.get("metadata") or {}).get("template_id")
            )

        if not isinstance(template_id, str) or not template_id:
            raise ValueError("template_id must be a non-empty str")

        tpl_dir = Path(__file__).parent.parent / "templates"
        self.template_path = tpl_dir / f"{template_id}.docx"
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"Template {self.template_path} not found. "
                "Place the .docx in ./backend/templates."
            )

    def __call__(self, fields: Dict[str, Any]) -> str:
        return self.run(fields)

    def run(self, fields: Dict[str, Any]) -> str:
        doc = DocxTemplate(str(self.template_path))
        doc.render(fields)

        client = fields.get("client", "output")
        safe = "".join(c for c in str(client) if c.isalnum() or c in ("_", "-"))
        out_path = Path("/tmp") / f"{safe}.docx"
        doc.save(out_path)
        return str(out_path)
