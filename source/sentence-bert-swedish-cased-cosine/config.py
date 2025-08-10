import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

# ------------Directories------------#
PDF_DIRECTORY = "pdf_data"
TOML_DIRECTORY_CLEANED = "questions/cleaned"
TOML_DIRECTORY_EMBEDDED = "questions/embedded"
RESULTS_DIRECTORY = "results"


# ----OpenAI and ChromaDB Configs----#
MAX_TOKENS = 256
OVERLAP = 50
BASE_NAME_VERSION = "sentence-bert-swedish-cased-cosine"

if OVERLAP > 0:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk_{OVERLAP}_Overlap"
else:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk"

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = f"docs_{VERSION_NAME}_collection"
PERSIST_DIRECTORY = f"docs_{VERSION_NAME}_storage"
EMBEDDING_MODEL_NAME = "KBLab/sentence-bert-swedish-cased"  # Changed embedding model name
# TOKEN_ENCODER = tiktoken.encoding_for_model(EMBEDDING_MODEL_NAME)


def get_client():
    return OpenAI(api_key=OPENAI_KEY)

def get_collection():
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

    #return chroma_client.get_or_create_collection(
    #    name=COLLECTION_NAME,
    #    embedding_function=sentence_transformer_ef,
    #    hnsw_config_overrides={
    #        "space": "cosine",
    #        "ef_construction": 200,
    #        "ef_search": 200,
    #        "max_neighbors": 32,
    #        "num_threads": 8
    #    }
    #)

    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef,
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
DISTANCE = 0.85
OUTPUT_DIRECTORY_RESULTS = f"{RESULTS_DIRECTORY}/{VERSION_NAME}/"


def get_results_filenames():
    base_dir = os.path.join(RESULTS_DIRECTORY, VERSION_NAME)
    os.makedirs(base_dir, exist_ok=True)
    if MULTIPROCESSING:
        RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME}_{TOLERANCE}_tol.csv")
        RESULTS_EXCEL_NAME = os.path.join(
            base_dir, f"{VERSION_NAME}_{TOLERANCE}_tol.xlsx"
        )
    else:
        RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.csv")
        RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.xlsx")

    return RESULTS_CSV_NAME, RESULTS_EXCEL_NAME
