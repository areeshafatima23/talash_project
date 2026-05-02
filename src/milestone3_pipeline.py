import os
import json
import re
import math
import pandas as pd
from collections import Counter
from loader import load_cvs_from_folder
from parser import extract_full_profile
from datetime import datetime

#  SAFE STRING HELPER  
def safe_str(val):
    """Returns a clean string; never raises AttributeError on None."""
    return str(val).strip() if val is not None else ""


#  MOCK DATABASES 
MOCK_JOURNALS = {
    "ieee transactions on pattern analysis": {"wos": True, "scopus": True, "quartile": "Q1", "if": 24.3},
    "nature":                                {"wos": True, "scopus": True, "quartile": "Q1", "if": 64.8},
    "expert systems with applications":      {"wos": True, "scopus": True, "quartile": "Q1", "if": 8.5},
    "ieee access":                           {"wos": True, "scopus": True, "quartile": "Q2", "if": 3.4},
}

MOCK_CONFERENCES = {
    "cvpr": "A*", "neurips": "A*", "icml": "A*", "iccv": "A*",
    "acl":  "A*", "emnlp":  "A*", "kdd":  "A*", "aaai": "A*", "ijcai": "A*",
}

THE_QS_RANKINGS = {
    "massachusetts institute of technology": "Rank 1 (QS)",
    "mit":                                   "Rank 1 (QS)",
    "stanford university":                   "Rank 2 (QS)",
    "harvard university":                    "Rank 4 (QS)",
    "university of oxford":                  "Rank 3 (QS)",
    "university of cambridge":               "Rank 5 (QS)",
    "national university of sciences and technology": "Top 400 (QS)",
    "nust":                                  "Top 400 (QS)",
    "lums":                                  "Top 600 (QS)",
    "lahore university of management sciences": "Top 600 (QS)",
    "fast nuces":                            "Top 1000 (QS)",
    "university of the punjab":              "Top 1000 (QS)",
    "comsats":                               "Top 800 (QS)",
}

#  TOPIC KEYWORD MAP 
TOPIC_KEYWORD_MAP = {
    "Machine Learning & AI":     ["machine learning", "deep learning", "neural network", "artificial intelligence",
                                   "classification", "regression", "random forest", "svm", "xgboost", "reinforcement",
                                   "federated", "transfer learning", "generative", "gan", "diffusion"],
    "Computer Vision":           ["computer vision", "image recognition", "object detection", "segmentation",
                                   "face recognition", "optical flow", "video analysis", "image processing",
                                   "convolutional", "cnn", "yolo", "detection"],
    "Natural Language Processing":["natural language", "nlp", "text classification", "sentiment", "named entity",
                                   "language model", "bert", "gpt", "transformer", "word embedding", "chatbot",
                                   "machine translation", "question answering", "summarization"],
    "Cybersecurity":             ["cybersecurity", "intrusion detection", "malware", "anomaly detection",
                                   "network security", "vulnerability", "encryption", "cryptography", "attack",
                                   "cyber threat", "firewall", "authentication"],
    "Data Science & Analytics":  ["data mining", "big data", "analytics", "visualization", "clustering",
                                   "dimensionality reduction", "pca", "feature selection", "exploratory",
                                   "predictive", "statistical", "data science"],
    "Software Engineering":      ["software engineering", "agile", "devops", "software development",
                                   "testing", "code review", "architecture", "microservices", "api",
                                   "design pattern", "software quality"],
    "Networks & IoT":            ["network", "iot", "internet of things", "wireless", "5g", "sensor",
                                   "edge computing", "cloud computing", "routing", "protocol", "bandwidth",
                                   "latency", "distributed", "noma", "heterogeneous", "resource allocation",
                                   "small cell", "hetnet", "backhaul", "ofdm", "antenna", "mimo",
                                   "channel", "spectrum", "relay", "cognitive radio", "beamforming",
                                   "energy efficiency", "path selection", "traveling salesman"],
    "Healthcare & Bioinformatics":["healthcare", "medical imaging", "bioinformatics", "genomics", "disease",
                                   "clinical", "diagnosis", "ecg", "mri", "radiology", "drug discovery",
                                   "patient", "hospital"],
    "Robotics & Automation":     ["robot", "autonomous", "drone", "control system", "path planning",
                                   "manipulation", "simulation", "actuator", "mechatronics"],
    "Education Technology":      ["e-learning", "education", "learning management", "student performance",
                                   "curriculum", "pedagogy", "blended learning", "moodle"],
}

#  SKILL CATEGORY MAP
SKILL_CATEGORIES = {
    "Programming Languages": ["python", "java", "c++", "c#", "javascript", "r", "matlab",
                               "scala", "go", "rust", "php", "swift", "kotlin", "typescript",
                               "ruby", "perl", "bash", "shell"],
    "ML / AI Frameworks":    ["tensorflow", "pytorch", "keras", "scikit-learn", "opencv",
                               "huggingface", "xgboost", "lightgbm", "catboost", "spacy",
                               "nltk", "fastai"],
    "Data & Analytics":      ["sql", "pandas", "numpy", "tableau", "power bi", "excel",
                               "spark", "hadoop", "databricks", "hive", "kafka", "airflow",
                               "dbt", "looker"],
    "Web & Cloud":           ["django", "flask", "fastapi", "react", "angular", "vue",
                               "node.js", "aws", "azure", "gcp", "docker", "kubernetes",
                               "terraform", "jenkins", "github actions"],
    "Tools & Practices":     ["git", "linux", "agile", "scrum", "devops", "ci/cd", "jira",
                               "latex", "rest api", "graphql", "postman", "figma"],
}


#  MODULE 1: TOPIC VARIABILITY ANALYSIS

def classify_publication_topics(publications):
    classified = []
    for pub in publications:
        text_to_search = " ".join([
            safe_str(pub.get("title",    "")),
            safe_str(pub.get("venue",    "")),
            safe_str(pub.get("abstract", "")),
        ]).lower()

        matched = []
        for theme, keywords in TOPIC_KEYWORD_MAP.items():
            if any(kw in text_to_search for kw in keywords):
                matched.append(theme)

        if not matched:
            matched = ["Other / Unclassified"]

        classified.append({
            "title":          safe_str(pub.get("title", "")),
            "year":           safe_str(pub.get("year",  "")),
            "venue":          safe_str(pub.get("venue", "")),
            "matched_themes": matched,
            "primary_theme":  matched[0],
        })

    return classified


def compute_topic_variability(classified_publications):
    if not classified_publications:
        return {
            "theme_distribution":  {},
            "theme_percentages":   {},
            "dominant_topic":      "N/A",
            "diversity_score":     0.0,
            "variability_label":   "Insufficient Data",
            "trend_over_time":     [],
            "total_publications":  0,
        }

    theme_counter = Counter()
    for pub in classified_publications:
        for theme in pub["matched_themes"]:
            theme_counter[theme] += 1

    total = len(classified_publications)
    theme_percentages = {t: round((c / total) * 100, 1) for t, c in theme_counter.items()}
    dominant_topic    = theme_counter.most_common(1)[0][0] if theme_counter else "N/A"

    diversity_score = 0.0
    if len(theme_counter) > 1:
        probs       = [c / total for c in theme_counter.values()]
        raw_entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(len(theme_counter))
        diversity_score = min(round(raw_entropy / max_entropy, 3), 1.0) if max_entropy > 0 else 0.0

    if diversity_score < 0.3:
        variability_label = "Specialist (Focused Research)"
    elif diversity_score < 0.65:
        variability_label = "Moderate Breadth"
    else:
        variability_label = "Interdisciplinary (Broad Research)"

    trend_over_time = []
    for pub in classified_publications:
        year = pub.get("year", "")
        if year and str(year).strip().isdigit():
            trend_over_time.append({
                "year":  int(str(year).strip()),
                "theme": pub["primary_theme"],
                "title": pub["title"],
            })
    trend_over_time.sort(key=lambda x: x["year"])

    return {
        "theme_distribution":  dict(theme_counter),
        "theme_percentages":   theme_percentages,
        "dominant_topic":      dominant_topic,
        "diversity_score":     diversity_score,
        "variability_label":   variability_label,
        "trend_over_time":     trend_over_time,
        "total_publications":  total,
    }


def interpret_topic_variability(variability_result, candidate_name="Candidate"):
    if variability_result["total_publications"] == 0:
        return f"{candidate_name} has no documented publications for topic analysis."

    dominant = variability_result["dominant_topic"]
    label    = variability_result["variability_label"]
    score    = variability_result["diversity_score"]
    n_themes = len(variability_result["theme_distribution"])
    total    = variability_result["total_publications"]
    top_pct  = variability_result["theme_percentages"].get(dominant, 0)

    text = (
        f"{candidate_name} has {total} publication(s) spanning {n_themes} research theme(s). "
        f"The dominant area is '{dominant}' ({top_pct}% of publications). "
        f"Diversity score: {score:.2f}/1.00 — classified as '{label}'. "
    )

    if label == "Specialist (Focused Research)":
        text += "This indicates deep expertise in a narrow domain, which is ideal for highly specialized roles."
    elif label == "Moderate Breadth":
        text += "The candidate shows a balance between specialization and cross-domain exposure."
    else:
        text += "The candidate demonstrates broad interdisciplinary research engagement across multiple fields."

    return text


