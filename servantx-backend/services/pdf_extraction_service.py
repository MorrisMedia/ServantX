import io

import PyPDF2

from services.storage_service import storage_service


def extract_text_from_pdf(file_path: str) -> str:
    try:
        pdf_bytes = storage_service.read_bytes(file_path)
        text = ""
        with io.BytesIO(pdf_bytes) as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"

        final_text = text.strip()
        if len(final_text) == 0:
            return "Warning: No text could be extracted from this PDF. It may be a scanned image or have text embedded as images."
        return final_text
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
