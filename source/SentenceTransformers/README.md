# BASELINE with SentenceTransformers

## Overview

Code was updated from BASELINE to use SentenceTransformers, more notably "all-MiniLM-L6-v2".
Also added OVERLAP functionality.

For more info, See [RAG Pipeline](#rag-pipeline-pdf-processing-and-query-evaluation)

### How to Install

```bash
pip install -U chromadb openai pymupdf4llm tiktoken tomlkit tomli pandas matplotlib seaborn openpyxl levenshtein tqdm joblib sentence-transformers
```

If you use UV then just do

```bash
uv sync
.\.venv\Scripts\activate.ps1
uv pip install sentence-transformers
```

### Files

Put your Questions toml files in "questions/cleaned" and your PDFs in "pdf_data".
<br><br>

# RAG Pipeline: PDF Processing and Query Evaluation

## High-Level Summary

This Python script implements a Retrieval-Augmented Generation (RAG) pipeline focused on information retrieval and evaluation, rather than text generation. Its primary function is to process a collection of PDF documents, extract their text content, and store them as indexed, searchable chunks (characters) in a vector database. It then systematically evaluates the retrieval quality by querying the database with a predefined set of questions from TOML files and comparing the retrieved text chunks against ground-truth answers. The final output is a detailed CSV and Excel report containing performance metrics for each query.

## Execution Flow Analysis

The script executes in a sequential manner, following these main phases:

1.  **Configuration:** Sets up global constants, including directory paths (`PDF_DIRECTORY`, `TOML_DIRECTORY`), vector store parameters (`COLLECTION_NAME`, `PERSIST_DIRECTORY`), and RAG model settings (`EMBEDDING_MODEL_NAME`, `MAX_TOKENS`, `CHUNK_OVERLAP`).

2.  **Initialization:** A persistent ChromaDB client is initialized, pointing to the `PERSIST_DIRECTORY`. A collection is created or loaded, configured with the `SentenceTransformerEmbeddingFunction` which will handle text embedding automatically.

3.  **PDF Processing and Ingestion:**

    - The main function `process_pdfs_and_insert` is called, which iterates through all PDF files in the `PDF_DIRECTORY`.
    - For each PDF, `chunk_pdf_by_tokens` is invoked. This function first calls `parse_document` to extract raw text from each page using the `fitz` library.
    - The extracted text is then chunked. The script splits the text into characters and reconstructs chunks up to a maximum character length (`MAX_TOKENS`), with a specified character overlap (`CHUNK_OVERLAP`) between consecutive chunks.
    - Each chunk, along with its metadata (source filename, page number), is "upserted" into the ChromaDB collection. The embedding function automatically converts the text chunk into a vector embedding upon insertion.

4.  **Question Loading:**

    - The `get_embedded_questions` function reads and parses all `.toml` files from the `TOML_DIRECTORY`. These files contain the evaluation dataset, including a question ID, the question text, the expected answer, and metadata about the source document.

5.  **Querying and Evaluation:**

    - The `query_documents_all_embeddings` function iterates through every loaded question.
    - For each question, it sends the text to ChromaDB, which embeds the query and performs a similarity search, returning the top `n_results` most relevant text chunks.
    - The script then evaluates each returned chunk by comparing its filename and page number against the ground-truth data from the TOML file.
    - It performs a detailed text match analysis using the `check_shrinking_matches` function, which leverages the Levenshtein distance to see how much of the expected answer is present in the retrieved chunk.
    - A comprehensive record for each result, including match success, distance scores, and other metadata, is compiled.

6.  **Reporting:**
    - All evaluation records are collected into a pandas DataFrame.
    - The DataFrame is saved to both a CSV file (`RESULTS_CSV_NAME`) and an Excel file (`RESULTS_EXCEL_NAME`) for further analysis.

## RAG Component Breakdown

#### Data Loading and Processing

- **Data Source**: Data is loaded from local PDF files located in the `./pdf_data` directory. The evaluation questions and answers are loaded from `.toml` files in the `questions/cleaned` directory.
- **Chunking Strategy**: The script uses a custom character-based chunking strategy implemented in `chunk_pdf_by_tokens`.
  - **Chunk Size**: `MAX_TOKENS = 512` characters. This size is chosen to be large enough to contain meaningful context but small enough to be a focused target for the embedding model.
  - **Chunk Overlap**: `CHUNK_OVERLAP = 150` characters. This overlap ensures that context is not lost at the boundaries between chunks. A sentence or concept that starts at the end of one chunk will be fully included in the next, improving the chances of a successful retrieval.

#### Embedding Models

- **Embedding Model**: The script uses `all-MiniLM-L12-v2`, a model from the `sentence-transformers` library. This is a compact but powerful model designed to create semantically meaningful embeddings for sentences and short paragraphs.
- **Purpose**: The model's role is to convert both the text chunks from the PDFs and the text of the input questions into high-dimensional numerical vectors. The similarity between these vectors corresponds to their semantic similarity, which is the basis for the retrieval process.

#### Vector Store/Database

- **Vector Store**: The script utilizes `ChromaDB`, a popular open-source vector database.
- **Role**: ChromaDB stores the vector embeddings of all text chunks along with their associated text and metadata. It provides the core functionality of the RAG pipeline: indexing the vectors for fast and efficient similarity search. When a query is received, ChromaDB finds the chunks whose embeddings are closest to the query's embedding in the vector space.

#### Retrieval and Generation

- **Retrieval Process**: A query (question text) is embedded using the same `all-MiniLM-L12-v2` model. ChromaDB then performs a k-nearest neighbor (k-NN) search to find the `n_results` vectors in its index that are most similar to the query vector. The corresponding text chunks are returned as the search results.
- **Language Model (LLM)**: This script **does not use an LLM for generation**. It is purely a retrieval and evaluation system. Instead of feeding the retrieved chunks to an LLM to generate an answer, it compares the retrieved chunks directly to a pre-existing "correct answer" from the TOML files to measure the performance of the retrieval step itself.
- **Final Output**: The final output is not a generated text answer but a structured report in CSV and Excel formats, detailing the performance of the retrieval for each test query.

## External APIs and Libraries

- **External APIs**: No external network APIs (like OpenAI or Hugging Face Hub) are directly called. The `sentence-transformers` library handles the download and local caching of the embedding model.
- **Key Libraries**:
  - `fitz` (PyMuPDF): Used for robustly extracting text content from PDF files.
  - `chromadb`: The core vector store for storing, indexing, and querying text embeddings.
  - `sentence-transformers` (via `chromadb`): Provides the text embedding model (`all-MiniLM-L12-v2`).
  - `tomli`: A fast and efficient library for parsing the `.toml` files that contain the questions and answers.
  - `pandas`: Used to structure the evaluation results into a DataFrame and export them to CSV and Excel formats.
  - `Levenshtein`: Used to calculate the string distance (edit distance) between the expected answer and the retrieved text, providing a quantitative measure of text match quality.
  - `rich`: For printing color-coded and formatted text to the console, improving readability of script output.