#  MODULE 2: CO-AUTHOR ANALYSIS

def parse_author_list(authors_string):
    if not authors_string:
        return []
    authors_string = re.sub(r'\s+and\s+', ', ', safe_str(authors_string), flags=re.IGNORECASE)
    authors_string = authors_string.replace('*', '')
    return [a.strip() for a in authors_string.split(',') if a.strip()]


def normalize_author_name(name):
    name = safe_str(name).lower()
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def is_same_author(name_a, name_b):
    a = normalize_author_name(name_a)
    b = normalize_author_name(name_b)

    if a == b:
        return True

    tokens_a = a.split()
    tokens_b = b.split()

    if not tokens_a or not tokens_b:
        return False

    last_a = tokens_a[-1]
    last_b = tokens_b[-1]

    if last_a == last_b and len(last_a) > 2:
        init_a = tokens_a[0][0] if tokens_a else ''
        init_b = tokens_b[0][0] if tokens_b else ''
        if init_a == init_b:
            return True

    return False


def analyze_coauthors(publications, candidate_name):
    if not publications:
        return {
            "unique_coauthors":        [],
            "total_unique_coauthors":  0,
            "coauthor_frequency":      {},
            "frequent_collaborators":  [],
            "avg_authors_per_paper":   0.0,
            "solo_papers":             0,
            "largest_team_size":       0,
            "collaboration_diversity": 0.0,
            "per_paper_details":       [],
            "interpretation":          f"{candidate_name} has no documented publications for co-author analysis.",
        }

    all_coauthors_flat  = []
    unique_coauthor_set = []
    per_paper_details   = []
    solo_count          = 0
    team_sizes          = []

    for pub in publications:
        author_list = parse_author_list(pub.get("authors", ""))
        team_size   = len(author_list)
        team_sizes.append(team_size)

        coauthors_this_paper = [a for a in author_list if not is_same_author(a, candidate_name)]

        if not coauthors_this_paper:
            solo_count += 1

        all_coauthors_flat.extend(coauthors_this_paper)

        for ca in coauthors_this_paper:
            if not any(is_same_author(ca, ex) for ex in unique_coauthor_set):
                unique_coauthor_set.append(ca)

        per_paper_details.append({
            "title":     safe_str(pub.get("title", "")),
            "year":      safe_str(pub.get("year",  "")),
            "coauthors": ", ".join(coauthors_this_paper) if coauthors_this_paper else "None (Solo)",
            "team_size": team_size,
        })

    freq_map = {}
    for ca in all_coauthors_flat:
        matched_key = next((k for k in freq_map if is_same_author(ca, k)), None)
        if matched_key:
            freq_map[matched_key] += 1
        else:
            freq_map[ca] = 1

    coauthor_frequency     = dict(sorted(freq_map.items(), key=lambda x: x[1], reverse=True))
    frequent_collaborators = [(n, c) for n, c in coauthor_frequency.items() if c >= 2]

    avg_authors  = round(sum(team_sizes) / len(team_sizes), 2) if team_sizes else 0
    largest_team = max(team_sizes) if team_sizes else 0
    total_unique = len(unique_coauthor_set)

    total_ca_appearances = sum(freq_map.values())
    collab_diversity = round(total_unique / total_ca_appearances, 3) if total_ca_appearances > 0 else 0.0

    interpretation = _interpret_coauthors(
        candidate_name, total_unique, frequent_collaborators,
        avg_authors, solo_count, len(publications), collab_diversity
    )

    return {
        "unique_coauthors":        unique_coauthor_set,
        "total_unique_coauthors":  total_unique,
        "coauthor_frequency":      coauthor_frequency,
        "frequent_collaborators":  frequent_collaborators,
        "avg_authors_per_paper":   avg_authors,
        "solo_papers":             solo_count,
        "largest_team_size":       largest_team,
        "collaboration_diversity": collab_diversity,
        "per_paper_details":       per_paper_details,
        "interpretation":          interpretation,
    }


def _interpret_coauthors(candidate_name, total_unique, frequent_collabs,
                          avg_authors, solo_count, total_papers, diversity):
    text = (
        f"{candidate_name} has collaborated with {total_unique} unique co-author(s) "
        f"across {total_papers} publication(s). "
        f"Average team size per paper: {avg_authors:.1f}. "
    )
    if solo_count > 0:
        text += f"{solo_count} paper(s) appear to be single-authored. "
    if frequent_collabs:
        top   = frequent_collabs[:3]
        names = ", ".join([f"{n} ({c} papers)" for n, c in top])
        text += f"Recurring collaborators: {names}. This suggests a stable research network. "
    else:
        text += "No recurring collaborators detected — the candidate may work with diverse, non-overlapping groups. "
    if diversity > 0.75:
        text += "High collaboration diversity indicates broad academic reach."
    elif diversity > 0.4:
        text += "Moderate collaboration diversity suggests a mix of stable partnerships and new collaborations."
    else:
        text += "Low collaboration diversity suggests concentrated work within a tight research group."
    return text


#  MODULE 3: BOOKS ANALYSIS

CREDIBLE_PUBLISHERS = [
    "springer", "elsevier", "wiley", "cambridge university press",
    "oxford university press", "mit press", "pearson", "mcgraw-hill",
    "taylor & francis", "routledge", "sage", "ieee press", "acm press",
    "packt", "o'reilly", "no starch press",
]


def analyze_books(books_list, candidate_name):
    if not books_list:
        return [], {
            "total_books":              0,
            "sole_authored":            0,
            "co_authored":              0,
            "credible_publisher_count": 0,
            "interpretation":           f"{candidate_name} has no documented books.",
        }

    enriched       = []
    sole_count     = 0
    co_count       = 0
    credible_count = 0

    for book in books_list:
        authors_str  = safe_str(book.get("authors", ""))
        author_list  = parse_author_list(authors_str)
        publisher    = safe_str(book.get("publisher", ""))
        publisher_lc = publisher.lower()

        if len(author_list) == 1:
            authorship_role = "Sole Author"
            sole_count += 1
        else:
            is_lead         = author_list and is_same_author(author_list[0], candidate_name)
            authorship_role = "Lead Author" if is_lead else "Co-Author"
            co_count += 1

        is_credible           = any(cp in publisher_lc for cp in CREDIBLE_PUBLISHERS)
        publisher_credibility = "Recognized Academic/Professional Publisher" if is_credible else "Unknown / Self-Published"
        if is_credible:
            credible_count += 1

        isbn = safe_str(book.get("isbn", ""))
        link = safe_str(book.get("link", book.get("url", "")))
        verification_url = link if link else (
            f"https://www.worldcat.org/search?q=isbn:{isbn}" if isbn else "No link provided"
        )

        enriched.append({
            "title":                 safe_str(book.get("title", "")),
            "authors":               authors_str,
            "authorship_role":       authorship_role,
            "isbn":                  isbn if isbn else "Not Stated",
            "publisher":             publisher if publisher else "Not Stated",
            "publisher_credibility": publisher_credibility,
            "year":                  safe_str(book.get("year", "")),
            "verification_url":      verification_url,
        })

    interp = (
        f"{candidate_name} has {len(books_list)} book(s): "
        f"{sole_count} sole-authored, {co_count} co-authored. "
    )
    if credible_count > 0:
        interp += f"{credible_count} book(s) published by recognized academic publishers. "
    else:
        interp += "No books from major recognized publishers detected. "
    if len(books_list) > 0:
        interp += (
            "Books demonstrate domain expertise and contribution to knowledge dissemination "
            "beyond journal/conference publications."
        )

    summary = {
        "total_books":              len(books_list),
        "sole_authored":            sole_count,
        "co_authored":              co_count,
        "credible_publisher_count": credible_count,
        "interpretation":           interp,
    }
    return enriched, summary


#  MODULE 4: PATENTS ANALYSIS

PATENT_DB_MAP = {
    "us": "https://patents.google.com/patent/US{number}",
    "pk": "https://www.ipop.gov.pk/",
    "ep": "https://patents.google.com/patent/EP{number}",
    "wo": "https://patents.google.com/patent/WO{number}",
    "gb": "https://patents.google.com/patent/GB{number}",
}


def build_patent_verification_url(patent_number, country):
    if not patent_number:
        return "No verification link"
    country_code = safe_str(country).lower()[:2]
    template     = PATENT_DB_MAP.get(country_code)
    clean_number = re.sub(r'^[A-Za-z]{2}', '', safe_str(patent_number))
    if template and "{number}" in template:
        return template.format(number=clean_number)
    return f"https://patents.google.com/?q={safe_str(patent_number).replace(' ', '+')}"


