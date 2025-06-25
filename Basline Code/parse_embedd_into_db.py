# --This script takes all pdf files in PDF_DIRECTORY (default=pdf_data) and parses them.
# --It also tokenizes, Chunks up text, creates embeddings.
# --Then it inserts the embeddings to chromadb, with metadata.
# --Only nedds to be run if you want to add documents to the db.
# --Check config.py, before running, to make sure you have the right settings for your case.

import fitz  # PyMuPDF
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from config import (
    PDF_DIRECTORY,
    EMBEDDING_MODEL_NAME,
    TOKEN_ENCODER,
    MAX_TOKENS,
    OVERLAP,
    get_collection,
    get_client
)

collection = get_collection() # set up db
client = get_client() # OpenAI client for embeddings


# -----------------------------------------------#
# --------------------Parse----------------------#
# -----------------------------------------------#
def normalize_text(input_text):
    # Remove split words at the end of lines
    normalized = re.sub(r"- ?\n", "", input_text.strip())
    # Replace any sequence of whitespace (including newlines) with a single space
    normalized = re.sub(r"\s+", " ", normalized)
    # Don't keep space if end of sentence
    normalized = re.sub(r" +\.\s", ". ", normalized)

    return normalized

def parse_document(pdf_path):
    doc = fitz.open(pdf_path)
    text_and_pagenumber = []  # List [(page_number, page_text)]

    for i, page in enumerate(doc):
        text = page.get_text(sort=True) # sort helps keep the right reading order in the page
        if text.strip():  # Skip empty pages
            norm_text = normalize_text(text)
            text_and_pagenumber.append((i + 1, norm_text + " "))
    doc.close()
    return text_and_pagenumber



# -----------------------------------------------#
# -------------Tokenize and Chunk up-------------#
# -----------------------------------------------#
def chunk_pdf_by_tokens(pdf_path, MAX_TOKENS=MAX_TOKENS, OVERLAP=OVERLAP):
    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path)  # List [(page_number, page_text)]
    chunks = []
    all_tokens = []
    token_page_map = []  # Keeps track of which page each token came from, [page number of token1, token2, token3 ...]
    for page_number, page_text in text_and_pagenumber:
        tokens = TOKEN_ENCODER.encode(page_text)
        all_tokens.extend(tokens)
        token_page_map.extend([page_number] * len(tokens))

    # Set up loop and chunk boundaries
    step = MAX_TOKENS - OVERLAP
    total_tokens = len(all_tokens)
    i = 0
    chunk_index = 1
    # Loop through all tokens and store chunk with metadata in the returned variable: chunks
    while i < total_tokens:
        start = i
        end = min(i + MAX_TOKENS, total_tokens)
        token_chunk = all_tokens[start:end]
        chunk_text = TOKEN_ENCODER.decode(token_chunk)
        chunk_pages = token_page_map[start:end]
        page_list = sorted(set(chunk_pages))
        chunk_metadata = {
            "id": f"{filename}_chunk{chunk_index}",
            "filename": filename,
            "page_number": ",".join(map(str, page_list)),
            "chunk_index": chunk_index,
        }

        chunks.append({"text": chunk_text, "metadata": chunk_metadata})
        i += step
        chunk_index += 1
        
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

# Get embeddings of chunks from client, store with metadata in db
def embed_and_insert(chunk):
    chunk_id = chunk["metadata"]["id"]
    try:
        embedding = client.embeddings.create(
            input=chunk["text"], model=EMBEDDING_MODEL_NAME
        ).data[0].embedding

        collection.upsert(
            ids=[chunk_id],
            documents=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[chunk["metadata"]],
        )
    except Exception as e:
        print(f"[Error] Failed for {chunk_id}: {e}")
        
# Get all chunks and call the embed_and_insert(chunk) function for all of them. With multiprocessing
def process_pdfs_and_insert(directory, max_workers=None):
    if max_workers is None:
        max_workers = get_max_workers()

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            print(f"\n📄 Processing file: {filename}")
            chunks = chunk_pdf_by_tokens(pdf_path)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(embed_and_insert, chunk) for chunk in chunks]
                for future in as_completed(futures):
                    future.result()

            print(f"✅ Finished processing: {filename}")


# --------------------------------------------------------------------#
# --Parse, Tokenize, Chunk up, Embedd PDFs and insert into database---#
# --------------------------------------------------------------------#
process_pdfs_and_insert(PDF_DIRECTORY)
