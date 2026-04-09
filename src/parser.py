# src/parser.py
import re
import json
import time
from dotenv import load_dotenv
load_dotenv()
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Will try each model in order until one works
FREE_MODELS = [
    "openrouter/free",                              # auto-picks best available free model
    "meta-llama/llama-3.3-70b-instruct:free",       # fallback 1
    "google/gemma-3-27b-it:free",                   # fallback 2
    "nvidia/llama-3.1-nemotron-nano-8b-v1:free",    # fallback 3
    "qwen/qwen3-8b:free",                           # fallback 4
]

def call_llm(prompt):
    for model in FREE_MODELS:
        try:
            print(f"Trying model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            print(f"Success with: {model}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Failed {model}: {e}")
            time.sleep(2)
            continue
    return None

def extract_full_profile(text):
    prompt = f"""
You are an expert CV parser. Extract ALL information from the CV text below.
Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

Rules:
- Extract EVERY education entry (school, college, bachelor, master, phd)
- Extract EVERY job/position in experience
- Extract ALL skills mentioned anywhere in the CV
- Extract ALL publications, papers, journals, conferences
- If a field is not found, use empty string "" or empty list []

Return exactly this structure:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "address": "city or country if found",
  "education": [
    {{
      "degree": "degree title",
      "institution": "university or school name",
      "start_year": "YYYY or empty string",
      "end_year": "YYYY or empty string",
      "marks_or_cgpa": "e.g. 3.8/4.0 or 85%",
      "specialization": "major or field"
    }}
  ],
  "experience": [
    {{
      "job_title": "position title",
      "organization": "company or university",
      "start_date": "Month YYYY or empty",
      "end_date": "Month YYYY or Present",
      "description": "brief description or empty"
    }}
  ],
  "skills": ["skill1", "skill2"],
  "publications": [
    {{
      "title": "paper title",
      "venue": "journal or conference name",
      "year": "YYYY or empty",
      "authors": "all authors as string"
    }}
  ],
  "patents": [],
  "books": [],
  "certifications": []
}}

CV Text:
{text}
"""

    raw = call_llm(prompt)

    if raw is None:
        print("All models failed, using regex fallback.")
        return {
            "name": extract_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text),
            "address": "", "education": [], "experience": [],
            "skills": [], "publications": [], "patents": [],
            "books": [], "certifications": []
        }

    try:
        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}\nRaw: {raw[:300]}")
        return _empty_profile()


def _empty_profile():
    return {
        "name": "", "email": "", "phone": "", "address": "",
        "education": [], "experience": [], "skills": [],
        "publications": [], "patents": [], "books": [],
        "certifications": []
    }

def extract_email(text):
    matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return matches[0] if matches else ""

def extract_phone(text):
    matches = re.findall(r"\+?\d[\d\s-]{6,}\d", text)
    return matches[0].replace("\n", "").strip() if matches else ""

def extract_name(text):
    name_lines = re.findall(r"Name\s+([A-Z\s]+)", text)
    if name_lines:
        return " ".join(name_lines[0].split())
    for line in text.split("\n"):
        line = line.strip()
        if line:
            return line
    return ""

# def _empty_profile():
#     return {
#         "name": "", "email": "", "phone": "", "address": "",
#         "education": [], "experience": [], "skills": [],
#         "publications": [], "patents": [], "books": [],
#         "certifications": []
#     }

# def extract_email(text):
#     matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
#     return matches[0] if matches else ""

# def extract_phone(text):
#     matches = re.findall(r"\+?\d[\d\s-]{6,}\d", text)
#     return matches[0].replace("\n", "").strip() if matches else ""

# def extract_name(text):
#     name_lines = re.findall(r"Name\s+([A-Z\s]+)", text)
#     if name_lines:
#         return " ".join(name_lines[0].split())
#     for line in text.split("\n"):
#         line = line.strip()
#         if line:
#             return line
#     return ""