def analyze_patents(patents_list, candidate_name):
    if not patents_list:
        return [], {
            "total_patents":       0,
            "lead_inventor_count": 0,
            "co_inventor_count":   0,
            "countries":           [],
            "interpretation":      f"{candidate_name} has no documented patents.",
        }

    enriched       = []
    lead_count     = 0
    co_count       = 0
    countries_seen = set()

    for patent in patents_list:
        inventors_str = safe_str(patent.get("inventors", patent.get("innovators", "")))
        inventor_list = parse_author_list(inventors_str)
        country       = safe_str(patent.get("country", ""))
        patent_number = safe_str(patent.get("patent_number", patent.get("number", "")))

        if country:
            countries_seen.add(country)

        if inventor_list:
            is_lead = is_same_author(inventor_list[0], candidate_name)
            role    = "Lead Inventor" if is_lead else "Co-Inventor"
            if is_lead:
                lead_count += 1
            else:
                co_count += 1
        else:
            role = "Unknown Role"

        provided_link    = safe_str(patent.get("link", patent.get("url", "")))
        verification_url = provided_link if provided_link else build_patent_verification_url(patent_number, country)

        enriched.append({
            "patent_number":    patent_number if patent_number else "Not Stated",
            "title":            safe_str(patent.get("title", "")),
            "date":             safe_str(patent.get("date", patent.get("year", ""))),
            "inventors":        inventors_str,
            "inventor_role":    role,
            "country":          country if country else "Not Stated",
            "verification_url": verification_url,
        })

    country_list = list(countries_seen)
    interp = (
        f"{candidate_name} holds {len(patents_list)} patent(s): "
        f"{lead_count} as lead inventor, {co_count} as co-inventor. "
    )
    if country_list:
        interp += f"Countries of filing: {', '.join(country_list)}. "
    interp += (
        "Patents indicate applied research output and demonstrate translation of research "
        "into protectable intellectual property."
    )

    summary = {
        "total_patents":       len(patents_list),
        "lead_inventor_count": lead_count,
        "co_inventor_count":   co_count,
        "countries":           country_list,
        "interpretation":      interp,
    }
    return enriched, summary


#  MODULE 5: SKILLS ANALYSIS

def analyze_skills(skills_list, candidate_name):
    if not skills_list:
        return {
            "total_skills":    0,
            "unique_skills":   0,
            "top_skills":      [],
            "skill_categories":{},
            "interpretation":  f"{candidate_name} has no documented skills.",
        }

    cleaned = [safe_str(s).lower() for s in skills_list if safe_str(s)]
    counter = Counter(cleaned)

    skill_categories = {}
    for skill in cleaned:
        matched_cat = None
        for cat, keywords in SKILL_CATEGORIES.items():
            if any(kw in skill for kw in keywords):
                matched_cat = cat
                break
        category = matched_cat if matched_cat else "Other"
        skill_categories[category] = skill_categories.get(category, 0) + 1

    top_skills = counter.most_common(10)

    interpretation = (
        f"{candidate_name} has {len(skills_list)} skill mention(s) "
        f"({len(counter)} unique). "
    )
    if top_skills:
        top_names = ", ".join([s for s, _ in top_skills[:5]])
        interpretation += f"Top skills: {top_names}. "
    if skill_categories:
        dominant_cat = max(skill_categories, key=skill_categories.get)
        interpretation += f"Dominant skill category: '{dominant_cat}'."

    return {
        "total_skills":     len(skills_list),
        "unique_skills":    len(counter),
        "top_skills":       top_skills,
        "skill_categories": skill_categories,
        "interpretation":   interpretation,
    }


#  MODULE 6: EXPERIENCE ANALYSIS

SENIORITY_KEYWORDS = [
    "intern", "trainee", "junior", "associate", "mid", "engineer", "analyst",
    "developer", "researcher", "senior", "lead", "principal", "staff",
    "manager", "director", "head", "chief", "vp", "president", "cto", "ceo",
]


def compute_experience_years(experience_list):
    total = 0
    for exp in experience_list:
        sy = parse_year(exp.get("start_date", exp.get("start_year", "")))
        ey = parse_year(exp.get("end_date",   exp.get("end_year",   ""))) or datetime.now().year
        if sy and ey:
            total += max(0, ey - sy)
    return total


def _seniority_score(title):
    title_lower = safe_str(title).lower()
    for i, kw in enumerate(SENIORITY_KEYWORDS):
        if kw in title_lower:
            return i
    return 0


def analyze_experience(experience_list, candidate_name):
    if not experience_list:
        return {
            "total_roles":        0,
            "total_years":        0,
            "avg_tenure_years":   0.0,
            "roles":              [],
            "career_progression": "No experience data",
            "interpretation":     f"{candidate_name} has no documented experience.",
        }

    total_years = compute_experience_years(experience_list)
    total_roles = len(experience_list)
    avg_tenure  = round(total_years / total_roles, 2) if total_roles > 0 else 0.0

    roles = []
    for exp in experience_list:
        sy       = parse_year(exp.get("start_date", exp.get("start_year", "")))
        ey       = parse_year(exp.get("end_date",   exp.get("end_year",   ""))) or datetime.now().year
        duration = max(0, ey - sy) if (sy and ey) else 0
        roles.append({
            "job_title":      safe_str(exp.get("job_title",    exp.get("title",   ""))),
            "organization":   safe_str(exp.get("organization", exp.get("company", ""))),
            "start_year":     sy,
            "end_year":       ey,
            "duration_years": duration,
        })

    career_progression = "Lateral Movement"
    if len(roles) >= 2:
        scores = [_seniority_score(r["job_title"]) for r in roles]
        if scores[-1] > scores[0]:
            career_progression = "Upward Progression"
        elif scores[-1] < scores[0]:
            career_progression = "Downward Shift"
        else:
            career_progression = "Lateral Movement"

    interpretation = (
        f"{candidate_name} has {total_roles} role(s) spanning approximately {total_years} year(s) "
        f"of total experience. Average tenure per role: {avg_tenure} year(s). "
        f"Career trajectory: {career_progression}."
    )

    return {
        "total_roles":        total_roles,
        "total_years":        total_years,
        "avg_tenure_years":   avg_tenure,
        "roles":              roles,
        "career_progression": career_progression,
        "interpretation":     interpretation,
    }

#  MODULE 7: STUDENT SUPERVISION ANALYSIS
def analyze_supervision(profile, candidate_name, publications):
    """
    Analyses the candidate's student supervision record.
    Extracts:
      - Number of MS/PhD students supervised as main supervisor
      - Number as co-supervisor
      - Publications co-authored with supervised students
      - Whether candidate is corresponding author in those papers
    supervision data is expected under profile key 'supervision' as a list of dicts.
    Each dict may have: student_name, degree (MS/PhD), role (main/co), graduation_year
    """
    supervision_list = profile.get("supervision", [])

    main_ms    = 0
    main_phd   = 0
    co_ms      = 0
    co_phd     = 0
    student_names = []

    for entry in supervision_list:
        degree = safe_str(entry.get("degree", "")).upper()
        role   = safe_str(entry.get("role", "")).lower()
        name   = safe_str(entry.get("student_name", ""))
        if name:
            student_names.append(name)

        is_main = "main" in role or "primary" in role or "principal" in role
        is_co   = "co" in role

        if "PHD" in degree or "PH.D" in degree or "DOCTORAL" in degree:
            if is_main:
                main_phd += 1
            elif is_co:
                co_phd += 1
            else:
                main_phd += 1  # default to main if role unspecified
        else:
            # default MS
            if is_main:
                main_ms += 1
            elif is_co:
                co_ms += 1
            else:
                main_ms += 1

    # Find publications co-authored with supervised students
    student_pubs = []
    for pub in publications:
        authors_str = safe_str(pub.get("authors", ""))
        author_list = parse_author_list(authors_str)
        matched_students = []
        for sname in student_names:
            if any(is_same_author(sname, a) for a in author_list):
                matched_students.append(sname)
        if matched_students:
            # Determine if candidate is corresponding author
            role = evaluate_authorship_role(candidate_name, authors_str)
            student_pubs.append({
                "title":             safe_str(pub.get("title", "")),
                "year":              safe_str(pub.get("year", "")),
                "venue":             safe_str(pub.get("venue", "")),
                "matched_students":  ", ".join(matched_students),
                "candidate_role":    role,
                "is_corresponding":  "Corresponding" in role or "First" in role,
            })

    total_supervised   = main_ms + main_phd + co_ms + co_phd
    total_student_pubs = len(student_pubs)

    # Build interpretation
    if total_supervised == 0 and not supervision_list:
        interpretation = (
            f"No supervision data found in {candidate_name}'s CV. "
            "The candidate should be asked to provide a list of supervised/co-supervised "
            "MS/PhD students with their graduation years."
        )
    else:
        interpretation = (
            f"{candidate_name} has supervised {main_ms + main_phd} student(s) as main supervisor "
            f"(MS: {main_ms}, PhD: {main_phd}) and {co_ms + co_phd} as co-supervisor "
            f"(MS: {co_ms}, PhD: {co_phd}). "
        )
        if total_student_pubs > 0:
            corresponding_count = sum(1 for p in student_pubs if p["is_corresponding"])
            interpretation += (
                f"{total_student_pubs} publication(s) co-authored with supervised students detected. "
                f"Candidate appears as lead/corresponding author in {corresponding_count} of these. "
            )
        else:
            interpretation += "No co-authored publications with supervised students detected. "

    # Draft email if supervision data missing
    supervision_email = ""
    if not supervision_list:
        supervision_email = (
            f"Subject: Request for Supervision Record\n\n"
            f"Dear {candidate_name},\n\n"
            f"As part of our candidate evaluation process, we require details of any "
            f"MS or PhD students you have supervised or co-supervised. "
            f"Please provide the following information for each student:\n"
            f"  - Student name\n"
            f"  - Degree (MS / PhD)\n"
            f"  - Your role (Main Supervisor / Co-Supervisor)\n"
            f"  - Year of graduation (if completed)\n\n"
            f"Regards,\nHR Team"
        )

    return {
        "main_supervisor_ms":      main_ms,
        "main_supervisor_phd":     main_phd,
        "co_supervisor_ms":        co_ms,
        "co_supervisor_phd":       co_phd,
        "total_supervised":        total_supervised,
        "student_publications":    student_pubs,
        "total_student_pubs":      total_student_pubs,
        "supervision_email":       supervision_email,
        "interpretation":          interpretation,
    }


