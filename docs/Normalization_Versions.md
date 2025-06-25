## At Parsing
These normalizations take place just after extracting the text by the parser. Which means that the normalized version will be in the database (Not the most flexible?). So it is done in the beginnig of the [parse_embedd_into_db.py](https://github.com/dc91/RAG/blob/main/parse_embedd_into_db.py) script, where it is called by parse_document(pdf_path):
 
```python
def parse_document(pdf_path):
    doc = fitz.open(pdf_path)
    text_and_pagenumber = []  # List [(page_number, page_text)]

    for i, page in enumerate(doc):
        text = page.get_text(sort=True)
        if text.strip():  # Skip empty pages
            norm_text = normalize_text(text)
            text_and_pagenumber.append((i + 1, norm_text + " "))
    doc.close()
    # Test print
    # print(text_and_pagenumber)
    return text_and_pagenumber
```
[This notebook](https://github.com/dc91/RAG/blob/main/extra_scripts/jupyter/RAG_project.ipynb) shows the effect of the normalization.

**Defaut Version**

```python
def normalize_text(input_text):
    # Remove split words at the end of lines
    normalized = re.sub(r"- ?\n", "", input_text.strip())
    # Replace any sequence of whitespace (including newlines) with a single space
    normalized = re.sub(r"\s+", " ", normalized)
    # Don't keep space if end of sentence
    normalized = re.sub(r" +\.\s", ". ", normalized)

    return normalized
```

**Possible versions**

*Tries to remove pagenumbers and solve hyphen problem*

```python
def normalize_text(input_text):
    text = input_text.strip()
    # Remove invisible/zero-width Unicode characters
    text = re.sub(r"[\u00AD\u200B\u200C\u200D\u200E\u200F]\s*", "", text)
    # Split into lines to check for page numbers
    lines = text.splitlines()

    if lines and re.fullmatch(r"\s*\d{1,3}\s*", lines[0]):
        lines = lines[1:]
    if lines and re.fullmatch(r"\s*\d{1,3}\s*", lines[-1]):
        lines = lines[:-1]
        
    # Re-join lines for further processing
    text = "\n".join(lines)
    # Fix hyphenated line breaks: "infor-\nmation" → "information"
    text = re.sub(r"-\s*\n\s*", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Clean up space before punctuation
    text = re.sub(r" +\.\s", ". ", text)
    
    return text.strip()
```

*removes dash space*
Removes dash space leftover of either parser or chunker. Read the comments for more info
```python
def remove_dash_space(text):
    """
    Removes '- ' from a string if it's surrounded by alphabet characters.

    Args:
      text: The input string.

    Returns:
      The modified string with '- ' removed under the specified conditions.
    """
    # The regex explained:
    # (?<=[a-zA-Z]) : Positive lookbehind to assert that there's an alphabet character before '- '
    # -             : Matches the literal hyphen
    #               : Matches the literal space
    # (?=[a-zA-Z])  : Positive lookahead to assert that there's an alphabet character after '- '
    return re.sub(r"(?<=[a-zA-Z])- (?=[a-zA-Z])", "", text)
```

We need to consider some of these control characters/invisble characters. Especially the ones around the hyphens, some are specific for that.
```
def clean_md_text(text):
    CONTROL_SPACE_REGEX = re.compile(
        r'[\x00-\x1F\x7F\u00A0\u1680\u180E\u2000-\u200F\u2028\u2029\u202F\u205F\u2060\u2061\u2062\u2063\u2064\uFEFF]'
    )
    text = re.sub(r"-[\u00AD\u200B\u200C\u200D\u200E\u200F]*\s*\n[\u00AD\u200B\u200C\u200D\u200E\u200F]*\s*", "", text)
    text = re.sub(r"[\u00AD\u200B\u200C\u200D\u200E\u200F]\s*", "", text)
    # Split text into lines
    lines = text.split('\n')
    
    cleaned_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        # Skip lines that only contain a number (e.g., page numbers)
        if re.fullmatch(r'\s*\d+\s*', line):
            continue
        # Skip empty lines
        if not stripped_line:
            continue
        cleaned_lines.append(line)
    
    # Join all lines into one paragraph-like text
    merged_text = '\n'.join(cleaned_lines)
    merged_text = re.sub(r"\s+", " ", merged_text)
    
    return CONTROL_SPACE_REGEX.sub('', merged_text).strip()
```
*Add your own here if you want to share*
