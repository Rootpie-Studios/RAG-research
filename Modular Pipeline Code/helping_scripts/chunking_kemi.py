import os
import re

import pandas as pd
from config import (
    MAX_TOKENS,
    OVERLAP,
    TOKEN_ENCODER,
    USE_OPENAI,
    ADD_LLM_CONTEXT
)
from langchain.text_splitter import RecursiveCharacterTextSplitter


#------------------------------------#
#---------Helping functions----------#
#------------------------------------#
def encode_text(text):
    return (
        TOKEN_ENCODER.encode(text, disallowed_special=())
        if USE_OPENAI else
        TOKEN_ENCODER.encode(text=text, add_special_tokens=False, truncation=True, max_length=512)
    )

def get_token_count(string: str) -> int:
    num_tokens = len(encode_text(string))
    return num_tokens

def add_context(filename):
    df = pd.read_csv("Produktnamn.csv")
    search_reg_nr = filename[:4]
    matched_row = df[df['Registreringsnummer'] == search_reg_nr]

    if not matched_row.empty:
        prod_name = matched_row.iloc[0]['Produktnamn']
    else:
        prod_name = ""
    context_addition = f"Reg nr: {filename[:4]}, Produktnamn: {prod_name}"
    return context_addition


#------------------------------------#
#-------Chunking Method, PAGE--------#
#------------------------------------#
def chunk_pdf_by_page(pdf_path, parse_document):
    filename = os.path.basename(pdf_path)
    match = re.search(r'(?<=_)\d{4}-\d{2}-\d{2}(?=\.)', filename)
    file_date = match.group()
    text_and_pagenumber = parse_document(pdf_path, filename)  # List [(page_number, page_text)]
    chunks = []
    
    for page_number, page_text in text_and_pagenumber:
        chunk_metadata = {
            "id": f"{filename}_chunk{page_number}",
            "filename": filename,
            "page_number": page_number,
            "chunk_index": page_number,
            "reg_nr": filename[:4],
            "date": file_date,
            "total_chunks": len(text_and_pagenumber)
        }
        if ADD_LLM_CONTEXT:
            chunks.append({"text": add_context(filename) + "\n\n" + page_text, "metadata": chunk_metadata})
        else:
            chunks.append({"text": page_text, "metadata": chunk_metadata})
            
    return chunks


#------------------------------------#
#------Chunking Method, TOKENS-------#
#------------------------------------#
def chunk_pdf_by_tokens(pdf_path, parse_document, max_tokens=MAX_TOKENS, overlap=OVERLAP):
    filename = os.path.basename(pdf_path)
    match = re.search(r'(?<=_)\d{4}-\d{2}-\d{2}(?=\.)', filename)
    file_date = match.group()
    text_and_pagenumber = parse_document(pdf_path, filename)  # List [(page_number, page_text)]
    chunks = []
    all_tokens = []
    token_page_map = []  # Keeps track of which page each token came from, [page number of token1, token2, token3 ...]
    for page_number, page_text in text_and_pagenumber:
        tokens = encode_text(page_text)
        all_tokens.extend(tokens)
        token_page_map.extend([page_number] * len(tokens))

    # Set up loop and chunk boundaries
    step = max_tokens - overlap
    total_tokens = len(all_tokens)
    i = 0
    chunk_index = 1
    # Loop through all tokens and store chunk with metadata in the returned variable: chunks
    while i < total_tokens:
        start = i
        end = min(i + max_tokens, total_tokens)
        token_chunk = all_tokens[start:end]
        chunk_text = TOKEN_ENCODER.decode(token_chunk)
        chunk_pages = token_page_map[start:end]
        page_list = sorted(set(chunk_pages))
        chunk_metadata = {
            "id": f"{filename}_chunk{chunk_index}",
            "filename": filename,
            "page_number": ",".join(map(str, page_list)),
            "chunk_index": chunk_index,
            "reg_nr": filename[:4],
            "date": file_date
        }
        if ADD_LLM_CONTEXT:
            chunks.append({"text": add_context(filename) + "\n\n" + chunk_text, "metadata": chunk_metadata})
        else:
            chunks.append({"text": chunk_text, "metadata": chunk_metadata})
        i += step
        chunk_index += 1
        
    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    return chunks


#------------------------------------#
#----Chunking Method, RECURSIVE------#
#------------------------------------#
def chunk_pdf_recursive_token_size(pdf_path, parse_document, max_tokens=MAX_TOKENS, overlap=OVERLAP):
    filename = os.path.basename(pdf_path)
    match = re.search(r'(?<=_)\d{4}-\d{2}-\d{2}(?=\.)', filename)
    file_date = ""
    if match:
        file_date = match.group()
    text_and_pagenumber = parse_document(pdf_path, filename)  # [(page_number, page_text)]
    
    splitter = RecursiveCharacterTextSplitter(
        length_function=get_token_count,
        chunk_size=max_tokens,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", "?", "!", " ", ""]
    )

    all_paragraphs = []
    paragraph_page_map = []

    for page_number, page_text in text_and_pagenumber:
        # Split by paragraphs on this page
        paragraph_chunks = splitter.split_text(page_text)
        all_paragraphs.extend(paragraph_chunks)
        paragraph_page_map.extend([page_number] * len(paragraph_chunks))

    # Now merge paragraphs into token-bounded chunks
    # I am doing these extra steps to let chunks span multiple pages
    # Also trying to merge small chunks if they are next to eachother
    all_chunks = []
    current_chunk = []
    chunk_page_numbers = []
    current_token_count = 0
    chunk_index = 1
    
    def finalize_chunk():
        nonlocal current_chunk, current_token_count, chunk_index
        if not current_chunk:
            return
        chunk_text = " ".join(current_chunk)
        page_list = sorted(set(chunk_page_numbers))
        chunk_metadata = {
            "id": f"{filename}_chunk{chunk_index}",
            "filename": filename,
            "page_number": ",".join(map(str, page_list)),
            "chunk_index": chunk_index,
            "reg_nr": filename[:4],
            "date": file_date
        }
        if ADD_LLM_CONTEXT:
            all_chunks.append({
                "text": add_context(filename) + "\n\n" + chunk_text, "metadata": chunk_metadata,
            })
        else:
            all_chunks.append({
                "text": chunk_text, "metadata": chunk_metadata,
            })
        chunk_index += 1
        current_chunk.clear()
        current_token_count = 0

    for paragraph, page_number in zip(all_paragraphs, paragraph_page_map):
        tokens = encode_text(paragraph)
        # print("token len: ", len(tokens))
        if current_token_count + len(tokens) >= max_tokens:
            finalize_chunk()
            chunk_page_numbers.clear()
        current_chunk.append(paragraph)
        current_token_count += len(tokens)
        chunk_page_numbers.append(page_number)

    finalize_chunk()  # Catch the last one

    total_chunks = len(all_chunks)
    for chunk in all_chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    return all_chunks