# MODULE 8: SKILL ALIGNMENT ANALYSIS

def analyze_skill_alignment(skills_list, experience_list, publications, candidate_name, job_description=""):
    """
    Evidence-based skill alignment:
    - Skill-to-experience alignment
    - Skill-to-publication alignment
    - Skill consistency across profile
    - Job relevance (if job_description provided)
    - Evidence classification: strongly / partially / weakly / unsupported
    """
    if not skills_list:
        return {
            "skill_evidence":        [],
            "strongly_evidenced":    [],
            "partially_evidenced":   [],
            "weakly_evidenced":      [],
            "unsupported":           [],
            "job_alignment_score":   0.0,
            "interpretation":        f"{candidate_name} has no skills to evaluate.",
        }

    # Build searchable text blobs
    exp_text = " ".join([
        safe_str(e.get("job_title", "")) + " " +
        safe_str(e.get("organization", "")) + " " +
        safe_str(e.get("description", ""))
        for e in experience_list
    ]).lower()

    pub_text = " ".join([
        safe_str(p.get("title", "")) + " " +
        safe_str(p.get("venue", "")) + " " +
        safe_str(p.get("abstract", ""))
        for p in publications
    ]).lower()

    jd_text = job_description.lower()

    skill_evidence = []
    strongly, partially, weakly, unsupported = [], [], [], []

    for skill in skills_list:
        skill_lower = safe_str(skill).lower()
        in_exp  = skill_lower in exp_text
        in_pub  = skill_lower in pub_text
        in_jd   = skill_lower in jd_text if jd_text else None

        if in_exp and in_pub:
            evidence = "Strongly Evidenced"
            strongly.append(skill)
        elif in_exp or in_pub:
            evidence = "Partially Evidenced"
            partially.append(skill)
        elif exp_text or pub_text:
            # Profile exists but skill not found anywhere
            evidence = "Weakly Evidenced"
            weakly.append(skill)
        else:
            evidence = "Unsupported"
            unsupported.append(skill)

        skill_evidence.append({
            "skill":           skill,
            "in_experience":   in_exp,
            "in_publications": in_pub,
            "in_job_desc":     in_jd,
            "evidence_level":  evidence,
        })

    # Job alignment score
    job_alignment_score = 0.0
    if jd_text and skills_list:
        matched_jd = sum(1 for s in skills_list if safe_str(s).lower() in jd_text)
        job_alignment_score = round(matched_jd / len(skills_list) * 100, 1)

    interpretation = (
        f"Skill alignment analysis for {candidate_name}: "
        f"{len(strongly)} strongly evidenced, {len(partially)} partially evidenced, "
        f"{len(weakly)} weakly evidenced, {len(unsupported)} unsupported. "
    )
    if strongly:
        interpretation += f"Core evidenced skills: {', '.join(strongly[:5])}. "
    if unsupported:
        interpretation += f"Skills lacking evidence: {', '.join(unsupported[:5])}. "
    if jd_text:
        interpretation += f"Job description alignment score: {job_alignment_score}%."

    return {
        "skill_evidence":      skill_evidence,
        "strongly_evidenced":  strongly,
        "partially_evidenced": partially,
        "weakly_evidenced":    weakly,
        "unsupported":         unsupported,
        "job_alignment_score": job_alignment_score,
        "interpretation":      interpretation,
    }

# MODULE 9: TIMELINE CONSISTENCY ANALYSIS (OVERLAP DETECTION)
def analyze_timeline_consistency(education_list, experience_list, candidate_name):
    """
    Detects:
    - Overlaps between education and employment periods
    - Overlaps between multiple concurrent jobs
    - Unexplained professional gaps
    Flags suspicious overlaps vs. legitimate ones (e.g. RA during PhD).
    """
    issues    = []
    warnings  = []
    info_msgs = []

    def to_year_range(start_raw, end_raw):
        sy = parse_year(start_raw)
        ey = parse_year(end_raw) or datetime.now().year
        return sy, ey

    # Build education periods
    edu_periods = []
    for e in education_list:
        sy, ey = to_year_range(e.get("start_year", ""), e.get("end_year", ""))
        if sy:
            edu_periods.append({
                "label":      safe_str(e.get("degree", e.get("level", "Education"))),
                "start_year": sy,
                "end_year":   ey,
                "type":       "education",
            })

    # Build experience periods
    exp_periods = []
    for ex in experience_list:
        sy, ey = to_year_range(
            ex.get("start_date", ex.get("start_year", "")),
            ex.get("end_date",   ex.get("end_year",   ""))
        )
        if sy:
            title = safe_str(ex.get("job_title", ""))
            org   = safe_str(ex.get("organization", ""))
            exp_periods.append({
                "label":      f"{title} at {org}" if org else title,
                "start_year": sy,
                "end_year":   ey,
                "title":      title.lower(),
                "type":       "experience",
            })

    # 1. Education–Employment overlaps
    for edu in edu_periods:
        for exp in exp_periods:
            overlap_start = max(edu["start_year"], exp["start_year"])
            overlap_end   = min(edu["end_year"],   exp["end_year"])
            if overlap_start <= overlap_end:
                overlap_years = overlap_end - overlap_start
                # Classify: RA, teaching, part-time during study = legitimate
                legitimate_keywords = ["research assistant", "teaching assistant", "ra ", "ta ",
                                        "lecturer", "tutor", "intern", "part-time", "part time"]
                is_likely_legit = any(kw in exp["title"] for kw in legitimate_keywords)

                if is_likely_legit or overlap_years <= 1:
                    info_msgs.append(
                        f"Minor/likely legitimate overlap ({overlap_years} yr): "
                        f"'{exp['label']}' overlaps with '{edu['label']}' "
                        f"({overlap_start}–{overlap_end}). Likely part-time or assistantship."
                    )
                else:
                    warnings.append(
                        f"Overlap detected ({overlap_years} yr): "
                        f"'{exp['label']}' overlaps with '{edu['label']}' "
                        f"({overlap_start}–{overlap_end}). "
                        f"Full-time employment during full-time study warrants clarification."
                    )

    # 2. Job–Job overlaps
    for i in range(len(exp_periods)):
        for j in range(i + 1, len(exp_periods)):
            a = exp_periods[i]
            b = exp_periods[j]
            overlap_start = max(a["start_year"], b["start_year"])
            overlap_end   = min(a["end_year"],   b["end_year"])
            if overlap_start <= overlap_end:
                overlap_years = overlap_end - overlap_start
                if overlap_years <= 1:
                    info_msgs.append(
                        f"Minor job overlap ({overlap_years} yr): "
                        f"'{a['label']}' and '{b['label']}' "
                        f"({overlap_start}–{overlap_end}). May indicate transition period."
                    )
                else:
                    issues.append(
                        f"Concurrent jobs detected ({overlap_years} yr): "
                        f"'{a['label']}' and '{b['label']}' "
                        f"({overlap_start}–{overlap_end}). Candidate may have held dual roles."
                    )

    # 3. Professional gaps (after last education, between jobs)
    all_sorted = sorted(exp_periods, key=lambda x: x["start_year"])
    for i in range(1, len(all_sorted)):
        prev_end   = all_sorted[i - 1]["end_year"]
        curr_start = all_sorted[i]["start_year"]
        gap = curr_start - prev_end
        if gap > 1:
            # Check if gap is covered by education
            covered = any(
                e["start_year"] <= prev_end and e["end_year"] >= curr_start
                for e in edu_periods
            )
            if covered:
                info_msgs.append(
                    f"Professional gap of {gap} yr between '{all_sorted[i-1]['label']}' "
                    f"and '{all_sorted[i]['label']}' appears covered by education."
                )
            else:
                warnings.append(
                    f"Unexplained professional gap of {gap} yr between "
                    f"'{all_sorted[i-1]['label']}' and '{all_sorted[i]['label']}' "
                    f"({prev_end}–{curr_start})."
                )

    # Build summary interpretation
    if not issues and not warnings:
        overall = f"{candidate_name}'s career timeline appears consistent with no major overlaps or gaps."
    else:
        overall = (
            f"{candidate_name}'s timeline has {len(issues)} concern(s) and "
            f"{len(warnings)} warning(s) requiring clarification. "
        )
        if issues:
            overall += f"Concerns: {issues[0]} "
        if warnings:
            overall += f"Warnings: {warnings[0]}"

    return {
        "issues":             issues,
        "warnings":           warnings,
        "info":               info_msgs,
        "total_issues":       len(issues),
        "total_warnings":     len(warnings),
        "overall_assessment": overall,
    }


