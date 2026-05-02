# # src/milestone3_pipeline.py

# import os
# import json
# import re
# import pandas as pd
# from loader import load_cvs_from_folder
# from parser import extract_full_profile
# from datetime import datetime

# # MOCK RANKINGS DATABASES for Demonstration
# MOCK_JOURNALS = {
#     "ieee transactions on pattern analysis": {"wos": True, "scopus": True, "quartile": "Q1", "if": 24.3},
#     "nature": {"wos": True, "scopus": True, "quartile": "Q1", "if": 64.8},
#     "expert systems with applications": {"wos": True, "scopus": True, "quartile": "Q1", "if": 8.5},
#     "ieee access": {"wos": True, "scopus": True, "quartile": "Q2", "if": 3.4},
# }

# MOCK_CONFERENCES = {
#     "cvpr": "A*",
#     "neurips": "A*",
#     "icml": "A*",
#     "iccv": "A*",
#     "acl": "A*",
#     "emnlp": "A*",
#     "kdd": "A*",
#     "aaai": "A*",
#     "ijcai": "A*"
# }

# THE_QS_RANKINGS = {
#     "massachusetts institute of technology": "Rank 1 (QS)",
#     "mit": "Rank 1 (QS)",
#     "stanford university": "Rank 2 (QS)",
#     "harvard university": "Rank 4 (QS)",
#     "university of oxford": "Rank 3 (QS)",
#     "university of cambridge": "Rank 5 (QS)",
#     "national university of sciences and technology": "Top 400 (QS)",
#     "nust": "Top 400 (QS)",
#     "lums": "Top 600 (QS)",
#     "lahore university of management sciences": "Top 600 (QS)",
#     "fast nuces": "Top 1000 (QS)",
#     "university of the punjab": "Top 1000 (QS)",
#     "comsats": "Top 800 (QS)",
# }

# def normalize_marks(marks_str):
#     if not marks_str:
#         return None, None
    
#     marks_str = str(marks_str).lower().strip()
    
#     # Check for CGPA (e.g., 3.8/4.0 or 3.8)
#     cgpa_match = re.search(r'([\d\.]+)\s*/\s*([45]\.0)', marks_str)
#     if cgpa_match:
#         obtained = float(cgpa_match.group(1))
#         scale = float(cgpa_match.group(2))
#         normalized = (obtained / scale) * 100
#         return obtained, normalized
    
#     # Check for generic CGPA without scale but looks like CGPA
#     cgpa_single = re.search(r'^([1-4]\.\d{1,2})$', marks_str)
#     if cgpa_single:
#         obtained = float(cgpa_single.group(1))
#         normalized = (obtained / 4.0) * 100
#         return obtained, normalized

#     # Check for Percentage
#     percent_match = re.search(r'([\d\.]+)\s*%', marks_str)
#     if percent_match:
#         val = float(percent_match.group(1))
#         return val, val

#     # Check for Marks out of Total (e.g. 850/1100)
#     fraction_match = re.search(r'(\d+)\s*/\s*(\d+)', marks_str)
#     if fraction_match:
#         obtained = float(fraction_match.group(1))
#         total = float(fraction_match.group(2))
#         if total > 0:
#             normalized = (obtained / total) * 100
#             return obtained, normalized

#     return None, None

# def get_institution_ranking(institution):
#     if not institution:
#         return "Unknown"
    
#     inst_lower = institution.lower()
#     for key, rank in THE_QS_RANKINGS.items():
#         if key in inst_lower:
#             return rank
            
#     return "Ranking Unavailable"

# def parse_year(year_str):
#     try:
#         matches = re.findall(r'\d{4}', str(year_str))
#         if matches:
#             return int(matches[-1])
#     except:
#         pass
#     return None

# def analyze_gaps(education_list, experience_list):
#     # Sort education by end_year
#     valid_edu = []
#     for edu in education_list:
#         sy = parse_year(edu.get('start_year'))
#         ey = parse_year(edu.get('end_year'))
#         if sy or ey:
#             valid_edu.append({
#                 'level': edu.get('level', 'Unknown'),
#                 'start_year': sy if sy else ey,
#                 'end_year': ey if ey else sy,
#                 'raw': edu
#             })
            
#     valid_edu.sort(key=lambda x: x['end_year'] if x['end_year'] else 0)
    
#     gaps = []
#     for i in range(1, len(valid_edu)):
#         prev_edu = valid_edu[i-1]
#         curr_edu = valid_edu[i]
        
#         if prev_edu['end_year'] and curr_edu['start_year']:
#             gap_years = curr_edu['start_year'] - prev_edu['end_year']
#             if gap_years > 1:
#                 # Check if gap is justified by experience
#                 justified = False
#                 justification = []
#                 for exp in experience_list:
#                     exp_sy = parse_year(exp.get('start_date'))
#                     exp_ey = parse_year(exp.get('end_date'))
                    
#                     if exp_sy:
#                         # If experience overlaps with the gap
#                         if exp_sy >= prev_edu['end_year'] and exp_sy <= curr_edu['start_year']:
#                             justified = True
#                             justification.append(f"{exp.get('job_title', 'Job')} at {exp.get('organization', 'Org')}")
                
#                 gaps.append({
#                     'between': f"{prev_edu['level']} and {curr_edu['level']}",
#                     'duration_years': gap_years,
#                     'justified': justified,
#                     'justification_details': ", ".join(justification) if justified else "Unexplained gap"
#                 })
                
#     return gaps

# def evaluate_progression(education_list):
#     scores = []
#     specializations = []
#     for edu in education_list:
#         _, norm = normalize_marks(edu.get('marks_or_cgpa', ''))
#         sy = parse_year(edu.get('start_year'))
#         spec = str(edu.get('specialization', '')).strip().lower()
#         if spec:
#             specializations.append(spec)
#         if norm and sy:
#             scores.append((sy, norm, edu.get('level', 'Unknown')))
            
#     scores.sort(key=lambda x: x[0])
    
