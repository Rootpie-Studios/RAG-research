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
