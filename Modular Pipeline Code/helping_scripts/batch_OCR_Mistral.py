import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
from mistralai import Mistral
import os
from config import MISTRAL_KEY
import pathlib

client = Mistral(api_key=MISTRAL_KEY)
results_folder = "ocr_results"
os.makedirs(results_folder, exist_ok=True)

with open("File_IDs_Mistral_OCR.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        file_id = row["file_id"]
        filename = row["filename"]

        print(f"Processing OCR for {filename} ({file_id})...")

        signed_url = client.files.get_signed_url(file_id=file_id)

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            include_image_base64=False
        )
        ocr_response_dict = ocr_response.model_dump()
        # Save each OCR result as markdown files
        markdown_ocr = [p.markdown for p in ocr_response.pages]
        
        for i, mark in enumerate(markdown_ocr):
            md_path = os.path.join(results_folder, f"{filename[:-4]}_page{i+1}.md")
            with open(md_path, "w", encoding="utf-8") as jf:
                pathlib.Path(md_path).write_bytes(mark.encode(encoding="utf-8"))
        print(f"OCR complete for {filename}, saved to {md_path}")
