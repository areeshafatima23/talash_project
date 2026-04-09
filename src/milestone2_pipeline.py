# src/milestone2_pipeline.py
import os
import json
import pandas as pd
from loader import load_cvs_from_folder
from parser import extract_full_profile
from collections import Counter
from datetime import datetime

def analyze_education(education_list):
    """
    Analyze education profile: count degrees, detect missing fields
    """
    degrees = []
    missing_fields = []
    for edu in education_list:
        degree = edu.get("degree", "").strip()
        institution = edu.get("institution", "").strip()
        start = edu.get("start_year", "")
        end = edu.get("end_year", "")
        marks = edu.get("marks_or_cgpa", "")
        specialization = edu.get("specialization", "")
        degrees.append(degree if degree else "Unknown Degree")
        # Check for missing info
        if not all([degree, institution, start, end]):
            missing_fields.append(f"Education: {degree or 'N/A'} at {institution or 'N/A'}")
    return degrees, missing_fields

def analyze_experience(experience_list):
    """
    Analyze professional experience: total experience, current job
    """
    total_months = 0
    missing_fields = []
    current_job = None
    for exp in experience_list:
        start = exp.get("start_date", "")
        end = exp.get("end_date", "")
        job_title = exp.get("job_title", "")
        org = exp.get("organization", "")
        # Missing info detection
        if not all([start, end, job_title, org]):
            missing_fields.append(f"Experience: {job_title or 'N/A'} at {org or 'N/A'}")
        # Calculate total experience in months
        try:
            start_dt = datetime.strptime(start, "%B %Y") if start else None
            end_dt = datetime.strptime(end, "%B %Y") if end and end.lower() != "present" else datetime.now()
            if start_dt:
                months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                total_months += max(months, 0)
        except:
            pass
        # Detect current job
        if end.lower() == "present":
            current_job = f"{job_title} at {org}"
    return total_months, current_job, missing_fields

def detect_missing_info(profile):
    """
    Detect missing key information and generate missing info list
    """
    missing = []
    if not profile.get("name"):
        missing.append("Name")
    if not profile.get("email"):
        missing.append("Email")
    if not profile.get("phone"):
        missing.append("Phone")
    if not profile.get("address"):
        missing.append("Address")
    # Education and experience
    _, edu_missing = analyze_education(profile.get("education", []))
    _, _, exp_missing = analyze_experience(profile.get("experience", []))
    missing.extend(edu_missing)
    missing.extend(exp_missing)
    return missing

def draft_missing_info_email(profile, missing_fields):
    """
    Generate a simple draft email for the candidate to fill missing info
    """
    if not profile.get("email"):
        return "Cannot generate email: missing candidate email."
    name = profile.get("name", "Candidate")
    missing_str = ", ".join(missing_fields)
    email_body = f"""Subject: Request for Missing Information

Hi {name},

We are reviewing your CV and noticed the following missing information:
{missing_str}

Kindly provide the missing details at your earliest convenience.

Best regards,
Recruitment Team
"""
    return email_body

def run_pipeline(cvs_folder, output_dir):
    """
    Main Milestone 2 pipeline:
    - Load CVs
    - Extract full profiles
    - Analyze education and experience
    - Detect missing info
    - Save multiple CSVs + JSONs
    - Generate draft emails
    """
    cvs = load_cvs_from_folder(cvs_folder)
    if not cvs:
        print("No PDFs found.")
        return []

    os.makedirs(output_dir, exist_ok=True)

    personal_rows = []
    education_rows = []
    experience_rows = []
    skills_rows = []
    missing_info_rows = []
    draft_email_rows = []

    for cv in cvs:
        print(f"Processing: {cv['file_name']}...")
        profile = extract_full_profile(cv["text"])
        profile["file_name"] = cv["file_name"]

        # ── Personal Info CSV ─────────────────────────────
        personal_rows.append({
            "file_name": profile["file_name"],
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "address": profile.get("address", "")
        })

        # ── Education CSV ─────────────────────────────────
        for edu in profile.get("education", []):
            education_rows.append({
                "file_name": profile["file_name"],
                "degree": edu.get("degree", ""),
                "institution": edu.get("institution", ""),
                "start_year": edu.get("start_year", ""),
                "end_year": edu.get("end_year", ""),
                "marks_or_cgpa": edu.get("marks_or_cgpa", ""),
                "specialization": edu.get("specialization", "")
            })

        # ── Experience CSV ───────────────────────────────
        for exp in profile.get("experience", []):
            experience_rows.append({
                "file_name": profile["file_name"],
                "job_title": exp.get("job_title", ""),
                "organization": exp.get("organization", ""),
                "start_date": exp.get("start_date", ""),
                "end_date": exp.get("end_date", ""),
                "description": exp.get("description", "")
            })

        # ── Skills CSV ───────────────────────────────────
        for skill in profile.get("skills", []):
            skills_rows.append({
                "file_name": profile["file_name"],
                "skill": skill
            })

        # ── Missing Info Detection ───────────────────────
        missing_fields = detect_missing_info(profile)
        if missing_fields:
            missing_info_rows.append({
                "file_name": profile["file_name"],
                "missing_fields": ", ".join(missing_fields)
            })

        # ── Draft Emails ────────────────────────────────
        if profile.get("email"):
            draft_email_rows.append({
                "file_name": profile["file_name"],
                "candidate_email": profile["email"],
                "draft_email": draft_missing_info_email(profile, missing_fields)
            })

        # ── Save JSON per candidate ─────────────────────
        with open(os.path.join(output_dir, profile["file_name"].replace(".pdf", "_profile.json")), "w") as f:
            json.dump(profile, f, indent=2)

    # ── Save CSVs ─────────────────────────────────────
    pd.DataFrame(personal_rows).to_csv(os.path.join(output_dir, "personal_info.csv"), index=False)
    pd.DataFrame(education_rows).to_csv(os.path.join(output_dir, "education.csv"), index=False)
    pd.DataFrame(experience_rows).to_csv(os.path.join(output_dir, "experience.csv"), index=False)
    pd.DataFrame(skills_rows).to_csv(os.path.join(output_dir, "skills.csv"), index=False)
    pd.DataFrame(missing_info_rows).to_csv(os.path.join(output_dir, "missing_info.csv"), index=False)
    pd.DataFrame(draft_email_rows).to_csv(os.path.join(output_dir, "draft_emails.csv"), index=False)

    print(f"Milestone 2 CSVs and JSONs saved in {output_dir}")
    return cvs