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

# ---------- CANDIDATE FUNCTIONS ----------
def create_candidate_from_match(match_id: int):
    """Create a candidate entry when a match is created"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get match details
        cursor.execute("""
            SELECT m.resume_id, m.job_id, m.job_source, m.creator_email,
                   r.user_id
            FROM matches m
            JOIN resumes r ON m.resume_id = r.id
            WHERE m.id = %s
        """, (match_id,))
        
        match_data = cursor.fetchone()
        if not match_data:
            print(f"⚠️ Match not found: {match_id}")
            conn.close()
            return False
        
        resume_id, job_id, job_source, creator_email, user_id = match_data
        
        # Get profile_id
        cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
        profile_row = cursor.fetchone()
        if not profile_row:
            print(f"⚠️ Profile not found for user_id: {user_id}")
            conn.close()
            return False
        
        profile_id = profile_row[0]
        
        # Insert candidate
        cursor.execute("""
            INSERT INTO candidates (match_id, user_id, profile_id, job_id, job_source, creator_email, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'available')
        """, (match_id, user_id, profile_id, job_id, job_source, creator_email))
        
        conn.commit()
        conn.close()
        print(f"✅ Candidate created for match_id: {match_id}")
        return True
        
    except sql.IntegrityError:
        # Candidate already exists
        if conn:
            conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating candidate: {e}")
        if conn:
            conn.close()
        return False


def get_candidates_by_recruiter(creator_email: str):
    """Get all candidates for a specific recruiter without filters"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                c.id as candidate_id,
                c.match_id,
                c.user_id,
                c.profile_id,
                c.job_id,
                c.job_source,
                c.status,
                c.contacted_at,
                c.interview_scheduled_at,
                c.created_at,
                c.updated_at,
                m.final_score,
                m.bert_score,
                m.skill_score,
                m.education_score,
                m.experience_score,
                up.name,
                up.email,
                up.location,
                up.skills,
                up.experience,
                up.resume_filename,
                up.upload_date,
                CASE 
                    WHEN c.job_source = 'jobs' THEN j.title
                    ELSE pj.title
                END as job_title,
                CASE 
                    WHEN c.job_source = 'jobs' THEN j.company
                    ELSE pj.company
                END as company
            FROM candidates c
            JOIN matches m ON c.match_id = m.id
            JOIN user_profiles up ON c.profile_id = up.id
            LEFT JOIN jobs j ON c.job_id = j.id AND c.job_source = 'jobs'
            LEFT JOIN posted_jobs pj ON c.job_id = pj.id AND c.job_source = 'posted_jobs'
            WHERE c.creator_email = %s
            ORDER BY m.final_score DESC
        """

        cursor.execute(query, (creator_email,))
        rows = cursor.fetchall()
        conn.close()

        candidates = []
        for row in rows:
            candidate_skills = safe_json_loads(row[19])
            candidate_experience = safe_json_loads(row[20])

            candidates.append({
                "candidate_id": row[0],
                "match_id": row[1],
                "user_id": row[2],
                "profile_id": row[3],
                "job_id": row[4],
                "job_source": row[5],
                "status": row[6],
                "contacted_at": row[7],
                "interview_scheduled_at": row[8],
                "created_at": row[9],
                "updated_at": row[10],
                "final_score": round(float(row[11]), 2) if row[11] else 0,
                "bert_score": round(float(row[12]), 2) if row[12] else 0,
                "skill_score": round(float(row[13]), 2) if row[13] else 0,
                "education_score": round(float(row[14]), 2) if row[14] else 0,
                "experience_score": round(float(row[15]), 2) if row[15] else 0,
                "name": row[16],
                "email": row[17],
                "location": row[18],
                "skills": candidate_skills,
                "experience": candidate_experience,
                "resume_filename": row[21],
                "upload_date": row[22],
                "job_title": row[23],
                "company": row[24]
            })

        return candidates

    except Exception as e:
        print(f"❌ Error fetching candidates by recruiter: {e}")
        return []


def get_candidate_by_id(candidate_id: int):
    """Get detailed information about a specific candidate"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.id as candidate_id,
                c.match_id,
                c.user_id,
                c.profile_id,
                c.job_id,
                c.job_source,
                c.status,
                c.contacted_at,
                c.interview_scheduled_at,
                c.created_at,
                c.updated_at,
                m.final_score,
                m.bert_score,
                m.skill_score,
                m.education_score,
                m.experience_score,
                up.name,
                up.email,
                up.location,
                up.skills,
                up.experience,
                up.resume_filename,
                up.resume_file_path,
                up.upload_date,
                CASE 
                    WHEN c.job_source = 'jobs' THEN j.title
                    ELSE pj.title
                END as job_title,
                CASE 
                    WHEN c.job_source = 'jobs' THEN j.company
                    ELSE pj.company
                END as company,
                CASE 
                    WHEN c.job_source = 'jobs' THEN j.description
                    ELSE pj.description
                END as job_description
            FROM candidates c
            JOIN matches m ON c.match_id = m.id
            JOIN user_profiles up ON c.profile_id = up.id
            LEFT JOIN jobs j ON c.job_id = j.id AND c.job_source = 'jobs'
            LEFT JOIN posted_jobs pj ON c.job_id = pj.id AND c.job_source = 'posted_jobs'
            WHERE c.id = %s
        """, (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "candidate_id": row[0],
            "match_id": row[1],
            "user_id": row[2],
            "profile_id": row[3],
            "job_id": row[4],
            "job_source": row[5],
            "status": row[6],
            "contacted_at": row[7],
            "interview_scheduled_at": row[8],
            "created_at": row[9],
            "updated_at": row[10],
            "final_score": round(float(row[11]), 2) if row[11] else 0,
            "bert_score": round(float(row[12]), 2) if row[12] else 0,
            "skill_score": round(float(row[13]), 2) if row[13] else 0,
            "education_score": round(float(row[14]), 2) if row[14] else 0,
            "experience_score": round(float(row[15]), 2) if row[15] else 0,
            "name": row[16],
            "email": row[17],
            "location": row[18],
            "skills": safe_json_loads(row[19]),
            "experience": safe_json_loads(row[20]),
            "resume_filename": row[21],
            "resume_file_path": row[22],
            "upload_date": row[23],
            "job_title": row[24],
            "company": row[25],
            "job_description": row[26]
        }
    except Exception as e:
        print(f"❌ Error fetching candidate by id: {e}")
        return None


def update_candidate_status(candidate_id: int, new_status: str):
    """Update candidate status"""
    conn = None
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM candidates WHERE id = %s", (candidate_id,))
        current_row = cursor.fetchone()
        
        if not current_row:
            print(f"❌ Candidate ID {candidate_id} not found")
            return False
        
        current_status = current_row[0]
        
        # Update with proper timestamp logic
        if current_status == 'available' and new_status != 'available':
            cursor.execute("""
                UPDATE candidates 
                SET status = %s, 
                    contacted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, candidate_id))
            
        elif new_status == 'interview_scheduled':
            cursor.execute("""
                UPDATE candidates 
                SET status = %s, 
                    interview_scheduled_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, candidate_id))
            
        else:
            cursor.execute("""
                UPDATE candidates 
                SET status = %s, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_status, candidate_id))
        
        conn.commit()
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            print(f"✅ Candidate status updated: ID {candidate_id} -> {new_status}")
            return True
        
        return False
    
    except Exception as e:
        print(f"❌ Error updating candidate status: {e}")
        return False
    
    finally:
        if conn:
            conn.close()


