# # src/parser.py

# import re
# import json
# import time
# import os
# from dotenv import load_dotenv
# from openai import OpenAI

# # Load environment variables from .env
# load_dotenv()

# # Read API key
# API_KEY = os.getenv("OPENROUTER_API_KEY")

# # Create client only if key exists
# client = None
# if API_KEY:
#     client = OpenAI(
#         base_url="https://openrouter.ai/api/v1",
#         api_key=API_KEY
#     )

# # Will try each model in order until one works
# FREE_MODELS = [
#     "openrouter/free",                           # auto-picks best available free model
#     "meta-llama/llama-3.3-70b-instruct:free",   # fallback 1
#     "google/gemma-3-27b-it:free",               # fallback 2
#     "nvidia/llama-3.1-nemotron-nano-8b-v1:free",# fallback 3
#     "qwen/qwen3-8b:free",                       # fallback 4
# ]

# def call_llm(prompt):
#     if client is None:
#         print("No OPENROUTER_API_KEY found. Skipping LLM call.")
#         return None

#     for model in FREE_MODELS:
#         try:
#             print(f"Trying model: {model}")
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             print(f"Success with: {model}")
#             return response.choices[0].message.content.strip()
#         except Exception as e:
#             print(f"Failed {model}: {e}")
#             time.sleep(2)

#     return None


# def extract_full_profile(text):
#     prompt = f"""
# You are an expert CV parser. Extract ALL information from the CV text below.
# Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

# Rules:
# - Extract EVERY education entry (school, college, bachelor, master, phd)
# - Extract EVERY job/position in experience
# - Extract ALL skills mentioned anywhere in the CV
# - Extract ALL publications, papers, journals, conferences
# - If a field is not found, use empty string "" or empty list []

# Return exactly this structure:
# {{
#   "name": "full name",
#   "email": "email address",
#   "phone": "phone number",
#   "address": "city or country if found",
#   "education": [
#     {{
#       "degree": "degree title",
#       "level": "one of: SSE, HSSC, UG, PG, PhD or unknown",
#       "institution": "university or school name",
#       "start_year": "YYYY or empty string",
#       "end_year": "YYYY or empty string",
#       "marks_or_cgpa": "e.g. 3.8/4.0 or 85%",
#       "specialization": "major or field"
#     }}
#   ],
#   "experience": [
#     {{
#       "job_title": "position title",
#       "organization": "company or university",
#       "start_date": "Month YYYY or empty",
#       "end_date": "Month YYYY or Present",
#       "description": "brief description or empty"
#     }}
#   ],
#   "skills": ["skill1", "skill2"],
#   "publications": [
#     {{
#       "title": "paper title",
#       "type": "Journal or Conference",
#       "venue": "journal or conference name",
#       "year": "YYYY or empty",
#       "authors": "all authors as string",
#       "issn": "ISSN if mentioned or empty",
#       "publisher": "e.g. IEEE, Springer, ACM, Elsevier or empty"
#     }}
#   ],
#   "patents": [],
#   "books": [],
#   "certifications": []
# }}

# CV Text:
# {text}
# """

#     raw = call_llm(prompt)

#     if raw is None:
#         print("All models failed or API key missing. Using regex fallback.")
#         return {
#             "name": extract_name(text),
#             "email": extract_email(text),
#             "phone": extract_phone(text),
#             "address": "",
#             "education": [],
#             "experience": [],
#             "skills": [],
#             "publications": [],
#             "patents": [],
#             "books": [],
#             "certifications": []
#         }

#     try:
#         # Remove markdown code fences if model returns them
#         raw = raw.strip()
#         raw = re.sub(r"^```json\s*", "", raw)
#         raw = re.sub(r"^```\s*", "", raw)
#         raw = re.sub(r"\s*```$", "", raw)

#         return json.loads(raw)

#     except json.JSONDecodeError as e:
#         print(f"JSON parse failed: {e}\nRaw output:\n{raw[:500]}")
#         return _empty_profile()


# def _empty_profile():
#     return {
#         "name": "",
#         "email": "",
#         "phone": "",
#         "address": "",
#         "education": [],
#         "experience": [],
#         "skills": [],
#         "publications": [],
#         "patents": [],
#         "books": [],
#         "certifications": []
#     }


# def extract_email(text):
#     matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
#     return matches[0] if matches else ""


# def extract_phone(text):
#     matches = re.findall(r"\+?\d[\d\s\-]{6,}\d", text)
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
# src/parser.py
# ─────────────────────────────────────────────────────────────────────────────
#  UPDATED for Milestone 3 (Member A)
#  Changes vs original:
#    - The LLM prompt now has detailed instructions to extract books and patents.
#    - The JSON schema for books and patents is fully specified.
#    - Retry logic kept as-is.
# ─────────────────────────────────────────────────────────────────────────────

import re
import json
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

client = None
if API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )

FREE_MODELS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "nvidia/llama-3.1-nemotron-nano-8b-v1:free",
    "qwen/qwen3-8b:free",
]


