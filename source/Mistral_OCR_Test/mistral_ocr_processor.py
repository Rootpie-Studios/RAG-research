# mistral_ocr_processor.py
# This Python script, mistral_ocr_processor.py, is designed to perform Optical Character Recognition (OCR) on a PDF file using the Mistral OCR API.
# It processes the PDF to extract text from each page and returns the results in a structured format.
# It also includes error handling for file operations and API interactions.
# It is intended to be used in conjunction with other scripts that handle PDF processing and database interactions.
# It is part of a larger project that involves parsing, tokenizing, chunking, embedding PDFs, and inserting the results into a database.
# It is important to ensure that the Mistral API key is set in the environment variables before running this script.
# This script is a standalone module that can be imported and used in other scripts.



import os
from mistralai import Mistral
from config_mistral import get_mistral_client, PDF_DIRECTORY
from typing import List, Tuple
import io
import mimetypes # Fortfarande bra att ha, men vi kommer att vara explicita för PDF
import time

def process_pdf_with_mistral_ocr(pdf_path: str, model_name: str = "mistral-ocr-latest") -> List[Tuple[int, str]]:
    """
    Processes a PDF file using Mistral OCR and returns a list of (page_number, extracted_markdown_text_for_page).
    """
    mistral_client = get_mistral_client()

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    print(f"Sending {pdf_path} to Mistral OCR for processing...")

    file_id = None
    try:
        # Läs in hela filinnehållet i bytes
        with open(pdf_path, "rb") as f_in:
            file_bytes_content = f_in.read()

        # NY KOD HÄR: Sätt MIME-typen explicit till application/pdf
        # Vi ignorerar mimetypes.guess_type för PDF-filer för att vara 100% säkra.
        mime_type_to_send = "application/pdf"

        print(f"Uploading {os.path.basename(pdf_path)}...")
        uploaded_file = mistral_client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": file_bytes_content,
                "mime_type": mime_type_to_send, # <-- Viktigt: Säkerställ att denna skickas med
            },
            purpose="ocr"
        )
        file_id = uploaded_file.id
        print(f"File uploaded successfully. File ID: {file_id}")

        print(f"Waiting for 5 seconds to ensure file availability for OCR processing...")
        time.sleep(5) # Vänta i 5 sekunder

        # Steg 2: Bearbeta dokumentet med det uppladdade filens ID
        response = mistral_client.ocr.process(
            model=model_name,
            document={'file_id': file_id},
        )

        pages_data = []
        for i, page in enumerate(response.pages):
            pages_data.append((i + 1, page.markdown))

        print(f"Successfully processed {pdf_path} with Mistral OCR.")
        return pages_data

    except Exception as e:
        print(f"Error processing PDF with Mistral OCR: {e}")
        raise
    finally:
        if file_id:
            try:
                print(f"Deleting uploaded file with ID: {file_id}...")
                mistral_client.files.delete(file_id=file_id)
                print(f"File {file_id} deleted successfully.")
            except Exception as delete_e:
                print(f"Error deleting file {file_id}: {delete_e}")


if __name__ == "__main__":
    test_pdf = os.path.join(PDF_DIRECTORY, "your_test_document.pdf")
    if os.path.exists(test_pdf):
        try:
            extracted_pages = process_pdf_with_mistral_ocr(test_pdf)
            print("\n--- Extracted Text from Mistral OCR ---")
            for page_num, page_text in extracted_pages:
                print(f"Page {page_num}: {page_text[:500]}...")
        except Exception as e:
            print(f"Could not run example: {e}")
    else:
        print(f"Please place a PDF file named 'your_test_document.pdf' in the '{PDF_DIRECTORY}' directory to run the example.")