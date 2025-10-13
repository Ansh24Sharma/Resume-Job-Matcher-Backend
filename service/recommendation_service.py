from service.db import init_db
from matcher import compute_similarity_bert
import MySQLdb as sql
from config import DB_CONFIG
import json
from models.recommendation_models import SaveJobStatus

def safe_json_loads(data):
    if data and data.strip():  # data is not None and not empty/whitespace
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse JSON: {data}")
    return []


def run_matcher():
    """Run the enhanced BERT matcher and store results into DB"""
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch resumes and jobs
    cursor.execute("SELECT * FROM resumes")
    resumes = cursor.fetchall()

    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()

    cursor.execute("SELECT * FROM posted_jobs")
    posted_jobs = cursor.fetchall()

    if not resumes:
        print("No resumes found in database")
        conn.close()
        return

    if not jobs and not posted_jobs:
        print("No jobs or posted_jobs found in database")
        conn.close()
        return

    print(f"Computing BERT-based matches for {len(resumes)} resumes, {len(jobs) if jobs else 0} jobs, and {len(posted_jobs) if posted_jobs else 0} posted_jobs...")
    
    # Use the new BERT matcher with priority weighting
    results = compute_similarity_bert(
        resumes, jobs, posted_jobs,
        weight_bert=0.4,        # BERT semantic similarity
        weight_skills=0.35,     # Skills matching (highest priority)
        weight_education=0.15,  # Education matching  
        weight_experience=0.1   # Experience matching
    )

    # Clear old matches that are not saved
    cursor.execute("DELETE FROM matches WHERE save_status = 'not_saved'")

    # Insert matches with BERT scores
    for r in results:
        cursor.execute("""
        INSERT INTO matches (resume_id, job_id, job_source, creator_email, final_score, bert_score, skill_score, education_score, experience_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            final_score = VALUES(final_score),
            bert_score = VALUES(bert_score),
            skill_score = VALUES(skill_score),
            education_score = VALUES(education_score),
            experience_score = VALUES(experience_score),
            creator_email = VALUES(creator_email),
            updated_at = CURRENT_TIMESTAMP
        """, (r["resume_id"], r["job_id"], r["job_source"], r["creator_email"], r["final_score"], r["bert_score"],
            r["skill_score"], r["education_score"], r["experience_score"]))

    conn.commit()
    conn.close()
    print(f"Stored {len(results)} BERT-enhanced match results")


