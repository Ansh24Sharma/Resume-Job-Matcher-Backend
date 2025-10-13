import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime


def safe_json_loads(data):
    if data and data.strip():  # data is not None and not empty/whitespace
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON: {data}")
    return []


# ---------- MATCH FUNCTIONS ----------
def get_match_scores():
    """Fetch all match scores for admin dashboard."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.resume_id, m.job_id, m.job_source, m.final_score,
                   m.bert_score, m.skill_score, m.education_score, m.experience_score
            FROM matches m
            ORDER BY m.final_score DESC
        """)
        rows = cursor.fetchall()
        conn.close()
 
        matches = []
        for row in rows:
            matches.append({
                "id": row[0],
                "resume_id": row[1],
                "job_id": row[2],
                "job_source": row[3],
                "final_score": row[4],
                "bert_score": row[5],
                "skill_score": row[6],
                "education_score": row[7],
                "experience_score": row[8]
            })
        return matches
    except Exception as e:
        print(f"❌ Error fetching match scores: {e}")
        return []

def get_matches_for_recruiter(creator_email: str):
    """
    Fetch matches for recruiter dashboard with status 'applied'.
    Candidate name comes from users table via resumes.user_id.
    """
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.resume_id, m.job_id, m.job_source, m.final_score,
                   j.title, u.username, m.updated_at
            FROM matches m
            JOIN jobs j ON m.job_id = j.id AND m.job_source = 'jobs'
            JOIN resumes r ON m.resume_id = r.id
            JOIN users u ON r.user_id = u.id
            WHERE j.creator_email = %s AND m.save_status = 'applied'

            UNION ALL

            SELECT m.id, m.resume_id, m.job_id, m.job_source, m.final_score,
                   pj.title, u.username, m.updated_at
            FROM matches m
            JOIN posted_jobs pj ON m.job_id = pj.id AND m.job_source = 'posted_jobs'
            JOIN resumes r ON m.resume_id = r.id
            JOIN users u ON r.user_id = u.id
            WHERE pj.creator_email = %s AND m.save_status = 'applied'
        """, (creator_email, creator_email))
        rows = cursor.fetchall()
        conn.close()

        matches = []
        for row in rows:
            matches.append({
                "match_id": row[0],
                "resume_id": row[1],
                "job_id": row[2],
                "job_source": row[3],
                "final_score": row[4],
                "title": row[5],
                "name": row[6],  
                "updated_at": row[7]
            })
        return matches
    except Exception as e:
        print(f"❌ Error fetching applied matches: {e}")
        return []

def get_detailed_match_explanation(resume_id, job_id, job_source='jobs'):
    """Get detailed explanation of why a resume matches a job from specific source, including status and updated_at.
    Candidate name comes from users table via resumes.user_id.
    """
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if job_source == 'jobs':
        cursor.execute("""
        SELECT r.skills AS resume_skills, r.education AS resume_education, r.experience AS resume_experience,
            j.title AS job_title, j.skills AS job_skills, j.education AS job_education, j.experience AS job_experience,
            m.final_score, m.bert_score, m.skill_score, m.education_score, m.experience_score,
            m.updated_at, u.username AS name, c.status AS status
        FROM matches m
        JOIN resumes r ON m.resume_id = r.id
        JOIN users u ON r.user_id = u.id
        JOIN candidates c ON u.id = c.user_id
        JOIN jobs j ON m.job_id = j.id AND m.job_source = 'jobs'
        WHERE m.resume_id = %s AND m.job_id = %s AND m.job_source = 'jobs'
        """, (resume_id, job_id))
    else:
        cursor.execute("""
        SELECT r.skills AS resume_skills, r.education AS resume_education, r.experience AS resume_experience,
            pj.title AS job_title, pj.skills AS job_skills, pj.education AS job_education, pj.experience AS job_experience,
            m.final_score, m.bert_score, m.skill_score, m.education_score, m.experience_score,
            m.updated_at, u.username AS name, c.status AS status
        FROM matches m
        JOIN resumes r ON m.resume_id = r.id
        JOIN users u ON r.user_id = u.id
        JOIN candidates c ON u.id = c.user_id
        JOIN posted_jobs pj ON m.job_id = pj.id AND m.job_source = 'posted_jobs'
        WHERE m.resume_id = %s AND m.job_id = %s AND m.job_source = 'posted_jobs'
        """, (resume_id, job_id))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return {
        'resume_skills': safe_json_loads(result[0]),
        'resume_education': safe_json_loads(result[1]),
        'resume_experience': safe_json_loads(result[2]),
        'job_title': result[3],
        'job_skills': safe_json_loads(result[4]),
        'job_education': safe_json_loads(result[5]),
        'job_experience': safe_json_loads(result[6]),
        'scores': {
            'final_score': result[7],
            'bert_score': result[8],
            'skill_score': result[9],
            'education_score': result[10],
            'experience_score': result[11]
        },
        'updated_at': result[12],  
        'name': result[13],
        'status': result[14]
    }
