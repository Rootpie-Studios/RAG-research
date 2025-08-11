import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from config import get_results_filenames

# Load the CSV file
RESULTS_CSV_NAME = get_results_filenames()[0]
df = pd.read_csv(RESULTS_CSV_NAME)

# Extract the query ID without the R1-R5 suffix
df["Query_Id"] = df["Result_Id"].str[:-2]

# Get the first 2 results (R1 and R2) for boolean fields
df_first2 = df[df["Result_Id"].str.endswith(("R1", "R2"))]

# Aggregate boolean values per query
summary = df_first2.groupby("Query_Id").agg({
    "Correct_File": "any",
    "Correct_Pages": "any",
    "Match_Threshold": "any"
}).reset_index()

# Get R5 data with final output fields
df_r5 = df[df["Result_Id"].str.endswith("R5")]
df_r5 = df_r5[["Query_Id", "Result_Id", "Question", "Expected_answer", "LLM_ANS"]]

# Merge both summaries
final_df = pd.merge(summary, df_r5, on="Query_Id")

# Write to a .txt file in the specified format
with open(RESULTS_CSV_NAME[:-4] + ".txt", "w", encoding="utf-8") as f:
    for _, row in final_df.iterrows():
        f.write(f"""\
{row['Result_Id']}, File_Match: {row['Correct_File']}, Page_Match: {row['Correct_Pages']}, Match_Threshold: {row['Match_Threshold']}.

Question: {row['Question']}

LLM_ANS: {row['LLM_ANS']}

Expected_Answer_Source: {row['Expected_answer']}
-----------------------------------------------

""")