"""
Document text extraction utilities.
"""

from pathlib import Path


def extract_text_from_file(file_path: Path, content_type: str) -> str:
    """Extract text from various document formats."""

    suffix = file_path.suffix.lower()

    if suffix == ".txt" or content_type == "text/plain":
        return file_path.read_text(encoding="utf-8")

    elif suffix == ".pdf" or content_type == "application/pdf":
        return _extract_from_pdf(file_path)

    elif (
        suffix == ".docx"
        or content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return _extract_from_docx(file_path)

    elif suffix in (".md", ".markdown"):
        return file_path.read_text(encoding="utf-8")

    else:
        # Try to read as plain text
        return file_path.read_text(encoding="utf-8")


def _extract_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def _extract_from_docx(file_path: Path) -> str:
    """Extract text from DOCX file."""
    from docx import Document

    doc = Document(file_path)
    text_parts = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    return "\n\n".join(text_parts)
