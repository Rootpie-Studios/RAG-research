# See Calling Functions way below for the main function calls.
# This script processes PDF files, normalizes text, chunks it into manageable pieces

from rich import print
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from tomlkit import (
    parse,
    dumps,
)  # allows to keep formatting, but slow. So only used for creating toml files
import tomli  # Used to read the toml files fast.
import pandas as pd
import re
from Levenshtein import distance
from Levenshtein import ratio

load_dotenv()

# -----------------------------------------------#
# -------------------Config----------------------#
# -----------------------------------------------#
PDF_DIRECTORY = "./pdf_data"
TOML_DIRECTORY = "questions/cleaned"
COLLECTION_NAME = (
    "doc_collection_norm_all_minilm"  # Changed collection name to differentiate
)
PERSIST_DIRECTORY = "doc_storage_norm_all_minilm"  # Changed persist directory
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Changed embedding model name
MAX_TOKENS = (
    512  # Increased MAX_TOKENS for better context, considering SentenceTransformer
)
CHUNK_OVERLAP = 150  # New: Define chunk overlap for characters
RESULTS_PER_QUERY = 5
MATCH_THRESHOLD = 50
RESULTS_CSV_NAME = "results/norm_queries_minilm.csv"  # Changed result file name
RESULTS_EXCEL_NAME = (
    "results/norm_queries_excel_minilm.xlsx"  # Changed result file name
)
# -----------------------------------------------#
# ------------ChromaDB Config--------------------#
# -----------------------------------------------#
# Initialize SentenceTransformerEmbeddingFunction
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL_NAME
)

chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
# If you want to delete a collection
# chroma_client.delete_collection(name=COLLECTION_NAME)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME, embedding_function=sentence_transformer_ef
)


# ------------------------------------------------------------------------#
# --------------------Function definitions--------------------------------#
# ---------------(Calls are done after all definitions)-------------------#


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
        text = page.get_text(sort=True)
        if text.strip():  # Skip empty pages
            norm_text = normalize_text(text)
            text_and_pagenumber.append((i + 1, norm_text + " "))
    doc.close()
    # Test print
    # print(text_and_pagenumber)
    return text_and_pagenumber


# -----------------------------------------------#
# -------------Tokenize and Chunk up-------------#
# -----------------------------------------------#
def chunk_pdf_by_tokens(pdf_path, max_tokens=MAX_TOKENS, chunk_overlap=CHUNK_OVERLAP):
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


# --------------------------------------------------------------#
# --------------------Embedd all questions----------------------#
# --------------------------------------------------------------#
# Creates new toml files with the embedding of the question added
def add_embeddings_to_toml(toml_dir):
    for filename in os.listdir(toml_dir):
        if filename.endswith(".toml"):
            with open(os.path.join(toml_dir, filename), "r", encoding="utf-8") as f:
                toml_f = parse(f.read())
            for question in toml_f["questions"]:
                # The embedding function associated with the collection will handle this when querying,
                # so we don't need to manually create and store embeddings in the TOML file for Sentence Transformers.
                # If you still want to store them, you would need to load the SentenceTransformer model
                # and generate embeddings here. For now, we'll rely on ChromaDB's query embedding.
                # If you need to store them in TOML for other reasons, add the following:
                # from sentence_transformers import SentenceTransformer
                # model = SentenceTransformer(EMBEDDING_MODEL_NAME)
                # question["question_embedding"] = model.encode(question["question"]).tolist()
                pass  # No change needed here for the main purpose of this code.

            # We are not adding embedding to toml now.
            # with open(toml_dir + "embedded_" + filename, "w", encoding="utf-8") as f:
            #     f.write(dumps(toml_f))
            print(
                f"Skipping embedding questions into {filename}. Embeddings will be generated during query."
            )


# Reads the toml files, with the embedded questions
def get_embedded_questions(toml_dir):
    all_embedded_questions = {}
    for filename in os.listdir(toml_dir):
        # We now look for original TOML files, as embeddings won't be pre-stored in "embedded_" files
        if filename.endswith(".toml") and not filename.startswith("embedded_"):
            file_path = os.path.join(toml_dir, filename)
            with open(file_path, "rb") as f:  # tomli requires binary mode
                toml_data = tomli.load(f)
            questions = toml_data.get("questions", [])
            for question in questions:
                q_id = question.get("id")
                if q_id:
                    all_embedded_questions[q_id] = question
    return all_embedded_questions


# -----------------------------------------------#
# -----------------Query Docs--------------------#
# -----------------------------------------------#

# --------------Helping Functions----------------#
# -----------------------------------------------#


