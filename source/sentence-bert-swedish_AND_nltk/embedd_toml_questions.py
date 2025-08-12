# --This takes all toml files in TOML_DIRECTORY_CLEANED and parses them.
# --Then it adds a key-value pair "question_embedding" = [embedding array of the question].
# --It then saves a new file in the directory TOML_DIRECTORY_EMBEDDED. The file will have an "embedded_"-prefix,
# ----which is a copy of the old toml, but with the embeddings included in the file.
# --Important to keep the "embedded_"-prefix, since other functions use that as a filter,
# ----to choose which file to read.

import multiprocessing
import os
from tomlkit import (
    parse,
    dumps,
)
from config import (
    EMBEDDING_MODEL_NAME,
    TOML_DIRECTORY_CLEANED,
    TOML_DIRECTORY_EMBEDDED,
    get_client,
)
from concurrent.futures import ThreadPoolExecutor, as_completed

client = get_client()


def get_max_workers(factor=1.5, fallback=4):
    try:
        return max(1, int(multiprocessing.cpu_count() * factor))
    except NotImplementedError:
        return fallback


def get_embedding(question):
    return (
        client.embeddings.create(input=question, model=EMBEDDING_MODEL_NAME)
        .data[0]
        .embedding
    )


def process_toml_file(filename):
    full_path = os.path.join(TOML_DIRECTORY_CLEANED, filename)
    with open(full_path, "r", encoding="utf-8") as f:
        toml_f = parse(f.read())
    for question in toml_f["questions"]:
        question["question_embedding"] = get_embedding(question["question"])
    os.makedirs(TOML_DIRECTORY_EMBEDDED, exist_ok=True)
    out_path = os.path.join(TOML_DIRECTORY_EMBEDDED, f"embedded_{filename}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(dumps(toml_f))


def add_embeddings_to_toml_workers(toml_dir, max_workers=None):
    if max_workers is None:
        max_workers = get_max_workers()
    toml_files = [f for f in os.listdir(toml_dir) if f.endswith(".toml")]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_toml_file, f) for f in toml_files]
        for future in as_completed(futures):
            future.result()


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


# --------------------------------------------------------------#
# -------Write new toml files with embeddings included----------#
# --------------------------------------------------------------#
add_embeddings_to_toml(TOML_DIRECTORY_CLEANED)
