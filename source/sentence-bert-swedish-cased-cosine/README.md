# RAG Evaluation Pipeline

This project is a comprehensive pipeline for evaluating the performance of a Retrieval-Augmented Generation (RAG) system when it comes to Swedish text. It provides tools to parse and embed PDF documents, query them with a predefined set of questions, and analyze the results to gauge the effectiveness of the retrieval component. This code is based on the BASELINE Code and was created to Evaluate the sentence-bert-swedish-cased embedding model that was trained on Swedish data.

## Features

- **PDF Parsing and Chunking:** Ingests PDF documents, extracts text, and splits them into configurable chunks.
- **Vector Embeddings:** Utilizes a Swedish Sentence-BERT model to generate embeddings for document chunks and questions. This code was writen to explicitly test sentence-bert-swedish-cased and see how it perform on embedding Swedish text.
- **Vector Database Storage:** Stores document chunks and their embeddings in a ChromaDB vector database.
- **Automated Evaluation:** Queries the database with questions from TOML files and compares the retrieved results against ground-truth answers.
- **Batch Processing:** Allows for running experiments with different chunking configurations (`MAX_TOKENS`, `OVERLAP`) in an automated fashion.
- **Interactive Mode:** An interactive CLI for running individual steps of the pipeline and modifying configurations on the fly.
- **Rich Result Analysis:** Generates detailed CSV and Excel reports with various metrics, including:
  - Filename and page number matching.
  - Text similarity scores (using Levenshtein distance).
  - Precision, recall, and accuracy metrics.
- **Data Visualization:** Creates a variety of plots to visualize the evaluation results, helping to understand performance by category, result ranking, and more.

## Project Structure

```
.
├── pdf_data/              # Directory for input PDF files
├── questions/
│   ├── cleaned/           # Directory for TOML files with questions and answers
├── results/               # Directory for output CSV, Excel, and plot files
├── batch_run.py           # Script for automated batch processing of different configs
├── config.py              # Central configuration file for the project
├── embedd_toml_questions.py # Script to pre-embed questions from TOML files (NOT USED)
├── main.py                # Main interactive script to run the pipeline
├── parse_embedd_into_db.py  # Script to parse PDFs and store them in the database
├── query_db_all_questions.py # Script to query the database and evaluate results
└── save_plots.py            # Script to generate plots from the evaluation results
```

## Setup and Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Rootpie-Studios/RAG-research.git
   cd RAG-research
   ```

2. **Create a virtual environment:**

   (skip if you use uv, see below)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Using uv ?**

   ```bash
   uv sync
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

5. **Set up your environment variables:**
   Create a `.env` file in the root of the project and add your OpenAI API key:

   ```bash
   OPENAI_API_KEY="your-openai-api-key"
   ```

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

### Pipeline Steps

1. **`parse_embedd_into_db.py`**: This script will process the PDFs in the `pdf_data` directory, chunk them according to the settings in `config.py`, and save them to the ChromaDB database.
2. **`embedd_toml_questions.py`**: This script processes the TOML files in the `questions/cleaned` directory and was intended to pre-calculate and store question embeddings. (Note: The current implementation generates embeddings at query time).
3. **`query_db_all_questions.py`**: This script takes the questions from the TOML files, queries the database, and generates a CSV and Excel file with the detailed results.
4. **`save_plots.py`**: This script reads the results from the CSV file and generates a series of plots to help visualize the performance of the RAG system.
