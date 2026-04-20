# src/milestone2_pipeline.py

import os
import json
import pandas as pd
from loader import load_cvs_from_folder
from parser import extract_full_profile
from datetime import datetime


# EDUCATION ANALYSIS
def analyze_education(education_list):
    missing = []

    for edu in education_list:
        if not edu.get("degree") or not edu.get("institution"):
            missing.append(f"Education missing: {edu}")

    return missing


# EXPERIENCE ANALYSIS
def analyze_experience(experience_list):
    missing = []
    total_months = 0

    for exp in experience_list:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "")

        if not exp.get("job_title") or not exp.get("organization"):
            missing.append(f"Experience missing: {exp}")

        try:
            if start:
                start_dt = datetime.strptime(start, "%B %Y")
                end_dt = datetime.now() if end.lower() == "present" else datetime.strptime(end, "%B %Y")

                months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                total_months += max(months, 0)
        except:
            pass

    return total_months, missing


# MISSING INFO DETECTION
def detect_missing(profile):
    missing = []

    for field in ["name", "email", "phone", "address"]:
        if not profile.get(field):
            missing.append(field)

    missing += analyze_education(profile.get("education", []))
    _, exp_missing = analyze_experience(profile.get("experience", []))
    missing += exp_missing

    return missing


# EMAIL GENERATION
def draft_email(profile, missing_fields):
    if not profile.get("email"):
        return "No email found"

    name = profile.get("name", "Candidate")

    return f"""
Subject: Missing Information Request

Dear {name},

We noticed missing information in your CV:

{", ".join(missing_fields)}

Please update your CV.

Regards,
HR Team
"""


# MAIN PIPELINE
def run_pipeline(cvs_folder, output_dir):
    cvs = load_cvs_from_folder(cvs_folder)

    if not cvs:
        print("No CVs found")
        return []

    os.makedirs(output_dir, exist_ok=True)

    personal, education, experience, skills = [], [], [], []
    missing_rows, email_rows = [], []
    all_profiles = []

    for cv in cvs:
        print(f"Processing {cv['file_name']}")

        profile = extract_full_profile(cv["text"])
        profile["file_name"] = cv["file_name"]
        all_profiles.append(profile)

        #  PERSONAL 
        personal.append({
            "file_name": cv["file_name"],
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "address": profile.get("address", "")
        })

        #  EDUCATION 
        for e in profile.get("education", []):
            education.append({
                "file_name": cv["file_name"],
                "degree": e.get("degree", ""),
                "institution": e.get("institution", ""),
                "start_year": e.get("start_year", ""),
                "end_year": e.get("end_year", "")
            })

        # EXPERIENCE 
        for ex in profile.get("experience", []):
            experience.append({
                "file_name": cv["file_name"],
                "job_title": ex.get("job_title", ""),
                "organization": ex.get("organization", ""),
                "start_date": ex.get("start_date", ""),
                "end_date": ex.get("end_date", "")
            })

        #  SKILLS 
        for s in profile.get("skills", []):
            skills.append({
                "file_name": cv["file_name"],
                "skill": s
            })

        #  MISSING INFO 
        missing = detect_missing(profile)

        if missing:
            missing_rows.append({
                "file_name": cv["file_name"],
                "missing_fields": ", ".join(missing)
            })

        #  EMAIL 
        email_rows.append({
            "file_name": cv["file_name"],
            "email": profile.get("email", ""),
            "draft_email": draft_email(profile, missing)
        })

        # SAVE JSON
        json_path = os.path.join(output_dir, cv["file_name"].replace(".pdf", ".json"))
        with open(json_path, "w") as f:
            json.dump(profile, f, indent=2)


    # SAVE CSV SAFELY

    def safe_save(df, path):
        if len(df) > 0:
            df.to_csv(path, index=False)
        else:
            pd.DataFrame(columns=["empty"]).to_csv(path, index=False)

    safe_save(pd.DataFrame(personal), os.path.join(output_dir, "personal_info.csv"))
    safe_save(pd.DataFrame(education), os.path.join(output_dir, "education.csv"))
    safe_save(pd.DataFrame(experience), os.path.join(output_dir, "experience.csv"))
    safe_save(pd.DataFrame(skills), os.path.join(output_dir, "skills.csv"))
    safe_save(pd.DataFrame(missing_rows), os.path.join(output_dir, "missing_info.csv"))
    safe_save(pd.DataFrame(email_rows), os.path.join(output_dir, "draft_emails.csv"))

    print("Milestone 2 completed")
    return all_profiles