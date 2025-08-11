# --This takes all toml files in TOML_DIRECTORY_CLEANED and parses them.
# --Then it adds a key-value pair "question_embedding" = [embedding array of the question].
# --It then saves a new file in the directory TOML_DIRECTORY_EMBEDDED. The file will have an "embedded_"-prefix, 
# ----which is a copy of the old toml, but with the embeddings included in the file.
# --Important to keep the "embedded_"-prefix, since other functions use that as a filter,
# ----to choose which file to read.

import os
from tomlkit import (
    parse,
    dumps,
)
from tqdm import tqdm
from config import (
    TOML_DIRECTORY_CLEANED,
    TOML_DIRECTORY_EMBEDDED,
    EMBEDDING_MODEL_NAME,
    get_client,
    pooling_setup,
    USE_OPENAI,
    LOCAL_EMBEDDING_SERVER,
    # AUTOMODEL_CUSTOM # If using AutoModel, from transformers library
)

BATCH_SIZE = 50

    
def get_embedding(question):
    if USE_OPENAI or LOCAL_EMBEDDING_SERVER:
        return get_client().embeddings.create(input=question, model=EMBEDDING_MODEL_NAME).data[0].embedding
    else:
        # If using AutoModel, from transformers library. Make sure to adjust for the specific model.
        formatted_question = f"Query: {question}"
        return pooling_setup(formatted_question)[0]
    
    
def add_embeddings_to_toml(toml_dir):
    toml_files = [f for f in os.listdir(toml_dir) if f.endswith(".toml")]
    
    for toml_file in tqdm(toml_files, desc="Processing TOML files"):
        full_path = os.path.join(TOML_DIRECTORY_CLEANED, toml_file)
        with open(full_path, "r", encoding="utf-8") as f:
            toml_file_edit = parse(f.read())
        for i in range(0, len(toml_file_edit["questions"]), BATCH_SIZE):
            batch = toml_file_edit["questions"][i:i + BATCH_SIZE]

            for question in batch:
                question["question_embedding"] = get_embedding(question["question"])
        os.makedirs(TOML_DIRECTORY_EMBEDDED, exist_ok=True)
        out_path = os.path.join(TOML_DIRECTORY_EMBEDDED, f"embedded_{toml_file}")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(dumps(toml_file_edit))


# --------------------------------------------------------------#
# -------Write new toml files with embeddings included----------#
# --------------------------------------------------------------#
add_embeddings_to_toml(TOML_DIRECTORY_CLEANED)