#     progression_status = "Insufficient data to determine progression."
#     if len(scores) >= 2:
#         trends = []
#         for i in range(1, len(scores)):
#             diff = scores[i][1] - scores[i-1][1]
#             if diff > 5:
#                 trends.append("Improving")
#             elif diff < -5:
#                 trends.append("Declining")
#             else:
#                 trends.append("Consistent")
                
#         if all(t == "Improving" for t in trends):
#             progression_status = "Consistently Improving"
#         elif all(t == "Declining" for t in trends):
#             progression_status = "Consistently Declining"
#         elif all(t == "Consistent" for t in trends):
#             progression_status = "Consistent Academic Performance"
#         else:
#             progression_status = "Mixed Academic Progression"

#     # Evaluate Specialization Consistency (very basic keyword overlap check)
#     spec_consistency = "Consistent Specialization"
#     if len(specializations) > 1:
#         # Check if there is some common word among the last two degrees
#         words1 = set(re.findall(r'\w+', specializations[-1]))
#         words2 = set(re.findall(r'\w+', specializations[-2]))
#         # Remove common stop words
#         stop_words = {'of', 'in', 'and', 'the', 'engineering', 'science', 'sciences', 'arts', 'management'}
#         words1 = words1 - stop_words
#         words2 = words2 - stop_words
#         if words1 and words2 and not words1.intersection(words2):
#             spec_consistency = "Shift in Specialization"

#     return progression_status, spec_consistency

# def interpret_educational_strength(education_list, gaps, progression_status, spec_consistency, enriched_education):
#     levels = [str(e.get('level', '')).upper() for e in education_list]
#     highest = "Unknown"
    
#     # Pathway detection
#     pathway = "Standard"
#     bs_count = sum(1 for e in education_list if "BS" in str(e.get('degree', '')).upper() or "BACHELOR" in str(e.get('degree', '')).upper())
#     ms_count = sum(1 for e in education_list if "MS" in str(e.get('degree', '')).upper() or "MASTER" in str(e.get('degree', '')).upper())
    
#     # Very basic 14 vs 16 yr detection (BSc followed by MSc vs BS direct)
#     has_bsc = any(re.search(r'\bbsc\b', str(e.get('degree', '')).lower()) for e in education_list)
#     has_msc = any(re.search(r'\bmsc\b', str(e.get('degree', '')).lower()) for e in education_list)
#     if has_bsc and has_msc and bs_count >= 1 and ms_count >= 1:
#         pathway = "14-year BSc + 16-year MSc Sequence"
#     elif bs_count > 0:
#         pathway = "Direct 16-year BS Sequence"

#     if "PHD" in levels: highest = "PhD"
#     elif "PG" in levels or "MS" in levels or "MPHIL" in levels: highest = "Postgraduate (MS/MPhil)"
#     elif "UG" in levels or "BS" in levels or "BACHELOR" in levels: highest = "Undergraduate (BS/BA)"
    
#     unjustified_gaps = [g for g in gaps if not g['justified']]
    
#     interpretation = f"The candidate's highest identified qualification is {highest} (Pathway: {pathway}). "
#     interpretation += f"Academic performance is generally {progression_status} with a {spec_consistency}. "
    
#     # Quality of Institutions summary
#     ranked_insts = [e['ranking'] for e in enriched_education if e['ranking'] and e['ranking'] not in ["Unknown", "Ranking Unavailable"]]
#     if ranked_insts:
#         interpretation += f"The candidate attended globally/nationally ranked institutions (e.g., {ranked_insts[0]}). "
#     else:
#         interpretation += "Institution rankings were mostly unranked or unavailable. "
    
#     if gaps:
#         if len(unjustified_gaps) == 0:
#             interpretation += f"The candidate has {len(gaps)} educational gap(s), all of which are justified by professional experience. "
#         else:
#             interpretation += f"The candidate has {len(unjustified_gaps)} unexplained educational gap(s). "
#     else:
#         interpretation += "There are no significant gaps in the educational timeline. "
        
#     return interpretation, highest


# # --- RESEARCH PROFILE ANALYSIS MODULE ---

# def evaluate_authorship_role(candidate_name, authors_string):
#     if not candidate_name or not authors_string:
#         return "Unknown"
        
#     candidate_parts = str(candidate_name).lower().split()
#     authors = [a.strip() for a in str(authors_string).lower().split(',')]
    
#     if not authors:
#         return "Unknown"
        
#     # Match candidate in authors list
#     candidate_pos = -1
#     for i, author in enumerate(authors):
#         # basic match: if any part of the candidate name is in the author string
#         if any(part in author for part in candidate_parts if len(part) > 2):
#             candidate_pos = i
#             break
            
#     if candidate_pos == -1:
#         return "Unlisted / Unknown"
        
#     is_first = (candidate_pos == 0)
    
#     # Heuristic for corresponding author: marked with '*' or listed last (common in some fields)
#     is_corresponding = '*' in authors[candidate_pos] or (candidate_pos == len(authors) - 1 and len(authors) > 2)
    
#     if is_first and is_corresponding:
#         return "Both First and Corresponding Author"
#     elif is_first:
#         return "First Author"
#     elif is_corresponding:
#         return "Corresponding Author"
#     else:
#         return "Co-author"

# def analyze_journal(pub, candidate_name):
#     venue = str(pub.get('venue', '')).lower()
#     issn = pub.get('issn', '')
    
#     # Mock Lookup
#     j_data = {"wos": False, "scopus": False, "quartile": "Unranked", "if": None}
#     for k, v in MOCK_JOURNALS.items():
#         if k in venue:
#             j_data = v
#             break
            
#     # If ISSN is present, assume we verified it via a database in a real scenario
#     legitimacy = "Verified (via ISSN)" if issn else ("Verified (by Name)" if j_data["wos"] else "Unverified")
    
#     role = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    
#     quality_interp = f"Published in a {j_data['quartile']} journal"
#     if j_data['wos']: quality_interp += f" (WoS Indexed, IF: {j_data['if']})"
#     elif j_data['scopus']: quality_interp += " (Scopus Indexed)"
#     else: quality_interp += " (Unindexed / Unknown standing)"
    
