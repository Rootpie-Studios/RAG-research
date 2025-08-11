# Helping scripts
The following scripts are necessary, and are mostly storing methods and variables used by other scripts:

`chunking.py` - Contains both chunking strategy methods. Called by `parse_embedd_insert.py`.

`generate_llm_response.py` - Contains methods for context and answer generation. Called by `query_db_all_questions.py`.

`norm_funcs.py` - Contains normalization methods. Called by `parse_embedd_insert.py` and `query_db_all_questions.py`.

`reranking.py` - Contains reranking methods. Called by `query_db_all_questions.py`.

# Extra scripts
The following scripts are helpful extra scripts:

`batch_upload_Mistral.py` - Uploads files to Mistral, saves Files IDs to csv for later use.

`batch_OCR_Mistral.py` - Gets OCR results from Mistral and saves them as markdown files.

`compare_parsing.py` - Compares the results of parsing from various parsers, saves to file. It is suggested to just use a subset of the data for this.

`get_llm_ans_to_text.py` - Compiles a more readable text file for analyzing results, after generating answers with LLM.

`get_results_table.py` - Generates a table with all results, from results folder. You need to run `query_db_all_questions.py` first and then `save_stats_and_plots.ipynb`, to be able to create the tables.
