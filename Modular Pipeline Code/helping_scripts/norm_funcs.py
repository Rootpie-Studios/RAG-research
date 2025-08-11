import re

LINEBREAKS = r"(?:\r\n|\r|\n|\u2028|\u2029)"
HYPHENS = r"[-‐‑‒–—−]"
CONTROL_SPACE_REGEX = re.compile(
    r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u00A0\u1680\u180E\u2000-\u200F\u202F\u205F\u2060-\u2064\uFEFF]'
)

# Norm 1
def normalize_text(input_text):
    # Remove control/invisible characters
    input_text = CONTROL_SPACE_REGEX.sub('', input_text)
    # Remove hyphenated linebreaks (e.g., "för-\ngrening" -> "förgrening")
    input_text = re.sub(HYPHENS + r"\s*" + LINEBREAKS + r"\s*", "", input_text)
    # Normalize all remaining whitespace to a single space
    input_text = re.sub(r"\s+", " ", input_text)
    # Clean up spacing before period
    input_text = re.sub(r" +\.\s", ". ", input_text)

    return input_text.strip()

# Norm 2
def clean_md_text(text):
    # Split text into lines
    text = re.sub(r"-[\u00AD\u200B\u200C\u200D\u200E\u200F]*\s*\n[\u00AD\u200B\u200C\u200D\u200E\u200F]*\s*", "", text)
    text = re.sub(r"[\u00AD\u200B\u200C\u200D\u200E\u200F]\s*", "", text)
    
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
    merged_text = " ".join(cleaned_lines)
    # Normalize whitespace
    merged_text = re.sub(r"\s+", " ", merged_text)
    
    return CONTROL_SPACE_REGEX.sub('', merged_text).strip()

# Still Norm 2
def remove_md_stuff(text):
    content = re.sub(r'(?:\n)?#{1,6}|(?:\n)?```(?:.|\n)*?```|(?:\n)?---+|(?:\n)?___+', '', text)

    # Replace spaces with a single space
    content = re.sub(r' +', ' ', content)

    # Remove bold (handles **bold** and __bold__)
    content = re.sub(r'(\*\*|__)(.*?)\1', r'\2', content)

    # Remove italic (handles *italic* and _italic_)
    content = re.sub(r'(\*|_)(.*?)\1', r'\2', content)
        
    return content

def normalize_spaces(input_text):
    normalized = re.sub(r" +", "", input_text)

    return normalized