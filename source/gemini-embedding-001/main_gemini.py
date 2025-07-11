import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
import multiprocessing
from tomlkit import (
    parse,
    dumps,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF
import re
import pandas as pd
import tomli
from Levenshtein import distance, ratio
from tqdm import tqdm
from joblib import Parallel, delayed
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns
import google.generativeai as genai # Import the Google Generative AI library

# =====================================================================================
# CONFIG
# =====================================================================================

load_dotenv()

# ------------Directories------------#
PDF_DIRECTORY = "pdf_data"
TOML_DIRECTORY_CLEANED = "questions/cleaned"
TOML_DIRECTORY_EMBEDDED = "questions/embedded"
RESULTS_DIRECTORY = "results"


# ----Gemini and ChromaDB Configs----#
MAX_TOKENS = 512 # Note: Tokenization will be handled by the Gemini embedding model
OVERLAP = 100
BASE_NAME_VERSION = "all-embedding-001-cosine"

if OVERLAP > 0:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk_{OVERLAP}_Overlap"
else:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk"
    
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Use a different environment variable for Gemini API key
COLLECTION_NAME = f"docs_{VERSION_NAME}_collection"
PERSIST_DIRECTORY = f"docs_{VERSION_NAME}_storage"
EMBEDDING_MODEL_NAME = "models/embedding-001" # Changed to Gemini embedding model name


def get_client():
    # For Gemini, we configure the generative AI library with the API key
    genai.configure(api_key=GEMINI_API_KEY)
    return genai

def get_collection():
    # Use the GoogleGenerativeAiEmbeddingFunction for ChromaDB
    gemini_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=GEMINI_API_KEY, 
        model_name=EMBEDDING_MODEL_NAME
    )
    chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        
#    return chroma_client.get_or_create_collection(
#        name=COLLECTION_NAME, embedding_function=gemini_ef
#    )
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=gemini_ef,
        configuration={
            "hnsw": {
                "space": "cosine",
                "ef_construction": 200
            }
        }
    )

# ----------Results Configs----------#
MATCH_THRESHOLD = 30
MIN_ANS_LENGTH = 3
RESULTS_PER_QUERY = 5
TOLERANCE = 0
MULTIPROCESSING = True if TOLERANCE > 0 else False
DISTANCE = 0.64
OUTPUT_DIRECTORY_RESULTS = f"{RESULTS_DIRECTORY}/{VERSION_NAME}/"

def get_results_filenames():
    base_dir = os.path.join(RESULTS_DIRECTORY, VERSION_NAME)
    os.makedirs(base_dir, exist_ok=True)
    if MULTIPROCESSING:
        RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME}_{TOLERANCE}_tol.csv")
        RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME}_{TOLERANCE}_tol.xlsx")
    else:
        RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.csv")
        RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.xlsx")

    return RESULTS_CSV_NAME, RESULTS_EXCEL_NAME

# =====================================================================================
# EMBED TOML QUESTIONS
# =====================================================================================

def get_max_workers_embed(factor=1.5, fallback=4):
    try:
        return max(1, int(multiprocessing.cpu_count() * factor))
    except NotImplementedError:
        return fallback

def get_embedding(question, client):
    # Use client.embed_content for Gemini embeddings
    return client.embed_content(model=EMBEDDING_MODEL_NAME, content=question)["embedding"]

def process_toml_file(filename, client):
    full_path = os.path.join(TOML_DIRECTORY_CLEANED, filename)
    with open(full_path, "r", encoding="utf-8") as f:
        toml_f = parse(f.read())
    for question in toml_f["questions"]:
        question["question_embedding"] = get_embedding(question["question"], client)
    os.makedirs(TOML_DIRECTORY_EMBEDDED, exist_ok=True)
    out_path = os.path.join(TOML_DIRECTORY_EMBEDDED, f"embedded_{filename}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(dumps(toml_f))

def add_embeddings_to_toml(toml_dir, client, max_workers=None):
    if max_workers is None:
        max_workers = get_max_workers_embed()
    toml_files = [f for f in os.listdir(toml_dir) if f.endswith(".toml")]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_toml_file, f, client) for f in toml_files]
        for future in as_completed(futures):
            future.result()

