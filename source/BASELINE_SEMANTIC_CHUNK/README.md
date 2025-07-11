-----



# PDF Q&A System with Semantic Search



This project implements a system for question-answering over PDF documents using semantic search. It leverages OpenAI embeddings, ChromaDB for vector storage, and LangChain's `SemanticChunker` for intelligent document parsing. The system processes PDF documents, embeds questions, queries the document store, and evaluates the results, providing detailed metrics and visualizations.



-----



## Features



&nbsp; * **PDF Parsing and Semantic Chunking**: Automatically extracts text from PDFs and intelligently breaks it down into meaningful chunks using LangChain's `SemanticChunker` for improved search relevance.

&nbsp; * **OpenAI Embeddings**: Converts both PDF chunks and questions into high-dimensional vectors using OpenAI's embedding models.

&nbsp; * **ChromaDB Vector Store**: Persistently stores and manages document embeddings, enabling efficient semantic similarity searches.

&nbsp; * **TOML-based Question Management**: Reads and embeds questions defined in TOML files, allowing for structured evaluation datasets.

&nbsp; * **Flexible Querying**: Supports querying the document store with embedded questions and retrieves relevant document chunks.

&nbsp; * **Result Analysis and Evaluation**:

&nbsp;     * Compares retrieved chunks against expected answers, evaluating filename and page number matches.

&nbsp;     * Calculates text similarity using Levenshtein distance and ratio, with an optional tolerance for inexact matches.

&nbsp;     * Generates comprehensive CSV and Excel reports of query results.

&nbsp; * **Extensive Visualization**: Produces a variety of plots (e.g., match vs. page, accuracy, precision, recall, heatmaps) to visualize system performance and insights.

&nbsp; * **Parallel Processing**: Utilizes multi-threading and multi-processing for faster embedding and querying of data.



-----



## Getting Started



Follow these instructions to set up and run the project.



### Prerequisites



Before you begin, ensure you have the following installed:



&nbsp; * Python 3.8+

&nbsp; * `pip` (Python package installer)



### Installation



1.  **Clone the repository:**



&nbsp;   ```bash

&nbsp;   git clone https://github.com/Rootpie-Studios/RAG-research.git>

&nbsp;   cd RAG-research

&nbsp;   ```



2.  **Create a virtual environment (recommended):**



&nbsp;   ```bash

&nbsp;   python -m venv venv

&nbsp;   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

&nbsp;   ```



3.  **Install the required Python packages:**



&nbsp;   ```bash

&nbsp;   pip install -r requirements.txt

&nbsp;   ```



&nbsp;   (Note: You will need to create a `requirements.txt` file based on the `import` statements in the provided code. A suggested `requirements.txt` is provided below.)



4.  **Set up OpenAI API Key:**

&nbsp;   Create a `.env` file in the project's root directory and add your OpenAI API key:



&nbsp;   ```

&nbsp;   OPENAI_API_KEY="your_openai_api_key_here"

&nbsp;   ```



### Project Structure



Organize your project directory as follows:



```

.

├── .env

├── pdf_data/

│   ├── document1.pdf

│   └── document2.pdf

├── questions/

│   ├── cleaned/

│   │   ├── questions1.toml

│   │   └── questions2.toml

│   └── embedded/  (Generated after running the script)

├── results/       (Generated after running the script)

│   └── BASELINE_SEMANTIC_CHUNK/

│       ├── BASELINE_SEMANTIC_CHUNK_no_tol.csv

│       ├── BASELINE_SEMANTIC_CHUNK_no_tol.xlsx

│       └── plots/

└── main_langchain_semantic.py

└── requirements.txt

```



&nbsp; * **`pdf_data/`**: Place your PDF documents here.

&nbsp; * **`questions/cleaned/`**: Store your TOML files containing "cleaned" questions.

&nbsp; * **`questions/embedded/`**: This directory will be created automatically, and embedded questions will be saved here.

&nbsp; * **`results/`**: This directory will store the CSV/Excel results and generated plots.



-----



## Usage



To run the full Q&A pipeline, execute the `main_langchain_semantic.py` script:



```bash

python main_langchain_semantic.py

```



The script will perform the following steps:



1.  **Parse, Chunk, Embed PDFs, and Insert into DB**: Reads PDFs from `pdf_data/`, chunks them semantically, embeds the chunks, and stores them in ChromaDB. A persistent ChromaDB collection will be created in the `docs_{VERSION_NAME}_storage` directory.

2.  **Embed TOML Questions**: Reads questions from `questions/cleaned/`, embeds them, and saves the embedded questions to `questions/embedded/`.

