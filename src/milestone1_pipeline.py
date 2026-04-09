# src/milestone1_pipeline.py
import os
import json
import pandas as pd
from loader import load_cvs_from_folder
from parser import extract_full_profile

def run_pipeline(cvs_folder, output_csv):
    cvs = load_cvs_from_folder(cvs_folder)

    if not cvs:
        print("No PDFs found.")
        return []

    rows = []
    for cv in cvs:
        print(f"Processing: {cv['file_name']}...")
        profile = extract_full_profile(cv["text"])
        profile["file_name"] = cv["file_name"]
        rows.append(profile)
        print(f"  Extracted: {profile.get('name', 'Unknown')}")

    # Save full JSON per candidate
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Flat CSV — one row per candidate, nested fields as JSON strings
    flat_rows = []
    for r in rows:
        flat_rows.append({
            "file_name":        r.get("file_name", ""),
            "name":             r.get("name", ""),
            "email":            r.get("email", ""),
            "phone":            r.get("phone", ""),
            "address":          r.get("address", ""),
            "education":        json.dumps(r.get("education", [])),
            "experience":       json.dumps(r.get("experience", [])),
            "skills":           ", ".join(r.get("skills", [])),
            "publications":     json.dumps(r.get("publications", [])),
            "patents":          json.dumps(r.get("patents", [])),
            "books":            json.dumps(r.get("books", [])),
            "certifications":   ", ".join(r.get("certifications", [])),
        })

    df = pd.DataFrame(flat_rows)
    df.to_csv(output_csv, index=False)
    print(f"CSV saved to {output_csv}")
    return rows

if __name__ == "__main__":
    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")
    run_pipeline(cvs_folder, output_csv)