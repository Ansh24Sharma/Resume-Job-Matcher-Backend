import json
import re
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
from difflib import SequenceMatcher
import torch

class BERTMatcher:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"Loading BERT model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        print(f"BERT model loaded on device: {self.device}")

    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.array([])
        cleaned_texts = [self._prepare_text_for_bert(text) for text in texts]
        embeddings = self.model.encode(
            cleaned_texts, 
            batch_size=batch_size, 
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings

    def _prepare_text_for_bert(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        words = text.split()
        if len(words) > 400:
            text = ' '.join(words[:400])
        return text

def safe_json(val):
    if val is None:
        return []
    if isinstance(val, (list, tuple, set)):
        return list(val)
    if isinstance(val, dict):
        try:
            return list(val.values())
        except:
            return []
    if isinstance(val, (bytes, bytearray)):
        try:
            val = val.decode()
        except:
            return []
    if isinstance(val, str):
        s = val.strip()
        if s == "" or s.lower() == "null":
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, (list, tuple, set)):
                return list(parsed)
            if isinstance(parsed, dict):
                return list(parsed.values())
        except:
            for sep in [",", ";", "|"]:
                if sep in s:
                    return [p.strip() for p in s.split(sep) if p.strip()]
            return [s]
    return []

def _normalize_skill_for_compare(s: str) -> str:
    """Simple and effective skill normalization"""
    if not s or not isinstance(s, str):
        return ""
    
    # Convert to lowercase and strip
    normalized = s.lower().strip()
    
    # Remove common prefixes/suffixes
    normalized = re.sub(r'\s+', '', normalized)  # Remove all spaces
    normalized = re.sub(r'[^a-z0-9+#]', '', normalized)  # Keep only alphanumeric, +, #
    
    # Common equivalents
    skill_map = {
        'javascript': 'js',
        'typescript': 'ts',
        'reactjs': 'react',
        'nodejs': 'node',
        'python3': 'python',
        'mysql': 'sql',
        'postgresql': 'sql',
        'mongodb': 'mongo',
    }
    
    return skill_map.get(normalized, normalized)

def _normalize_edu_for_compare(e: str) -> Tuple[str, str, str]:
    """Education normalizer with strict degree hierarchy"""
    if not e or not isinstance(e, str):
        return ("", "", "")
    
    text = e.lower().strip()
    # Keep only alphanumeric and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Strict degree level mappings
    degree_mappings = {
        'bachelor': ['bachelor', 'bachelors', 'btech', 'b tech', 'be', 'b e', 'bsc', 'b sc', 'ba', 'b a', 'bcom', 'b com', 'bba', 'bca'],
        'master': ['master', 'masters', 'mtech', 'm tech', 'me', 'm e', 'msc', 'm sc', 'ma', 'm a', 'mba', 'mca'],
        'doctorate': ['phd', 'ph d', 'doctorate', 'doctoral'],
        'diploma': ['diploma', 'associate'],
        'certification': ['certificate', 'certification']
    }
    
    field_mappings = {
        'cs': ['computer science', 'comp science', 'cs', 'computing', 'computer applications', 'bca', 'mca', 'computer engg', 'computer engineering', 'comp engg', 'cse'],
        'it': ['information technology', 'info technology', 'it', 'info tech', 'information tech'],
        'ece': ['electronics', 'ece', 'electronics and communication', 'electronics communication', 'electrical', 'eee'],
        'mech': ['mechanical', 'mech'],
        'civil': ['civil'],
        'business': ['business', 'management', 'mba', 'bba', 'commerce', 'human resources', 'hr'],
        'science': ['science', 'physics', 'chemistry', 'mathematics', 'biology']
    }
    
    degree_type = ""
    for standard_degree, patterns in degree_mappings.items():
        for pattern in patterns:
            if pattern in text:
                degree_type = standard_degree
                break
        if degree_type:
            break
    
    field = ""
    for standard_field, patterns in field_mappings.items():
        for pattern in patterns:
            if pattern in text:
                field = standard_field
                break
        if field:
            break
    
    return (degree_type, field, text)

def calculate_education_similarity_enhanced(resume_edu, job_edu):
    """
    Education matching with strict degree and field requirements.
    
    Rules:
    1. BOTH degree level AND field must match for high scores
    2. Different degree levels (Bachelor vs Master) = low score
    3. Different fields (CS vs Business) = low score
    4. CS and IT are equivalent fields
    """
    if not job_edu:
        return 1.0
    
    if not resume_edu:
        return 0.0

    resume_parsed = []
    for r in resume_edu:
        if isinstance(r, str) and r.strip():
            parsed = _normalize_edu_for_compare(r)
            if parsed[0] or parsed[1]:  # Has degree or field
                resume_parsed.append(parsed)
    
    job_parsed = []
    for j in job_edu:
        if isinstance(j, str) and j.strip():
            parsed = _normalize_edu_for_compare(j)
            if parsed[0] or parsed[1]:
                job_parsed.append(parsed)
    
    if not resume_parsed:
        return 0.0
    
    if not job_parsed:
        return 1.0

    best_score = 0.0
    
    for r_degree, r_field, r_text in resume_parsed:
        for j_degree, j_field, j_text in job_parsed:
            score = 0.0
            
            # Check for exact degree level match
            degree_match = (r_degree == j_degree and r_degree != "")
            
            # Check for field match (including CS/IT equivalence)
            field_match = (r_field == j_field and r_field != "")
            cs_it_match = (r_field in ['cs', 'it'] and j_field in ['cs', 'it'])
            
            # Scoring logic:
            if degree_match and (field_match or cs_it_match):
                # Perfect match: same degree level and same field
                score = 1.0
            
            elif degree_match and r_field and j_field:
                # Same degree level but different field (e.g., B.Tech CS vs B.Tech Mech)
                score = 0.3
            
            elif (field_match or cs_it_match) and r_degree and j_degree:
                # Different degree level but same field (e.g., B.Tech CS vs M.Tech CS)
                # Give credit if resume has higher degree
                if r_degree == 'master' and j_degree == 'bachelor':
                    score = 0.8  # Overqualified but acceptable
                elif r_degree == 'doctorate' and j_degree in ['bachelor', 'master']:
                    score = 0.8  # Overqualified but acceptable
                else:
                    score = 0.2  # Underqualified
            
            elif degree_match and not r_field and not j_field:
                # Degree match but no field information
                score = 0.4
            
            else:
                # No meaningful match - use token overlap as last resort
                r_tokens = set(re.findall(r'\b\w+\b', r_text))
                j_tokens = set(re.findall(r'\b\w+\b', j_text))
                if j_tokens and len(j_tokens) > 2:  # Only if job has meaningful tokens
                    overlap = len(r_tokens & j_tokens) / len(j_tokens)
                    score = min(0.3, overlap)  # Cap at 0.3
            
            best_score = max(best_score, score)
    
    return min(1.0, best_score)

def extract_years_from_exp_list(exp):
    """
    Extracts min and max years from experience input.
    Handles: numbers, '1 year', '1-2 years', '1 to 2 years', lists, etc.
    Returns (min_years, max_years, has_data)
    """
    if exp is None:
        return (None, None, False)

    # If it's a number
    if isinstance(exp, (int, float)):
        years = int(exp)
        return (years, years, True)

    # If it's a list/tuple/set, join to string
    if isinstance(exp, (list, tuple, set)):
        exp = " ".join([str(x) for x in exp if x and str(x).strip().lower() not in ['null', 'none', '']])

    if not isinstance(exp, str):
        exp = str(exp)

    text = exp.strip().lower()
    if text in ['null', 'none', '']:
        return (None, None, False)

    # Entry level/fresher
    if any(keyword in text for keyword in ['entry level', 'fresher', 'entry-level', 'graduate', 'no experience']):
        return (0, 0, True)

    # Range: "1-2 years" or "1 to 2 years"
    range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', text)
    if range_match:
        min_years = int(range_match.group(1))
        max_years = int(range_match.group(2))
        return (min_years, max_years, True)

    # Single year: "2+ years", "2 years", "2 year"
    single_match = re.search(r'(\d+)\s*\+?', text)
    if single_match:
        years = int(single_match.group(1))
        if '+' in text:
            return (years, 999, True)
        else:
            return (years, years, True)

    return (None, None, False)

def calculate_experience_similarity(resume_exp, job_exp):
    """
    Experience matching with proper logic:
    - Job: 0, Resume: 1+ = MATCH (candidate has more experience than needed)
    - Job: 1-2, Resume: 1 = MATCH (within range)
    """
    resume_min, resume_max, resume_has_data = extract_years_from_exp_list(resume_exp)
    job_min, job_max, job_has_data = extract_years_from_exp_list(job_exp)

    # No job requirement -> always match
    if not job_has_data:
        return 1.0

    # Job requires but resume has no data -> no match
    if job_has_data and not resume_has_data:
        return 0.0

    # Set defaults
    if resume_min is None:
        resume_min = 0
    if resume_max is None:
        resume_max = resume_min
    if job_min is None:
        job_min = 0
    if job_max is None:
        job_max = job_min

    # Use minimum of resume experience for comparison
    resume_years = resume_min

    # If job requires 0 experience (entry level), any experience is good
    if job_min == 0 and job_max == 0:
        return 1.0

    # Check if resume experience falls within or exceeds job requirement
    if resume_years >= job_min and resume_years <= job_max:
        return 1.0

    # Resume exceeds maximum required (overqualified but still good)
    if resume_years > job_max:
        return 1.0

    # Resume has at least 80% of minimum requirement
    if resume_years >= job_min * 0.8 and job_min > 0:
        return 0.8

    return 0.0


def calculate_skill_similarity_bert(resume_skills, job_skills, bert_matcher):
    """Skill matching - all job requirements must be met"""
    if not job_skills:
        return 1.0
    
    if not resume_skills:
        return 0.0

    # Normalize all skills
    resume_norm = set()
    for s in resume_skills:
        if isinstance(s, str) and s.strip():
            norm = _normalize_skill_for_compare(s)
            if norm:
                resume_norm.add(norm)
    
    job_norm = set()
    for s in job_skills:
        if isinstance(s, str) and s.strip():
            norm = _normalize_skill_for_compare(s)
            if norm:
                job_norm.add(norm)
    
    if not job_norm:
        return 1.0
    
    if not resume_norm:
        return 0.0

    # Count exact matches
    matched = len(resume_norm & job_norm)
    total_required = len(job_norm)
    
    # Check fuzzy matches for unmatched skills
    unmatched_job = job_norm - resume_norm
    for j_skill in unmatched_job:
        for r_skill in resume_norm:
            if SequenceMatcher(None, r_skill, j_skill).ratio() >= 0.85:
                matched += 1
                break
    
    # If all matched, return 1.0
    if matched >= total_required:
        return 1.0
    
    # Try BERT for remaining unmatched
    still_unmatched = total_required - matched
    if still_unmatched > 0:
        try:
            # Use original skill names for BERT
            resume_original = [s.strip() for s in resume_skills if isinstance(s, str) and s.strip()]
            job_original = [s.strip() for s in job_skills if isinstance(s, str) and s.strip()]
            
            unmatched_jobs = []
            for j in job_original:
                j_norm = _normalize_skill_for_compare(j)
                if j_norm in unmatched_job:
                    unmatched_jobs.append(j)
            
            semantic_matched = 0
            for j_skill in unmatched_jobs:
                best_sim = 0.0
                for r_skill in resume_original:
                    embeddings = bert_matcher.encode_texts([r_skill, j_skill])
                    if len(embeddings) == 2:
                        sim = sklearn_cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                        best_sim = max(best_sim, sim)
                
                if best_sim >= 0.65:
                    semantic_matched += 1
            
            matched += semantic_matched
        except Exception as e:
            print(f"BERT error: {e}")
    
    return min(1.0, matched / total_required)

def compute_similarity_bert(resumes, jobs, posted_jobs=None,
                           weight_bert=0.20,
                           weight_skills=0.50,
                           weight_education=0.20,
                           weight_experience=0.10):
    if not resumes:
        return []

    all_jobs = []
    job_sources = []
    
    if jobs:
        all_jobs.extend(jobs)
        job_sources.extend(['jobs'] * len(jobs))
    
    if posted_jobs:
        all_jobs.extend(posted_jobs)
        job_sources.extend(['posted_jobs'] * len(posted_jobs))
    
    if not all_jobs:
        return []

    print(f"Computing similarities for {len(resumes)} resumes and {len(all_jobs)} jobs...")
    
    bert_matcher = BERTMatcher()

    resume_texts = [row[3] if len(row) > 2 and row[3] else "" for row in resumes]
    job_texts = [row[2] if len(row) > 2 and row[2] else "" for row in all_jobs]

    print("Encoding texts with BERT...")
    resume_embeddings = bert_matcher.encode_texts(resume_texts)
    job_embeddings = bert_matcher.encode_texts(job_texts)

    if len(resume_embeddings) > 0 and len(job_embeddings) > 0:
        bert_similarity_matrix = sklearn_cosine_similarity(resume_embeddings, job_embeddings)
    else:
        bert_similarity_matrix = np.zeros((len(resume_texts), len(job_texts)))

    resume_skills_list = [safe_json(r[4]) for r in resumes]
    job_skills_list = [safe_json(j[3]) for j in all_jobs]
    resume_edu_list = [safe_json(r[5]) for r in resumes]
    job_edu_list = [safe_json(j[4]) for j in all_jobs]
    resume_exp_list = [safe_json(r[6]) if len(r) > 5 else [] for r in resumes]
    job_exp_list = [safe_json(j[5]) if len(j) > 5 else [] for j in all_jobs]

    print("Computing component scores...")
    skill_scores = [[calculate_skill_similarity_bert(r_skills, j_skills, bert_matcher) 
                     for j_skills in job_skills_list] for r_skills in resume_skills_list]
    
    edu_scores = [[calculate_education_similarity_enhanced(r_edu, j_edu) 
                   for j_edu in job_edu_list] for r_edu in resume_edu_list]
    
    exp_scores = [[calculate_experience_similarity(r_exp, j_exp) 
                   for j_exp in job_exp_list] for r_exp in resume_exp_list]

    results = []
    for i, resume_row in enumerate(resumes):
        for j, job_row in enumerate(all_jobs):
            final_score = (
                weight_bert * float(bert_similarity_matrix[i][j]) +
                weight_skills * float(skill_scores[i][j]) +
                weight_education * float(edu_scores[i][j]) +
                weight_experience * float(exp_scores[i][j])
            )
            
            results.append({
                "resume_id": resume_row[0],
                "job_id": job_row[0],
                "job_source": job_sources[j],
                "creator_email": job_row[8] if len(job_row) > 8 else None,
                "final_score": final_score,
                "bert_score": float(bert_similarity_matrix[i][j]),
                "skill_score": float(skill_scores[i][j]),
                "education_score": float(edu_scores[i][j]),
                "experience_score": float(exp_scores[i][j])
            })

    print(f"Computed {len(results)} similarity scores")
    return results

def cosine_similarity(resumes, jobs, **kwargs):
    return compute_similarity_bert(resumes, jobs, **kwargs)

def compute_similarity(resumes, jobs, **kwargs):
    return compute_similarity_bert(resumes, jobs, **kwargs)