#     return {
#         "title": pub.get('title', ''),
#         "venue": pub.get('venue', ''),
#         "year": pub.get('year', ''),
#         "issn": issn,
#         "legitimacy": legitimacy,
#         "wos_indexed": j_data["wos"],
#         "scopus_indexed": j_data["scopus"] or j_data["wos"], # Assume WoS is also Scopus for mock
#         "quartile": j_data["quartile"],
#         "impact_factor": j_data["if"],
#         "authorship_role": role,
#         "quality_interpretation": quality_interp
#     }

# def analyze_conference(pub, candidate_name):
#     venue = str(pub.get('venue', '')).lower()
#     publisher = str(pub.get('publisher', '')).lower()
    
#     # A* Status Lookup
#     a_star = False
#     for k, v in MOCK_CONFERENCES.items():
#         if k in venue:
#             a_star = (v == "A*")
#             break
            
#     # Maturity Extraction
#     maturity = "Unknown"
#     mat_match = re.search(r'(\d+(?:st|nd|rd|th))\s', pub.get('venue', ''))
#     if mat_match:
#         maturity = mat_match.group(1) + " edition"
        
#     # Indexing Extraction
#     indexed_in = "Unverified"
#     if "ieee" in publisher or "ieee" in venue: indexed_in = "IEEE Xplore"
#     elif "acm" in publisher: indexed_in = "ACM Digital Library"
#     elif "springer" in publisher: indexed_in = "Springer"
#     elif "scopus" in publisher: indexed_in = "Scopus"
    
#     role = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    
#     quality_interp = "Top-tier A* Conference" if a_star else "Standard Conference"
#     quality_interp += f" ({maturity})" if maturity != "Unknown" else " (Maturity Unknown)"
#     quality_interp += f", Indexed in {indexed_in}" if indexed_in != "Unverified" else ", Indexing Unknown"
    
#     return {
#         "title": pub.get('title', ''),
#         "venue": pub.get('venue', ''),
#         "year": pub.get('year', ''),
#         "publisher": pub.get('publisher', ''),
#         "a_star_status": a_star,
#         "maturity": maturity,
#         "indexed_in": indexed_in,
#         "authorship_role": role,
#         "quality_interpretation": quality_interp
#     }

# def interpret_research_profile(journal_results, conf_results):
#     total_pubs = len(journal_results) + len(conf_results)
#     if total_pubs == 0:
#         return "Candidate has no documented research publications."
        
#     q1_count = sum(1 for j in journal_results if j['quartile'] == 'Q1')
#     wos_count = sum(1 for j in journal_results if j['wos_indexed'])
#     astar_count = sum(1 for c in conf_results if c['a_star_status'])
#     first_author_count = sum(1 for p in (journal_results + conf_results) if "First" in p['authorship_role'])
    
#     interpretation = f"Candidate has {total_pubs} publications ({len(journal_results)} journals, {len(conf_results)} conferences). "
    
#     if q1_count > 0 or astar_count > 0:
#         interpretation += f"Strong quality profile with {q1_count} Q1 journals and {astar_count} A* conferences. "
#     elif wos_count > 0:
#         interpretation += f"Solid visibility with {wos_count} WoS-indexed journals. "
#     else:
#         interpretation += "Publications are primarily in lower-tier or unverified venues. "
        
#     if first_author_count > 0:
#         interpretation += f"Demonstrates research leadership (First author in {first_author_count} papers)."
#     else:
#         interpretation += "Primarily contributes as a co-author."
        
#     return interpretation

# def run_pipeline(cvs_folder, output_dir):
#     cvs = load_cvs_from_folder(cvs_folder)
#     if not cvs:
#         print("No CVs found")
#         return []
        
#     os.makedirs(output_dir, exist_ok=True)
#     all_profiles = []
    
#     analysis_results = []
    
#     for cv in cvs:
#         print(f"Processing Educational Profile for {cv['file_name']}")
#         profile = extract_full_profile(cv['text'])
#         profile['file_name'] = cv['file_name']
#         all_profiles.append(profile)
        
#         education = profile.get("education", [])
#         experience = profile.get("experience", [])
        
#         enriched_education = []
#         for edu in education:
#             obtained, normalized = normalize_marks(edu.get('marks_or_cgpa', ''))
#             ranking = get_institution_ranking(edu.get('institution', ''))
            
#             enriched_education.append({
#                 "file_name": cv['file_name'],
#                 "degree": edu.get('degree', ''),
#                 "level": edu.get('level', ''),
#                 "specialization": edu.get('specialization', ''),
#                 "institution": edu.get('institution', ''),
#                 "ranking": ranking,
#                 "start_year": edu.get('start_year', ''),
#                 "end_year": edu.get('end_year', ''),
#                 "marks_original": edu.get('marks_or_cgpa', ''),
#                 "marks_normalized_percent": normalized
#             })
            
#         gaps = analyze_gaps(education, experience)
#         progression_status, spec_consistency = evaluate_progression(education)
#         interpretation, highest_qual = interpret_educational_strength(education, gaps, progression_status, spec_consistency, enriched_education)
        
#         # Format gaps for output
#         gaps_str = "; ".join([f"Gap of {g['duration_years']} yrs between {g['between']} ({g['justification_details']})" for g in gaps])
        
        
#         # --- RESEARCH PROFILE LOGIC ---
#         publications = profile.get("publications", [])
#         candidate_name = profile.get("name", "")
        
#         j_res = []
#         c_res = []
        
#         for pub in publications:
#             pub_type = str(pub.get("type", "")).lower()
#             venue_str = str(pub.get("venue", "")).lower()
            
#             if "journal" in pub_type or "journal" in venue_str or "transactions" in venue_str:
#                 j = analyze_journal(pub, candidate_name)
#                 j['file_name'] = cv['file_name']
#                 j_res.append(j)
#             else:
#                 c = analyze_conference(pub, candidate_name)
#                 c['file_name'] = cv['file_name']
#                 c_res.append(c)
                
#         research_interp = interpret_research_profile(j_res, c_res)
        
