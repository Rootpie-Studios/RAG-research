import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
from mistralai import Mistral
from config import PDF_DIRECTORY, MISTRAL_KEY

client = Mistral(api_key=MISTRAL_KEY)

pdf_folder = PDF_DIRECTORY
output_csv = "File_IDs_Mistral_OCR.csv"

# Open CSV to save: filename, file_id
with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "file_id"])

    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(pdf_folder, filename)
            print(f"Uploading {filename}...")

            uploaded_pdf = client.files.upload(
                file={
                    "file_name": filename,
                    "content": open(path, "rb"),
                },
                purpose="ocr"
            )

            writer.writerow([filename, uploaded_pdf.id])
            print(f"Uploaded {filename}, file_id={uploaded_pdf.id}")
