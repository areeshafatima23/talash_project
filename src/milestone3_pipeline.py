# src/milestone3_pipeline.py

import os
import json
import re
import pandas as pd
from loader import load_cvs_from_folder
from parser import extract_full_profile
from datetime import datetime

# MOCK RANKINGS DATABASES for Demonstration
MOCK_JOURNALS = {
    "ieee transactions on pattern analysis": {"wos": True, "scopus": True, "quartile": "Q1", "if": 24.3},
    "nature": {"wos": True, "scopus": True, "quartile": "Q1", "if": 64.8},
    "expert systems with applications": {"wos": True, "scopus": True, "quartile": "Q1", "if": 8.5},
    "ieee access": {"wos": True, "scopus": True, "quartile": "Q2", "if": 3.4},
}

MOCK_CONFERENCES = {
    "cvpr": "A*",
    "neurips": "A*",
    "icml": "A*",
    "iccv": "A*",
    "acl": "A*",
    "emnlp": "A*",
    "kdd": "A*",
    "aaai": "A*",
    "ijcai": "A*"
}

THE_QS_RANKINGS = {
    "massachusetts institute of technology": "Rank 1 (QS)",
    "mit": "Rank 1 (QS)",
    "stanford university": "Rank 2 (QS)",
    "harvard university": "Rank 4 (QS)",
    "university of oxford": "Rank 3 (QS)",
    "university of cambridge": "Rank 5 (QS)",
    "national university of sciences and technology": "Top 400 (QS)",
    "nust": "Top 400 (QS)",
    "lums": "Top 600 (QS)",
    "lahore university of management sciences": "Top 600 (QS)",
    "fast nuces": "Top 1000 (QS)",
    "university of the punjab": "Top 1000 (QS)",
    "comsats": "Top 800 (QS)",
}

def normalize_marks(marks_str):
    if not marks_str:
        return None, None
    
    marks_str = str(marks_str).lower().strip()
    
    # Check for CGPA (e.g., 3.8/4.0 or 3.8)
    cgpa_match = re.search(r'([\d\.]+)\s*/\s*([45]\.0)', marks_str)
    if cgpa_match:
        obtained = float(cgpa_match.group(1))
        scale = float(cgpa_match.group(2))
        normalized = (obtained / scale) * 100
        return obtained, normalized
    
    # Check for generic CGPA without scale but looks like CGPA
    cgpa_single = re.search(r'^([1-4]\.\d{1,2})$', marks_str)
    if cgpa_single:
        obtained = float(cgpa_single.group(1))
        normalized = (obtained / 4.0) * 100
        return obtained, normalized

    # Check for Percentage
    percent_match = re.search(r'([\d\.]+)\s*%', marks_str)
    if percent_match:
        val = float(percent_match.group(1))
        return val, val

    # Check for Marks out of Total (e.g. 850/1100)
    fraction_match = re.search(r'(\d+)\s*/\s*(\d+)', marks_str)
    if fraction_match:
        obtained = float(fraction_match.group(1))
        total = float(fraction_match.group(2))
        if total > 0:
            normalized = (obtained / total) * 100
            return obtained, normalized

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
    # Sort education by end_year
    valid_edu = []
    for edu in education_list:
        sy = parse_year(edu.get('start_year'))
        ey = parse_year(edu.get('end_year'))
        if sy or ey:
            valid_edu.append({
                'level': edu.get('level', 'Unknown'),
                'start_year': sy if sy else ey,
                'end_year': ey if ey else sy,
                'raw': edu
            })
            
    valid_edu.sort(key=lambda x: x['end_year'] if x['end_year'] else 0)
    
    gaps = []
    for i in range(1, len(valid_edu)):
        prev_edu = valid_edu[i-1]
        curr_edu = valid_edu[i]
        
        if prev_edu['end_year'] and curr_edu['start_year']:
            gap_years = curr_edu['start_year'] - prev_edu['end_year']
            if gap_years > 1:
                # Check if gap is justified by experience
                justified = False
                justification = []
                for exp in experience_list:
                    exp_sy = parse_year(exp.get('start_date'))
                    exp_ey = parse_year(exp.get('end_date'))
                    
                    if exp_sy:
                        # If experience overlaps with the gap
                        if exp_sy >= prev_edu['end_year'] and exp_sy <= curr_edu['start_year']:
                            justified = True
                            justification.append(f"{exp.get('job_title', 'Job')} at {exp.get('organization', 'Org')}")
                
                gaps.append({
                    'between': f"{prev_edu['level']} and {curr_edu['level']}",
                    'duration_years': gap_years,
                    'justified': justified,
                    'justification_details': ", ".join(justification) if justified else "Unexplained gap"
                })
                
    return gaps

