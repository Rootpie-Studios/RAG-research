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

*From Pierre's file*
```python
def normalize_text(input_text):
    # Split into lines and clean
    lines = input_text.strip().split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove bullet points and keep the content
        if line.startswith("•"):
            cleaned_lines.append(line.replace("•", "").strip() + ",")
        else:
            cleaned_lines.append(line)

    # Merge lines intelligently (join split words ?)
    full_text = ""
    skipNextSpace = False
    for line in cleaned_lines:
        if line.endswith("-"):
            full_text += line[:-1]
            skipNextSpace = True
        elif skipNextSpace:
            full_text += line
            skipNextSpace = False
        else:
            full_text += " " + line

    # todo: after bullet removal there might be a "," when there should be a "."

    return full_text.strip()
```
*Add your own here if you want to share*
