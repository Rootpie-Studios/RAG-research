# takes all pdf files in the pdf folder and parses them with different parsers.
# Compares the regular text parsing with the the markdown conversion as well.
# PyMuPDF4llm will save images in the same directory as well.

import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import fitz  # PyMuPDF
from mistralai import Mistral
import pymupdf4llm
import pathlib

from config import (
    PDF_DIRECTORY,
    OUTPUT_DIRECTORY_COMPARE_SPLITS
)
from docling.document_converter import DocumentConverter

if __name__ == "__main__":

    converter = DocumentConverter()
    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)


    for filename in os.listdir(PDF_DIRECTORY):
        if filename.endswith(".pdf"):
            filename_s = filename[:-4]  # Remove '.pdf'
            pdf_path = os.path.join(PDF_DIRECTORY, filename)
            out_dir = os.path.join(OUTPUT_DIRECTORY_COMPARE_SPLITS, filename_s)
            os.makedirs(out_dir, exist_ok=True)
            
            # # -----------
            # # Mistral OCR
            # # -----------
            # # Upload files
            # uploaded_pdf = client.files.upload(
            #     file={
            #         "file_name": os.path.join(PDF_DIRECTORY, filename),
            #         "content": open(os.path.join(PDF_DIRECTORY, filename), "rb"),
            #     },
            #     purpose="ocr"
            # )
            # # Retrieve files
            # retrieved_file = client.files.retrieve(file_id=uploaded_pdf.id)
            # signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
            # # Run OCR
            # ocr_response = client.ocr.process(
            #     model="mistral-ocr-latest",
            #     document={
            #         "type": "document_url",
            #         "document_url": signed_url.url,
            #     },
            #     include_image_base64=True
            # ) 
            # # Save responses as markdown
            # repsonses_ocr = [p.markdown for p in ocr_response.pages]
            # mistral_md = "\n".join(repsonses_ocr)
            # file_path_mistral_md = os.path.join(out_dir, "parsed_ToMd_Mistral.md")
            # pathlib.Path(file_path_mistral_md).write_bytes(mistral_md.encode())
            
            # -----------
            # PyMuPDF Text
            # -----------
            doc = fitz.open(pdf_path)
            file_path_txt = os.path.join(out_dir, "parsed_ToText_PyMuPDF.txt")
            with open(file_path_txt, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"Metadata: Filename: {filename_s}\n")
                f.write("=" * 60 + "\n")
                for i, page in enumerate(doc):
                    f.write("=" * 60 + "\n")
                    f.write(f"Metadata: Page: {i+1}\n")
                    f.write("=" * 60 + "\n")
                    f.write(page.get_text(sort=True) + "\n\n")
            
            # -----------
            # PyMuPDF Markdown
            # -----------
            file_path_md = os.path.join(out_dir, "parsed_ToMd_PyMuPDF4llm.md")
            md_text = pymupdf4llm.to_markdown(
                f"./{PDF_DIRECTORY}/{filename}",
                write_images=True,
                filename=f"{filename_s}",
                image_path=f"{OUTPUT_DIRECTORY_COMPARE_SPLITS}/{filename_s}/",
            )
            pathlib.Path(file_path_md).write_bytes(md_text.encode())
            
            # -----------
            # Docling
            # -----------
            docling_doc = converter.convert(pdf_path)
            docling_text = docling_doc.document.export_to_text()
            docling_md = docling_doc.document.export_to_markdown()

            file_path_docling_txt = os.path.join(out_dir, "parsed_ToText_Docling.txt")
            file_path_docling_md = os.path.join(out_dir, "parsed_ToMd_Docling.md")
                
            with open(file_path_docling_txt, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write(f"Metadata: Filename: {filename_s}\n")
                f.write("=" * 60 + "\n")
                f.write(docling_text + "\n\n")
                
            pathlib.Path(file_path_docling_md).write_bytes(docling_md.encode())

            
