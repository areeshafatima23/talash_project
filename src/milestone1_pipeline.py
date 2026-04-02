import os
import pandas as pd # type: ignore
from loader import load_cvs_from_folder
from parser import extract_email, extract_phone, extract_name

def run_pipeline(cvs_folder, output_csv):
    cvs = load_cvs_from_folder(cvs_folder)
    
    data = []
    for cv in cvs:
        text = cv["text"]
        data.append({
            "file_name": cv["file_name"],
            "name": extract_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text)
        })
    
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"CSV saved to {output_csv}")

if __name__ == "__main__":
    cvs_folder = os.path.join(os.path.dirname(__file__), "../cvs")
    output_csv = os.path.join(os.path.dirname(__file__), "../output/milestone1_output.csv")
    run_pipeline(cvs_folder, output_csv)