# MODULE 10: CANDIDATE SUMMARY GENERATION

def generate_candidate_summary(row, supervision_result, skill_alignment_result, timeline_result):
    """
    Generates a concise candidate summary highlighting:
    - Key strengths
    - Key concerns
    - Suitability assessment
    - Overall profile interpretation
    """
    name = safe_str(row.get("candidate_name", row.get("file_name", "Candidate")))

    strengths = []
    concerns  = []

    # Education strengths/concerns
    highest = safe_str(row.get("highest_qualification", ""))
    if "PhD" in highest:
        strengths.append("Holds a PhD qualification")
    elif "Postgraduate" in highest:
        strengths.append("Holds a postgraduate (MS/MPhil) qualification")
    if "Improving" in safe_str(row.get("academic_progression", "")):
        strengths.append("Consistently improving academic performance")
    if row.get("detected_gaps", ""):
        concerns.append(f"Educational gaps detected: {safe_str(row['detected_gaps'])[:80]}...")

    # Research strengths/concerns
    total_pubs = int(row.get("total_publications", 0) or 0)
    if total_pubs > 10:
        strengths.append(f"Strong publication record ({total_pubs} publications)")
    elif total_pubs > 5:
        strengths.append(f"Moderate publication record ({total_pubs} publications)")
    elif total_pubs == 0:
        concerns.append("No documented publications")

    res_interp = safe_str(row.get("research_interpretation", ""))
    if "Q1" in res_interp or "A*" in res_interp:
        strengths.append("Publications in high-quality Q1 journals or A* conferences")

    # Topic diversity
    var_label = safe_str(row.get("research_variability_label", ""))
    if var_label:
        strengths.append(f"Research profile: {var_label}")

    # Collaboration
    coauthors = int(row.get("total_unique_coauthors", 0) or 0)
    if coauthors > 10:
        strengths.append(f"Broad collaboration network ({coauthors} unique co-authors)")

    # Books & Patents
    if int(row.get("total_books", 0) or 0) > 0:
        strengths.append(f"{row['total_books']} book(s) authored")
    if int(row.get("total_patents", 0) or 0) > 0:
        strengths.append(f"{row['total_patents']} patent(s) filed — applied research output")

    # Skills
    unique_skills = int(row.get("unique_skills", 0) or 0)
    if unique_skills > 15:
        strengths.append(f"Broad skill set ({unique_skills} unique skills)")
    elif unique_skills < 5:
        concerns.append("Limited documented skills")

    # Skill alignment
    unsupported = skill_alignment_result.get("unsupported", [])
    strongly    = skill_alignment_result.get("strongly_evidenced", [])
    if len(strongly) > 0:
        strengths.append(f"{len(strongly)} skill(s) strongly evidenced by experience and publications")
    if len(unsupported) > 3:
        concerns.append(f"{len(unsupported)} claimed skill(s) lack supporting evidence in the profile")

    # Experience
    exp_years = int(row.get("experience_years", 0) or 0)
    if exp_years >= 10:
        strengths.append(f"Extensive professional experience ({exp_years} years)")
    elif exp_years >= 5:
        strengths.append(f"Solid professional experience ({exp_years} years)")
    elif exp_years == 0:
        concerns.append("No documented professional experience")

    prog = safe_str(row.get("career_progression", ""))
    if prog == "Upward Progression":
        strengths.append("Clear upward career progression")
    elif prog == "Downward Shift":
        concerns.append("Downward career trajectory detected")

    # Supervision
    total_supervised = supervision_result.get("total_supervised", 0)
    if total_supervised > 0:
        strengths.append(f"Supervised {total_supervised} MS/PhD student(s)")
    if not supervision_result.get("supervision_email", "") == "":
        concerns.append("Supervision record not provided in CV — follow-up email drafted")

    # Timeline
    timeline_issues   = timeline_result.get("total_issues", 0)
    timeline_warnings = timeline_result.get("total_warnings", 0)
    if timeline_issues > 0:
        concerns.append(f"{timeline_issues} timeline inconsistency/inconsistencies detected")
    if timeline_warnings > 0:
        concerns.append(f"{timeline_warnings} timeline warning(s) requiring clarification")

    # Final score
    final_score = float(row.get("final_score", 0) or 0)
    if final_score >= 70:
        suitability = "Strong Candidate — Highly Recommended for Interview"
    elif final_score >= 50:
        suitability = "Moderate Candidate — Recommended with Reservations"
    elif final_score >= 30:
        suitability = "Weak Candidate — Significant Gaps Identified"
    else:
        suitability = "Insufficient Profile Data for Full Assessment"

    summary = {
        "candidate_name": name,
        "suitability":    suitability,
        "final_score":    final_score,
        "strengths":      strengths,
        "concerns":       concerns,
        "strengths_text": "; ".join(strengths) if strengths else "None identified",
        "concerns_text":  "; ".join(concerns)  if concerns  else "None identified",
        "overall_summary": (
            f"{name} — Score: {final_score}/100. Suitability: {suitability}. "
            f"Key strengths: {'; '.join(strengths[:3]) if strengths else 'None'}. "
            f"Key concerns: {'; '.join(concerns[:3]) if concerns else 'None'}."
        ),
    }
    return summary


#  ORIGINAL HELPER FUNCTIONS  
def normalize_marks(marks_str):
    if not marks_str:
        return None, None
    marks_str   = safe_str(marks_str).lower()
    cgpa_match  = re.search(r'([\d\.]+)\s*/\s*([45]\.0)', marks_str)
    if cgpa_match:
        obtained = float(cgpa_match.group(1))
        scale    = float(cgpa_match.group(2))
        return obtained, round((obtained / scale) * 100, 2)
    cgpa_single = re.search(r'^([1-4]\.\d{1,2})$', marks_str)
    if cgpa_single:
        obtained = float(cgpa_single.group(1))
        return obtained, round((obtained / 4.0) * 100, 2)
    percent_match = re.search(r'([\d\.]+)\s*%', marks_str)
    if percent_match:
        val = float(percent_match.group(1))
        return val, val
    fraction_match = re.search(r'(\d+)\s*/\s*(\d+)', marks_str)
    if fraction_match:
        obtained = float(fraction_match.group(1))
        total    = float(fraction_match.group(2))
        if total > 0:
            return obtained, round((obtained / total) * 100, 2)
    return None, None


def get_institution_ranking(institution):
    if not institution:
        return "Unknown"
    inst_lower = safe_str(institution).lower()
    for key, rank in THE_QS_RANKINGS.items():
        if key in inst_lower:
            return rank
    return "Ranking Unavailable"


def parse_year(year_str):
    try:
        matches = re.findall(r'\d{4}', str(year_str))
        if matches:
            return int(matches[-1])
    except:
        pass
    return None


def analyze_gaps(education_list, experience_list):
    valid_edu = []
    for edu in education_list:
        sy = parse_year(edu.get('start_year'))
        ey = parse_year(edu.get('end_year'))
        if sy or ey:
            valid_edu.append({
                'level':      edu.get('level', 'Unknown'),
                'start_year': sy if sy else ey,
                'end_year':   ey if ey else sy,
                'raw':        edu,
            })
    valid_edu.sort(key=lambda x: x['end_year'] if x['end_year'] else 0)

    gaps = []
    for i in range(1, len(valid_edu)):
        prev = valid_edu[i - 1]
        curr = valid_edu[i]
        if prev['end_year'] and curr['start_year']:
            gap_years = curr['start_year'] - prev['end_year']
            if gap_years > 1:
                justified     = False
                justification = []
                for exp in experience_list:
                    exp_sy = parse_year(exp.get('start_date'))
                    if exp_sy and prev['end_year'] <= exp_sy <= curr['start_year']:
                        justified = True
                        justification.append(
                            f"{safe_str(exp.get('job_title','Job'))} at {safe_str(exp.get('organization','Org'))}"
                        )
                gaps.append({
                    'between':               f"{prev['level']} and {curr['level']}",
                    'duration_years':        gap_years,
                    'justified':             justified,
                    'justification_details': ", ".join(justification) if justified else "Unexplained gap",
                })
    return gaps


