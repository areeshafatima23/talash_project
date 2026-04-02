# src/loader.py
import os
import pdfplumber # type: ignore

def load_cvs_from_folder(folder_path):
    """
    Load all PDFs from the given folder and return a list of their text contents.
    """
    cvs_text = []
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder does not exist: {folder_path}")

    for file_name in os.listdir(folder_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(folder_path, file_name)
            text = extract_text_from_pdf(file_path)
            cvs_text.append({"file_name": file_name, "text": text})

    return cvs_text

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a single PDF using pdfplumber.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text