# Info

Converted to use SentenceTransformers, more notably "all-MiniLM-L12-v2".
Also added OVERLAP functionality.

## How to Install

```bash
pip install -U chromadb openai pymupdf4llm tiktoken tomlkit tomli pandas matplotlib seaborn openpyxl levenshtein tqdm joblib sentence-transformers
```

If you use UV then just do

```bash
uv sync
.\.venv\Scripts\activate.ps1
uv pip install sentence-transformers
```

## Run

```bash
uv run main.py
# or
python main.py
```