def evaluate_progression(education_list):
    scores          = []
    specializations = []
    for edu in education_list:
        _, norm = normalize_marks(edu.get('marks_or_cgpa', ''))
        sy      = parse_year(edu.get('start_year'))
        spec    = safe_str(edu.get('specialization', '')).lower()
        if spec:
            specializations.append(spec)
        if norm and sy:
            scores.append((sy, norm, edu.get('level', 'Unknown')))
    scores.sort(key=lambda x: x[0])

    progression_status = "Insufficient data to determine progression."
    if len(scores) >= 2:
        trends = []
        for i in range(1, len(scores)):
            diff = scores[i][1] - scores[i - 1][1]
            if diff > 5:    trends.append("Improving")
            elif diff < -5: trends.append("Declining")
            else:           trends.append("Consistent")
        if all(t == "Improving"   for t in trends): progression_status = "Consistently Improving"
        elif all(t == "Declining"  for t in trends): progression_status = "Consistently Declining"
        elif all(t == "Consistent" for t in trends): progression_status = "Consistent Academic Performance"
        else:                                        progression_status = "Mixed Academic Progression"

    spec_consistency = "Consistent Specialization"
    if len(specializations) > 1:
        stop_words = {'of', 'in', 'and', 'the', 'engineering', 'science', 'sciences', 'arts', 'management'}
        w1 = set(re.findall(r'\w+', specializations[-1])) - stop_words
        w2 = set(re.findall(r'\w+', specializations[-2])) - stop_words
        if w1 and w2 and not w1.intersection(w2):
            spec_consistency = "Shift in Specialization"

    return progression_status, spec_consistency


def interpret_educational_strength(education_list, gaps, progression_status, spec_consistency, enriched_education):
    levels   = [safe_str(e.get('level', '')).upper() for e in education_list]
    highest  = "Unknown"
    bs_count = sum(1 for e in education_list if "BS"      in safe_str(e.get('degree', '')).upper()
                                             or "BACHELOR" in safe_str(e.get('degree', '')).upper())
    ms_count = sum(1 for e in education_list if "MS"     in safe_str(e.get('degree', '')).upper()
                                             or "MASTER"  in safe_str(e.get('degree', '')).upper())

    has_bsc = any(re.search(r'\bbsc\b', safe_str(e.get('degree', '')).lower()) for e in education_list)
    has_msc = any(re.search(r'\bmsc\b', safe_str(e.get('degree', '')).lower()) for e in education_list)
    pathway = "14-year BSc + 16-year MSc Sequence" if (has_bsc and has_msc and bs_count >= 1 and ms_count >= 1) \
              else ("Direct 16-year BS Sequence" if bs_count > 0 else "Standard")

    if "PHD"    in levels: highest = "PhD"
    elif "PG"   in levels or "MS" in levels or "MPHIL" in levels: highest = "Postgraduate (MS/MPhil)"
    elif "UG"   in levels or "BS" in levels or "BACHELOR" in levels: highest = "Undergraduate (BS/BA)"

    unjustified_gaps = [g for g in gaps if not g['justified']]
    ranked_insts     = [e['ranking'] for e in enriched_education if e['ranking'] not in ["Unknown", "Ranking Unavailable"]]

    interpretation  = f"The candidate's highest identified qualification is {highest} (Pathway: {pathway}). "
    interpretation += f"Academic performance is generally {progression_status} with a {spec_consistency}. "
    interpretation += (f"The candidate attended globally/nationally ranked institutions (e.g., {ranked_insts[0]}). "
                       if ranked_insts else "Institution rankings were mostly unranked or unavailable. ")
    if gaps:
        if not unjustified_gaps:
            interpretation += f"The candidate has {len(gaps)} educational gap(s), all justified by professional experience. "
        else:
            interpretation += f"The candidate has {len(unjustified_gaps)} unexplained educational gap(s). "
    else:
        interpretation += "There are no significant gaps in the educational timeline. "

    return interpretation, highest


def evaluate_authorship_role(candidate_name, authors_string):
    if not candidate_name or not authors_string:
        return "Unknown"
    candidate_parts = safe_str(candidate_name).lower().split()
    authors         = [a.strip() for a in safe_str(authors_string).lower().split(',')]
    candidate_pos   = -1
    for i, author in enumerate(authors):
        if any(part in author for part in candidate_parts if len(part) > 2):
            candidate_pos = i
            break
    if candidate_pos == -1:
        return "Unlisted / Unknown"
    is_first         = (candidate_pos == 0)
    is_corresponding = ('*' in authors[candidate_pos] or
                        (candidate_pos == len(authors) - 1 and len(authors) > 2))
    if is_first and is_corresponding: return "Both First and Corresponding Author"
    if is_first:                       return "First Author"
    if is_corresponding:               return "Corresponding Author"
    return "Co-author"


def analyze_journal(pub, candidate_name):
    venue  = safe_str(pub.get('venue', '')).lower()
    issn   = pub.get('issn', '')
    j_data = {"wos": False, "scopus": False, "quartile": "Unranked", "if": None}
    for k, v in MOCK_JOURNALS.items():
        if k in venue:
            j_data = v
            break
    legitimacy     = "Verified (via ISSN)" if issn else ("Verified (by Name)" if j_data["wos"] else "Unverified")
    role           = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    quality_interp = f"Published in a {j_data['quartile']} journal"
    if j_data['wos']:     quality_interp += f" (WoS Indexed, IF: {j_data['if']})"
    elif j_data['scopus']:quality_interp += " (Scopus Indexed)"
    else:                 quality_interp += " (Unindexed / Unknown standing)"
    return {
        "title": safe_str(pub.get('title','')), "venue": safe_str(pub.get('venue','')),
        "year": safe_str(pub.get('year','')), "issn": issn, "legitimacy": legitimacy,
        "wos_indexed": j_data["wos"], "scopus_indexed": j_data["scopus"] or j_data["wos"],
        "quartile": j_data["quartile"], "impact_factor": j_data["if"],
        "authorship_role": role, "quality_interpretation": quality_interp,
    }


def analyze_conference(pub, candidate_name):
    venue      = safe_str(pub.get('venue', '')).lower()
    publisher  = safe_str(pub.get('publisher', '')).lower()
    a_star     = any(k in venue for k, v in MOCK_CONFERENCES.items() if v == "A*")
    mat_match  = re.search(r'(\d+(?:st|nd|rd|th))\s', safe_str(pub.get('venue', '')))
    maturity   = mat_match.group(1) + " edition" if mat_match else "Unknown"
    indexed_in = ("IEEE Xplore"        if "ieee"    in publisher or "ieee"   in venue
                  else "ACM Digital Library" if "acm"     in publisher
                  else "Springer"           if "springer" in publisher
                  else "Scopus"             if "scopus"   in publisher
                  else "Unverified")
    role           = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    quality_interp = ("Top-tier A* Conference" if a_star else "Standard Conference")
    quality_interp += f" ({maturity})" if maturity != "Unknown" else " (Maturity Unknown)"
    quality_interp += f", Indexed in {indexed_in}" if indexed_in != "Unverified" else ", Indexing Unknown"
    return {
        "title": safe_str(pub.get('title','')), "venue": safe_str(pub.get('venue','')),
        "year": safe_str(pub.get('year','')), "publisher": safe_str(pub.get('publisher','')),
        "a_star_status": a_star, "maturity": maturity, "indexed_in": indexed_in,
        "authorship_role": role, "quality_interpretation": quality_interp,
    }


def interpret_research_profile(journal_results, conf_results):
    total = len(journal_results) + len(conf_results)
    if total == 0:
        return "Candidate has no documented research publications."
    q1_count    = sum(1 for j in journal_results if j['quartile'] == 'Q1')
    wos_count   = sum(1 for j in journal_results if j['wos_indexed'])
    astar_count = sum(1 for c in conf_results   if c['a_star_status'])
    first_count = sum(1 for p in (journal_results + conf_results) if "First" in p['authorship_role'])
    interp      = f"Candidate has {total} publications ({len(journal_results)} journals, {len(conf_results)} conferences). "
    if q1_count > 0 or astar_count > 0:
        interp += f"Strong quality profile with {q1_count} Q1 journals and {astar_count} A* conferences. "
    elif wos_count > 0:
        interp += f"Solid visibility with {wos_count} WoS-indexed journals. "
    else:
        interp += "Publications are primarily in lower-tier or unverified venues. "
    interp += (f"Demonstrates research leadership (First author in {first_count} papers)."
               if first_count > 0 else "Primarily contributes as a co-author.")
    return interp


#  SCORING FUNCTIONS
def score_education(highest_qualification, progression, gaps):
    score = 50
    if "PhD"           in highest_qualification: score += 30
    elif "Postgraduate" in highest_qualification: score += 20
    elif "Undergraduate"in highest_qualification: score += 10
    if "Improving" in progression: score += 10
    elif "Declining"in progression: score -= 10
    if gaps: score -= 10
    return max(0, min(score, 100))


