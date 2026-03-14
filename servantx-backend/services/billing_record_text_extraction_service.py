from pathlib import Path
import json

from services.pdf_extraction_service import extract_text_from_pdf


def _read_text_file(relative_path: str) -> str:
    full_path = Path("uploads") / relative_path
    if not full_path.exists():
        return f"File not found: {relative_path}"
    try:
        return full_path.read_text(encoding="utf-8", errors="ignore").strip()
    except Exception as exc:
        return f"Error extracting text from file: {str(exc)}"


def extract_billing_record_text(relative_path: str, file_name: str = "") -> str:
    extension = (Path(file_name).suffix or Path(relative_path).suffix).lower()

    if extension == ".pdf":
        return extract_text_from_pdf(relative_path)

    if extension in {".csv", ".edi", ".hl7", ".hlz", ".dat", ".txt"}:
        return _read_text_file(relative_path)

    if extension == ".json":
        raw = _read_text_file(relative_path)
        if raw.startswith(("Error extracting text", "File not found", "Warning:")):
            return raw
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, ensure_ascii=True, indent=2)
        except Exception:
            return raw

    if extension in {".jpg", ".jpeg", ".png"}:
        return "Warning: Image OCR is not enabled for this billing record format yet."

    return f"Warning: Unsupported billing record file type: {extension or 'unknown'}"
