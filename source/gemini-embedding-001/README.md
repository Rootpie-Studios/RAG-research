# PDF Q&A System with Gemini Embeddings

## Introduction

This code is based on the `BASELINE Code` and was created to Evaluate Gemini Embedding model on Swedish documents.

## 1. Project Workflow

The primary workflow is as follows:

1.  **Process and Embed Documents:** Ingests PDF files, chunks them into manageable pieces, and stores their vector embeddings in a ChromaDB database.
2.  **Embed Questions:** Processes a set of questions from TOML files and generates their corresponding embeddings.
3.  **Query and Retrieve:** For each question, it queries the document database to retrieve the most relevant text chunks.
4.  **Evaluate and Analyze:** Compares the retrieved results against a ground truth to calculate various performance metrics.
5.  **Visualize:** Generates a suite of plots to visually represent the system's performance.

---

## 2. System Architecture

The pipeline is orchestrated in the `main()` function and can be broken down into these main stages:

1. **Initialization:**
   Sets up the environment, including API keys, directory paths, and configurations for the embedding model and vector database.
2. **PDF Ingestion:**
   - Scans the `pdf_data` directory for PDF files.
   - Parses each PDF to extract text content.
   - Chunks the text into smaller segments.
   - Generates an embedding for each chunk using the Gemini `embedding-001` model.
   - Stores the chunks and their embeddings in a persistent ChromaDB collection.
3. **Question Ingestion:**
   - Reads questions from `.toml` files in the `questions/cleaned` directory.
   - Generates an embedding for each question.
   - Saves the questions along with their embeddings into new `.toml` files in the `questions/embedded` directory.
4. **Query Execution:**
   - Loads the embedded questions.
   - Queries the ChromaDB collection to find the top `k` most similar document chunks for each question based on cosine similarity.
   - This process can be run in parallel for efficiency.
5. **Results Evaluation & Visualization:**
   - The retrieved results are compared against the ground truth answers defined in the question files.
   - A detailed report is saved in CSV and Excel format in the `results` directory.
   - A comprehensive set of analytical plots is generated and saved in the `results` directory.

---

## 3. Key Components & Logic

### 3.1. Configuration (`CONFIG`)

The script is configured through a set of global variables at the beginning of the file. These control various aspects of the pipeline:

- **Directories:** Paths for input PDFs (`PDF_DIRECTORY`), cleaned questions (`TOML_DIRECTORY_CLEANED`), embedded questions (`TOML_DIRECTORY_EMBEDDED`), and output results (`RESULTS_DIRECTORY`).
- **Embedding & Chunking:**
  - `MAX_TOKENS`: The target maximum number of tokens for each text chunk. **Note:** This is an approximation based on word count, as the actual tokenization is handled internally by the Gemini API.
  - `OVERLAP`: The number of tokens from the end of one chunk to include at the beginning of the next. This helps maintain context across chunks.
  - `EMBEDDING_MODEL_NAME`: Specifies the Gemini model to use (`models/embedding-001`).
- **ChromaDB:**
  - `COLLECTION_NAME`: The name of the collection within ChromaDB.
  - `PERSIST_DIRECTORY`: The location where the vector database is stored on disk.
- **Query Evaluation:**
  - `MATCH_THRESHOLD`: A score threshold to determine if a retrieved text chunk is a valid match.
  - `RESULTS_PER_QUERY`: The number of results to retrieve for each question.
  - `DISTANCE`: A distance threshold used for calculating precision and recall.

### 3.2. PDF Processing & Embedding

This is a critical part of the RAG pipeline, handled by the `process_pdfs_and_insert` function.

#### Text Extraction and Normalization

- `parse_document`: Uses the `PyMuPDF` (fitz) library to open a PDF and extract text from each page, keeping track of the page number.
- `normalize_text`: Cleans the extracted text by removing hyphenated line breaks and extra whitespace, ensuring a more uniform text representation.

#### Text Chunking (`chunk_pdf_by_tokens`)

This function is responsible for splitting the document text into smaller, semantic chunks suitable for embedding.

- **Strategy:** The function iterates through the text word by word, building up a `current_chunk_text`.
- **Chunk Size:** It uses a simple word count (`len(...).split()`) as an approximation to stay under the `MAX_TOKENS` limit. While not a precise tokenizer, it's a fast and effective heuristic.
- **Overlap:** When a chunk reaches its maximum size, the next chunk is started with the last `OVERLAP` words from the previous one. This is achieved with `current_chunk_text.split()[-int(MAX_TOKENS * OVERLAP / MAX_TOKENS):]`. This overlap helps preserve the semantic context that might otherwise be lost at chunk boundaries.
- **Metadata:** Each chunk is stored with rich metadata, including the original `filename`, the `page_number`(s) it spans, its `chunk_index`, and the `total_chunks` for that document. This metadata is crucial for tracing retrieved chunks back to their source.

#### Embedding and Storage

- `embed_and_insert`: This function takes a text chunk, sends it to the Gemini API via `client.embed_content`, and receives a vector embedding.
- The chunk's text, its embedding, and its metadata are then "upserted" into the ChromaDB collection. `upsert` conveniently adds the entry if it's new or updates it if an entry with the same ID already exists.

### 3.3. Querying and Evaluation

- **Querying:** The `query_documents_all_embeddings` (and its parallel version) function iterates through each embedded question and uses the `collection.query` method. This method takes the question's embedding and finds the `n_results` most similar document embeddings based on the distance metric configured in ChromaDB (cosine similarity).
- **Evaluation Logic:** For each retrieved result, the script performs several checks:
  - `Filename_Match`: Is the source filename of the chunk correct?
  - `Page_Match`: Does the chunk's page range overlap with the expected answer's page range?
  - `Text_Match`: The `get_text_match_info` function checks how much of the expected answer text is present in the retrieved chunk. It does this by progressively shrinking the answer text from both the start and the end to find partial matches. This is robust against cases where the retrieved chunk only contains a portion of the answer.

---

## 4. Setup and Installation

### **Project Structure:**

```bash
.
├── pdf_data/        # Directory for input PDF files
├── questions/
│   ├── cleaned/     # Directory for TOML files with Q/A
├── results/         # Directory for output CSV, Excel, and plot files
└── main_gemini.py   # Main script to run the pipeline

```

### **Clone the repository:**

```bash
git clone https://github.com/Rootpie-Studios/RAG-research.git
cd RAG-research
```

### **Install the dependencies:**

```bash
uv sync
# bash
source venv/bin/activate
# On Windows
.venv\Scripts\activate
```

### **Setup:**

- Create a `.env` file in the root directory and add your Gemini API key:

  ```bash
  GEMINI_API_KEY="YOUR_API_KEY_HERE"
  ```

- Place your PDF documents into the `pdf_data` directory.
- Place your cleaned question TOML files into the `questions/cleaned` directory.

### **Execution:**

- Run the script from your terminal:

  ```bash
  python main_gemini.py
  # or using uv
  uv run main_gemini.py
  ```

- The script will print its progress through the different stages.

### **Outputs:**

- The final evaluation results will be in the `results/{VERSION_NAME}/` directory as CSV and Excel files.
- All generated plots will also be saved as PNG files in the same directory.

---

## 5. Dependencies

This script requires the following Python libraries:

- `python-dotenv`
- `chromadb`
- `google-generativeai`
- `tomlkit`
- `PyMuPDF`
- `pandas`
- `tomli`
- `python-levenshtein`
- `tqdm`
- `joblib`
- `matplotlib`
- `seaborn`