# =====================================================================================
# PARSE AND EMBED PDFS INTO DB
# =====================================================================================

def normalize_text(input_text):
    normalized = re.sub(r"- ?\n", "", input_text.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r" +\.\s", ". ", normalized)
    return normalized

def parse_document(pdf_path):
    doc = fitz.open(pdf_path)
    text_and_pagenumber = []
    for i, page in enumerate(doc):
        text = page.get_text(sort=True)
        if text.strip():
            norm_text = normalize_text(text)
            text_and_pagenumber.append((i + 1, norm_text + " "))
    doc.close()
    return text_and_pagenumber

def chunk_pdf_by_tokens(pdf_path, MAX_TOKENS=MAX_TOKENS, OVERLAP=OVERLAP):
    # NOTE: With Gemini embeddings, you don't use tiktoken for token counting.
    # The MAX_TOKENS here will serve as an approximate guide for chunking,
    # but the actual token count for Gemini might differ.
    filename = os.path.basename(pdf_path)
    text_and_pagenumber = parse_document(pdf_path)
    
    chunks = []
    current_chunk_text = ""
    current_chunk_pages = set()
    chunk_index = 1

    for page_number, page_text in text_and_pagenumber:
        words = page_text.split()
        for word in words:
            if len((current_chunk_text + " " + word).split()) <= MAX_TOKENS: # Approximate word count
                current_chunk_text += " " + word
                current_chunk_pages.add(page_number)
            else:
                if current_chunk_text.strip():
                    chunks.append({
                        "text": current_chunk_text.strip(),
                        "metadata": {
                            "id": f"{filename}_chunk{chunk_index}",
                            "filename": filename,
                            "page_number": ",".join(map(str, sorted(list(current_chunk_pages)))),
                            "chunk_index": chunk_index,
                        }
                    })
                    chunk_index += 1
                
                # Handle overlap by taking the last part of the previous chunk
                overlap_text_words = current_chunk_text.split()[-int(MAX_TOKENS * OVERLAP / MAX_TOKENS):] if OVERLAP > 0 else []
                current_chunk_text = " ".join(overlap_text_words) + " " + word
                current_chunk_pages = {page_number} # Reset pages for new chunk, include current page

    # Add the last chunk if any text remains
    if current_chunk_text.strip():
        chunks.append({
            "text": current_chunk_text.strip(),
            "metadata": {
                "id": f"{filename}_chunk{chunk_index}",
                "filename": filename,
                "page_number": ",".join(map(str, sorted(list(current_chunk_pages)))),
                "chunk_index": chunk_index,
            }
        })

    total_chunks = len(chunks)
    for chunk in chunks:
        chunk["metadata"]["total_chunks"] = total_chunks
    return chunks


def get_max_workers_parse(factor=1.5, fallback=4):
    try:
        return max(1, int(multiprocessing.cpu_count() * factor))
    except NotImplementedError:
        return fallback

def embed_and_insert(chunk, client, collection):
    chunk_id = chunk["metadata"]["id"]
    try:
        # Use client.embed_content for Gemini embeddings
        embedding = client.embed_content(
            model=EMBEDDING_MODEL_NAME, content=chunk["text"]
        )["embedding"]
        collection.upsert(
            ids=[chunk_id],
            documents=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[chunk["metadata"]],
        )
    except Exception as e:
        print(f"[Error] Failed for {chunk_id}: {e}")

def process_pdfs_and_insert(directory, client, collection, max_workers=None):
    if max_workers is None:
        max_workers = get_max_workers_parse()

    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            print(f"\n📄 Processing file: {filename}")
            chunks = chunk_pdf_by_tokens(pdf_path)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(embed_and_insert, chunk, client, collection) for chunk in chunks]
                for future in as_completed(futures):
                    future.result()
            print(f"✅ Finished processing: {filename}")

# =====================================================================================
# QUERY DB
# =====================================================================================

