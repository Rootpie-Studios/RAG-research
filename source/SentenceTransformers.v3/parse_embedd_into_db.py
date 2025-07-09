# --This script takes all pdf files in PDF_DIRECTORY (default=pdf_data) and parses them.
# --It also tokenizes, Chunks up text, creates embeddings.
# --Then it inserts the embeddings to chromadb, with metadata.
# --Only nedds to be run if you want to add documents to the db.
# --Check config.py, before running, to make sure you have the right settings for your case.
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

import fitz  # PyMuPDF
#import pymupdf # imports the pymupdf library
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from config import (
    PDF_DIRECTORY,
    EMBEDDING_MODEL_NAME,
#    TOKEN_ENCODER,
    MAX_TOKENS,
    OVERLAP,
    get_collection,
    get_client,
)

collection = get_collection()  # set up db


# -----------------------------------------------#
# --------------------Parse----------------------#
# -----------------------------------------------#

def parse_document(pdf_path):
    doc = fitz.open(pdf_path)
    text_and_pagenumber = []  # List [(page_number, page_text)]

    for i, page in enumerate(doc):
        text = page.get_text(sort=True)
        if text.strip():  # Skip empty pages
            norm_text = text
            text_and_pagenumber.append((i + 1, norm_text + " "))
    doc.close()
    # Test print
    # print(text_and_pagenumber)
    return text_and_pagenumber


# -----------------------------------------------#
# -------------Tokenize and Chunk up-------------#
# -----------------------------------------------#
def chunk_pdf_by_sentences(pdf_path, max_sentences=MAX_TOKENS, sentence_overlap=OVERLAP):
    from collections import Counter

    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path)  # [(page_number, page_text)]
    chunks = []
    all_sentences_with_pages = []

    for page_number, text in text_and_pagenumber:
        sentences = sent_tokenize(text)
        for sentence in sentences:
            if sentence.strip():
                all_sentences_with_pages.append((sentence.strip(), page_number))

    i = 0
    chunk_index = 0
    while i < len(all_sentences_with_pages):
        chunk_sentences = all_sentences_with_pages[i:i + max_sentences]
        if not chunk_sentences:
            break

        chunk_text = " ".join([s for s, _ in chunk_sentences])
        page_numbers = [p for _, p in chunk_sentences]
        most_common_page = Counter(page_numbers).most_common(1)[0][0]

        chunk_index += 1
        chunk_metadata = {
            "id": f"{filename}_chunk{chunk_index}",
            "filename": filename,
            "page_number": most_common_page,
            "chunk_index": chunk_index,
            "total_chunks": -1,  # Updated later
        }
        chunks.append({"text": chunk_text, "metadata": chunk_metadata})

        # Slide forward by chunk size minus overlap
        i += max_sentences - sentence_overlap if (max_sentences - sentence_overlap) > 0 else 1

    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    return chunks



# -----------------------------------------------#
# -----Embedd PDFs and Insert to ChromaDB--------#
# -----------------------------------------------#
def get_max_workers(factor=1.5, fallback=4):
    try:
        return max(1, int(multiprocessing.cpu_count() * factor))
    except NotImplementedError:
        return fallback


def process_pdfs_and_insert(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            print(f"Processing: {filename}")
            pdf_path = os.path.join(directory, filename)
            chunks = chunk_pdf_by_sentences(pdf_path)

            for chunk in chunks:
                chunk_id = chunk["metadata"]["id"]
                chunk_text = chunk["text"]
                # Test print
                # print("Chunk", chunk_id, ": ", chunk_text)
                # Embeddings are handled automatically by ChromaDB's embedding_function
                print(f"Inserting chunk {chunk_id} into ChromaDB")
                collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk_text],
                    metadatas=[chunk["metadata"]],
                )


# --------------------------------------------------------------------#
# --Parse, Tokenize, Chunk up, Embedd PDFs and insert into database---#
# --------------------------------------------------------------------#
process_pdfs_and_insert(PDF_DIRECTORY)
