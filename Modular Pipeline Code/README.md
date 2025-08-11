# Description
This is a modular python pipeline for RAG with ChromaDB vector database. There are 5 main files:

* `config.py` - This is where all settings are set.

* `parse_embedd_insert.py` - Run this to parse files, chunk up, embed, and insert into ChromaDB

* `embedd_toml_questions.py` - Adds a field with embeddings for all questions in TOML_DIRECTORY (`config.py`), and saves new files to TOML_DIRECTORY_EMBEDDED (`config.py`).

* `query_db_all_questions.py` - Run this to query the database with all saved questions, and save results.

* `save_stats_and_plots.ipynb` - Calculates and saves results, as well as plots.

# Dependencies
```python
pip install chromadb openai mistralai langchain pymupdf4llm tiktoken tomlkit tomli pandas matplotlib seaborn openpyxl tqdm joblib docling cohere transformers
```

# Usage
Clone repo, add pdf files and questions into respective directories. Read through `config.py`!
There is no 'main' file to run, start to finish. Instead, the config file decides all parameters, and you run the desired script, which will use config.py for importing settings.


# File structure description
packages/button
```
RAG
├── databases
│   └── This is where your databases will be created.
├── helping_scripts
│   └── Also contains extra scripts for Mistral usage, result table compiling and parser comparisons.
│   
├── pdf_data
│   └── This is where you store your PDF documents, for parsing and so on.
│   
├── md_data
│   └── This is where markdown pre-parsed documents will be created.
│   
├── questions
│   └── Your questions in toml format.
│   
├── results
│   └── Results folder, where file is created after query. Plots will also be saved here.
│   
├── config.py
│   └── This is where you choose your settings.
│   
├── embedd_toml_questions.py
│   └── Script for embedding questions and saving new toml files, with embeddings.
│   
├── parse_embedd_insert.py
│   └── Parses all files in PDF_DIRECTORY, chunks up and embedds documents, and insert them to ChromaDB
│   
├── pre_parse_pdf_save_md_files.py
│   └── Script pre-parsing files in PDF_DIRECTORY, results are saved in 'md_data'.
│   
├── query_db_all_questions.py
│   └── Queries database with embedded questions, which were created with embedd_toml_questions.py.
│   
└── save_stats_and_plots.ipynb
    └── Notebook for generating plots and calculating results.
```



# Overview
This section will give an overview to the modularity of the pipeline. 

#### Config
All settings are set in `config.py`. This is where embedding models, parsers, directories, boolean flags and input/output options can be set.

#### Parse
PyMuPDF and Docling can be used to parse PDF files as text, while PyMuPDF4llm and Docling can be used for markdown conversion. There is an option to pre-parse PDF files as markdown files (`parse_pdf_save_md_files.py`), so that it can be done in advance and used multiple times. 

#### Chunk
There are two chunking strategies available, both are token based. 

    1. Regular token split

    2. Recursive character split with added separators: 
        separators=["\n\n", "\n", ".", "?", "!", " ", ""].

#### Embedding Models
There are three ways to use embedding models. 

    1. API calls and loading clients from libraries such as OpenAI and Mistral

    2. Loading local models and using OpenAI's client to connect to a local server (LM Studio or smimlar).

    3. Loading local models with AutoTokenizer and AutoModel using the Transformers package.

#### Database
There is a choice between linear space and cosine space for the vector database.

#### Query
There are several settings to vary for querying and result retreival, such as:

* Match Thresholds
* Minimum answer length
* Nr of returned results
* Metadata filtering
* Distance filtering
* Reranking
* Generating LLM response


# config.py - Variables
Here we specify what the various settings do.

## API keys
Keys are saved in a `.env file`, and loaded here:
```python
#---------------------------------------#
#-----------------KEYS------------------#
#---------------------------------------#
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
COHERE_KEY = os.getenv("CHOHERE_API_KEY")
JINA_KEY = os.getenv("JINA_API_KEY")
```

## Directories
Directories are set here:
```python
#---------------------------------------#
#---------------Directories-------------#
#---------------------------------------#
PDF_DIRECTORY = "pdf_data"
TOML_DIRECTORY_CLEANED = "questions/cleaned"
TOML_DIRECTORY_EMBEDDED = "questions/embedded"
OUTPUT_DIRECTORY_COMPARE_SPLITS = "compare_splits_from_parser"
RESULTS_DIRECTORY = "results"
MD_DIRECTORY = "md_data" # If you choose to pre-prase md-files
LOCAL_BASE_URL = "http://192.168.8.3:1234/v1"
```

## Generall settings:
```python
#---------------------------------------#
#------------General Settings-----------#
#---------------------------------------#
BASE_NAME = "BASELINE"
USE_OPENAI = True
LOCAL_EMBEDDING_SERVER = False
ADD_LLM_CONTEXT = True
RERANK = False
RERANK_MODEL = "JINA_API"# "COHERE", "JINA_API" or "JINA_LOCAL"
COS = True
```