def call_llm(prompt, retries=3):
    if client is None:
        print("No OPENROUTER_API_KEY found. Skipping LLM call.")
        return None

    for model in FREE_MODELS:
        for attempt in range(retries):
            try:
                print(f"Trying model: {model}  (attempt {attempt + 1})")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = response.choices[0].message.content.strip()
                print(f"Success with: {model}")
                return result
            except Exception as e:
                print(f"Failed {model} attempt {attempt + 1}: {e}")
                time.sleep(2)

    return None


def extract_full_profile(text):
    """
    Sends the CV text to the LLM and returns a structured JSON profile dict.
    Includes books and patents extraction (updated for Milestone 3).
    Falls back to regex extraction if the LLM is unavailable.
    """
    prompt = f"""
You are an expert CV/resume parser. Read the CV text below very carefully and extract ALL information.
Return ONLY a valid JSON object — NO markdown, NO explanation, NO code fences, NO backticks.

EXTRACTION RULES:
- Extract EVERY education entry (school/matric, college/intermediate, bachelor, master, PhD).
- Extract EVERY job or position in experience, including research assistantships and teaching.
- Extract ALL skills mentioned anywhere in the CV (technical skills, tools, languages, soft skills).
- Extract ALL publications: journal papers, conference papers, book chapters, workshop papers.
- Extract ALL books authored or co-authored (look for "Books", "Textbooks", "Authored" sections).
- Extract ALL patents (look for "Patents", "Intellectual Property", "Inventions" sections).
- If a field is not found, use empty string "" or empty list [].
- Do NOT invent information. Only extract what is explicitly written in the CV.

Return EXACTLY this JSON structure (no extra keys, no missing keys):
{{
  "name": "full name of the candidate",
  "email": "email address or empty string",
  "phone": "phone number or empty string",
  "address": "city or country if found, else empty string",
  "education": [
    {{
      "degree": "exact degree title e.g. BS Computer Science",
      "level": "one of: SSE, HSSC, UG, PG, PhD — pick the closest match",
      "institution": "university or school name",
      "start_year": "YYYY or empty string",
      "end_year": "YYYY or empty string",
      "marks_or_cgpa": "e.g. 3.8/4.0 or 85% or 900/1100 — keep original format",
      "specialization": "major or field of study or empty string"
    }}
  ],
  "experience": [
    {{
      "job_title": "position title",
      "organization": "company or university name",
      "start_date": "Month YYYY or YYYY or empty string",
      "end_date": "Month YYYY or Present or empty string",
      "description": "one-line description or empty string"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "publications": [
    {{
      "title": "full paper title",
      "type": "Journal or Conference or Book Chapter or Workshop",
      "venue": "journal name or conference name",
      "year": "YYYY or empty string",
      "authors": "all authors as a single comma-separated string",
      "issn": "ISSN number if explicitly mentioned, else empty string",
      "publisher": "publisher name e.g. IEEE, Springer, ACM, Elsevier, or empty string"
    }}
  ],
  "books": [
    {{
      "title": "full book title",
      "authors": "all authors as a single comma-separated string",
      "isbn": "ISBN if mentioned, else empty string",
      "publisher": "publisher name or empty string",
      "year": "YYYY or empty string",
      "link": "URL or online link if mentioned, else empty string"
    }}
  ],
  "patents": [
    {{
      "patent_number": "patent number or application number, or empty string",
      "title": "title of the patent",
      "date": "date or year of filing/grant",
      "inventors": "all inventors as a single comma-separated string",
      "country": "country of filing e.g. US, PK, EP, or empty string",
      "link": "verification URL if mentioned, else empty string"
    }}
  ],
  "certifications": ["certification1", "certification2"]
}}

CV Text:
{text}
"""

    raw = call_llm(prompt)

    if raw is None:
        print("All models failed or API key missing. Using regex fallback.")
        return {
            "name": extract_name(text),
            "email": extract_email(text),
            "phone": extract_phone(text),
            "address": "",
            "education": [],
            "experience": [],
            "skills": [],
            "publications": [],
            "books": [],
            "patents": [],
            "certifications": [],
        }

    try:
        raw = raw.strip()
        # Strip markdown code fences if the model wraps the JSON
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*",     "", raw)
        raw = re.sub(r"\s*```$",     "", raw)
        return json.loads(raw)

    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}\nRaw output (first 500 chars):\n{raw[:500]}")
        return _empty_profile()


def _empty_profile():
    return {
        "name":           "",
        "email":          "",
        "phone":          "",
        "address":        "",
        "education":      [],
        "experience":     [],
        "skills":         [],
        "publications":   [],
        "books":          [],
        "patents":        [],
        "certifications": [],
    }


# ── Regex fallback helpers ────────────────────────────────────────────────────

def extract_email(text):
    matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return matches[0] if matches else ""


def extract_phone(text):
    matches = re.findall(r"\+?\d[\d\s\-]{6,}\d", text)
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