import re

def extract_email(text):
    matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return matches[0] if matches else ""

def extract_phone(text):
    # Matches +92 312 5355098, 0312 5355098, 5147939 etc.
    matches = re.findall(r"\+?\d[\d\s-]{6,}\d", text)
    return matches[0].replace("\n","").strip() if matches else ""

def extract_name(text):
    # Look for line that contains 'Name ' (capitalized), then take following words
    name_lines = re.findall(r"Name\s+([A-Z\s]+)", text)
    if name_lines:
        return " ".join(name_lines[0].split())
    else:
        # fallback: first non-empty line
        for line in text.split("\n"):
            line = line.strip()
            if line:
                return line
    return ""