* `USE_OPENAI` controls which client and tokenizer is loaded, together with `LOCAL_EMBEDDING_SERVER`. 

* If `USE_OPENAI == true`, it uses OpenAI's client and tiktoken as tokenizer. 

* If `USE_OPENAI == false` it either uses the local client (if `LOCAL_EMBEDDING_SERVER == True`),
    or uses the Mistral client. In both cases it uses AutoTokenizer to load the tokenizer. 

* `LOCAL_EMBEDDING_SERVER == True`, also loads the local embedding model with AutoModel. 


* `ADD_LLM_CONTEXT` == True, Will use the generate_partial_context method from 
        `generate_llm_response.py` to generate some context for the current chunk. 
        It does this by adding current and previous page as context to a local LLM server,
        which is fed the system prompt (`SYS_PROMPT_FOR_CONTEXT`) to generate the desired context. 
        The context is prepended to the chunk before embedding and inserting to database.


* RERANK == True, Will use the rerank model specified with `RERANK_MODEL` to rerank the results at query. 
        The reranking methods are specified in `reranking.py`. 
        There are 3 choices for reranking: `"COHERE"`, `"JINA_API"` or `"JINA_LOCAL"`. 
        The first two require an API key.


* `COS`, Toggles the space type in the database.
If `COS == False`, linear space will be used.
If `COS == True`, cosine space will be used.

## Parsing
```python
#---------------------------------------#
#----------------Parsing----------------#
#---------------------------------------#
PARSE_AS_MD = True
USE_RECURSIVE_SPLIT = True
NORMALIZE_AT_PARSE = False
MAX_TOKENS = 2048
OVERLAP =  0
```

* It is suggested to pre-parse to markdown file with `pre_parse_pdf_save_md_files.py`, 
        if that is the desired parsing method. 

* After that, you can run `parse_embedd_insert.py` to parse all files in `PDF_DIRECTORY` 
        if normal text parsing is used, or `MD_DIRECTORY` if markdown is used.


* `PARSE_AS_MD = True`, Will use the pre-parsed markdown files in `MD_DIRECTORY` to embed and insert.


* `USE_RECURSIVE_SPLIT`, Toggles between chunking strategies: regular and recursive split,
    specified in `chunking.py`.

* `NORMALIZE_AT_PARSE`, Toggles usage of normalization at parse.
Normalizing methods are specified in `norm_funcs.py`.

* `MAX_TOKENS`, Sets max number of tokens.

* `OVERLAP`, Sets overlap, measured in tokens.


## Embeddings
```python
#---------------------------------------#
# --------------Embedding---------------#
#---------------------------------------#
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
# EMBEDDING_MODEL_NAME = "text-embedding-3-large"
# EMBEDDING_MODEL_NAME = "jinaai/jina-embeddings-v3"
...

if USE_OPENAI:
    TOKEN_ENCODER = tiktoken.encoding_for_model(EMBEDDING_MODEL_NAME)
else:
    if not LOCAL_EMBEDDING_SERVER:
        AUTOMODEL_CUSTOM = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME, trust_remote_code=True)
        AUTOMODEL_CUSTOM.eval()
    TOKEN_ENCODER = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
    
def get_client():
    if USE_OPENAI:
        return OpenAI(api_key=OPENAI_KEY)
    else:
        if LOCAL_EMBEDDING_SERVER:
            return OpenAI(base_url=LOCAL_BASE_URL, api_key="not-needed")
        else:
            return Mistral(api_key=MISTRAL_KEY)
```

* `EMBEDDING_MODEL_NAME` is used to specify which embedding model and tokenizer to load.

* `get_client()` returns the client, which depends on previously set booleans.

## File naming
For automatic naming of output files and directories. 
Helps user to not overwrite databases and other files, when settings are changed.
```python
#---------------------------------------#
#---Automatic naming of VERSION_NAME----#
#---------------------------------------#
NORM_NR = 1 if NORMALIZE_AT_PARSE else 0
BASE_NAME_VERSION = f"{BASE_NAME}_N{NORM_NR}"
if PARSE_AS_MD:
    BASE_NAME_VERSION = f"MD_{BASE_NAME_VERSION}"
if COS:
    BASE_NAME_VERSION = f"COS_{BASE_NAME_VERSION}"
    
if OVERLAP > 0:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk_{OVERLAP}_Overlap"
else:
    VERSION_NAME = f"{BASE_NAME_VERSION}_{MAX_TOKENS}_Chunk"
```

## ChromaDB
Uses the generated naming from above, for persistent database directory and collection.
```python
#---------------------------------------#
# -----------ChromaDB Configs-----------#
#---------------------------------------#    
COLLECTION_NAME = f"docs_{VERSION_NAME}_collection"
PERSIST_DIRECTORY = f"docs_{VERSION_NAME}_storage"

def get_collection():  
    chroma_client = chromadb.PersistentClient(path="databases/" + PERSIST_DIRECTORY)
    
    if COS:# If you do not want the standard distance function L2. This uses cosine instead.
        return chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            configuration={
                "hnsw": {
                    "space": "cosine", # Cohere models often use cosine space
                    "ef_search": 200,
                    "ef_construction": 200,
                    "max_neighbors": 32,
                    "num_threads": 8
                },
            }
        )
    else:
        return chroma_client.get_or_create_collection(
            name=COLLECTION_NAME
        )
```