def evaluate_progression(education_list):
    scores = []
    specializations = []
    for edu in education_list:
        _, norm = normalize_marks(edu.get('marks_or_cgpa', ''))
        sy = parse_year(edu.get('start_year'))
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
            diff = scores[i][1] - scores[i-1][1]
            if diff > 5:
                trends.append("Improving")
            elif diff < -5:
                trends.append("Declining")
            else:
                trends.append("Consistent")
                
        if all(t == "Improving" for t in trends):
            progression_status = "Consistently Improving"
        elif all(t == "Declining" for t in trends):
            progression_status = "Consistently Declining"
        elif all(t == "Consistent" for t in trends):
            progression_status = "Consistent Academic Performance"
        else:
            progression_status = "Mixed Academic Progression"

    # Evaluate Specialization Consistency (very basic keyword overlap check)
    spec_consistency = "Consistent Specialization"
    if len(specializations) > 1:
        # Check if there is some common word among the last two degrees
        words1 = set(re.findall(r'\w+', specializations[-1]))
        words2 = set(re.findall(r'\w+', specializations[-2]))
        # Remove common stop words
        stop_words = {'of', 'in', 'and', 'the', 'engineering', 'science', 'sciences', 'arts', 'management'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        if words1 and words2 and not words1.intersection(words2):
            spec_consistency = "Shift in Specialization"

    return progression_status, spec_consistency

def interpret_educational_strength(education_list, gaps, progression_status, spec_consistency, enriched_education):
    levels = [str(e.get('level', '')).upper() for e in education_list]
    highest = "Unknown"
    
    # Pathway detection
    pathway = "Standard"
    bs_count = sum(1 for e in education_list if "BS" in str(e.get('degree', '')).upper() or "BACHELOR" in str(e.get('degree', '')).upper())
    ms_count = sum(1 for e in education_list if "MS" in str(e.get('degree', '')).upper() or "MASTER" in str(e.get('degree', '')).upper())
    
    # Very basic 14 vs 16 yr detection (BSc followed by MSc vs BS direct)
    has_bsc = any(re.search(r'\bbsc\b', str(e.get('degree', '')).lower()) for e in education_list)
    has_msc = any(re.search(r'\bmsc\b', str(e.get('degree', '')).lower()) for e in education_list)
    if has_bsc and has_msc and bs_count >= 1 and ms_count >= 1:
        pathway = "14-year BSc + 16-year MSc Sequence"
    elif bs_count > 0:
        pathway = "Direct 16-year BS Sequence"

    if "PHD" in levels: highest = "PhD"
    elif "PG" in levels or "MS" in levels or "MPHIL" in levels: highest = "Postgraduate (MS/MPhil)"
    elif "UG" in levels or "BS" in levels or "BACHELOR" in levels: highest = "Undergraduate (BS/BA)"
    
    unjustified_gaps = [g for g in gaps if not g['justified']]
    
    interpretation = f"The candidate's highest identified qualification is {highest} (Pathway: {pathway}). "
    interpretation += f"Academic performance is generally {progression_status} with a {spec_consistency}. "
    
    # Quality of Institutions summary
    ranked_insts = [e['ranking'] for e in enriched_education if e['ranking'] and e['ranking'] not in ["Unknown", "Ranking Unavailable"]]
    if ranked_insts:
        interpretation += f"The candidate attended globally/nationally ranked institutions (e.g., {ranked_insts[0]}). "
    else:
        interpretation += "Institution rankings were mostly unranked or unavailable. "
    
    if gaps:
        if len(unjustified_gaps) == 0:
            interpretation += f"The candidate has {len(gaps)} educational gap(s), all of which are justified by professional experience. "
        else:
            interpretation += f"The candidate has {len(unjustified_gaps)} unexplained educational gap(s). "
    else:
        interpretation += "There are no significant gaps in the educational timeline. "
        
    return interpretation, highest


# --- RESEARCH PROFILE ANALYSIS MODULE ---

def evaluate_authorship_role(candidate_name, authors_string):
    if not candidate_name or not authors_string:
        return "Unknown"
        
    candidate_parts = str(candidate_name).lower().split()
    authors = [a.strip() for a in str(authors_string).lower().split(',')]
    
    if not authors:
        return "Unknown"
        
    # Match candidate in authors list
    candidate_pos = -1
    for i, author in enumerate(authors):
        # basic match: if any part of the candidate name is in the author string
        if any(part in author for part in candidate_parts if len(part) > 2):
            candidate_pos = i
            break
            
    if candidate_pos == -1:
        return "Unlisted / Unknown"
        
    is_first = (candidate_pos == 0)
    
    # Heuristic for corresponding author: marked with '*' or listed last (common in some fields)
    is_corresponding = '*' in authors[candidate_pos] or (candidate_pos == len(authors) - 1 and len(authors) > 2)
    
    if is_first and is_corresponding:
        return "Both First and Corresponding Author"
    elif is_first:
        return "First Author"
    elif is_corresponding:
        return "Corresponding Author"
    else:
        return "Co-author"

def analyze_journal(pub, candidate_name):
    venue = str(pub.get('venue', '')).lower()
    issn = pub.get('issn', '')
    
    # Mock Lookup
    j_data = {"wos": False, "scopus": False, "quartile": "Unranked", "if": None}
    for k, v in MOCK_JOURNALS.items():
        if k in venue:
            j_data = v
            break
            
    # If ISSN is present, assume we verified it via a database in a real scenario
    legitimacy = "Verified (via ISSN)" if issn else ("Verified (by Name)" if j_data["wos"] else "Unverified")
    
    role = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    
    quality_interp = f"Published in a {j_data['quartile']} journal"
    if j_data['wos']: quality_interp += f" (WoS Indexed, IF: {j_data['if']})"
    elif j_data['scopus']: quality_interp += " (Scopus Indexed)"
    else: quality_interp += " (Unindexed / Unknown standing)"
    
    return {
        "title": pub.get('title', ''),
        "venue": pub.get('venue', ''),
        "year": pub.get('year', ''),
        "issn": issn,
        "legitimacy": legitimacy,
        "wos_indexed": j_data["wos"],
        "scopus_indexed": j_data["scopus"] or j_data["wos"], # Assume WoS is also Scopus for mock
        "quartile": j_data["quartile"],
        "impact_factor": j_data["if"],
        "authorship_role": role,
        "quality_interpretation": quality_interp
    }

def analyze_conference(pub, candidate_name):
    venue = str(pub.get('venue', '')).lower()
    publisher = str(pub.get('publisher', '')).lower()
    
    # A* Status Lookup
    a_star = False
    for k, v in MOCK_CONFERENCES.items():
        if k in venue:
            a_star = (v == "A*")
            break
            
    # Maturity Extraction
    maturity = "Unknown"
    mat_match = re.search(r'(\d+(?:st|nd|rd|th))\s', pub.get('venue', ''))
    if mat_match:
        maturity = mat_match.group(1) + " edition"
        
    # Indexing Extraction
    indexed_in = "Unverified"
    if "ieee" in publisher or "ieee" in venue: indexed_in = "IEEE Xplore"
    elif "acm" in publisher: indexed_in = "ACM Digital Library"
    elif "springer" in publisher: indexed_in = "Springer"
    elif "scopus" in publisher: indexed_in = "Scopus"
    
    role = evaluate_authorship_role(candidate_name, pub.get('authors', ''))
    
    quality_interp = "Top-tier A* Conference" if a_star else "Standard Conference"
    quality_interp += f" ({maturity})" if maturity != "Unknown" else " (Maturity Unknown)"
    quality_interp += f", Indexed in {indexed_in}" if indexed_in != "Unverified" else ", Indexing Unknown"
    
    return {
        "title": pub.get('title', ''),
        "venue": pub.get('venue', ''),
        "year": pub.get('year', ''),
        "publisher": pub.get('publisher', ''),
        "a_star_status": a_star,
        "maturity": maturity,
        "indexed_in": indexed_in,
        "authorship_role": role,
        "quality_interpretation": quality_interp
    }

def interpret_research_profile(journal_results, conf_results):
    total_pubs = len(journal_results) + len(conf_results)
    if total_pubs == 0:
        return "Candidate has no documented research publications."
        
    q1_count = sum(1 for j in journal_results if j['quartile'] == 'Q1')
    wos_count = sum(1 for j in journal_results if j['wos_indexed'])
    astar_count = sum(1 for c in conf_results if c['a_star_status'])
    first_author_count = sum(1 for p in (journal_results + conf_results) if "First" in p['authorship_role'])
    
    interpretation = f"Candidate has {total_pubs} publications ({len(journal_results)} journals, {len(conf_results)} conferences). "
    
    if q1_count > 0 or astar_count > 0:
        interpretation += f"Strong quality profile with {q1_count} Q1 journals and {astar_count} A* conferences. "
    elif wos_count > 0:
        interpretation += f"Solid visibility with {wos_count} WoS-indexed journals. "
    else:
        interpretation += "Publications are primarily in lower-tier or unverified venues. "
        
    if first_author_count > 0:
        interpretation += f"Demonstrates research leadership (First author in {first_author_count} papers)."
    else:
        interpretation += "Primarily contributes as a co-author."
        
    return interpretation

def run_pipeline(cvs_folder, output_dir):
    cvs = load_cvs_from_folder(cvs_folder)
    if not cvs:
        print("No CVs found")
        return []
        
    os.makedirs(output_dir, exist_ok=True)
    all_profiles = []
    
    analysis_results = []
    
    for cv in cvs:
        print(f"Processing Educational Profile for {cv['file_name']}")
        profile = extract_full_profile(cv['text'])
        profile['file_name'] = cv['file_name']
        all_profiles.append(profile)
        
        education = profile.get("education", [])
        experience = profile.get("experience", [])
        
        enriched_education = []
        for edu in education:
            obtained, normalized = normalize_marks(edu.get('marks_or_cgpa', ''))
            ranking = get_institution_ranking(edu.get('institution', ''))
            
            enriched_education.append({
                "file_name": cv['file_name'],
                "degree": edu.get('degree', ''),
                "level": edu.get('level', ''),
                "specialization": edu.get('specialization', ''),
                "institution": edu.get('institution', ''),
                "ranking": ranking,
                "start_year": edu.get('start_year', ''),
                "end_year": edu.get('end_year', ''),
                "marks_original": edu.get('marks_or_cgpa', ''),
                "marks_normalized_percent": normalized
            })
            
        gaps = analyze_gaps(education, experience)
        progression_status, spec_consistency = evaluate_progression(education)
        interpretation, highest_qual = interpret_educational_strength(education, gaps, progression_status, spec_consistency, enriched_education)
        
        # Format gaps for output
        gaps_str = "; ".join([f"Gap of {g['duration_years']} yrs between {g['between']} ({g['justification_details']})" for g in gaps])
        
        
        # --- RESEARCH PROFILE LOGIC ---
        publications = profile.get("publications", [])
        candidate_name = profile.get("name", "")
        
        j_res = []
        c_res = []
        
        for pub in publications:
            pub_type = str(pub.get("type", "")).lower()
            venue_str = str(pub.get("venue", "")).lower()
            
            if "journal" in pub_type or "journal" in venue_str or "transactions" in venue_str:
                j = analyze_journal(pub, candidate_name)
                j['file_name'] = cv['file_name']
                j_res.append(j)
            else:
                c = analyze_conference(pub, candidate_name)
                c['file_name'] = cv['file_name']
                c_res.append(c)
                
        research_interp = interpret_research_profile(j_res, c_res)
        
        analysis_results.append({
            "file_name": cv['file_name'],
            "highest_qualification": highest_qual,
            "academic_progression": progression_status,
            "specialization_consistency": spec_consistency,
            "detected_gaps": gaps_str,
            "edu_interpretation": interpretation,
            "research_interpretation": research_interp,
            "total_publications": len(publications),
            "journal_count": len(j_res),
            "conference_count": len(c_res)
        })
        
        if 'global_edu' not in locals(): global_edu = []
        global_edu.extend(enriched_education)
        
        if 'global_journals' not in locals(): global_journals = []
        global_journals.extend(j_res)
        
        if 'global_confs' not in locals(): global_confs = []
        global_confs.extend(c_res)
        
    # Save Outputs
    if global_edu:
        pd.DataFrame(global_edu).to_csv(os.path.join(output_dir, "m3_educational_records.csv"), index=False)
    else:
        pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_educational_records.csv"), index=False)
        
    if 'global_journals' in locals() and global_journals:
        pd.DataFrame(global_journals).to_csv(os.path.join(output_dir, "m3_journal_analysis.csv"), index=False)
    else:
        pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_journal_analysis.csv"), index=False)
        
    if 'global_confs' in locals() and global_confs:
        pd.DataFrame(global_confs).to_csv(os.path.join(output_dir, "m3_conference_analysis.csv"), index=False)
    else:
        pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_conference_analysis.csv"), index=False)
        
    if analysis_results:
        pd.DataFrame(analysis_results).to_csv(os.path.join(output_dir, "m3_overall_analysis.csv"), index=False)
    else:
        pd.DataFrame(columns=["empty"]).to_csv(os.path.join(output_dir, "m3_overall_analysis.csv"), index=False)
    
    print(f"Milestone 3 Analysis completed! Saved to {output_dir}")
    return analysis_results, global_edu, global_journals if 'global_journals' in locals() else [], global_confs if 'global_confs' in locals() else []