#         analysis_results.append({
#             "file_name": cv['file_name'],
#             "highest_qualification": highest_qual,
#             "academic_progression": progression_status,
#             "specialization_consistency": spec_consistency,
#             "detected_gaps": gaps_str,
#             "edu_interpretation": interpretation,
#             "research_interpretation": research_interp,
#             "total_publications": len(publications),
#             "journal_count": len(j_res),
#             "conference_count": len(c_res)
#         })
        
#         if 'global_edu' not in locals(): global_edu = []
#         global_edu.extend(enriched_education)
        
#         if 'global_journals' not in locals(): global_journals = []
#         global_journals.extend(j_res)
        
#         if 'global_confs' not in locals(): global_confs = []
#         global_confs.extend(c_res)
        
#     # Save Outputs
#     if global_edu:
#         pd.DataFrame(global_edu).to_csv(os.path.join(output_dir, "m3_educational_records.csv"), index=False)
#     else:
#         pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_educational_records.csv"), index=False)
        
#     if 'global_journals' in locals() and global_journals:
#         pd.DataFrame(global_journals).to_csv(os.path.join(output_dir, "m3_journal_analysis.csv"), index=False)
#     else:
#         pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_journal_analysis.csv"), index=False)
        
#     if 'global_confs' in locals() and global_confs:
#         pd.DataFrame(global_confs).to_csv(os.path.join(output_dir, "m3_conference_analysis.csv"), index=False)
#     else:
#         pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_conference_analysis.csv"), index=False)
        
#     if analysis_results:
#         pd.DataFrame(analysis_results).to_csv(os.path.join(output_dir, "m3_overall_analysis.csv"), index=False)
#     else:
#         pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_overall_analysis.csv"), index=False)
    
#     print(f"Milestone 3 Analysis completed! Saved to {output_dir}")
#     return analysis_results, global_edu, global_journals if 'global_journals' in locals() else [], global_confs if 'global_confs' in locals() else []

# src/milestone3_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────
#  MILESTONE 3 PIPELINE  –  Member A additions marked with  # [MEMBER A]
#  New modules added:
#    1. Topic Variability Analysis
#    2. Co-Author Analysis
#    3. Books Analysis
#    4. Patents Analysis
#  Parser prompt is also updated (see parser.py) to extract books/patents.
# ─────────────────────────────────────────────────────────────────────────────

import os
import json
import re
import math
import pandas as pd
from collections import Counter
from loader import load_cvs_from_folder
from parser import extract_full_profile
from datetime import datetime

# ─────────────────────────────────────────
#  MOCK DATABASES  (keep from original)
# ─────────────────────────────────────────
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

# ─────────────────────────────────────────
#  TOPIC KEYWORD MAP  [MEMBER A]
# ─────────────────────────────────────────
# Each theme maps to a list of keywords that indicate that research area.
# The system checks publication titles, venue names, and abstracts against these.
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


# ─────────────────────────────────────────────────────────────────────────────
#  [MEMBER A]  MODULE 1: TOPIC VARIABILITY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def classify_publication_topics(publications):
    """
    Given a list of publication dicts (with 'title', 'venue', 'year'),
    assigns each publication to one or more research themes using keyword matching.
    Returns a list of dicts: {title, year, matched_themes}
    """
    classified = []
    for pub in publications:
        text_to_search = " ".join([
            str(pub.get("title", "")),
            str(pub.get("venue", "")),
            str(pub.get("abstract", "")),    # may be empty — that's fine
        ]).lower()

        matched = []
        for theme, keywords in TOPIC_KEYWORD_MAP.items():
            if any(kw in text_to_search for kw in keywords):
                matched.append(theme)

        if not matched:
            matched = ["Other / Unclassified"]

        classified.append({
            "title":          pub.get("title", ""),
            "year":           pub.get("year", ""),
            "venue":          pub.get("venue", ""),
            "matched_themes": matched,
            "primary_theme":  matched[0],   # first matched = dominant
        })

    return classified


def compute_topic_variability(classified_publications):
    """
    Given classified publications, computes:
      - theme_distribution: {theme: count}
      - theme_percentages:  {theme: percentage}
      - dominant_topic:     str
      - diversity_score:    float 0-1  (Shannon entropy normalized)
      - variability_label:  'Specialist' | 'Moderate' | 'Interdisciplinary'
      - trend_over_time:    list of {year, theme} for timeline view
    """
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

    # Count how many publications fall in each theme (a pub can match multiple)
    theme_counter = Counter()
    for pub in classified_publications:
        for theme in pub["matched_themes"]:
            theme_counter[theme] += 1

    total = len(classified_publications)
    theme_percentages = {t: round((c / total) * 100, 1) for t, c in theme_counter.items()}

    dominant_topic = theme_counter.most_common(1)[0][0] if theme_counter else "N/A"

    # Shannon Entropy Diversity Score (normalized 0-1)
    # Higher = more spread across topics = more interdisciplinary
    diversity_score = 0.0
    if len(theme_counter) > 1:
        probs = [c / total for c in theme_counter.values()]
        raw_entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy  = math.log2(len(theme_counter))
        diversity_score = min(round(raw_entropy / max_entropy, 3), 1.0) if max_entropy > 0 else 0.0

    # Label
    if diversity_score < 0.3:
        variability_label = "Specialist (Focused Research)"
    elif diversity_score < 0.65:
        variability_label = "Moderate Breadth"
    else:
        variability_label = "Interdisciplinary (Broad Research)"

    # Trend over time — one entry per publication with a valid year
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
    """Generates a human-readable interpretation string."""
    if variability_result["total_publications"] == 0:
        return f"{candidate_name} has no documented publications for topic analysis."

    dominant  = variability_result["dominant_topic"]
    label     = variability_result["variability_label"]
    score     = variability_result["diversity_score"]
    n_themes  = len(variability_result["theme_distribution"])
    total     = variability_result["total_publications"]

    top_pct   = variability_result["theme_percentages"].get(dominant, 0)

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


