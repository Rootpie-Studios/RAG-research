import os
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions

# Import Mistral client
from mistralai import Mistral 

load_dotenv()

# ------------Directories------------#
PDF_DIRECTORY = "pdf_data"
TOML_DIRECTORY_CLEANED = "questions/cleaned"
TOML_DIRECTORY_EMBEDDED = "questions/embedded"
RESULTS_DIRECTORY = "results"


# ----OpenAI and ChromaDB Configs----#
MAX_TOKENS = 65
OVERLAP = 0
BASE_NAME_VERSION = "BASELINE"

if OVERLAP > 0:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk_{OVERLAP}_Overlap"
else:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk"
    
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY") # Get Mistral API key

COLLECTION_NAME = f"docs_{VERSION_NAME}_collection"
PERSIST_DIRECTORY = f"docs_{VERSION_NAME}_storage"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
TOKEN_ENCODER = tiktoken.encoding_for_model(EMBEDDING_MODEL_NAME)


def get_openai_client(): # Renamed for clarity
    return OpenAI(api_key=OPENAI_KEY)

def get_mistral_client(): # New function to get Mistral client
    if not MISTRAL_KEY:
        raise ValueError("MISTRAL_API_KEY not found in environment variables.")
    return Mistral(api_key=MISTRAL_KEY)

def get_collection():
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_KEY, 
        model_name=EMBEDDING_MODEL_NAME
    )
    chroma_client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=openai_ef
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
        RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME}_{TOLERANCE}_tol.xlsx")
    else:
        RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.csv")
        RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME}_no_tol.xlsx")

    return RESULTS_CSV_NAME, RESULTS_EXCEL_NAME