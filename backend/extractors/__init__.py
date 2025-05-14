"""
backend.extractors
------------------
Registry of document-text extractors plus a convenience
`extract_text(Path) -> str` helper.

Supported out-of-the-box:
    • .txt   – UTF-8 read
    • .docx  – python-docx
    • .pdf   – pdfminer (optional)

Add new extractors by decorating with `@register(".ext")`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

REGISTRY: Dict[str, Callable[[Path], str]] = {}


# ----------------------------------------------------------------------
# Registration decorator
# ----------------------------------------------------------------------
def register(ext: str):
    """Register a new extractor for *ext* (dot-prefixed)."""
    def _wrap(fn: Callable[[Path], str]):
        REGISTRY[ext.lower()] = fn
        return fn
    return _wrap


# ----------------------------------------------------------------------
# TXT
# ----------------------------------------------------------------------
@register(".txt")
def _extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


# ----------------------------------------------------------------------
# DOCX
# ----------------------------------------------------------------------
try:
    import docx  # python-docx

    @register(".docx")
    def _extract_docx(path: Path) -> str:
        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

except ModuleNotFoundError:
    pass  # .docx extraction unavailable


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------
try:
    from pdfminer.high_level import extract_text as _pdf_extract

    @register(".pdf")
    def _extract_pdf(path: Path) -> str:
        return _pdf_extract(str(path))

except ModuleNotFoundError:
    pass  # .pdf extraction unavailable


# ----------------------------------------------------------------------
# Dispatch helper
# ----------------------------------------------------------------------
def extract_text(path: Path) -> str:
    """Return plain text from *path* using the registered extractor."""
    ext = path.suffix.lower()
    if ext not in REGISTRY:
        raise ValueError(f"Unsupported file type: {ext}")
    return REGISTRY[ext](path)