def score_research(journal_count, conference_count, interpretation):
    score = (journal_count * 10) + (conference_count * 5)
    if "Q1" in interpretation or "A*" in interpretation:
        score += 30
    return max(0, min(score, 100))


def score_topic_diversity(diversity_score):
    return int(diversity_score * 100)


def score_collaboration(total_coauthors, avg_authors):
    score = total_coauthors * 2 + avg_authors * 5
    return max(0, min(int(score), 100))


def score_books(total_books):
    return min(total_books * 15, 100)


def score_patents(total_patents):
    return min(total_patents * 20, 100)


def score_skills(total_skills, unique_skills):
    score = min(unique_skills * 3, 60)
    if total_skills >= 15:   score += 40
    elif total_skills >= 10: score += 25
    elif total_skills >= 5:  score += 10
    return max(0, min(int(score), 100))


def score_experience(total_years, total_roles):
    score  = min(total_years * 5, 60)
    score += min(total_roles * 5, 40)
    return max(0, min(int(score), 100))


def compute_final_score(row):
    edu    = score_education(row["highest_qualification"],
                             row["academic_progression"],
                             row["detected_gaps"])
    res    = score_research(row["journal_count"],
                            row["conference_count"],
                            row["research_interpretation"])
    topic  = score_topic_diversity(row["research_diversity_score"])
    coll   = score_collaboration(row["total_unique_coauthors"],
                                 row["avg_authors_per_paper"])
    books  = score_books(row["total_books"])
    pats   = score_patents(row["total_patents"])
    skills = score_skills(row.get("total_skills",  0),
                          row.get("unique_skills",  0))
    exp    = score_experience(row.get("experience_years", 0),
                              row.get("total_roles",      0))

    final = (
        0.20 * edu   +
        0.25 * res   +
        0.10 * topic +
        0.10 * coll  +
        0.05 * books +
        0.05 * pats  +
        0.15 * skills +
        0.10 * exp
    )
    return round(final, 2)


