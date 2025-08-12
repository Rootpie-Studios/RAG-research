# RAG System with Sentence Transformers and ChromaDB

## Introduction

This code is based on the `BASELINE Code` and was created to Evaluate the embedding model: `KBLab/sentence-bert-swedish-cased` that was trained on Swedish text and The Natural Language Toolkit (`nltk`) is used for sentence tokenization.

## Project Workflow

The project follows a sequential workflow, managed by a series of Python scripts:

1.  **Configuration**: All key parameters, such as model names, file paths, and chunking settings, are centralized in `config.py`.
2.  **Data Ingestion & Embedding**: The `parse_embedd_into_db.py` script reads PDF files from the `pdf_data` directory. It extracts text, splits it into manageable chunks based on sentences, and uses the configured sentence-transformer model to generate vector embeddings for each chunk. These embeddings and their corresponding text/metadata are then stored (upserted) into a persistent ChromaDB database.
3.  **Question Embedding (Optional)**: The `embedd_toml_questions.py` script was designed to pre-embed questions from `.toml` files. However, in the current workflow, embeddings are generated on-the-fly at query time to ensure consistency with the database's embedding function.
4.  **Querying & Evaluation**: `query_db_all_questions.py` reads questions from `.toml` files in the `questions/cleaned` directory. For each question, it queries the ChromaDB to retrieve the most relevant text chunks (documents). It then compares the retrieved results against the ground-truth answers defined in the TOML files, evaluating performance based on filename, page number, and text content matching.
5.  **Result Analysis & Visualization**: After the evaluation, `save_plots.py` reads the detailed results from the generated CSV file and creates a suite of plots (e.g., accuracy, precision/recall, heatmaps) to visualize the system's performance. These plots are saved in the `results/` directory.
6.  **Batch Processing**: The `batch_run.py` script facilitates automated experimentation by allowing you to run the entire workflow with different configurations (e.g., varying chunk sizes and overlaps) in a single command.

## System Architecture

The system is composed of several interconnected components:

- **Data Source**: A directory of PDF files (`pdf_data/`) and a directory of TOML files containing questions and answers (`questions/cleaned/`).
- **Processing Engine**: A set of Python scripts that orchestrate the entire pipeline.
- **Text Processor (NLTK)**: The Natural Language Toolkit (`nltk`) is used for sentence tokenization, which forms the basis of the text chunking strategy.
- **Embedding Model (Sentence-Transformers)**: A pre-trained language model (`KBLab/sentence-bert-swedish-cased`) that converts text chunks and questions into high-dimensional vectors (embeddings).
- **Vector Database (ChromaDB)**: A persistent, local vector database that stores the text chunks, their embeddings, and associated metadata (like source filename and page number). It performs efficient similarity searches to find relevant chunks.
- **Evaluation & Reporting**: The system uses `pandas` for data manipulation and `matplotlib`/`seaborn` to generate reports and visualizations that quantify the retrieval accuracy.

## Key Components & Logic

### Embeddings Model

The core of the retrieval system is the sentence-embedding model. This project uses `KBLab/sentence-bert-swedish-cased`, a Sentence-BERT model specifically trained for the Swedish language.

- **How it Works**: Instead of just looking at keywords, Sentence-BERT is trained to understand the meaning of a whole sentence. It maps a variable-length sentence to a fixed-size, dense vector in a high-dimensional space. Sentences with similar meanings are mapped to nearby points in this vector space.
- **Integration**: The model is seamlessly integrated via ChromaDB's `SentenceTransformerEmbeddingFunction`. When a text chunk is inserted into the database, this function automatically converts the text into a vector embedding. Likewise, when a query is made, the question text is converted into a vector using the _same_ model, allowing for a meaningful "apples-to-apples" comparison in the vector space. The database then finds the text chunk vectors that are closest (by cosine similarity or L2 distance) to the question vector.

### Text Chunking with NLTK

Effective retrieval heavily depends on how the source documents are broken down into chunks. If chunks are too large, the specific answer might be diluted by irrelevant context. If they are too small, the context needed to understand the answer might be lost.

This project employs a sentence-based chunking strategy using `nltk.tokenize.sent_tokenize`:

1.  **Sentence Tokenization**: In `parse_embedd_into_db.py`, the text from each page of a PDF is first tokenized into a list of individual sentences using `sent_tokenize`. This is generally more robust than splitting by a simple character like a period, as `nltk` can handle abbreviations and other linguistic nuances.
2.  **Grouping into Chunks**: The script then groups these sentences into chunks. The `MAX_TOKENS` variable in `config.py` defines how many sentences constitute a single chunk.
3.  **Overlapping Chunks**: To avoid losing context at the edges of a chunk, an overlap can be configured with the `OVERLAP` variable. For example, if `MAX_TOKENS` is 8 and `OVERLAP` is 2, the first chunk will contain sentences 1-8, the second will contain sentences 7-16 (overlapping by 2 sentences), the third 15-22, and so on. This ensures that a single idea or answer that spans a chunk boundary can still be found intact in a subsequent chunk.

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Rootpie-Studios/RAG-research.git
    cd RAG-research
    ```

2.  **Create a virtual environment:**

    ```bash
    uv sync
    # bash
    source venv/bin/activate
    # On Windows, use
    .venv\Scripts\activate
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your OpenAI API key if you plan to use OpenAI models. For the current setup, this is not strictly necessary as the embedding model is local.

    ```
    OPENAI_API_KEY="your_key_here"
    ```

4.  **Place your data:**
    - Place your PDF documents in the `pdf_data/` directory.
    - Place your question/answer `.toml` files in the `questions/cleaned/` directory.

## Usage

### Interactive Mode

The easiest way to get started is to use the interactive `main.py` script.

```bash
python main.py
```

This will present you with a menu to run the different parts of the pipeline. You can also change configuration variables like `MAX_TOKENS`, `OVERLAP` and `BASE_NAME_VERSION` before running the scripts.

### Batch Mode

For running multiple experiments with different configurations, you can use the `batch_run.py` script.

```bash
python batch_run.py --base_name=MyExperiment --tokens=256/50,512/100
```

This will run the entire pipeline twice, once with `MAX_TOKENS=256` and `OVERLAP=50`, and a second time with `MAX_TOKENS=512` and `OVERLAP=100`. The results will be saved in separate directories under the `results/` folder.

## Project Structure

```
.
├── pdf_data/                  # Directory for input PDF documents.
├── questions/
│   ├── cleaned/               # Directory for TOML files with questions and answers.
│   └── embedded/              # Directory for TOML files with pre-computed embeddings.
├── results/                   # Directory for output CSV/Excel reports and plots.
├── config.py                  # Central configuration for models, paths, and parameters.
├── parse_embedd_into_db.py    # Parses, chunks, and embeds PDFs into ChromaDB.
├── embedd_toml_questions.py   # (Optional) Embeds questions from TOML files.
├── query_db_all_questions.py  # Queries the DB with questions and evaluates results.
├── save_plots.py              # Generates and saves plots from the evaluation results.
├── main.py                    # Interactive menu to run individual scripts.
├── batch_run.py               # Script to run experiments with multiple configurations.
└── README.md                  # This file.
```
