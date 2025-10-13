import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime

# ---------- POSTED JOB FUNCTIONS ----------
def insert_posted_job(title: str, description: str, entities: dict, company: str = None, 
                     location: str = None, job_type: str = None, salary: str = None,
                     creator_email: str = None):
    """
    Insert posted job into posted_jobs table with creator email and job_source automatically set to 'posted_jobs'
    """
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
 
        cursor.execute("""
            INSERT INTO posted_jobs (
                title, description, company, location, job_type, salary, 
                creator_email, skills, education, experience, job_source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title,
            description,
            company,
            location,
            job_type,
            salary,
            creator_email,
            json.dumps(entities.get("skills", []), ensure_ascii=False),
            json.dumps(entities.get("education", []), ensure_ascii=False),
            json.dumps(entities.get("experience", []), ensure_ascii=False),
            'posted_jobs'  # Explicitly set job_source to 'posted_jobs'
        ))
 
        conn.commit()
        job_id = cursor.lastrowid
        print(f"✅ Posted job inserted: {title} (ID: {job_id}, Source: posted_jobs)")
        return job_id
    except sql.Error as err:
        print(f"❌ MySQL Error while inserting posted job: {err}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected Error while inserting posted job: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_all_posted_jobs():
    """Fetch all posted jobs for dashboard."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, company, location, job_type, salary, 
                   skills, education, experience, creator_email, status, created_at, updated_at 
            FROM posted_jobs
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
 
        posted_jobs = []
        for row in rows:
            posted_jobs.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "company": row[3],
                "location": row[4],
                "job_type": row[5],
                "salary": row[6],
                "skills": json.loads(row[7]) if row[7] else [],
                "education": json.loads(row[8]) if row[8] else [],
                "experience": json.loads(row[9]) if row[9] else [],
                "creator_email": row[10],
                "status": row[11],
                "created_at": row[12],
                "updated_at": row[13]
            })
        return posted_jobs
    except Exception as e:
        print(f"❌ Error fetching posted jobs: {e}")
        return []


def get_posted_jobs_by_creator(creator_email: str):
    """Get all posted jobs created by a specific recruiter"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, company, location, job_type, salary, 
                   skills, education, experience, creator_email, status, job_source, created_at, updated_at 
            FROM posted_jobs
            WHERE creator_email = %s
            ORDER BY created_at DESC
        """, (creator_email,))
        rows = cursor.fetchall()
        conn.close()
 
        posted_jobs = []
        for row in rows:
            posted_jobs.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "company": row[3],
                "location": row[4],
                "job_type": row[5],
                "salary": row[6],
                "skills": json.loads(row[7]) if row[7] else [],
                "education": json.loads(row[8]) if row[8] else [],
                "experience": json.loads(row[9]) if row[9] else [],
                "creator_email": row[10],
                "status": row[11],
                "job_source": row[12],
                "created_at": row[13],
                "updated_at": row[14]
            })
        return posted_jobs
    except Exception as e:
        print(f"❌ Error fetching posted jobs by creator: {e}")
        return []
    

def delete_posted_job(job_id: int):
    """Delete a posted job."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Delete associated matches and candidates
        cursor.execute("DELETE FROM candidates WHERE job_id = %s AND job_source = 'posted_jobs'", (job_id,))
        cursor.execute("DELETE FROM matches WHERE job_id = %s AND job_source = 'posted_jobs'", (job_id,))
        
        # Delete the job
        cursor.execute("DELETE FROM posted_jobs WHERE id = %s", (job_id,))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        if rows_affected > 0:
            print(f"✅ Posted job deleted: ID {job_id}")
            return True
        else:
            print(f"⚠️ No posted job found with ID {job_id}")
            return False
            
    except sql.Error as err:
        print(f"❌ MySQL Error while deleting posted job: {err}")
        return False
    except Exception as e:
        print(f"⚠️ Unexpected Error while deleting posted job: {e}")
        return False
    
def update_posted_job(job_id: int, creator_email: str, update_data: dict):
    """
    Update a job in the posted_jobs table
    """
    def row_to_dict(cursor, row):
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    try:
        connection = sql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # First verify the job belongs to the creator
        cursor.execute(
            "SELECT * FROM posted_jobs WHERE id = %s AND creator_email = %s",
            (job_id, creator_email)
        )
        job = cursor.fetchone()
        
        if not job:
            return None
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        for key, value in update_data.items():
            if value is not None:
                if key in ['skills', 'education', 'experience']:
                    # Convert list to JSON string
                    update_fields.append(f"{key} = %s")
                    params.append(json.dumps(value))
                else:
                    update_fields.append(f"{key} = %s")
                    params.append(value)
        
        if not update_fields:
            # Nothing to update, return current job as dict
            return row_to_dict(cursor, job)
        
        params.append(job_id)
        params.append(creator_email)
        
        query = f"""
            UPDATE posted_jobs 
            SET {', '.join(update_fields)}
            WHERE id = %s AND creator_email = %s
        """
        
        cursor.execute(query, params)
        connection.commit()
        
        # Fetch updated job
        cursor.execute(
            "SELECT * FROM posted_jobs WHERE id = %s",
            (job_id,)
        )
        updated_job_row = cursor.fetchone()
        
        if updated_job_row:
            updated_job = row_to_dict(cursor, updated_job_row)
            
            if updated_job.get('skills'):
                updated_job['skills'] = json.loads(updated_job['skills'])
            if updated_job.get('education'):
                updated_job['education'] = json.loads(updated_job['education'])
            if updated_job.get('experience'):
                updated_job['experience'] = json.loads(updated_job['experience'])
        else:
            updated_job = None
        
        cursor.close()
        return updated_job
    
    except sql.Error as err:
        print(f"❌ MySQL Error while updating posted job: {err}")
        return False
        
    except Exception as e:
        print(f"Error updating posted job: {e}")
        connection.rollback()
        return None
