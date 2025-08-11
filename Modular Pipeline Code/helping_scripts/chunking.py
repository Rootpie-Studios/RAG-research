import os
from config import (
    ADD_LLM_CONTEXT,
    MAX_TOKENS,
    OVERLAP,
    SYS_PROMPT_FOR_CONTEXT,
    TOKEN_ENCODER,
    USE_OPENAI
)
from helping_scripts.generate_llm_response import generate_partial_context
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

def add_context(current_chunk, context_chunks, prompt):
    context_addition = generate_partial_context(current_chunk, context_chunks, prompt)
    return context_addition

def get_page_span(token_page_map, chunk_pages):
    max_page_doc = max(token_page_map)
    min_page_doc = min(token_page_map)
    min_page_chunk = min(chunk_pages)
    max_page_chunk = max(chunk_pages)
    page_span = (max(min_page_doc, min_page_chunk - 1), min(max_page_doc, max_page_chunk + 0))
    return page_span


#------------------------------------#
#------Chunking Method, TOKENS-------#
#------------------------------------#
def chunk_pdf_by_tokens(pdf_path, parse_document, MAX_TOKENS=MAX_TOKENS, OVERLAP=OVERLAP):
    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path, filename)  # List [(page_number, page_text)]
    chunks = []
    all_tokens = []
    token_page_map = []  # Keeps track of which page each token came from, [page number of token1, token2, token3 ...]
    for page_number, page_text in text_and_pagenumber:
        tokens = encode_text(page_text)
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
            "chunk_index": chunk_index
        }

        if ADD_LLM_CONTEXT:
            context_page_span = get_page_span(token_page_map, chunk_pages)
            context_chunks = [page_text for _, page_text in text_and_pagenumber[context_page_span[0] - 1:context_page_span[1] - 1]]
            chunks.append({"text": add_context(chunk_text, context_chunks, SYS_PROMPT_FOR_CONTEXT) + "\n\n" + chunk_text, "metadata": chunk_metadata})
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
def chunk_pdf_recursive_token_size(pdf_path, parse_document, MAX_TOKENS=MAX_TOKENS, OVERLAP=OVERLAP):
    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path, filename)  # [(page_number, page_text)]
    
    splitter = RecursiveCharacterTextSplitter(
        length_function=get_token_count,
        chunk_size=MAX_TOKENS,
        chunk_overlap=OVERLAP,
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
    chunks = []
    current_chunk = []
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
        }
        if ADD_LLM_CONTEXT:
            context_page_span = get_page_span(paragraph_page_map, page_list)
            context_chunks = [page_text for _, page_text in text_and_pagenumber[context_page_span[0] - 1:context_page_span[1] - 1]]
            chunks.append({"text": add_context(chunk_text, context_chunks, SYS_PROMPT_FOR_CONTEXT) + "\n\n" + chunk_text, "metadata": chunk_metadata})
        else:
            chunks.append({"text": chunk_text, "metadata": chunk_metadata})

        chunk_index += 1
        current_chunk.clear()
        current_token_count = 0

    chunk_page_numbers = []

    for paragraph, page_number in zip(all_paragraphs, paragraph_page_map):
        tokens = encode_text(paragraph)
        if current_token_count + len(tokens) > MAX_TOKENS:
            finalize_chunk()
            chunk_page_numbers.clear()
        current_chunk.append(paragraph)
        current_token_count += len(tokens)
        chunk_page_numbers.append(page_number)

    finalize_chunk()  # Catch the last one

    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks

    return chunks