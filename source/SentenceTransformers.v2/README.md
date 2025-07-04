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

## Files

Put your Questions toml files in "questions/cleaned" and your PDFs in "pdf_data". Run it once and then comment out the
"add_embeddings_to_toml(TOML_DIRECTORY)" row.

## Automated BATCH_RUN

You can run an automated batch script that goes through different MAX_TOKENS and OVERLAP and saves the results.

```bash
python batch_run.py --base_name PMC --tokens='384/0,384/100,512/120'
```

how to use the script:

```bash
python batch_run.py --help
```