# ─────────────────────────────────────────────────────────────────────────────
#  [MEMBER A]  MODULE 2: CO-AUTHOR ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def parse_author_list(authors_string):
    """
    Splits an authors string into a clean list of individual author names.
    Handles comma-separated and 'and'-separated formats.
    Strips asterisks (corresponding author markers) and extra whitespace.
    """
    if not authors_string:
        return []

    # Replace ' and ' with comma for uniform splitting
    authors_string = re.sub(r'\s+and\s+', ', ', authors_string, flags=re.IGNORECASE)
    # Remove asterisks
    authors_string = authors_string.replace('*', '')

    parts = [a.strip() for a in authors_string.split(',') if a.strip()]
    return parts


def normalize_author_name(name):
    """
    Normalizes an author name to 'lastname firstname' lowercase for matching.
    Handles 'First Last', 'Last, First', and abbreviated names like 'A. Khan'.
    """
    name = name.strip().lower()
    # Remove dots from initials (e.g., "A. B. Khan" → "a b khan")
    name = re.sub(r'\.', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def is_same_author(name_a, name_b):
    """
    Fuzzy check: returns True if two author name strings likely refer to the same person.
    Uses substring matching on last name + first initial.
    """
    a = normalize_author_name(name_a)
    b = normalize_author_name(name_b)

    # Direct match
    if a == b:
        return True

    # Split into tokens
    tokens_a = a.split()
    tokens_b = b.split()

    if not tokens_a or not tokens_b:
        return False

    # Last name match (last token) + first initial match
    last_a = tokens_a[-1]
    last_b = tokens_b[-1]

    if last_a == last_b and len(last_a) > 2:
        # Check if first initials match
        init_a = tokens_a[0][0] if tokens_a else ''
        init_b = tokens_b[0][0] if tokens_b else ''
        if init_a == init_b:
            return True

    return False


def analyze_coauthors(publications, candidate_name):
    """
    Analyzes co-authorship patterns for a candidate across all their publications.

    Returns a dict with:
      - unique_coauthors:          list of unique co-author names
      - total_unique_coauthors:    int
      - coauthor_frequency:        {author_name: count}  (how often they appear)
      - frequent_collaborators:    list of (name, count) for those appearing 2+ times
      - avg_authors_per_paper:     float
      - solo_papers:               int (papers with only the candidate)
      - collaboration_diversity:   float 0-1
      - interpretation:            str
    """
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

    all_coauthors_flat = []   # every co-author mention (duplicates kept for frequency)
    unique_coauthor_set = []  # deduplicated list
    per_paper_details   = []
    solo_count          = 0
    team_sizes          = []

    for pub in publications:
        author_list = parse_author_list(pub.get("authors", ""))
        team_size   = len(author_list)
        team_sizes.append(team_size)

        # Filter out the candidate themselves
        coauthors_this_paper = []
        for author in author_list:
            if not is_same_author(author, candidate_name):
                coauthors_this_paper.append(author)

        if not coauthors_this_paper:
            solo_count += 1

        # Add to flat list for frequency counting
        all_coauthors_flat.extend(coauthors_this_paper)

        # Add to deduplicated set
        for ca in coauthors_this_paper:
            already_exists = any(is_same_author(ca, existing) for existing in unique_coauthor_set)
            if not already_exists:
                unique_coauthor_set.append(ca)

        per_paper_details.append({
            "title":      pub.get("title", ""),
            "year":       pub.get("year", ""),
            "coauthors":  ", ".join(coauthors_this_paper) if coauthors_this_paper else "None (Solo)",
            "team_size":  team_size,
        })

    # Frequency count — normalize names before counting
    freq_map = {}
    for ca in all_coauthors_flat:
        norm = normalize_author_name(ca)
        # Find if already exists under a slightly different spelling
        matched_key = None
        for existing_key in freq_map:
            if is_same_author(ca, existing_key):
                matched_key = existing_key
                break
        if matched_key:
            freq_map[matched_key] += 1
        else:
            freq_map[ca] = 1

    # Sort by frequency
    coauthor_frequency  = dict(sorted(freq_map.items(), key=lambda x: x[1], reverse=True))
    frequent_collaborators = [(name, count) for name, count in coauthor_frequency.items() if count >= 2]

    avg_authors   = round(sum(team_sizes) / len(team_sizes), 2) if team_sizes else 0
    largest_team  = max(team_sizes) if team_sizes else 0
    total_unique  = len(unique_coauthor_set)

    # Collaboration diversity score:
    # Based on ratio of unique collaborators to total co-author appearances
    total_coauthor_appearances = sum(freq_map.values())
    collab_diversity = round(total_unique / total_coauthor_appearances, 3) \
                       if total_coauthor_appearances > 0 else 0.0

    # Interpretation
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
    """Builds a human-readable co-author summary."""
    text = (
        f"{candidate_name} has collaborated with {total_unique} unique co-author(s) "
        f"across {total_papers} publication(s). "
        f"Average team size per paper: {avg_authors:.1f}. "
    )

    if solo_count > 0:
        text += f"{solo_count} paper(s) appear to be single-authored. "

    if frequent_collabs:
        top = frequent_collabs[:3]  # show top 3
        names = ", ".join([f"{n} ({c} papers)" for n, c in top])
        text += f"Recurring collaborators: {names}. "
        text += "This suggests a stable research network. "
    else:
        text += "No recurring collaborators detected — the candidate may work with diverse, non-overlapping groups. "

    if diversity > 0.75:
        text += "High collaboration diversity indicates broad academic reach."
    elif diversity > 0.4:
        text += "Moderate collaboration diversity suggests a mix of stable partnerships and new collaborations."
    else:
        text += "Low collaboration diversity suggests concentrated work within a tight research group."

    return text


# ─────────────────────────────────────────────────────────────────────────────
#  [MEMBER A]  MODULE 3: BOOKS ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

# Known credible academic publishers for quality scoring
CREDIBLE_PUBLISHERS = [
    "springer", "elsevier", "wiley", "cambridge university press",
    "oxford university press", "mit press", "pearson", "mcgraw-hill",
    "taylor & francis", "routledge", "sage", "ieee press", "acm press",
    "packt", "o'reilly", "no starch press",
]


def analyze_books(books_list, candidate_name):
    """
    Analyzes books authored or co-authored by the candidate.

    books_list: list of dicts from the parser with keys:
        title, authors, isbn, publisher, year, link/url

    Returns a list of enriched dicts plus a summary dict.
    """
    if not books_list:
        return [], {
            "total_books":           0,
            "sole_authored":         0,
            "co_authored":           0,
            "credible_publisher_count": 0,
            "interpretation":        f"{candidate_name} has no documented books.",
        }

    enriched = []
    sole_count     = 0
    co_count       = 0
    credible_count = 0

    for book in books_list:
        authors_str  = str(book.get("authors", ""))
        author_list  = parse_author_list(authors_str)
        publisher    = str(book.get("publisher", "")).strip()
        publisher_lc = publisher.lower()

        # Authorship role
        if len(author_list) == 1:
            authorship_role = "Sole Author"
            sole_count += 1
        else:
            # Check if candidate is first/lead
            is_lead = author_list and is_same_author(author_list[0], candidate_name)
            authorship_role = "Lead Author" if is_lead else "Co-Author"
            co_count += 1

        # Publisher credibility
        is_credible = any(cp in publisher_lc for cp in CREDIBLE_PUBLISHERS)
        publisher_credibility = "Recognized Academic/Professional Publisher" if is_credible else "Unknown / Self-Published"
        if is_credible:
            credible_count += 1

        # Verification link
        isbn  = str(book.get("isbn", "")).strip()
        link  = str(book.get("link", book.get("url", ""))).strip()
        verification_url = link if link else (
            f"https://www.worldcat.org/search?q=isbn:{isbn}" if isbn else "No link provided"
        )

        enriched.append({
            "title":                 book.get("title", ""),
            "authors":               authors_str,
            "authorship_role":       authorship_role,
            "isbn":                  isbn if isbn else "Not Stated",
            "publisher":             publisher if publisher else "Not Stated",
            "publisher_credibility": publisher_credibility,
            "year":                  book.get("year", ""),
            "verification_url":      verification_url,
        })

    # Summary interpretation
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

#  [MEMBER A]  MODULE 4: PATENTS ANALYSIS

PATENT_DB_MAP = {
    "us":   "https://patents.google.com/patent/US{number}",
    "pk":   "https://www.ipop.gov.pk/",   # Pakistan IP office — no direct URL pattern
    "ep":   "https://patents.google.com/patent/EP{number}",
    "wo":   "https://patents.google.com/patent/WO{number}",
    "gb":   "https://patents.google.com/patent/GB{number}",
}


def build_patent_verification_url(patent_number, country):
    """Builds a verification URL from patent number and country code."""
    if not patent_number:
        return "No verification link"

    country_code = str(country).lower().strip()[:2]
    template = PATENT_DB_MAP.get(country_code)

    # Clean the number (remove country prefix if present)
    clean_number = re.sub(r'^[A-Za-z]{2}', '', str(patent_number)).strip()

    if template and "{number}" in template:
        return template.format(number=clean_number)

    # Default: Google Patents search
    return f"https://patents.google.com/?q={patent_number.replace(' ', '+')}"


def analyze_patents(patents_list, candidate_name):
    """
    Analyzes patents associated with the candidate.

    patents_list: list of dicts from the parser with keys:
        patent_number, title, date, inventors, country, link/url

    Returns a list of enriched patent dicts plus a summary dict.
    """
    if not patents_list:
        return [], {
            "total_patents":      0,
            "lead_inventor_count": 0,
            "co_inventor_count":  0,
            "countries":          [],
            "interpretation":     f"{candidate_name} has no documented patents.",
        }

    enriched           = []
    lead_count         = 0
    co_count           = 0
    countries_seen     = set()

    for patent in patents_list:
        inventors_str  = str(patent.get("inventors", patent.get("innovators", "")))
        inventor_list  = parse_author_list(inventors_str)
        country        = str(patent.get("country", "")).strip()
        patent_number  = str(patent.get("patent_number", patent.get("number", ""))).strip()

        if country:
            countries_seen.add(country)

        # Inventor role
        if inventor_list:
            is_lead = is_same_author(inventor_list[0], candidate_name)
            role    = "Lead Inventor" if is_lead else "Co-Inventor"
            if is_lead:
                lead_count += 1
            else:
                co_count += 1
        else:
            role = "Unknown Role"

        # Build verification URL
        provided_link = str(patent.get("link", patent.get("url", ""))).strip()
        verification_url = provided_link if provided_link else build_patent_verification_url(patent_number, country)

        enriched.append({
            "patent_number":      patent_number if patent_number else "Not Stated",
            "title":              patent.get("title", ""),
            "date":               patent.get("date", patent.get("year", "")),
            "inventors":          inventors_str,
            "inventor_role":      role,
            "country":            country if country else "Not Stated",
            "verification_url":   verification_url,
        })

    # Summary interpretation
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


# ─────────────────────────────────────────────────────────────────────────────
#  ORIGINAL HELPER FUNCTIONS  (unchanged from original milestone3_pipeline.py)
# ─────────────────────────────────────────────────────────────────────────────

def normalize_marks(marks_str):
    if not marks_str:
        return None, None
    marks_str = str(marks_str).lower().strip()
    cgpa_match = re.search(r'([\d\.]+)\s*/\s*([45]\.0)', marks_str)
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
    inst_lower = institution.lower()
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
                        justification.append(f"{exp.get('job_title','Job')} at {exp.get('organization','Org')}")
                gaps.append({
                    'between':              f"{prev['level']} and {curr['level']}",
                    'duration_years':       gap_years,
                    'justified':            justified,
                    'justification_details': ", ".join(justification) if justified else "Unexplained gap",
                })
    return gaps


def evaluate_progression(education_list):
    scores = []
    specializations = []
    for edu in education_list:
        _, norm = normalize_marks(edu.get('marks_or_cgpa', ''))
        sy   = parse_year(edu.get('start_year'))
        spec = str(edu.get('specialization', '')).strip().lower()
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
            if diff > 5:      trends.append("Improving")
            elif diff < -5:   trends.append("Declining")
            else:             trends.append("Consistent")
        if all(t == "Improving"  for t in trends): progression_status = "Consistently Improving"
        elif all(t == "Declining" for t in trends): progression_status = "Consistently Declining"
        elif all(t == "Consistent"for t in trends): progression_status = "Consistent Academic Performance"
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
    levels   = [str(e.get('level', '')).upper() for e in education_list]
    highest  = "Unknown"
    bs_count = sum(1 for e in education_list if "BS" in str(e.get('degree', '')).upper() or "BACHELOR" in str(e.get('degree', '')).upper())
    ms_count = sum(1 for e in education_list if "MS" in str(e.get('degree', '')).upper() or "MASTER"   in str(e.get('degree', '')).upper())

    has_bsc  = any(re.search(r'\bbsc\b', str(e.get('degree', '')).lower()) for e in education_list)
    has_msc  = any(re.search(r'\bmsc\b', str(e.get('degree', '')).lower()) for e in education_list)
    pathway  = "14-year BSc + 16-year MSc Sequence" if (has_bsc and has_msc and bs_count >= 1 and ms_count >= 1) \
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


# ── Research helpers (unchanged) ──────────────────────────────────────────────

def evaluate_authorship_role(candidate_name, authors_string):
    if not candidate_name or not authors_string:
        return "Unknown"
    candidate_parts = str(candidate_name).lower().split()
    authors = [a.strip() for a in str(authors_string).lower().split(',')]
    candidate_pos = -1
    for i, author in enumerate(authors):
        if any(part in author for part in candidate_parts if len(part) > 2):
            candidate_pos = i
            break
    if candidate_pos == -1:
        return "Unlisted / Unknown"
    is_first       = (candidate_pos == 0)
    is_corresponding = '*' in authors[candidate_pos] or (candidate_pos == len(authors) - 1 and len(authors) > 2)
    if is_first and is_corresponding: return "Both First and Corresponding Author"
    if is_first:                       return "First Author"
    if is_corresponding:               return "Corresponding Author"
    return "Co-author"


def analyze_journal(pub, candidate_name):
    venue   = str(pub.get('venue', '')).lower()
    issn    = pub.get('issn', '')
    j_data  = {"wos": False, "scopus": False, "quartile": "Unranked", "if": None}
    for k, v in MOCK_JOURNALS.items():
        if k in venue:
            j_data = v
            break
    legitimacy      = "Verified (via ISSN)" if issn else ("Verified (by Name)" if j_data["wos"] else "Unverified")
    role            = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    quality_interp  = f"Published in a {j_data['quartile']} journal"
    if j_data['wos']:    quality_interp += f" (WoS Indexed, IF: {j_data['if']})"
    elif j_data['scopus']:quality_interp += " (Scopus Indexed)"
    else:                quality_interp += " (Unindexed / Unknown standing)"
    return {
        "title": pub.get('title',''), "venue": pub.get('venue',''), "year": pub.get('year',''),
        "issn": issn, "legitimacy": legitimacy, "wos_indexed": j_data["wos"],
        "scopus_indexed": j_data["scopus"] or j_data["wos"], "quartile": j_data["quartile"],
        "impact_factor": j_data["if"], "authorship_role": role, "quality_interpretation": quality_interp,
    }


def analyze_conference(pub, candidate_name):
    venue     = str(pub.get('venue', '')).lower()
    publisher = str(pub.get('publisher', '')).lower()
    a_star    = any(k in venue for k, v in MOCK_CONFERENCES.items() if v == "A*")
    mat_match = re.search(r'(\d+(?:st|nd|rd|th))\s', pub.get('venue', ''))
    maturity  = mat_match.group(1) + " edition" if mat_match else "Unknown"
    indexed_in = ("IEEE Xplore" if "ieee" in publisher or "ieee" in venue
                  else "ACM Digital Library" if "acm" in publisher
                  else "Springer" if "springer" in publisher
                  else "Scopus"   if "scopus"   in publisher
                  else "Unverified")
    role            = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    quality_interp  = ("Top-tier A* Conference" if a_star else "Standard Conference")
    quality_interp += f" ({maturity})" if maturity != "Unknown" else " (Maturity Unknown)"
    quality_interp += f", Indexed in {indexed_in}" if indexed_in != "Unverified" else ", Indexing Unknown"
    return {
        "title": pub.get('title',''), "venue": pub.get('venue',''), "year": pub.get('year',''),
        "publisher": pub.get('publisher',''), "a_star_status": a_star, "maturity": maturity,
        "indexed_in": indexed_in, "authorship_role": role, "quality_interpretation": quality_interp,
    }


def interpret_research_profile(journal_results, conf_results):
    total       = len(journal_results) + len(conf_results)
    if total == 0:
        return "Candidate has no documented research publications."
    q1_count    = sum(1 for j in journal_results if j['quartile'] == 'Q1')
    wos_count   = sum(1 for j in journal_results if j['wos_indexed'])
    astar_count = sum(1 for c in conf_results if c['a_star_status'])
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


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(cvs_folder, output_dir):
    cvs = load_cvs_from_folder(cvs_folder)
    if not cvs:
        print("No CVs found")
        return [], [], [], [], [], [], [], []

    os.makedirs(output_dir, exist_ok=True)

    all_profiles      = []
    analysis_results  = []

    # Accumulator lists for CSV export
    global_edu        = []
    global_journals   = []
    global_confs      = []
    global_topic_rows = []   # [MEMBER A]
    global_coauthor_rows = [] # [MEMBER A]
    global_book_rows  = []   # [MEMBER A]
    global_patent_rows= []   # [MEMBER A]

    for cv in cvs:
        fname = cv['file_name']
        print(f"\n── Processing: {fname} ──")
        profile = extract_full_profile(cv['text'])
        profile['file_name'] = fname
        all_profiles.append(profile)

        candidate_name = profile.get("name", fname)
        education      = profile.get("education",    [])
        experience     = profile.get("experience",   [])
        publications   = profile.get("publications", [])
        books          = profile.get("books",        [])
        patents        = profile.get("patents",       [])

        # ── Educational Analysis (original) ──────────────────────────────────
        enriched_education = []
        for edu in education:
            obtained, normalized = normalize_marks(edu.get('marks_or_cgpa', ''))
            ranking = get_institution_ranking(edu.get('institution', ''))
            enriched_education.append({
                "file_name":               fname,
                "degree":                  edu.get('degree', ''),
                "level":                   edu.get('level', ''),
                "specialization":          edu.get('specialization', ''),
                "institution":             edu.get('institution', ''),
                "ranking":                 ranking,
                "start_year":              edu.get('start_year', ''),
                "end_year":                edu.get('end_year', ''),
                "marks_original":          edu.get('marks_or_cgpa', ''),
                "marks_normalized_percent":normalized,
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

        # ── Research Profile Analysis (original) ─────────────────────────────
        j_res, c_res = [], []
        for pub in publications:
            pub_type  = str(pub.get("type", "")).lower()
            venue_str = str(pub.get("venue", "")).lower()
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

        # ── [MEMBER A] Topic Variability ─────────────────────────────────────
        print(f"  → Running Topic Variability Analysis...")
        classified_pubs   = classify_publication_topics(publications)
        variability_result= compute_topic_variability(classified_pubs)
        topic_interp      = interpret_topic_variability(variability_result, candidate_name)

        # Flatten per-publication topic rows for CSV
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

        # ── [MEMBER A] Co-Author Analysis ────────────────────────────────────
        print(f"  → Running Co-Author Analysis...")
        coauthor_result = analyze_coauthors(publications, candidate_name)

        # Flatten per-paper co-author rows for CSV
        for pp in coauthor_result["per_paper_details"]:
            global_coauthor_rows.append({
                "file_name":  fname,
                "candidate":  candidate_name,
                "title":      pp["title"],
                "year":       pp["year"],
                "coauthors":  pp["coauthors"],
                "team_size":  pp["team_size"],
            })

        # ── [MEMBER A] Books Analysis ─────────────────────────────────────────
        print(f"  → Running Books Analysis...")
        enriched_books, books_summary = analyze_books(books, candidate_name)
        for book in enriched_books:
            book["file_name"]  = fname
            book["candidate"]  = candidate_name
            global_book_rows.append(book)

        # ── [MEMBER A] Patents Analysis ───────────────────────────────────────
        print(f"  → Running Patents Analysis...")
        enriched_patents, patents_summary = analyze_patents(patents, candidate_name)
        for patent in enriched_patents:
            patent["file_name"] = fname
            patent["candidate"] = candidate_name
            global_patent_rows.append(patent)

        # ── Aggregate result for this candidate ──────────────────────────────
        analysis_results.append({
            "file_name":               fname,
            "candidate_name":          candidate_name,
            # Education
            "highest_qualification":   highest_qual,
            "academic_progression":    progression_status,
            "specialization_consistency": spec_consistency,
            "detected_gaps":           gaps_str,
            "edu_interpretation":      interpretation,
            # Research (original)
            "research_interpretation": research_interp,
            "total_publications":      len(publications),
            "journal_count":           len(j_res),
            "conference_count":        len(c_res),
            # [MEMBER A] Topic Variability
            "dominant_research_topic": variability_result["dominant_topic"],
            "research_diversity_score":variability_result["diversity_score"],
            "research_variability_label": variability_result["variability_label"],
            "topic_distribution":      json.dumps(variability_result["theme_distribution"]),
            "topic_interpretation":    topic_interp,
            # [MEMBER A] Co-Author
            "total_unique_coauthors":  coauthor_result["total_unique_coauthors"],
            "avg_authors_per_paper":   coauthor_result["avg_authors_per_paper"],
            "solo_papers":             coauthor_result["solo_papers"],
            "frequent_collaborators":  str(coauthor_result["frequent_collaborators"][:5]),
            "coauthor_interpretation": coauthor_result["interpretation"],
            # [MEMBER A] Books
            "total_books":             books_summary["total_books"],
            "books_interpretation":    books_summary["interpretation"],
            # [MEMBER A] Patents
            "total_patents":           patents_summary["total_patents"],
            "patents_interpretation":  patents_summary["interpretation"],
        })

    # ── Save all CSVs ─────────────────────────────────────────────────────────
    def save_df(data, filename, default_cols):
        path = os.path.join(output_dir, filename)
        df   = pd.DataFrame(data) if data else pd.DataFrame(columns=default_cols)
        df.to_csv(path, index=False)
        print(f"  Saved → {filename}  ({len(df)} rows)")

    save_df(analysis_results,    "m3_overall_analysis.csv",    ["file_name"])
    save_df(global_edu,          "m3_educational_records.csv", ["file_name"])
    save_df(global_journals,     "m3_journal_analysis.csv",    ["file_name"])
    save_df(global_confs,        "m3_conference_analysis.csv", ["file_name"])
    save_df(global_topic_rows,   "m3_topic_variability.csv",   ["file_name", "candidate", "title", "primary_theme"])  # [MEMBER A]
    save_df(global_coauthor_rows,"m3_coauthor_details.csv",    ["file_name", "candidate", "title", "coauthors"])       # [MEMBER A]
    save_df(global_book_rows,    "m3_books_analysis.csv",      ["file_name", "candidate", "title"])                    # [MEMBER A]
    save_df(global_patent_rows,  "m3_patents_analysis.csv",    ["file_name", "candidate", "patent_number"])            # [MEMBER A]

    print(f"\nMilestone 3 Analysis complete — outputs saved to {output_dir}")

    return (
        analysis_results,
        global_edu,
        global_journals,
        global_confs,
        global_topic_rows,      # [MEMBER A]
        global_coauthor_rows,   # [MEMBER A]
        global_book_rows,       # [MEMBER A]
        global_patent_rows,     # [MEMBER A]
    )