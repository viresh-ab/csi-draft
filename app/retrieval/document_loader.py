from pathlib import Path
from app.core.config import CS_ROOT
import pdfplumber
from docx import Document as DocxDocument
from pptx import Presentation


def extract_text(file_path: Path) -> str:
    """Extracts plain text from PDF, DOCX, or PPTX files."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)

    elif suffix == ".docx":
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs)

    elif suffix == ".pptx":
        prs = Presentation(file_path)
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    texts.append(shape.text)
        return "\n".join(texts)

    else:
        raise ValueError(
            f"Unsupported file type: '{suffix}'. "
            f"Supported formats: .pdf, .docx, .pptx"
        )


def load_from_file_path(csv_file_path: str) -> dict:
    """
    Primary loader — uses the file_path column from the CSV directly.
    Handles Windows backslashes and resolves relative to project root.
    """
    # Normalise slashes
    normalised = csv_file_path.replace("\\", "/")
    path = Path(normalised)

    # If relative, resolve from cwd (where uvicorn/streamlit was launched)
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}\n"
            f"Original CSV path: {csv_file_path}\n"
            f"Ensure you are running the app from the csi-engine/ root directory."
        )

    text = extract_text(path)
    return {"file_path": str(path), "content": text}


def resolve_path(industry: str, filename: str) -> Path:
    """Fallback resolver using industry folder + filename."""
    path = CS_ROOT / industry / filename
    if path.exists():
        return path
    matches = list(CS_ROOT.rglob(filename))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Cannot find '{filename}' under {CS_ROOT}.")


def load_case_study(industry: str, filename: str) -> dict:
    """Fallback loader. Prefer load_from_file_path when file_path column exists."""
    path = resolve_path(industry, filename)
    text = extract_text(path)
    return {"file_path": str(path), "content": text}
