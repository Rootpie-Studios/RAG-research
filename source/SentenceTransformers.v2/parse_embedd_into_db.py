# --This script takes all pdf files in PDF_DIRECTORY (default=pdf_data) and parses them.
# --It also tokenizes, Chunks up text, creates embeddings.
# --Then it inserts the embeddings to chromadb, with metadata.
# --Only nedds to be run if you want to add documents to the db.
# --Check config.py, before running, to make sure you have the right settings for your case.

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
client = get_client()  # OpenAI client for embeddings


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
def chunk_pdf_by_tokens(pdf_path, max_tokens=MAX_TOKENS, chunk_overlap=OVERLAP):
    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path)  # List [(page_number, page_text)]
    chunks = []

    current_chunk_text = ""
    current_chunk_pages = []
    chunk_index = 0

    # Stores (word, page_number) tuples
    all_words_with_pages = []
    for page_number, page_text in text_and_pagenumber:
        words = page_text.split()
        for word in words:
            all_words_with_pages.append((word, page_number))

    i = 0
    while i < len(all_words_with_pages):
        start_word_index = i
        current_chunk_text = ""
        current_chunk_pages = []

        # Build a chunk until it exceeds MAX_TOKENS
        j = start_word_index
        while j < len(all_words_with_pages):
            word, page_number = all_words_with_pages[j]
            # Check if adding the next word (plus a space) exceeds MAX_TOKENS
            if len(current_chunk_text) + len(word) + 1 <= max_tokens:
                current_chunk_text += word + " "
                current_chunk_pages.append(page_number)
                j += 1
            else:
                break

        # If we have a chunk, store it
        if current_chunk_text.strip():
            chunk_index += 1
            most_common_page = (
                max(set(current_chunk_pages), key=current_chunk_pages.count)
                if current_chunk_pages
                else None
            )
            chunk_metadata = {
                "id": f"{filename}_chunk{chunk_index}",
                "filename": filename,
                "page_number": most_common_page,
                "chunk_index": chunk_index,
                "total_chunks": -1,  # Will be updated later
            }
            chunks.append(
                {"text": current_chunk_text.strip(), "metadata": chunk_metadata}
            )

        # Determine the starting point for the next chunk with overlap
        # Move 'i' back by enough words to achieve the desired character overlap
        overlap_chars_count = 0
        overlap_words_count = 0
        # Iterate backwards from the end of the current chunk to find the overlap point
        for k in range(j - 1, start_word_index - 1, -1):
            word_len_with_space = len(all_words_with_pages[k][0]) + 1
            if (
                overlap_chars_count + word_len_with_space <= chunk_overlap
                and k >= start_word_index
            ):
                overlap_chars_count += word_len_with_space
                overlap_words_count += 1
            else:
                break

        # If no words fit in overlap, just move to next word
        if overlap_words_count == 0 and j > start_word_index:
            i = j  # No overlap possible, move to next word
        else:
            i = j - overlap_words_count

        # Edge case: if i goes negative, reset to 0
        if i < 0:
            i = 0

        # If the inner loop didn't add any words (e.g., a very long single word)
        # or if we are at the end of the document
        if j == start_word_index:  # means no new words were added to current_chunk_text
            i += 1  # move to the next word to avoid infinite loop
        elif j >= len(all_words_with_pages):  # reached end of document
            break

    # Update total_chunks for all chunks
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
        embedding = (
            client.embeddings.create(input=chunk["text"], model=EMBEDDING_MODEL_NAME)
            .data[0]
            .embedding
        )

        collection.upsert(
            ids=[chunk_id],
            documents=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[chunk["metadata"]],
        )
    except Exception as e:
        print(f"[Error] Failed for {chunk_id}: {e}")


# Get all chunks and call the embed_and_insert(chunk) function for all of them. With multiprocessing
def process_pdfs_and_insert_workers(directory, max_workers=None):
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


def process_pdfs_and_insert(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            print(f"Processing: {filename}")
            pdf_path = os.path.join(directory, filename)
            chunks = chunk_pdf_by_tokens(pdf_path)

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