#  MAIN PIPELINE
def run_pipeline(cvs_folder, output_dir):
    cvs = load_cvs_from_folder(cvs_folder)
    if not cvs:
        print("No CVs found")
        return [], [], [], [], [], [], [], [], [], [], [], [], []

    os.makedirs(output_dir, exist_ok=True)

    all_profiles     = []
    analysis_results = []

    global_edu              = []
    global_journals         = []
    global_confs            = []
    global_topic_rows       = []
    global_coauthor_rows    = []
    global_book_rows        = []
    global_patent_rows      = []
    global_skills_rows      = []
    global_exp_rows         = []
    global_supervision_rows = []   # NEW
    global_skill_align_rows = []   # NEW
    global_timeline_rows    = []   # NEW
    global_summaries        = []   # NEW

    for cv in cvs:
        fname = cv['file_name']
        print(f"\n── Processing: {fname} ──")
        profile          = extract_full_profile(cv['text'])
        profile['file_name'] = fname
        all_profiles.append(profile)

        candidate_name = safe_str(profile.get("name", fname))
        education      = profile.get("education",    [])
        experience     = profile.get("experience",   [])
        publications   = profile.get("publications", [])
        books          = profile.get("books",        [])
        patents        = profile.get("patents",       [])
        skills         = profile.get("skills",       [])

        # Educational Analysis 
        enriched_education = []
        for edu in education:
            obtained, normalized = normalize_marks(edu.get('marks_or_cgpa', ''))
            ranking = get_institution_ranking(edu.get('institution', ''))
            enriched_education.append({
                "file_name":                fname,
                "degree":                   safe_str(edu.get('degree', '')),
                "level":                    safe_str(edu.get('level', '')),
                "specialization":           safe_str(edu.get('specialization', '')),
                "institution":              safe_str(edu.get('institution', '')),
                "ranking":                  ranking,
                "start_year":               safe_str(edu.get('start_year', '')),
                "end_year":                 safe_str(edu.get('end_year', '')),
                "marks_original":           safe_str(edu.get('marks_or_cgpa', '')),
                "marks_normalized_percent": normalized,
            })
        global_edu.extend(enriched_education)

        gaps = analyze_gaps(education, experience)
        progression_status, spec_consistency = evaluate_progression(education)
        interpretation, highest_qual = interpret_educational_strength(
            education, gaps, progression_status, spec_consistency, enriched_education)
        gaps_str = "; ".join([
            f"Gap of {g['duration_years']} yrs between {g['between']} ({g['justification_details']})"
            for g in gaps
        ])

        # Research Profile Analysis 
        j_res, c_res = [], []
        for pub in publications:
            pub_type  = safe_str(pub.get("type",  "")).lower()
            venue_str = safe_str(pub.get("venue", "")).lower()
            if "journal" in pub_type or "journal" in venue_str or "transactions" in venue_str:
                j = analyze_journal(pub, candidate_name)
                j['file_name'] = fname
                j_res.append(j)
            else:
                c = analyze_conference(pub, candidate_name)
                c['file_name'] = fname
                c_res.append(c)
        global_journals.extend(j_res)
        global_confs.extend(c_res)
        research_interp = interpret_research_profile(j_res, c_res)

        #  Topic Variability 
        print(f"  → Running Topic Variability Analysis...")
        classified_pubs    = classify_publication_topics(publications)
        variability_result = compute_topic_variability(classified_pubs)
        topic_interp       = interpret_topic_variability(variability_result, candidate_name)

        for cp in classified_pubs:
            global_topic_rows.append({
                "file_name":     fname,
                "candidate":     candidate_name,
                "title":         cp["title"],
                "year":          cp["year"],
                "venue":         cp["venue"],
                "primary_theme": cp["primary_theme"],
                "all_themes":    ", ".join(cp["matched_themes"]),
            })

        # Co-Author Analysis 
        print(f"  → Running Co-Author Analysis...")
        coauthor_result = analyze_coauthors(publications, candidate_name)
        for pp in coauthor_result["per_paper_details"]:
            global_coauthor_rows.append({
                "file_name": fname,
                "candidate": candidate_name,
                "title":     pp["title"],
                "year":      pp["year"],
                "coauthors": pp["coauthors"],
                "team_size": pp["team_size"],
            })

        # Books Analysis 
        print(f"  → Running Books Analysis...")
        enriched_books, books_summary = analyze_books(books, candidate_name)
        for book in enriched_books:
            book["file_name"] = fname
            book["candidate"] = candidate_name
            global_book_rows.append(book)

        # Patents Analysis
        print(f"  → Running Patents Analysis...")
        enriched_patents, patents_summary = analyze_patents(patents, candidate_name)
        for patent in enriched_patents:
            patent["file_name"] = fname
            patent["candidate"] = candidate_name
            global_patent_rows.append(patent)

        # Skills Analysis 
        print(f"  → Running Skills Analysis...")
        skills_result = analyze_skills(skills, candidate_name)
        for skill, freq in skills_result["top_skills"]:
            global_skills_rows.append({
                "file_name": fname,
                "candidate": candidate_name,
                "skill":     skill,
                "frequency": freq,
            })
        for cat, cnt in skills_result["skill_categories"].items():
            global_skills_rows.append({
                "file_name": fname,
                "candidate": candidate_name,
                "skill":     f"[CATEGORY] {cat}",
                "frequency": cnt,
            })

        # Experience Analysis 
        print(f"  → Running Experience Analysis...")
        exp_result = analyze_experience(experience, candidate_name)
        for role in exp_result["roles"]:
            global_exp_rows.append({
                "file_name":      fname,
                "candidate":      candidate_name,
                "job_title":      role["job_title"],
                "organization":   role["organization"],
                "start_year":     role["start_year"],
                "end_year":       role["end_year"],
                "duration_years": role["duration_years"],
            })

        #  Student Supervision Analysis 
        print(f"  → Running Supervision Analysis...")
        supervision_result = analyze_supervision(profile, candidate_name, publications)
        for sp in supervision_result["student_publications"]:
            global_supervision_rows.append({
                "file_name":        fname,
                "candidate":        candidate_name,
                "pub_title":        sp["title"],
                "year":             sp["year"],
                "venue":            sp["venue"],
                "matched_students": sp["matched_students"],
                "candidate_role":   sp["candidate_role"],
                "is_corresponding": sp["is_corresponding"],
            })
        # Also store summary row
        global_supervision_rows.append({
            "file_name":           fname,
            "candidate":           candidate_name,
            "pub_title":           "[SUMMARY]",
            "year":                "",
            "venue":               "",
            "matched_students":    f"Main MS:{supervision_result['main_supervisor_ms']} PhD:{supervision_result['main_supervisor_phd']} | Co MS:{supervision_result['co_supervisor_ms']} PhD:{supervision_result['co_supervisor_phd']}",
            "candidate_role":      supervision_result["interpretation"],
            "is_corresponding":    "",
        })

        #  Skill Alignment Analysis 
        print(f"  → Running Skill Alignment Analysis...")
        skill_alignment_result = analyze_skill_alignment(
            skills, experience, publications, candidate_name, job_description=""
        )
        for se in skill_alignment_result["skill_evidence"]:
            global_skill_align_rows.append({
                "file_name":       fname,
                "candidate":       candidate_name,
                "skill":           se["skill"],
                "in_experience":   se["in_experience"],
                "in_publications": se["in_publications"],
                "in_job_desc":     se["in_job_desc"],
                "evidence_level":  se["evidence_level"],
            })

        # Timeline Consistency Analysis
        print(f"  → Running Timeline Consistency Analysis...")
        timeline_result = analyze_timeline_consistency(education, experience, candidate_name)
        for issue in timeline_result["issues"]:
            global_timeline_rows.append({
                "file_name": fname, "candidate": candidate_name,
                "severity": "Issue", "description": issue,
            })
        for warning in timeline_result["warnings"]:
            global_timeline_rows.append({
                "file_name": fname, "candidate": candidate_name,
                "severity": "Warning", "description": warning,
            })
        for info in timeline_result["info"]:
            global_timeline_rows.append({
                "file_name": fname, "candidate": candidate_name,
                "severity": "Info", "description": info,
            })

        #  Aggregate result 
        analysis_results.append({
            "file_name":                  fname,
            "candidate_name":             candidate_name,
            # Education
            "highest_qualification":      highest_qual,
            "academic_progression":       progression_status,
            "specialization_consistency": spec_consistency,
            "detected_gaps":              gaps_str,
            "edu_interpretation":         interpretation,
            # Research
            "research_interpretation":    research_interp,
            "total_publications":         len(publications),
            "journal_count":              len(j_res),
            "conference_count":           len(c_res),
            # Topic Variability
            "dominant_research_topic":    variability_result["dominant_topic"],
            "research_diversity_score":   variability_result["diversity_score"],
            "research_variability_label": variability_result["variability_label"],
            "topic_distribution":         json.dumps(variability_result["theme_distribution"]),
            "topic_interpretation":       topic_interp,
            # Co-Author
            "total_unique_coauthors":     coauthor_result["total_unique_coauthors"],
            "avg_authors_per_paper":      coauthor_result["avg_authors_per_paper"],
            "solo_papers":                coauthor_result["solo_papers"],
            "frequent_collaborators":     str(coauthor_result["frequent_collaborators"][:5]),
            "coauthor_interpretation":    coauthor_result["interpretation"],
            # Books
            "total_books":                books_summary["total_books"],
            "books_interpretation":       books_summary["interpretation"],
            # Patents
            "total_patents":              patents_summary["total_patents"],
            "patents_interpretation":     patents_summary["interpretation"],
            # Skills
            "total_skills":               skills_result["total_skills"],
            "unique_skills":              skills_result["unique_skills"],
            "top_skills":                 str(skills_result["top_skills"][:5]),
            "skill_categories":           json.dumps(skills_result["skill_categories"]),
            "skills_interpretation":      skills_result["interpretation"],
            # Experience
            "experience_years":           exp_result["total_years"],
            "total_roles":                exp_result["total_roles"],
            "avg_tenure_years":           exp_result["avg_tenure_years"],
            "career_progression":         exp_result["career_progression"],
            "experience_interpretation":  exp_result["interpretation"],
            # NEW: Supervision
            "supervision_main_ms":        supervision_result["main_supervisor_ms"],
            "supervision_main_phd":       supervision_result["main_supervisor_phd"],
            "supervision_co_ms":          supervision_result["co_supervisor_ms"],
            "supervision_co_phd":         supervision_result["co_supervisor_phd"],
            "total_supervised":           supervision_result["total_supervised"],
            "total_student_pubs":         supervision_result["total_student_pubs"],
            "supervision_interpretation": supervision_result["interpretation"],
            "supervision_email":          supervision_result["supervision_email"],
            # NEW: Skill Alignment
            "skills_strongly_evidenced":  len(skill_alignment_result["strongly_evidenced"]),
            "skills_partially_evidenced": len(skill_alignment_result["partially_evidenced"]),
            "skills_weakly_evidenced":    len(skill_alignment_result["weakly_evidenced"]),
            "skills_unsupported":         len(skill_alignment_result["unsupported"]),
            "skill_alignment_interpretation": skill_alignment_result["interpretation"],
            # NEW: Timeline
            "timeline_issues":            timeline_result["total_issues"],
            "timeline_warnings":          timeline_result["total_warnings"],
            "timeline_assessment":        timeline_result["overall_assessment"],
        })

    # Save all CSVs 
    def save_df(data, filename, default_cols):
        path = os.path.join(output_dir, filename)
        df   = pd.DataFrame(data) if data else pd.DataFrame(columns=default_cols)
        df.to_csv(path, index=False)
        print(f"  Saved → {filename}  ({len(df)} rows)")

    save_df(analysis_results,       "m3_overall_analysis.csv",    ["file_name"])
    save_df(global_edu,             "m3_educational_records.csv", ["file_name"])
    save_df(global_journals,        "m3_journal_analysis.csv",    ["file_name"])
    save_df(global_confs,           "m3_conference_analysis.csv", ["file_name"])
    save_df(global_topic_rows,      "m3_topic_variability.csv",   ["file_name", "candidate", "title", "primary_theme"])
    save_df(global_coauthor_rows,   "m3_coauthor_details.csv",    ["file_name", "candidate", "title", "coauthors"])
    save_df(global_book_rows,       "m3_books_analysis.csv",      ["file_name", "candidate", "title"])
    save_df(global_patent_rows,     "m3_patents_analysis.csv",    ["file_name", "candidate", "patent_number"])
    save_df(global_skills_rows,     "m3_skills_analysis.csv",     ["file_name", "candidate", "skill", "frequency"])
    save_df(global_exp_rows,        "m3_experience_analysis.csv", ["file_name", "candidate", "job_title"])
    save_df(global_supervision_rows,"m3_supervision_analysis.csv",["file_name", "candidate", "pub_title"])   # NEW
    save_df(global_skill_align_rows,"m3_skill_alignment.csv",     ["file_name", "candidate", "skill", "evidence_level"])  # NEW
    save_df(global_timeline_rows,   "m3_timeline_consistency.csv",["file_name", "candidate", "severity", "description"])  # NEW

    # Candidate Ranking
    print("\nGenerating Candidate Rankings...")
    df_rank = pd.DataFrame(analysis_results)
    if not df_rank.empty:
        df_rank["final_score"] = df_rank.apply(compute_final_score, axis=1)
        df_rank = df_rank.sort_values(by="final_score", ascending=False)
        df_rank["rank"] = range(1, len(df_rank) + 1)
        ranking_path = os.path.join(output_dir, "m3_candidate_ranking.csv")
        df_rank.to_csv(ranking_path, index=False)
        print(f"  Saved → m3_candidate_ranking.csv ({len(df_rank)} rows)")

    #  Candidate Summaries 
    print("\nGenerating Candidate Summaries...")
    if not df_rank.empty:
        # We need supervision/skill_alignment/timeline per candidate for summary
        # Build lookup dicts keyed by file_name
        supervision_lookup   = {}
        skill_align_lookup   = {}
        timeline_lookup      = {}

        for i, cv in enumerate(cvs):
            fname = cv['file_name']
            profile = all_profiles[i]
            candidate_name = safe_str(profile.get("name", fname))
            education  = profile.get("education",  [])
            experience = profile.get("experience", [])
            publications = profile.get("publications", [])
            skills_l     = profile.get("skills", [])
            supervision_lookup[fname]  = analyze_supervision(profile, candidate_name, publications)
            skill_align_lookup[fname]  = analyze_skill_alignment(skills_l, experience, publications, candidate_name)
            timeline_lookup[fname]     = analyze_timeline_consistency(education, experience, candidate_name)

        for _, row in df_rank.iterrows():
            fname = row["file_name"]
            summary = generate_candidate_summary(
                row,
                supervision_lookup.get(fname, {"total_supervised": 0, "supervision_email": "", "student_publications": []}),
                skill_align_lookup.get(fname, {"strongly_evidenced": [], "unsupported": []}),
                timeline_lookup.get(fname,    {"total_issues": 0, "total_warnings": 0}),
            )
            global_summaries.append(summary)

        save_df(global_summaries, "m3_candidate_summaries.csv", ["candidate_name", "suitability", "final_score"])
        print(f"  Saved → m3_candidate_summaries.csv ({len(global_summaries)} rows)")

    print(f"\nMilestone 3 Analysis complete — outputs saved to {output_dir}")

    return (
        analysis_results,
        global_edu,
        global_journals,
        global_confs,
        global_topic_rows,
        global_coauthor_rows,
        global_book_rows,
        global_patent_rows,
        global_skills_rows,
        global_exp_rows,
        global_supervision_rows,   
        global_skill_align_rows,   
        global_timeline_rows,      
        global_summaries,         
    )