# **Iterative Optimization - Parser, Chunking & Tokenizers**

**Goal:** Improve chunk quality and relevance through advanced parsing and chunking strategies.

**Tasks for Each Iteration:**

1.  **Experiment with Different Parsers:**
    * **Task:** Try parsers specifically designed for your document types.
    * **Examples to Try:**
        * **`Unstructured.io`:** Excellent for extracting structured content from diverse formats (PDFs, images, HTML, PPTX, etc.). Can identify titles, tables, list items, etc.
        * **`PyMuPDF` (for PDFs):** More robust PDF parsing than basic options, allows for better text extraction and layout understanding.
        * **`LlamaParse` (LlamaIndex):** Specifically designed for complex PDF parsing, can extract tables and structured data.
        * **`Mistral OCR`**
        * **Custom Parsers:** If your data has a unique, predictable structure.
    * **Evaluation:** Re-run queries and re-evaluate retrieved chunks for improved completeness and coherence.

2.  **Experiment with `chunk_size` and `chunk_overlap`:**
    * **Task:** Systematically vary `chunk_size` (e.g., 256, 382, 512 characters) and `chunk_overlap` (e.g., 0, 50, 100, 150 characters).
    * Experiment with Chunking paragraphs or chapters etc.
    * **Reasoning:**
        * **Smaller chunks:** Can be more precise, but might lose context.
        * **Larger chunks:** More context, but can dilute the main topic and introduce noise.
        * **Overlap:** Helps maintain context across chunk boundaries. Can also
        be used to select neiboring chunks if part of the text is in a boundary.
    * **Evaluation:** Observe the trade-offs in relevance and completeness of retrieved chunks.

3.  **Tokenizers vs. Character Chunks:**
    * **Task:** Compare character-based chunking with tokenizer-aware chunking.
    * **Reasoning:** Embedding models operate on tokens. Chunking based on tokens can ensure that chunks don't cut off words or important semantic units in the middle.
    * **Implementation:**
        * **Tokenizer-Aware Chunks:** Use a tokenizer (e.g., from `transformers` library, matching your embedding model's tokenizer) to split text into chunks based on token count. This ensures chunks align with how the model "sees" the text.
    * **Evaluation:** Does token-aware chunking lead to more semantically coherent chunks and better retrieval?
		* Did we improve beyond baseline ? 
		* Total improvement ?

4.  **Semantic/Contextual Chunking:**
    * **Task:** Implement more advanced chunking strategies that respect semantic boundaries.
    * **Examples to Try:**
        * **Recursive Character Text Splitter (Langchain/LlamaIndex):** Tries to split by paragraphs, then sentences, then words, preserving semantic units where possible.
        * **Sentence Splitter:** Ensures each chunk is a complete sentence or a few sentences.
        * **NLTK/SpaCy:** Can be used for more sophisticated sentence boundary detection.
        * **Custom Logic:** Based on headings, sections, or other structural elements identified by your parser.
    * **Evaluation:** Are the retrieved chunks more meaningful and less fragmented?
		* Did we improve beyond baseline ? 
		* Total improvement ?
---

# **Iterative Optimization - Embedding Models & Vector Databases**

**Goal:** Enhance retrieval accuracy and efficiency through better embeddings and optimized storage.

**Tasks for Each Iteration:**

1.  **Experiment with Different Embedding Models:**
    * **Task:** Systematically try a range of embedding models.
    * **Example Options to Try (progressing in size/performance):**
        * **`all-MiniLM-L12-v2` (Sentence-Transformers):** Larger version of MiniLM.
        * **`bge-base-en-v1.5` (BAAI):** Base version, generally stronger.
        * **`e5-base-v2` (Microsoft):** Base version.
        * **`GTE-base` (Alibaba):** Good general-purpose model.
        * **`text-embedding-ada-002` (OpenAI):** If you are considering commercial options, this is a very strong baseline.
        * **`sentence-bert-swedish-cased`:** swedish model.
        * **Instruction-Tuned Embeddings:** Models designed for specific tasks (e.g., query-document similarity).
    * **Considerations:** Model size, inference speed, performance on your specific data.
    * **Evaluation:**
    	* See result vs baseline (eg baseline embedder)
		* Did they improve ? 
		* Did we improve beyond baseline ? 
		* Total improvement ?

2.  **Experiment with Different Vector Databases:**
    * **Task:** Explore different vector databases for their features, scalability, and performance.
    * **Example Options to Try:**
        * **`FAISS` (Facebook AI Similarity Search):** fast local testing.
        * **`Chroma` (client-server mode or persistent):** More features, good for small to medium scale.
        * **`Qdrant`:** Production-ready, robust features, good for filtering.
        * **`Weaviate`:** Graph-based semantic search, powerful filtering and multi-modal.
        * **`Milvus/Zilliz`:** Open-source, distributed, very scalable.
    * **Considerations:**
        * **Scalability:** How many vectors can it handle?
        * **Features:** Filtering, metadata storage, hybrid search.
        * **Deployment:** Local, self-hosted, managed service.
        * **Search Performance:** Query latency, throughput.
    * **Evaluation:**
    	* See result vs baseline
		* Did we improve beyond baseline ? 
		* Total improvement ?
        * **Retrieval Quality:** Does the vector database choice impact the quality of the `top-k` results (less likely, but check for unexpected issues)?
        * **Performance Benchmarks:** Measure ingestion time and query latency for a representative dataset size.

---

# **Advanced Retrieval Techniques**

**Goal:** Further refine retrieval beyond simple similarity search.

**Tasks:**

1.  **Hybrid Search:**
    * **Task:** Combine vector similarity search with keyword search (e.g., BM25 or TF-IDF).
    * **Reasoning:** Keyword search can be excellent for exact matches and rare terms, while vector search captures semantic similarity. Combining them often yields better results.
    * **Implementation:** Many vector databases support this, or you can implement a fusion strategy (e.g., Reciprocal Rank Fusion - RRF).

2.  **Re-ranking:**
    * **Task:** After initial retrieval, use a more powerful (but slower) re-ranking model to sort the top-k results.
    * **Reasoning:** Initial retrieval is fast but might bring some less relevant results. A re-ranker can significantly improve the precision of the top results.
    * **Example Models:**
        * **`cross-encoder/ms-marco-MiniLM-L-6-v2` (Sentence-Transformers):** Good starting point.
        * **`bge-reranker-base` (BAAI):** Powerful re-ranking model.
    * **Implementation:** The re-ranker takes a query and a retrieved document/chunk and scores their relevance.

3.  **Contextual Window/Padding:**
    * **Task:** Retrieve not just the top-k chunks, but also some surrounding context (e.g., the sentences/paragraphs before and after) to provide more complete information to the LLM.
    * **Reasoning:** A single retrieved chunk might lack essential context.