def check_shrinking_matches(
    text_list, chunk, shrink_from_start=False, text_or_embedding="text", tolerance=1
):
    print(chunk)
    # chunk = normalize_text(chunk.lower())
    chunk = chunk.lower()
    text_len = len(text_list)
    chunk_len = len(chunk)

    for i in range(text_len - 3):
        # Determine the current substring based on shrinking direction
        current = text_list[i:] if shrink_from_start else text_list[: text_len - i]
        substring = "".join(current).lower()
        # substring = normalize_text(substring)
        substring_len = len(substring)
        # Use a sliding window over the chunk to compare with the substring
        for j in range(chunk_len - substring_len + 1):
            window = chunk[j : j + substring_len]
            dist = distance(substring, window, score_cutoff=1, score_hint=0)
            # Check if the distance is within the allowed tolerance
            if dist <= tolerance:
                percent_of_answer_kept = 100.0 * len(current) / text_len
                ratios = ratio(substring, window)
                if text_or_embedding == "text":
                    idx = chunk.find(window)
                    print(
                        f"Match within sliding window: \n'{substring}' \n== \n'{window}'"
                    )
                    print(f"Ratio match within window: {ratios}")
                    print(
                        f"Percent of answer kept:[green] {percent_of_answer_kept:.2f}%, {len(substring)}/{text_len} characters kept[/green]"
                    )
                    print(f"Match starts at char position: {idx}")
                    print(f"Match ends at char position: {idx + len(substring) - 1}")
                    print(f"Match length: {len(substring)}")
                    if not shrink_from_start:
                        print("\nPiece from chunk: ", chunk)
                return True, percent_of_answer_kept, substring_len

    return False, 0, 0


# This is just a function that calls check_shrinking_matches, and prints stuff around it
# Only used with query_documents_one_embedding
def match_strings(chunk_text, answer):
    answer_chars = list(answer.lower())
    print("[Shrinking from end and matching...]")
    match_from_start_bool = check_shrinking_matches(
        answer_chars, chunk_text, shrink_from_start=False, text_or_embedding="text"
    )[0]
    if match_from_start_bool:
        print("(Match from start)")
    else:
        print("(No match from start)")
    print("-" * 30)
    print("[Shrinking from start and matching...]")
    match_from_end_bool = check_shrinking_matches(
        answer_chars, chunk_text, shrink_from_start=True, text_or_embedding="text"
    )[0]
    if match_from_end_bool:
        print("(Match from end)")
    else:
        print("(No match from end)")
    return match_from_start_bool, match_from_end_bool


# Only concerns the excel file output
def escape_excel_formulas(val):
    if isinstance(val, str) and val.startswith("="):
        return (
            "'" + val
        )  # Maybe find another way? Because this kind of changes the chunk. It adds ' to chunks with = in the beginning.
    return val


def save_data_from_result(all_rows, all_columns, csv_name, excel_name):
    df = pd.DataFrame(all_rows, columns=all_columns)
    df.to_csv(csv_name, encoding="utf-8", index=False)

    df = df.map(escape_excel_formulas)
    # This is needed since some chunks start with '=' which excel interprets as a formula.
    # The loop below can check for instances of chunks starting with '='
    # for i, row in enumerate(all_rows):
    #    for j, val in enumerate(row):
    #        if isinstance(val, str) and val.strip().startswith("="):
    #            print(f"Warning: Cell at row {i}, column {j} starts with '=' and may be interpreted as a formula")
    with pd.ExcelWriter(excel_name) as writer:
        df.to_excel(writer, sheet_name="Test_Query", index=False)


# ----------------Query Functions----------------#
# -----------------------------------------------#
# There are 3 different ones.
# (query_documents_all_embeddings) is for query with all embeddings,
# (query_documents_one_embedding) is for a single embedding query,
# (query_documents_text_input) is for a single text query.


