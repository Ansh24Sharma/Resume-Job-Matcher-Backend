import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime

# ---------- JOB FUNCTIONS ----------
def insert_job(title: str, description: str, entities: dict, company: str = None, 
               location: str = None, creator_email: str = None):
    """
    Insert job into jobs table with creator email and job_source automatically set to 'jobs'
    """
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
 
        cursor.execute("""
            INSERT INTO jobs (
                title, description, company, location, creator_email, 
                skills, education, experience, job_source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            title,
            description,
            company,
            location,
            creator_email,
            json.dumps(entities.get("skills", []), ensure_ascii=False),
            json.dumps(entities.get("education", []), ensure_ascii=False),
            json.dumps(entities.get("experience", []), ensure_ascii=False),
            'jobs'  # Explicitly set job_source to 'jobs'
        ))
 
        conn.commit()
        job_id = cursor.lastrowid
        print(f"✅ Job inserted: {title} (ID: {job_id}, Source: jobs)")
        return job_id
    except sql.Error as err:
        print(f"❌ MySQL Error while inserting job: {err}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected Error while inserting job: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()


def get_all_jobs():
    """Fetch all jobs for dashboard."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, skills, education, experience, 
                   company, location, creator_email, job_type, salary, status, created_at
            FROM jobs
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
 
        jobs = []
        for row in rows:
            jobs.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "skills": json.loads(row[3]) if row[3] else [],
                "education": json.loads(row[4]) if row[4] else [],
                "experience": json.loads(row[5]) if row[5] else [],
                "company": row[6],
                "location": row[7],
                "creator_email": row[8],
                "job_type": row[9],
                "salary": row[10],
                "status": row[11],
                "created_at": row[12]
            })
        return jobs
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        return []


def get_jobs_by_creator(creator_email: str):
    """Get all jobs created by a specific recruiter"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, description, skills, education, experience, 
                   company, location, creator_email, job_type, salary, status, job_source, created_at, updated_at
            FROM jobs
            WHERE creator_email = %s
            ORDER BY created_at DESC
        """, (creator_email,))
        rows = cursor.fetchall()
        conn.close()
 
        jobs = []
        for row in rows:
            jobs.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "skills": json.loads(row[3]) if row[3] else [],
                "education": json.loads(row[4]) if row[4] else [],
                "experience": json.loads(row[5]) if row[5] else [],
                "company": row[6],
                "location": row[7],
                "creator_email": row[8],
                "job_type": row[9],
                "salary": row[10],
                "status": row[11],
                "job_source": row[12],
                "created_at": row[13],
                "updated_at": row[14]
            })
        return jobs
    except Exception as e:
        print(f"❌ Error fetching jobs by creator: {e}")
        return []


def update_job(job_id: int, creator_email: str, update_data: dict):
    """
    Update a job in the jobs table
    """
    def row_to_dict(cursor, row):
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))

    try:
        connection = sql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Verify job belongs to creator
        cursor.execute(
            "SELECT * FROM jobs WHERE id = %s AND creator_email = %s",
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
            UPDATE jobs 
            SET {', '.join(update_fields)}
            WHERE id = %s AND creator_email = %s
        """

        cursor.execute(query, params)
        connection.commit()

        # Fetch updated job
        cursor.execute(
            "SELECT * FROM jobs WHERE id = %s",
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
        print(f"❌ MySQL Error while updating job: {err}")
        return False

    except Exception as e:
        print(f"Error updating job: {e}")
        connection.rollback()
        return None