def fetch_saved_jobs(resume_id):
    """
    Fetch all saved jobs for a resume
    
    Args:
        resume_id: The resume ID to fetch saved jobs for
    
    Returns:
        List of saved job recommendations
    """
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        (SELECT j.id AS job_id, j.title, j.description, m.final_score,
            m.bert_score, m.skill_score, m.education_score, m.experience_score,
            m.job_source, 'jobs' as table_source, m.id as match_id,
            j.company, j.location, NULL as job_type, j.experience,
            NULL as salary, j.education, j.skills
        FROM matches m
        JOIN jobs j ON m.job_id = j.id AND m.job_source = 'jobs'
        WHERE m.resume_id = %s AND m.save_status = 'saved')
        UNION ALL
        (SELECT pj.id AS job_id, pj.title, pj.description, m.final_score,
               m.bert_score, m.skill_score, m.education_score, m.experience_score,
               m.job_source, 'posted_jobs' as table_source, m.id as match_id,
               pj.company, pj.location, pj.job_type, pj.experience,
               pj.salary, pj.education, pj.skills
        FROM matches m
        JOIN posted_jobs pj ON m.job_id = pj.id AND m.job_source = 'posted_jobs'
        WHERE m.resume_id = %s AND m.save_status = 'saved')
        ORDER BY final_score DESC
        """, (resume_id, resume_id))
        
        results = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary format
        recommendations = []
        for row in results:
            recommendations.append({
                'job_id': row[0],
                'title': row[1],
                'description': row[2],
                'final_score': row[3],
                'bert_score': row[4],
                'skill_score': row[5],
                'education_score': row[6],
                'experience_score': row[7],
                'job_source': row[8],
                'table_source': row[9],
                'match_id': row[10],
                'company': row[11],
                'location': row[12],
                'job_type': row[13],
                'experience': row[14],
                'salary': row[15],
                'education': row[16],
                'skills': safe_json_loads(row[17])
            })
        
        return recommendations
    
    except Exception as e:
        conn.close()
        print(f"Error fetching saved jobs: {str(e)}")
        return []


def get_user_active_resume_id(user_id):
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM resumes
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_top_recommendations(resume_id, top_n=5):
    """Fetch top N job recommendations for a resume from BOTH jobs and posted_jobs tables"""
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Updated UNION query to select m.id as match_id
    cursor.execute("""
    (SELECT j.id AS job_id, j.title, j.description, m.final_score,
           m.bert_score, m.skill_score, m.education_score, m.experience_score,
           m.job_source, 'jobs' as table_source, m.id as match_id
    FROM matches m
    JOIN jobs j ON m.job_id = j.id AND m.job_source = 'jobs'
    WHERE m.resume_id = %s)
    UNION ALL
    (SELECT pj.id AS job_id, pj.title, pj.description, m.final_score,
           m.bert_score, m.skill_score, m.education_score, m.experience_score,
           m.job_source, 'posted_jobs' as table_source, m.id as match_id
    FROM matches m
    JOIN posted_jobs pj ON m.job_id = pj.id AND m.job_source = 'posted_jobs'
    WHERE m.resume_id = %s)
    ORDER BY final_score DESC
    LIMIT %s
    """, (resume_id, resume_id, top_n))

    results = cursor.fetchall()
    conn.close()
    
    # Convert to dictionary format
    recommendations = []
    for row in results:
        recommendations.append({
            'job_id': row[0],
            'title': row[1],
            'description': row[2],
            'final_score': row[3],
            'bert_score': row[4],
            'skill_score': row[5],
            'education_score': row[6],
            'experience_score': row[7],
            'job_source': row[8],  # Include source info
            'table_source': row[9], # For debugging
            'match_id': row[10]    # Added match ID here
        })
    
    return recommendations

def update_job_save_status(match_id: int, save_status: SaveJobStatus):
    """
    Update the save_status of a match in the database

    Args:
        match_id: The ID of the match to update
        save_status: The new save status ('saved' or 'not_saved')

    Returns:
        Dictionary with success status and message
    """
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Verify the match exists
        cursor.execute("SELECT id FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if not match:
            conn.close()
            return {
                'success': False,
                'message': f"Match with ID {match_id} not found"
            }

        # Update the save_status
        cursor.execute("""
            UPDATE matches 
            SET save_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (save_status.value, match_id))


        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return {
                'success': False,
                'message': "No changes were made"
            }

        conn.close()
        return {
            'success': True,
            'message': f"Job save status updated to '{save_status.value}' successfully"
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            'success': False,
            'message': f"Database error: {str(e)}"
        }
    
def update_job_status_to_applied(match_id: int):
    """
    Update the save_status of a match to 'applied' in the database

    Args:
        match_id: The ID of the match to update

    Returns:
        Dictionary with success status and message
    """
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Verify the match exists
        cursor.execute("SELECT id FROM matches WHERE id = %s", (match_id,))
        match = cursor.fetchone()

        if not match:
            conn.close()
            return {
                'success': False,
                'message': f"Match with ID {match_id} not found"
            }

        # Update the save_status to 'applied'
        cursor.execute("""
            UPDATE matches 
            SET save_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ('applied', match_id))

        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return {
                'success': False,
                'message': "No changes were made"
            }

        conn.close()
        return {
            'success': True,
            'message': f"Job save status updated to 'applied' successfully"
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {
            'success': False,
            'message': f"Database error: {str(e)}"
        }

def get_skills_based_recommendations(resume_id, top_n=5):
    """Get recommendations prioritized by skills similarity from BOTH tables"""
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
    (SELECT j.id AS job_id, j.title, j.description, m.final_score,
           m.bert_score, m.skill_score, m.education_score, m.experience_score,
           m.job_source
    FROM matches m
    JOIN jobs j ON m.job_id = j.id AND m.job_source = 'jobs'
    WHERE m.resume_id = %s)
    UNION ALL
    (SELECT pj.id AS job_id, pj.title, pj.description, m.final_score,
           m.bert_score, m.skill_score, m.education_score, m.experience_score,
           m.job_source
    FROM matches m
    JOIN posted_jobs pj ON m.job_id = pj.id AND m.job_source = 'posted_jobs'
    WHERE m.resume_id = %s)
    ORDER BY skill_score DESC, final_score DESC
    LIMIT %s
    """, (resume_id, resume_id, top_n))

    results = cursor.fetchall()
    conn.close()
    
    recommendations = []
    for row in results:
        recommendations.append({
            'job_id': row[0],
            'title': row[1],
            'description': row[2],
            'final_score': row[3],
            'bert_score': row[4],
            'skill_score': row[5],
            'education_score': row[6],
            'experience_score': row[7],
            'job_source': row[8]
        })
    
    return recommendations