def get_embedded_questions(toml_dir):
    all_embedded_questions = {}
    for filename in os.listdir(toml_dir):
        if filename.endswith(".toml") and "embedded_" in filename:
            file_path = os.path.join(toml_dir, filename)
            with open(file_path, "rb") as f:
                toml_data = tomli.load(f)
            questions = toml_data.get("questions", [])
            for question in questions:
                q_id = question.get("id")
                if q_id:
                    all_embedded_questions[q_id] = question
    return all_embedded_questions

def check_shrinking_matches_no_tolerance(text_list, chunk, shrink_from_start=False):
    chunk = chunk.lower()
    text_len = len(text_list)
    for i in range(text_len - MIN_ANS_LENGTH):
        current = text_list[i:] if shrink_from_start else text_list[: text_len - i]
        substring = "".join(current).lower()
        if substring in chunk:
            percent_match = 100.0 * len(current) / text_len
            return True, percent_match, len(substring)
    return False, 0, 0

def check_shrinking_matches_with_tolerance(text_list, chunk, shrink_from_start=False):
    chunk = chunk.lower()
    text_len = len(text_list)
    chunk_len = len(chunk)
    for i in range(text_len - MIN_ANS_LENGTH):
        current = text_list[i:] if shrink_from_start else text_list[: text_len - i]
        substring = "".join(current).lower()
        substring_len = len(substring)
        for j in range(chunk_len - substring_len + 1):
            window = chunk[j : j + substring_len]
            dist = distance(substring, window, score_cutoff=1, score_hint=0)
            ratios = ratio(substring, window)
            if dist <= TOLERANCE and ratios >= 0.92:
                percent_of_answer_kept = 100.0 * len(current) / text_len
                return True, percent_of_answer_kept, substring_len
    return False, 0, 0

def get_text_match_info(value, document):
    func = (
        check_shrinking_matches_with_tolerance
        if TOLERANCE > 0
        else check_shrinking_matches_no_tolerance
    )
    answer_list = list(value["answer"])
    match_from_start = func(answer_list, document, shrink_from_start=False)
    match_from_end = func(answer_list, document, shrink_from_start=True)
    return (*match_from_start, *match_from_end)

def escape_excel_formulas(val):
    if isinstance(val, str) and val.startswith("="):
        return "'" + val
    return val

def save_data_from_result(all_rows, all_columns, csv_name, excel_name):
    df = pd.DataFrame(all_rows, columns=all_columns)
    df.to_csv(csv_name, encoding="utf-8", index=False)
    df = df.map(escape_excel_formulas)
    with pd.ExcelWriter(excel_name) as writer:
        df.to_excel(writer, sheet_name="Test_Query", index=False)

def query_documents_all_embeddings(question, collection, n_results=3):
    all_columns = [
        "Result_Id", "Correct_File", "Guessed_File",
        "Filename_Match", "Correct_Pages", "Guessed_Page",
        "Page_Match", "Distance", "Text_Match_Start_Percent",
        "Match_Length_Start", "Text_Match_End_Percent",
        "Match_Length_End", "No_match", "Match_Threshold",
        "Difficulty", "Category", "Expected_answer",
        "Question", "Returned_Chunk", "Chunk_Id",
    ]
    all_rows = []
    for value in tqdm(question.values(), desc="Processing questions"):
        results = collection.query(
            query_embeddings=[value["question_embedding"]], n_results=n_results
        )
        for idx, document in enumerate(results["documents"][0]):
            distance_val = results["distances"][0][idx]
            metadata = results["metadatas"][0][idx]
            correct_file = value["files"][0]["file"].lower()
            guessed_file = metadata.get("filename").lower()
            filename_match = guessed_file == correct_file
            correct_pages = value["files"][0]["page_numbers"]
            guessed_page = metadata.get("page_number")
            guessed_page_list = list(map(int, guessed_page.split(",")))
            page_match = any(page in correct_pages for page in guessed_page_list) if filename_match else False
            (match_from_start_bool, match_from_start_float,
                match_from_start_length, match_from_end_bool,
                match_from_end_float, match_from_end_length,) = get_text_match_info(value, document)
            match_threshold = (
                match_from_start_float + match_from_end_float > MATCH_THRESHOLD
            )
            no_match = not (match_from_start_bool or match_from_end_bool)
            result_id = f"{value['id']}R{idx + 1}"
            row = [
                result_id, correct_file, guessed_file, filename_match,
                correct_pages, guessed_page, page_match, distance_val,
                match_from_start_float, match_from_start_length,
                match_from_end_float, match_from_end_length, no_match,
                match_threshold, value["difficulty"], value["category"],
                value["answer"], value["question"], document,
                results["ids"][0][idx],
            ]
            all_rows.append(row)
    RESULTS_CSV_NAME, RESULTS_EXCEL_NAME = get_results_filenames()
    save_data_from_result(all_rows, all_columns, RESULTS_CSV_NAME, RESULTS_EXCEL_NAME)

def process_question(value, n_results):
    collection = get_collection()
    results = collection.query(
        query_embeddings=[value["question_embedding"]], n_results=n_results
    )
    all_rows = []
    for idx, document in enumerate(results["documents"][0]):
        distance_val = results["distances"][0][idx]
        metadata = results["metadatas"][0][idx]
        correct_file = value["files"][0]["file"].lower()
        guessed_file = metadata.get("filename").lower()
        filename_match = guessed_file == correct_file
        correct_pages = value["files"][0]["page_numbers"]
        guessed_page = metadata.get("page_number")
        guessed_page_list = list(map(int, guessed_page.split(",")))
        page_match = any(page in correct_pages for page in guessed_page_list) if filename_match else False
        (
            match_from_start_bool, match_from_start_float,
            match_from_start_length, match_from_end_bool,
            match_from_end_float, match_from_end_length,
        ) = get_text_match_info(value, document)
        match_threshold = (
            match_from_start_float + match_from_end_float > MATCH_THRESHOLD
        )
        no_match = not (match_from_start_bool or match_from_end_bool)
        result_id = f"{value['id']}R{idx + 1}"
        row = [
            result_id, correct_file, guessed_file, filename_match,
            correct_pages, guessed_page, page_match, distance_val,
            match_from_start_float, match_from_start_length,
            match_from_end_float, match_from_end_length, no_match,
            match_threshold, value["difficulty"], value["category"],
            value["answer"], value["question"], document,
            results["ids"][0][idx],
        ]
        all_rows.append(row)
    return all_rows

def query_documents_all_embeddings_parallel(question_dict, n_results=3):
    all_columns = [
        "Result_Id", "Correct_File", "Guessed_File",
        "Filename_Match", "Correct_Pages", "Guessed_Page",
        "Page_Match", "Distance", "Text_Match_Start_Percent",
        "Match_Length_Start", "Text_Match_End_Percent",
        "Match_Length_End", "No_match", "Match_Threshold",
        "Difficulty", "Category", "Expected_answer",
        "Question", "Returned_Chunk", "Chunk_Id",
    ]
    results = Parallel(n_jobs=-1)(
        delayed(process_question)(val, n_results)
        for val in tqdm(question_dict.values(), desc="Parallel Processing")
    )
    all_rows = [row for result in results for row in result]
    RESULTS_CSV_NAME, RESULTS_EXCEL_NAME = get_results_filenames()
    save_data_from_result(all_rows, all_columns, RESULTS_CSV_NAME, RESULTS_EXCEL_NAME)


SAVE_PLOTS = True

def match_combo(row):
    if row["Filename_Match"] and row["Page_Match"]:
        return "File and Page"
    elif row["Filename_Match"]:
        return "Filename Only"
    elif row["Page_Match"]:
        return "Page Only"
    else:
        return "Neither"
    
def plot_acc_by_cat(df, output_dir):
    df['Query_ID'] = df['Result_Id'].str[:-2]
    query_match = df.groupby('Query_ID')['Match_Threshold'].any().reset_index()
    query_match.rename(columns={'Match_Threshold': 'Any_Match'}, inplace=True)
    query_category = df.groupby('Query_ID')['Category'].first().reset_index()
    query_summary = pd.merge(query_match, query_category, on='Query_ID')
    df_counts = query_summary.groupby(['Category', 'Any_Match']).size().unstack(fill_value=0)
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(16, 8))
    categories = df_counts.index
    true_counts = df_counts[True] if True in df_counts else [0]*len(categories)
    false_counts = df_counts[False] if False in df_counts else [0]*len(categories)
    plt.bar(categories, false_counts, label='False', color='salmon')
    plt.bar(categories, true_counts, bottom=false_counts, label='True', color='seagreen')
    plt.title("Match Threshold Accuracy by Category (at least one match per query)")
    plt.ylabel("Count of Queries")
    plt.xticks(rotation=45)
    plt.legend(title="Any Match Threshold Met")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_acc_by_cat.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
        
def plot_match_file_vs_page(df, output_dir):
    df["Match_Combo"] = df["Filename_Match"].astype(str) + "File_" + df["Page_Match"].astype(str) + "Page"
    plt.figure(figsize=(8, 6))
    sns.countplot(data=df, x="Match_Combo", order=df["Match_Combo"].value_counts().index, hue="Match_Combo")
    plt.title("Combined Filename and Page Match For all Results")
    plt.xlabel("Match Combination (Filename_Page)")
    plt.ylabel("Count")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_match_file_vs_page.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_threshold_given_page_match(df, output_dir):
    filtered_df = df[df["Page_Match"]]
    threshold_counts = filtered_df["Match_Threshold"].value_counts().reindex([True, False], fill_value=0)
    plt.figure(figsize=(6, 5))
    plt.bar(threshold_counts.index.map(str), threshold_counts.values, color=['seagreen', 'salmon'])
    plt.title("Match Threshold Counts (Only Where Page Match = True)")
    plt.xlabel("Match_Threshold")
    plt.ylabel("Count")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_threshold_given_page_match.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_best_result_by_text_match(df, output_dir):
    df["Combined_Score"] = df["Text_Match_Start_Percent"] + df["Text_Match_End_Percent"]
    df["Result_Tag"] = df["Result_Id"].str[-2:]
    df["Question_Id"] = df["Result_Id"].str[:-2]
    best_results = df.loc[df.groupby("Question_Id")["Combined_Score"].idxmax()]
    result_counts = best_results["Result_Tag"].value_counts().reindex(["R1", "R2", "R3", "R4", "R5"], fill_value=0)
    plt.figure(figsize=(6, 5))
    plt.bar(result_counts.index, result_counts.values, color="cornflowerblue")
    plt.title("Best Result Based on Combined Text Match")
    plt.xlabel("Result (R1, R2, R3, R4, R5)")
    plt.ylabel("Number of Times Best")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_best_result_by_text_match.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_matches_heatmap_split(df, output_dir):
    g = sns.FacetGrid(df, col="Match_Threshold", height=6, aspect=1)
    g.map_dataframe(
        sns.histplot,
        x="Text_Match_End_Percent",
        y="Text_Match_Start_Percent",
        bins=30,
        cmap="coolwarm",
        cbar=True
    )
    g.set_axis_labels("Text Match from End (%)", "Text Match from Start (%)")
    g.figure.subplots_adjust(top=0.85)
    g.figure.suptitle("Heatmap of Text Match Start vs End (%) by Threshold")
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_matches_heatmap_split.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_accuracy_precision_recall(df, output_dir):
    df['Query_ID'] = df['Result_Id'].str[:-2]
    accuracy_df = df.groupby('Query_ID')['Filename_Match'].any()
    accuracy = accuracy_df.mean()
    print("- For Files")
    filtered_df = df[df['Distance'] <= DISTANCE]
    matches_after_filter = filtered_df.groupby('Query_ID')['Filename_Match'].any()
    queries_with_results = filtered_df['Query_ID'].unique()
    precision = matches_after_filter.sum() / len(queries_with_results)
    all_queries = df['Query_ID'].unique()
    queries_with_no_results = set(all_queries) - set(queries_with_results)
    recall = matches_after_filter.sum() / (matches_after_filter.sum() + len(queries_with_no_results))
    with open(os.path.join(output_dir, "APR_Files.txt"), "w") as f:
        def log(message):
            print(message)
            f.write(message + "\n")
        log(f"Accuracy: {accuracy:.2f}")
        log(f"Precision: {precision:.2f}")
        log(f"Recall: {recall:.2f}")
        log("Queries with results after filtering: " + str(len(queries_with_results)))
        log("Queries with no results after filtering: " + str(len(queries_with_no_results)))
        log("Total number of queries: " + str(len(all_queries)))
    plt.figure(figsize=(8, 5))
    plt.bar(['Accuracy', 'Precision', 'Recall'], [accuracy, precision, recall], color=['blue', 'green', 'orange'])
    plt.ylabel('Score')
    plt.ylim(0, 1)
    plt.title('Evaluation Metrics (Files)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_accuracy_precision_recall.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_accuracy_precision_recall_pages(df, output_dir):
    df['Query_ID'] = df['Result_Id'].str[:-2]
    accuracy_df = df.groupby('Query_ID')['Page_Match'].any()
    accuracy = accuracy_df.mean()
    print("- For Pages")
    filtered_df = df[df['Distance'] <= DISTANCE]
    matches_after_filter = filtered_df.groupby('Query_ID')['Page_Match'].any()
    queries_with_results = filtered_df['Query_ID'].unique()
    precision = matches_after_filter.sum() / len(queries_with_results)
    all_queries = df['Query_ID'].unique()
    queries_with_no_results = set(all_queries) - set(queries_with_results)
    recall = matches_after_filter.sum() / (matches_after_filter.sum() + len(queries_with_no_results))
    with open(os.path.join(output_dir, "APR_Pages.txt"), "w") as f:
        def log(message):
            print(message)
            f.write(message + "\n")
        log(f"Accuracy: {accuracy:.2f}")
        log(f"Precision: {precision:.2f}")
        log(f"Recall: {recall:.2f}")
        log("Queries with results after filtering: " + str(len(queries_with_results)))
        log("Queries with no results after filtering: " + str(len(queries_with_no_results)))
        log("Total number of queries: " + str(len(all_queries)))
    plt.figure(figsize=(8, 5))
    plt.bar(['Accuracy', 'Precision', 'Recall'], [accuracy, precision, recall], color=['blue', 'green', 'orange'])
    plt.ylabel('Score')
    plt.ylim(0, 1)
    plt.title('Evaluation Metrics  (Pages)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_accuracy_precision_recall_pages.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_accuracy_precision_recall_chunks(df, output_dir):
    df['Query_ID'] = df['Result_Id'].str[:-2]
    accuracy_df = df.groupby('Query_ID')['Match_Threshold'].any()
    accuracy = accuracy_df.mean()
    print("- For Chunks")
    filtered_df = df[df['Distance'] <= DISTANCE]
    matches_after_filter = filtered_df.groupby('Query_ID')['Match_Threshold'].any()
    queries_with_results = filtered_df['Query_ID'].unique()
    precision = matches_after_filter.sum() / len(queries_with_results)
    all_queries = df['Query_ID'].unique()
    queries_with_no_results = set(all_queries) - set(queries_with_results)
    recall = matches_after_filter.sum() / (matches_after_filter.sum() + len(queries_with_no_results))
    with open(os.path.join(output_dir, "APR_Chunks.txt"), "w") as f:
        def log(message):
            print(message)
            f.write(message + "\n")
        log(f"Accuracy: {accuracy:.2f}")
        log(f"Precision: {precision:.2f}")
        log(f"Recall: {recall:.2f}")
        log("Queries with results after filtering: " + str(len(queries_with_results)))
        log("Queries with no results after filtering: " + str(len(queries_with_no_results)))
        log("Total number of queries: " + str(len(all_queries)))
    plt.figure(figsize=(8, 5))
    plt.bar(['Accuracy', 'Precision', 'Recall'], [accuracy, precision, recall], color=['blue', 'green', 'orange'])
    plt.ylabel('Score')
    plt.ylim(0, 1)
    plt.title('Evaluation Metrics (Chunks)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_accuracy_precision_recall_chunks.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_match_file_vs_page_by_result(df, output_dir):
    df["Result_Num"] = df["Result_Id"].str.extract(r'(R[1-5])')
    df["Match_Combo"] = df["Filename_Match"].astype(str) + "_File_" + df["Page_Match"].astype(str) + "_Page"
    count_df = df.groupby(["Match_Combo", "Result_Num"]).size().unstack(fill_value=0)
    count_df = count_df.loc[count_df.sum(axis=1).sort_values(ascending=False).index]
    count_df.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="tab10")
    plt.title("Filename and Page Matches by Result Number (Stacked)")
    plt.xlabel("Match Combination (Filename_Page)")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Result Number")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_match_file_vs_page_by_result.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()

def plot_stacked_matches_by_result3(df, output_dir):
    df["Result_Num"] = df["Result_Id"].str.extract(r'(R[1-5])')
    df["Match_Combo"] = df["Filename_Match"].astype(str) + "_File_" + df["Page_Match"].astype(str) + "_Page"
    count_df = df.groupby(["Result_Num", "Match_Combo"]).size().unstack(fill_value=0)
    count_df = count_df[count_df.sum().sort_values(ascending=False).index]
    count_df.plot(kind="bar", stacked=True, figsize=(10, 6), colormap="tab20")
    plt.title("Stacked Match Combinations by Result Number")
    plt.xlabel("Result Number")
    plt.ylabel("Count")
    plt.xticks(rotation=0)
    plt.legend(title="Match Combination", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_stacked_matches_by_result3.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_match_file_vs_page_by_result2(df, output_dir):
    df["Result_Num"] = df["Result_Id"].str.extract(r'(R[1-5])')
    df["Match_Combo"] = df["Filename_Match"].astype(str) + "_File_" + df["Page_Match"].astype(str) + "_Page"
    g = sns.FacetGrid(df, col="Result_Num", col_order=["R1", "R2", "R3", "R4", "R5"], 
                      col_wrap=3, height=4, sharex=False, sharey=True)
    g.map(sns.countplot, "Match_Combo", order=df["Match_Combo"].value_counts().index)
    g.set_titles("Result: {col_name}")
    for ax in g.axes.flat:
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    g.set_axis_labels("Match Combination (Filename_Page)", "Count")
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_match_file_vs_page_by_result2.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_matches_heatmap_split_with_match_type(df, output_dir):
    df["Match_Combo"] = df.apply(match_combo, axis=1)
    size_map = {"File and Page": 200, "Filename Only": 150, "Page Only": 100, "Neither": 50}
    color_map = {"File and Page": "pink", "Filename Only": "blue", "Page Only": "orange", "Neither": "red"}
    df["Match_Type"] = df["Match_Combo"].map(lambda x: {"File and Page": "File and Page", "Filename Only": "Filename Only", "Page Only": "Page Only", "Neither": "Neither"}[x])
    df["Point_Size"] = df["Match_Type"].map(size_map)
    df["Point_Color"] = df["Match_Type"].map(color_map)
    g = sns.FacetGrid(df, col="Match_Threshold", height=6, aspect=1)
    g.map_dataframe(
        sns.scatterplot, x="Text_Match_End_Percent", y="Text_Match_Start_Percent",
        hue="Match_Type", size="Point_Size", sizes=(50, 200), alpha=0.6,
        palette=color_map, legend="full"
    )
    g.set_axis_labels("Text Match from End (%)", "Text Match from Start (%)")
    g.figure.subplots_adjust(top=0.85)
    g.figure.suptitle("Match Type Scatter Heatmap by Threshold")
    first_ax = g.axes[0][0]
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=match_type,
               markerfacecolor=color_map[match_type], markersize=(size_map[match_type] ** 0.5) * 1.2)
        for match_type in size_map.keys()
    ]
    first_ax.legend(handles=legend_elements, title="Match Type", loc='upper left', frameon=True, borderpad=1)
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_matches_heatmap_split_with_match_type.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
def plot_text_match_info(df, output_dir):
    total_match = df["Match_Threshold"].sum()
    page_match = (df["Match_Threshold"] & df["Page_Match"]).sum()
    page_no_match = (df["Match_Threshold"] & df["Filename_Match"] & ~df["Page_Match"]).sum()
    filename_no_match = (df["Match_Threshold"] & ~df["Filename_Match"]).sum()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar('Total', total_match, color='skyblue')
    ax.bar('Filename Match (stacked)', page_match, color='orange', label='Page Match')
    ax.bar('Filename Match (stacked)', page_no_match, bottom=page_match, color='red', label='No Page Match')
    ax.bar('No Filename Match', filename_no_match, color='green')
    ax.legend()
    ax.set_ylabel("Count")
    ax.set_title("Text Match Types (for all Match_Threshold = True)")
    plt.xticks(rotation=15)
    plt.tight_layout()
    if SAVE_PLOTS:
        plt.savefig(os.path.join(output_dir, "plot_text_match_info.png"), dpi=300, bbox_inches='tight')
    else:
        plt.show()

def main():
    # --- Initialization ---
    client = get_client()
    collection = get_collection()
    RESULTS_CSV_NAME, RESULTS_EXCEL_NAME = get_results_filenames()
    
    # --- Step 1: Parse, Chunk, Embed PDFs and Insert into DB ---
    print("\nStep 1: Processing PDFs and inserting into database...")
    process_pdfs_and_insert(PDF_DIRECTORY, client, collection)
    print("✅ Finished processing PDFs.")

    # --- Step 2: Embed TOML Questions ---
    print("Step 2: Embedding TOML questions...")
    add_embeddings_to_toml(TOML_DIRECTORY_CLEANED, client)
    print("✅ Finished embedding TOML questions.")

    # --- Step 3: Query DB with Embedded Questions ---
    print("\nStep 3: Querying the database with all questions...")
    question_dict = get_embedded_questions(TOML_DIRECTORY_EMBEDDED)
    if MULTIPROCESSING:
        query_documents_all_embeddings_parallel(
            question_dict, n_results=RESULTS_PER_QUERY
        )
    else:
        query_documents_all_embeddings(question_dict, collection, n_results=RESULTS_PER_QUERY)
    print(f"✅ Finished querying. Results saved to {RESULTS_CSV_NAME}")

    # --- Step 4: Generate and Save Plots ---
    print("\nStep 4: Generating and saving plots...")
    df = pd.read_csv(RESULTS_CSV_NAME, sep=",", encoding="utf-8")
    
    plot_match_file_vs_page_by_result2(df, OUTPUT_DIRECTORY_RESULTS)
    plot_match_file_vs_page_by_result(df, OUTPUT_DIRECTORY_RESULTS)
    plot_stacked_matches_by_result3(df, OUTPUT_DIRECTORY_RESULTS)
    plot_match_file_vs_page(df, OUTPUT_DIRECTORY_RESULTS)
    plot_accuracy_precision_recall(df, OUTPUT_DIRECTORY_RESULTS)
    plot_accuracy_precision_recall_pages(df, OUTPUT_DIRECTORY_RESULTS)
    plot_accuracy_precision_recall_chunks(df, OUTPUT_DIRECTORY_RESULTS)
    plot_text_match_info(df, OUTPUT_DIRECTORY_RESULTS)
    plot_threshold_given_page_match(df, OUTPUT_DIRECTORY_RESULTS)
    plot_matches_heatmap_split(df, OUTPUT_DIRECTORY_RESULTS)
    plot_matches_heatmap_split_with_match_type(df, OUTPUT_DIRECTORY_RESULTS)
    plot_best_result_by_text_match(df, OUTPUT_DIRECTORY_RESULTS)
    plot_acc_by_cat(df, OUTPUT_DIRECTORY_RESULTS)

    print(f"\n\nAll plots and calculations are saved in: {OUTPUT_DIRECTORY_RESULTS}")
    print("---Done---")


if __name__ == "__main__":
    main()