def get_candidate_statistics(creator_email: str):
    """Get candidate statistics for a recruiter's dashboard"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Total candidates
        cursor.execute("""
            SELECT COUNT(*) FROM candidates WHERE creator_email = %s
        """, (creator_email,))
        total_candidates = cursor.fetchone()[0]
        
        # Candidates by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM candidates
            WHERE creator_email = %s
            GROUP BY status
        """, (creator_email,))
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Average match score
        cursor.execute("""
            SELECT AVG(m.final_score)
            FROM candidates c
            JOIN matches m ON c.match_id = m.id
            WHERE c.creator_email = %s
        """, (creator_email,))
        avg_score_row = cursor.fetchone()
        avg_score = round(avg_score_row[0], 2) if avg_score_row[0] else 0
        
        # Recent candidates (last 7 days)
        cursor.execute("""
            SELECT COUNT(*)
            FROM candidates
            WHERE creator_email = %s
            AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """, (creator_email,))
        recent_candidates = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_candidates": total_candidates,
            "available": status_counts.get('available', 0),
            "interview_scheduled": status_counts.get('interview_scheduled', 0),
            "under_review": status_counts.get('under_review', 0),
            "hired": status_counts.get('hired', 0),
            "rejected": status_counts.get('rejected', 0),
            "average_match_score": avg_score,
            "recent_candidates": recent_candidates
        }
    except Exception as e:
        print(f"❌ Error fetching candidate statistics: {e}")
        return {
            "total_candidates": 0,
            "available": 0,
            "interview_scheduled": 0,
            "under_review": 0,
            "hired": 0,
            "rejected": 0,
            "average_match_score": 0,
            "recent_candidates": 0
        }