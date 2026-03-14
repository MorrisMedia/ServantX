from pathlib import Path
from typing import Optional
import PyPDF2

def extract_text_from_pdf(file_path: str) -> str:
    try:
        full_path = Path("uploads") / file_path
        
        if not full_path.exists():
            error_msg = f"File not found: {file_path}"
            print(f"ERROR: {error_msg}")
            return error_msg
        
        print(f"\nExtracting text from PDF: {file_path}")
        
        text = ""
        with open(full_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"PDF has {num_pages} page(s)")
            
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                print(f"Page {i+1} extracted {len(page_text)} characters")
                text += page_text + "\n"
        
        final_text = text.strip()
        print(f"Total extracted: {len(final_text)} characters")
        
        if len(final_text) == 0:
            return "Warning: No text could be extracted from this PDF. It may be a scanned image or have text embedded as images."
        
        return final_text
    
    except Exception as e:
        error_msg = f"Error extracting text from PDF: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg
