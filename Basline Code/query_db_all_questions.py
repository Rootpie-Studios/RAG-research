import os
import pandas as pd
import tomli
from Levenshtein import distance
from Levenshtein import ratio
from tqdm import tqdm
from joblib import Parallel, delayed
from config import (
    TOML_DIRECTORY_EMBEDDED,
    RESULTS_PER_QUERY,
    TOLERANCE,
    MATCH_THRESHOLD,
    MIN_ANS_LENGTH,
    MULTIPROCESSING,
    get_collection,
    get_results_filenames
)

RESULTS_CSV_NAME, RESULTS_EXCEL_NAME = get_results_filenames()
collection = get_collection()


# -----------------------------------------------#
# ---------------Helping functions---------------#
# -----------------------------------------------#
# Reads the toml files, with the embedded questions
def get_embedded_questions(toml_dir):
    all_embedded_questions = {}
    for filename in os.listdir(toml_dir):
        if filename.endswith(".toml") and "embedded_" in filename:
            file_path = os.path.join(toml_dir, filename)
            with open(file_path, "rb") as f:  # tomli requires binary mode
                toml_data = tomli.load(f)
            questions = toml_data.get("questions", [])
            for question in questions:
                q_id = question.get("id")
                if q_id:
                    all_embedded_questions[q_id] = question
    return all_embedded_questions


# Checks the saved answer with the fetched chunk
# If no match, it shrinks by one character and tries again.
# until characters run out or match is found. Forwards and backwards is possible.
# You can change range of loop to not shrink until the very last character
# since that is a bad match anyway.
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


# A version with tolerance for character mismatch, but it is very slow. Some questions takes much longer than others.
# The number of characters that can mismatch is set by the TOLERANCE variable at the top.
def check_shrinking_matches_with_tolerance(text_list, chunk, shrink_from_start=False):
    chunk = chunk.lower()
    text_len = len(text_list)
    chunk_len = len(chunk)
    for i in range(text_len - MIN_ANS_LENGTH):
        # Determine the current substring based on shrinking direction
        current = text_list[i:] if shrink_from_start else text_list[: text_len - i]
        substring = "".join(current).lower()
        substring_len = len(substring)
        # Use a sliding window over the chunk to compare with the substring
        for j in range(chunk_len - substring_len + 1):
            window = chunk[j : j + substring_len]
            dist = distance(substring, window, score_cutoff=1, score_hint=0)
            ratios = ratio(substring, window)
            # Check if the distance is within the allowed tolerance
            # ratios limit tries to block very short answers that have changed too many characters. (needs optimizing and testing)
            if dist <= TOLERANCE and ratios >= 0.92:
                percent_of_answer_kept = 100.0 * len(current) / text_len
                return True, percent_of_answer_kept, substring_len
    return False, 0, 0


# Selection of function type based on need for parallel processing
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


# Only concerns the excel file output
def escape_excel_formulas(val):
    if isinstance(val, str) and val.startswith("="):
        return "'" + val
    return val


# Save results to csv and xlsx files
def save_data_from_result(all_rows, all_columns, csv_name, excel_name):
    df = pd.DataFrame(all_rows, columns=all_columns)
    df.to_csv(csv_name, encoding="utf-8", index=False)
    df = df.map(escape_excel_formulas)
    with pd.ExcelWriter(excel_name) as writer:
        df.to_excel(writer, sheet_name="Test_Query", index=False)


# -----------------------------------------------#
# --------------Query function-------------------#
# -----------------------------------------------#
# Columns stored in the results file
all_columns = [
        "Result_Id", "Correct_File", "Guessed_File",
        "Filename_Match", "Correct_Pages", "Guessed_Page",
        "Page_Match", "Distance", "Text_Match_Start_Percent",
        "Match_Length_Start", "Text_Match_End_Percent",
        "Match_Length_End", "No_match", "Match_Threshold",
        "Difficulty", "Category", "Expected_answer",
        "Question", "Returned_Chunk", "Chunk_Id",
    ]


def query_documents_all_embeddings(question, n_results=3):
    all_rows = []
    for value in tqdm(question.values(), desc="Processing questions"):
        results = collection.query(
            query_embeddings=[value["question_embedding"]], n_results=n_results
        )
        for idx, document in enumerate(results["documents"][0]):
            # document here refers to chunks, due to chromadb naming
            # so we are looking at the results for returned chunks here.
            distance_val = results["distances"][0][idx]
            metadata = results["metadatas"][0][idx]

            correct_file = value["files"][0]["file"].lower()
            guessed_file = metadata.get("filename").lower() # since toml parser might change case
            filename_match = guessed_file == correct_file

            correct_pages = value["files"][0]["page_numbers"]
            guessed_page = metadata.get("page_number")
            guessed_page_list = list(map(int, guessed_page.split(",")))
            # Don't check for page matches if wrong file
            page_match = any(page in correct_pages for page in guessed_page_list) if filename_match else False

            (match_from_start_bool, match_from_start_float,
                match_from_start_length, match_from_end_bool,
                match_from_end_float, match_from_end_length,) = get_text_match_info(value, document)
            # We need to figure out what the thershold is, and how to calculate it. This adds both matches.
            # We could use match length somehow as well?
            match_threshold = (
                match_from_start_float + match_from_end_float > MATCH_THRESHOLD
            )
            no_match = not (match_from_start_bool or match_from_end_bool)
            result_id = f"{value['id']}R{idx + 1}"

            # Rows stored in results file. Order matters! Needs to match column order.
            row = [
                result_id,
                correct_file,
                guessed_file,
                filename_match,
                correct_pages,
                guessed_page,
                page_match,
                distance_val,
                match_from_start_float,
                match_from_start_length,
                match_from_end_float,
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
    # Save results to file
    save_data_from_result(all_rows, all_columns, RESULTS_CSV_NAME, RESULTS_EXCEL_NAME)


# Same as above but for parallel processing
def process_question(value, n_results):
    collection = get_collection() # Slow to load collection each time, but needed for multiprocessing to work right now.
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
            match_from_start_bool,
            match_from_start_float,
            match_from_start_length,
            match_from_end_bool,
            match_from_end_float,
            match_from_end_length,
        ) = get_text_match_info(value, document)

        match_threshold = (
            match_from_start_float + match_from_end_float > MATCH_THRESHOLD
        )
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
            distance_val,
            match_from_start_float,
            match_from_start_length,
            match_from_end_float,
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
    return all_rows


def query_documents_all_embeddings_parallel(question_dict, n_results=3):
    results = Parallel(n_jobs=-1)(
        delayed(process_question)(val, n_results)
        for val in tqdm(question_dict.values(), desc="Parallel Processing")
    )

    all_rows = [row for result in results for row in result]
    save_data_from_result(all_rows, all_columns, RESULTS_CSV_NAME, RESULTS_EXCEL_NAME)

if __name__ == "__main__": # Needed for multiprocessing to work correctly
    # --------------------------------------------------------------#
    # -------Get the data from toml files, with embedding-----------#
    # --------------------------------------------------------------#
    question_dict = get_embedded_questions(TOML_DIRECTORY_EMBEDDED)

    # --------------------------------------------------------------#
    # -------------Run an embedded query from toml files------------#
    # --------------------------------------------------------------#
    if MULTIPROCESSING:
        query_documents_all_embeddings_parallel(
            question_dict, n_results=RESULTS_PER_QUERY
        )
    else:
        query_documents_all_embeddings(question_dict, n_results=RESULTS_PER_QUERY)