* `get_collection()` will create, or return, the specified collection (`COLLECTION_NAME`).


## Results
Configurations for results. These are used at query, by `query_db_all_questions.py`.
```python
#---------------------------------------#
#-------------Results Configs-----------#
#---------------------------------------#
MATCH_THRESHOLD = 50
MIN_ANS_LENGTH = 3
RESULTS_PER_QUERY = 5
FILTER_BY_REG_NR = False # Only applies to kemi data
USE_LLM_ANSWERS = False
LLM_USED = "_MISTRAL" if USE_LLM_ANSWERS else "_No_LLM"


if COS:
    DISTANCE = 0.55
else:
    DISTANCE = 0.85
OUTPUT_DIRECTORY_RESULTS = f"{RESULTS_DIRECTORY}/{VERSION_NAME}/"

def get_results_filenames():
    base_dir = os.path.join(RESULTS_DIRECTORY, VERSION_NAME)
    os.makedirs(base_dir, exist_ok=True)
    RESULTS_CSV_NAME = os.path.join(base_dir, f"{VERSION_NAME + LLM_USED}_no_tol.csv")
    RESULTS_EXCEL_NAME = os.path.join(base_dir, f"{VERSION_NAME + LLM_USED}_no_tol.xlsx")

    return RESULTS_CSV_NAME, RESULTS_EXCEL_NAME

```

* `MATCH_THRESHOLD`, sets the threshold for what is considered a text match, in percent. The number is a sum and represents how much was kept of the shrinking answer to get a match. Since the text matching method checks for matches by shrinking the answer, once by shrinking the answer from the end, and a second time by shrinking the answer from the start of the answer string. The matches are summed up, meaning that the sum range is [0, 200%].

* `MIN_ANS_LENGTH`, sets the minimum number of characters for an answer to be considered, in the shrinking text matching method.

* `RESULTS_PER_QUERY`, sets the number of results to be returned by the database for each query.

* `FILTER_BY_REG_NR`, only relevant for the chemistry dataset. 
    It applies metadata filtering, by registration number, at query.

* `USE_LLM_ANSWERS`, toggles if local LLM is used to generate answers from the retrieved results, together with the query.

* `LLM_USED`, specifies which LLM was used. Only used for naming, is not used to load the actual LLM.

* `DISTANCE`, The filtering distance for returned results.

* `OUTPUT_DIRECTORY_RESULTS`, sets the path for the results
* `get_results_filenames()`, sets and gets the filenames for result files.

## System prompts for local LLMs
These prompts are used by local LLM in generate_llm_response.py.
```python
#---------------------------------------#
#------------------LLM------------------#
#---------------------------------------#
SYS_PROMPT_FOR_CONTEXT = """
Två texter tillhandahålls: en längre text (originaldokumentet) och ett kortare utdrag som förekommer i den längre texten. 
Kontexten till utdraget ska beskrivas så specifikt och kortfattat som möjligt, utan att nämna uppgiften. 
Fokusera endast på vad utdraget handlar om och dess direkta omgivning. Undvik allmän beskrivning av dokumentet. 
Svaret ska vara på svenska, bestå av högst 200 tecken och innehålla endast en sammanhängande mening eller två. 
Inga rubriker, metainformation eller hänvisningar till uppgiften får förekomma i svaret.
"""

SYS_PROMPT_FOR_OUTPUT = """
Använd endast det angivna kontextet för att besvara frågan. Lägg inte till information. 
Om du inte kan svaret på frågan i kontextet, säg att du inte vet svaret. 
Det första stycket i kontextet har störst chans att innehålla svaret. 
Var kort och koncis och svara alltid på svenska.
"""
```

* `SYS_PROMPT_FOR_CONTEXT`, is used when generating context for chunk.

* `SYS_PROMPT_FOR_OUTPUT`, is used when generating answer from returned chunks.

## Automodel Pooling method
Pooling method for AutoModel, check huggingface to ensure correct method is used for specific model.
```python
#---------------------------------------#
#-----------AUTOMODEL POOLING-----------#
#---------------------------------------#
def pooling_setup(texts):
    if isinstance(texts, str):
        texts = [texts]
    inputs = TOKEN_ENCODER(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
    with torch.no_grad():
        outputs = AUTOMODEL_CUSTOM(**inputs)
        last_hidden_state = outputs.last_hidden_state

        # Mean Pooling
        attention_mask = inputs['attention_mask']
        mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        pooled = torch.sum(last_hidden_state * mask_expanded, 1) / torch.clamp(mask_expanded.sum(1), min=1e-9)

    embeddings = pooled.cpu().tolist()  # Convert to list-of-lists for ChromaDB
    return embeddings
```