def query_documents_all_embeddings(question_dict, n_results=3):
    all_columns = [
        "Result_Id",
        "Correct_File",
        "Guessed_File",
        "Filename_Match",
        "Correct_Pages",
        "Guessed_Page",
        "Page_Match",
        "Distance",
        "Text_Match_Start_Percent",
        "Match_Length_Start",
        "Text_Match_End_Percent",
        "Match_Length_End",
        "No_match",
        "Match_Threshold",
        "Difficulty",
        "Category",
        "Expected_answer",
        "Question",
        "Returned_Chunk",
        "Chunk_Id",
    ]
    all_rows = []
    for value in question_dict.values():
        # For Sentence Transformers, we query with text, and the embedding function handles the embedding
        results = collection.query(query_texts=[value["question"]], n_results=n_results)
        for idx, document in enumerate(
            results["documents"][0]
        ):  # document here refers to chunks, due to chromadb naming
            distance = results["distances"][0][idx]
            metadata = results["metadatas"][0][idx]

            correct_file = value["files"][0]["file"]
            guessed_file = metadata.get("filename")
            filename_match = guessed_file == correct_file

            correct_pages = value["files"][0]["page_numbers"]
            guessed_page = metadata.get("page_number")
            # Don't check for page matches if wrong file
            if filename_match:
                page_match = guessed_page in correct_pages
            else:
                page_match = False

            match_from_start_bool, match_from_start_float, match_from_start_length = (
                check_shrinking_matches(
                    list(value["answer"].lower()), document, shrink_from_start=False
                )
            )
            match_from_end_bool, match_from_end_float, match_from_end_length = (
                check_shrinking_matches(
                    list(value["answer"].lower()), document, shrink_from_start=True
                )
            )
            # We need to figure out what the thershold is, and how to calculate it. This adds both matches.
            # We could use match length somehow as well?
            match_threshold = (
                True
                if (match_from_start_float + match_from_end_float > MATCH_THRESHOLD)
                else False
            )

            text_match_start_value = match_from_start_float
            text_match_end_value = match_from_end_float
            no_match = not (match_from_start_bool or match_from_end_bool)
            result_id = f"{value['id']}R{idx + 1}"

            row = [
                result_id,
                correct_file,
                guessed_file,
                filename_match,
                correct_pages,
                guessed_page,
                page_match,
                distance,
                text_match_start_value,
                match_from_start_length,
                text_match_end_value,
                match_from_end_length,
                no_match,
                match_threshold,
                value["difficulty"],
                value["category"],
                value["answer"],
                value["question"],
                document,
                results["ids"][0][idx],
            ]
            all_rows.append(row)

    save_data_from_result(all_rows, all_columns, RESULTS_CSV_NAME, RESULTS_EXCEL_NAME)


# For query with one question, using text input (ChromaDB handles embedding)
def query_documents_one_embedding(question_data, n_results=3):
    results = collection.query(
        query_texts=[question_data["question"]], n_results=n_results
    )
    for idx, document in enumerate(results["documents"][0]):
        distance = results["distances"][0][idx]
        metadata = results["metadatas"][0][idx]  # Include metadata if needed
        print("-" * 60)
        print("-" * 20, f"Result {idx + 1}", "-" * 20)
        print("-" * 60)
        print("Question: ", question_data["question"])
        print("Answer expected: ", question_data["answer"])
        print(
            "\nFile from result: ",
            metadata.get("filename"),
            " | File from toml: ",
            question_data["files"][0]["file"],
        )
        if metadata.get("filename") == question_data["files"][0]["file"]:
            print("Right File!")
            print(
                "Expected Pages",
                question_data["files"][0]["page_numbers"],
                " | Pages from result: ",
                metadata.get("page_number"),
            )
            if metadata.get("page_number") in question_data["files"][0]["page_numbers"]:
                print("Right Pages!")
            else:
                print("Wrong Pages!")
        else:
            print("Wrong File!")
        print("Distance between question and chunk embedding: ", distance)
        print("-" * 30)
        match_strings(
            document, question_data["answer"]
        )  # Does not use the returns, just the prints


# For query with one question, using text
# Chroma will first embed each query text with the collection's embedding function, if query_texts is used
def query_documents_text_input(question_text, n_results=3):
    results = collection.query(query_texts=[question_text], n_results=n_results)
    # Extract the relevant chunks. Flatten the list of lists
    # results["documents"] is a list of lists, where each sublist corresponds to a document
    relevant_chunks = [doc for sublist in results["documents"] for doc in sublist]
    for idx, document in enumerate(results["documents"][0]):
        doc_id = results["ids"][0][idx]
        distance = results["distances"][0][idx]
        metadata = results["metadatas"][0][idx]  # Include metadata if needed
        print("-" * 60)
        print(
            f"Found chunk: ID={doc_id}, Page={metadata.get('page_number')}, Distance={distance}"
        )
        print("-" * 60)
        print(f"Content:\n{document}\n\n---\n")

    return relevant_chunks


# ------------------------------------------------------------------------#
# -----------------------Calling Functions--------------------------------#
# ---------------(Some functions are only meant top be ran once)----------#
# ------------------------------------------------------------------------#

print("[green]Make sure your PDFs are in the pdf_data folder![/green]")
print("[green]Make sure your questions are in the questions/cleaned folder![/green]")
print(
    "[red]If you change MAX_TOKENS, CHUNK_OVERLAP or EMBEDDING_MODEL_NAME, you need to delete the doc_storage_norm_all_minilm folder![/red]"
)
process_pdfs_and_insert(PDF_DIRECTORY)

add_embeddings_to_toml(TOML_DIRECTORY)

question_dict = get_embedded_questions(TOML_DIRECTORY)

query_documents_one_embedding(
    question_dict["PMCSKOLVERKET004"], n_results=RESULTS_PER_QUERY
)
# query_documents_all_embeddings(question_dict, n_results=RESULTS_PER_QUERY)
