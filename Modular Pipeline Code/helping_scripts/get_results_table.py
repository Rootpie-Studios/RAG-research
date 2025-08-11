import sys
import os
# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
from config import RESULTS_DIRECTORY

root_dir = RESULTS_DIRECTORY
output_csv = 'metrics_summary.csv'

# Map of base metric names to the line prefixes in the text files
base_metrics = {
    'Accuracy': 'Accuracy:',
    'Precision': 'Precision:',
    'Recall': 'Recall:',
    'Queries_with_results': 'Queries with results after filtering:',
    'Queries_with_no_results': 'Queries with no results after filtering:',
    'Total_queries': 'Total number of queries:'
}

# The metric suffixes based on filename
file_type_suffix_map = {
    'APR_Files.txt': '_Files',
    'APR_Pages.txt': '_Pages',
    'APR_Chunks.txt': '_Chunks'
}

# Collected data per parent folder (assuming all three files exist in one folder)
results = {}

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename in file_type_suffix_map:
            filepath = os.path.join(dirpath, filename)
            folder_id = os.path.relpath(dirpath, root_dir)  # key by relative path

            if folder_id not in results:
                results[folder_id] = {}

            suffix = file_type_suffix_map[filename]

            with open(filepath, 'r') as f:
                for line in f:
                    for key, prefix in base_metrics.items():
                        if line.startswith(prefix):
                            value = line.split(':')[1].strip()
                            # Add suffix only to Accuracy, Precision, Recall
                            if key in ['Accuracy', 'Precision', 'Recall']:
                                col_name = key + suffix
                            else:
                                col_name = key
                            results[folder_id][col_name] = value

# Collect all possible column names
all_columns = set()
for data in results.values():
    all_columns.update(data.keys())

# Order the columns: sort for consistency, but keep file path first
all_columns = sorted(all_columns)
header = ['Folder'] + all_columns

# Write to CSV
with open(output_csv, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    for folder_id, data in results.items():
        row = [folder_id] + [data.get(col, '') for col in all_columns]
        writer.writerow(row)

print(f'Data saved to {output_csv}')
