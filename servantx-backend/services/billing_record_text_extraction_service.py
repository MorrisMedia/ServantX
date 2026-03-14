from pathlib import Path
import json

from services.pdf_extraction_service import extract_text_from_pdf
from services.storage_service import storage_service


def _read_text_file(relative_path: str) -> str:
    try:
        return storage_service.read_text(relative_path).strip()
    except FileNotFoundError:
        return f"File not found: {relative_path}"
    except Exception as exc:
        return f"Error extracting text from file: {str(exc)}"


def extract_billing_record_text(relative_path: str, file_name: str = "") -> str:
    extension = (Path(file_name).suffix or Path(relative_path).suffix).lower()

    if extension == ".pdf":
        return extract_text_from_pdf(relative_path)

    if extension in {".csv", ".edi", ".hl7", ".hlz", ".dat", ".txt", ".835", ".837"}:
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
