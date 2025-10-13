import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime

# ---------- RESUME FUNCTIONS ---------- 
def insert_resume(name: str, description: str, entities: dict, user_id: int = None):
    """Insert resume into DB with formatting preserved."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
 
        cursor.execute("""
            INSERT INTO resumes (user_id, name, description, skills, education, experience)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            name,
            description,  # ✅ Keep line breaks (\n)
            json.dumps(entities.get("skills", []), ensure_ascii=False),
            json.dumps(entities.get("education", []), ensure_ascii=False),
            json.dumps(entities.get("experience", []), ensure_ascii=False)
        ))
 
        conn.commit()
        print(f"✅ Resume inserted: {name}")
    except sql.Error as err:
        print(f"❌ MySQL Error while inserting resume: {err}")
    except Exception as e:
        print(f"⚠️ Unexpected Error while inserting resume: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()
 
 
def get_all_resumes():
    """Fetch all resumes for dashboard."""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name, description, skills, education, experience FROM resumes")
        rows = cursor.fetchall()
        conn.close()
 
        resumes = []
        for row in rows:
            resumes.append({
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "description": row[3],
                "skills": json.loads(row[4]) if row[4] else [],
                "education": json.loads(row[5]) if row[5] else [],
                "experience": json.loads(row[6]) if row[6] else []
            })
        return resumes
    except Exception as e:
        print(f"❌ Error fetching resumes: {e}")
        return []