3.  **Query DB with Embedded Questions**: Queries the ChromaDB with the embedded questions and generates a detailed results report in CSV and Excel formats within the `results/{VERSION_NAME}/` directory.

4.  **Generate and Save Plots**: Creates various analytical plots based on the query results, saving them to a `plots/` subdirectory within `results/{VERSION_NAME}/`.



-----



## Configuration



Key configurations can be adjusted within the `main_langchain_semantic.py` file under the `CONFIG` section:



&nbsp; * **`PDF_DIRECTORY`**: Path to the directory containing your PDF files.

&nbsp; * **`TOML_DIRECTORY_CLEANED`**: Path to the directory where your cleaned TOML question files are stored.

&nbsp; * **`TOML_DIRECTORY_EMBEDDED`**: Path where the embedded TOML question files will be saved.

&nbsp; * **`RESULTS_DIRECTORY`**: Base directory for storing all results (CSV, Excel, plots).

&nbsp; * **`BASE_NAME_VERSION`**: A base name for versioning your results and ChromaDB collection (e.g., `BASELINE_SEMANTIC_CHUNK`). This affects directory and file names.

&nbsp; * **`OPENAI_KEY`**: Your OpenAI API key (loaded from `.env`).

&nbsp; * **`COLLECTION_NAME`**: The name of the ChromaDB collection (derived from `VERSION_NAME`).

&nbsp; * **`PERSIST_DIRECTORY`**: The directory where ChromaDB will store its data persistently (derived from `VERSION_NAME`).

&nbsp; * **`EMBEDDING_MODEL_NAME`**: The OpenAI embedding model to use (default: `text-embedding-3-small`).

&nbsp; * **`MATCH_THRESHOLD`**: A combined percentage threshold for text matches from the start and end of the answer to consider a "match."

&nbsp; * **`MIN_ANS_LENGTH`**: Minimum length of an answer substring to be considered for matching.

&nbsp; * **`RESULTS_PER_QUERY`**: The number of top-k results to retrieve from ChromaDB for each question.

&nbsp; * **`TOLERANCE`**: Levenshtein distance tolerance for fuzzy text matching. Set to `0` for exact matches.

&nbsp; * **`MULTIPROCESSING`**: Set to `True` to enable parallel processing for querying when `TOLERANCE > 0`.



-----



## Understanding the Results



The generated CSV and Excel files will contain detailed information for each query, including:



&nbsp; * **`Result_Id`**: Unique identifier for each retrieved result.

&nbsp; * **`Correct_File`**: The expected PDF filename containing the answer.

&nbsp; * **`Guessed_File`**: The filename of the PDF chunk retrieved by the system.

&nbsp; * **`Filename_Match`**: Boolean indicating if `Correct_File` matches `Guessed_File`.

&nbsp; * **`Correct_Pages`**: The expected page numbers containing the answer.

&nbsp; * **`Guessed_Page`**: The page number(s) of the retrieved chunk.

&nbsp; * **`Page_Match`**: Boolean indicating if any `Correct_Pages` matches `Guessed_Page` (and `Filename_Match` is true).

&nbsp; * **`Distance`**: Semantic distance from the query embedding to the chunk embedding.

&nbsp; * **`Text_Match_Start_Percent`**: Percentage of the expected answer matched from the start of the retrieved chunk.

&nbsp; * **`Match_Length_Start`**: Length of the matched substring from the start.

&nbsp; * **`Text_Match_End_Percent`**: Percentage of the expected answer matched from the end of the retrieved chunk.

&nbsp; * **`Match_Length_End`**: Length of the matched substring from the end.

&nbsp; * **`No_match`**: Boolean indicating if no text match was found.

&nbsp; * **`Match_Threshold`**: Boolean indicating if the combined `Text_Match_Start_Percent` and `Text_Match_End_Percent` exceeds `MATCH_THRESHOLD`.

&nbsp; * **`Difficulty`**: Difficulty level of the question (from TOML).

&nbsp; * **`Category`**: Category of the question (from TOML).

&nbsp; * **`Expected_answer`**: The answer as provided in the TOML file.

&nbsp; * **`Question`**: The original question.

&nbsp; * **`Returned_Chunk`**: The actual text content of the retrieved chunk.

&nbsp; * **`Chunk_Id`**: The unique ID of the retrieved chunk.



The plots provide visual summaries of the system's performance, including:



&nbsp; * Accuracy, precision, and recall based on file, page, and chunk matches.

&nbsp; * Distribution of text match percentages.

&nbsp; * Heatmaps illustrating various match types.

&nbsp; * Accuracy broken down by question category.



