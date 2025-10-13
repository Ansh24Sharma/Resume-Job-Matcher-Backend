import pandas as pd
from preprocess import clean_text
from service.db import insert_resume, insert_job
from entities import extract_entities
 
 
# helper to find first available column (case-insensitive)
def pick_column(row, candidates):
    for c in candidates:
        if c in row.index:
            return row.get(c)
    lower_map = {col.lower(): col for col in row.index}
    for cand in candidates:
        key = cand.lower()
        if key in lower_map:
            return row.get(lower_map[key])
    return None
 
 
def text_from_columns(row, candidates):
    vals = []
    for c in candidates:
        v = pick_column(row, [c])
        if v is not None and str(v).strip().lower() != "nan":
            vals.append(str(v))
    return " ".join(vals)
 
 
def csv_to_list(text):
    if not text or str(text).lower() == "nan":
        return []
    text = str(text)
    for sep in [",", ";", "|"]:
        if sep in text:
            return [p.strip() for p in text.split(sep) if p.strip()]
    return [text.strip()]

def normalize_list(items):
    """Lowercase + strip + deduplicate while preserving order."""
    seen = set()
    result = []
    for i in items:
        norm = str(i).strip()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(i.strip())
            return result
 
 
def load_sample_resumes(file_path="data/resume_dataset.csv"):
    df = pd.read_csv(file_path)
    resumes = []
 
    for idx, row in df.iterrows():
        name = f"resume_{idx+1}"
 
        career_obj = text_from_columns(row, ["Career_objective", "Carrer_objective", "Career Objective", "Summary", "Objective"])
        skills_text = pick_column(row, ["Skills", "skills", "skill", "Skill"]) or ""
        exp_text = text_from_columns(row, ["Experience_requirement", "Experience Requirement", "Experience", "Experience_details", "Experience requirement"])
        edu_text = pick_column(row, ["Education", "education", "Degree", "Qualification"])
 
        # ✅ cast everything to string safely
        parts = [str(x) for x in [career_obj, skills_text, exp_text, edu_text] if str(x).strip().lower() != "nan"]
        full_text = " ".join(parts).strip()
 
        extracted = extract_entities(full_text)
 
        csv_skills = [s.strip().lower() for s in csv_to_list(skills_text)]
        merged_skills = list(dict.fromkeys([s for s in (extracted.get("skills", []) + csv_skills) if s]))
 
        merged_education = extracted.get("education", [])
        
        if edu_text and str(edu_text).strip().lower() != "nan":
            edu_clean = str(edu_text).strip().lower()
            merged_education = [e.lower() for e in merged_education]  # normalize
            if edu_clean not in merged_education: 
                merged_education.append(edu_clean)
        
        # keep unique
        merged_education = list(dict.fromkeys(merged_education))
 
        csv_exp = [e.strip() for e in csv_to_list(exp_text)]
        merged_experience = list(dict.fromkeys([s for s in (extracted.get("experience", []) + csv_exp) if s]))
 
        entities = {
            "skills": merged_skills,
            "education": merged_education,
            "experience": merged_experience
        }
 
        resumes.append((name, clean_text(full_text), entities))
 
    return resumes
 
 
def load_sample_jobs(file_path="data/job_dataset.csv"):
    df = pd.read_csv(file_path)
    jobs = []
 
    for idx, row in df.iterrows():
        title = pick_column(row, ["Title", "Job Title", "title"]) or f"job_{idx+1}"
 
        responsibilities = text_from_columns(row, ["Responsibilities", "Description", "Job Description", "responsibilities"])
        keywords = text_from_columns(row, ["Keywords", "KeyWords", "keywords"])
        skills_text = pick_column(row, ["Skills", "skills", "skill"]) or ""
        experience_level = pick_column(row, ["Experience Level", "Experience_Level", "ExperienceLevel", "Experience level"]) or ""
        years_exp = pick_column(row, ["Years of experience", "Years_experience", "Years Experience", "Years_of_experience"]) or ""
 
        description = " ".join([responsibilities, keywords, skills_text]).strip()
 
        extracted = extract_entities(description)
 
        csv_skills = [s.strip().lower() for s in csv_to_list(skills_text)]
        merged_skills = list(dict.fromkeys([s for s in (extracted.get("skills", []) + csv_skills) if s]))

        merged_education = extracted.get("education", [])
        edu_text = pick_column(row, ["Education", "education", "Degree", "Qualification"])
        
        if edu_text and str(edu_text).strip().lower() != "nan":
            edu_clean = str(edu_text).strip().lower()
            merged_education = [e.lower() for e in merged_education]
            if edu_clean not in merged_education:
                merged_education.append(edu_clean)
        
        merged_education = list(dict.fromkeys(merged_education))
 
 
        exp_list = extracted.get("experience", [])
        if experience_level and str(experience_level).strip().lower() != "nan":
            exp_list.append(str(experience_level).strip())
        if years_exp and str(years_exp).strip().lower() != "nan":
            exp_list.append(str(years_exp).strip())
        merged_experience = list(dict.fromkeys([s for s in exp_list if s]))
 
        entities = {
            "skills": merged_skills,
            "education": merged_education,
            "experience": merged_experience
        }
 
        jobs.append((title, clean_text(description), entities))
 
    return jobs
 
 
def insert_sample_data(limit_resumes=100, limit_jobs=100):
    print("📂 Loading resumes...")
    resumes = load_sample_resumes()
 
    print("📂 Loading jobs...")
    jobs = load_sample_jobs()
 
    if limit_resumes:
        resumes = resumes[:limit_resumes]
    if limit_jobs:
        jobs = jobs[:limit_jobs]
 
    for name, cleaned, entities in resumes:
        insert_resume(name, cleaned, entities)
 
    for title, cleaned, entities in jobs:
        insert_job(title, cleaned, entities)
 
    print("✅ Sample data inserted.")