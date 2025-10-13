import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime

# ---------- USER PROFILE FUNCTIONS ----------
def get_user_profile(user_id: int):
    """Get user profile by user_id"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, name, email, experience, skills, location, 
                   resume_filename, resume_file_path, upload_date, completion_percentage,
                   created_at, updated_at
            FROM user_profiles 
            WHERE user_id = %s
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "email": row[3],
                "experience": json.loads(row[4]) if row[4] else [],
                "skills": json.loads(row[5]) if row[5] else [],
                "location": row[6],
                "resume_filename": row[7],
                "resume_file_path": row[8],
                "upload_date": row[9],
                "completion_percentage": row[10] if row[10] is not None else 0,
                "created_at": row[11],
                "updated_at": row[12],
            }
        return None
    except Exception as e:
        print(f"❌ Error fetching user profile: {e}")
        return None


def update_user_profile(user_id: int, profile_data: dict):
    """Update user profile with provided data and sync to resumes table"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Build dynamic update query based on provided fields
        update_fields = []
        values = []
        
        # Track if we need to update resumes table
        resume_update_needed = False
        resume_update_data = {}
        
        if 'name' in profile_data:
            update_fields.append("name = %s")
            values.append(profile_data['name'])
            
        if 'email' in profile_data:
            update_fields.append("email = %s")
            values.append(profile_data['email'])
            
        if 'experience' in profile_data:
            update_fields.append("experience = %s")
            values.append(json.dumps(profile_data['experience'], ensure_ascii=False))
            resume_update_needed = True
            resume_update_data['experience'] = profile_data['experience']
            
        if 'skills' in profile_data:
            update_fields.append("skills = %s")
            values.append(json.dumps(profile_data['skills'], ensure_ascii=False))
            resume_update_needed = True
            resume_update_data['skills'] = profile_data['skills']
            
        if 'location' in profile_data:
            update_fields.append("location = %s")
            values.append(profile_data['location'])
            
        if 'resume_filename' in profile_data:
            update_fields.append("resume_filename = %s")
            values.append(profile_data['resume_filename'])
            
        if 'resume_file_path' in profile_data:
            update_fields.append("resume_file_path = %s")
            values.append(profile_data['resume_file_path'])
        
        # Add completion percentage if provided
        if 'completion_percentage' in profile_data:
            update_fields.append("completion_percentage = %s")
            values.append(profile_data['completion_percentage'])
        
        # Update user_profiles table
        if update_fields:
            query = f"UPDATE user_profiles SET {', '.join(update_fields)} WHERE user_id = %s"
            values.append(user_id)
            cursor.execute(query, values)
            conn.commit()
        
        # Update resumes table if skills or experience changed
        if resume_update_needed:
            resume_update_fields = []
            resume_values = []
            
            if 'skills' in resume_update_data:
                resume_update_fields.append("skills = %s")
                resume_values.append(json.dumps(resume_update_data['skills'], ensure_ascii=False))
            
            if 'experience' in resume_update_data:
                resume_update_fields.append("experience = %s")
                resume_values.append(json.dumps(resume_update_data['experience'], ensure_ascii=False))
            
            if resume_update_fields:
                resume_query = f"UPDATE resumes SET {', '.join(resume_update_fields)} WHERE user_id = %s"
                resume_values.append(user_id)
                cursor.execute(resume_query, resume_values)
                conn.commit()
                print(f"✅ Updated resumes table for user_id: {user_id}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating user profile: {e}")
        if conn:
            conn.close()
        return False


def update_profile_from_resume(user_id: int, filename: str, file_path: str, entities: dict):
    """Update profile when resume is uploaded and sync to resumes table"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        skills_json = json.dumps(entities.get("skills", []), ensure_ascii=False)
        experience_json = json.dumps(entities.get("experience", []), ensure_ascii=False)
        upload_date = datetime.now()
        
        # Update user_profiles table
        cursor.execute("""
            UPDATE user_profiles 
            SET resume_filename = %s, 
                resume_file_path = %s,
                skills = %s,
                experience = %s,
                upload_date = %s
            WHERE user_id = %s
        """, (
            filename,
            file_path,
            skills_json,
            experience_json,
            upload_date,
            user_id
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Updated both user_profiles and resumes tables for user_id: {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error updating profile from resume: {e}")
        if conn:
            conn.close()
        return False


def get_all_user_profiles():
    """Get all user profiles for admin dashboard"""
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT up.id, up.user_id, up.name, up.email, up.experience, up.skills, 
                   up.location, up.resume_filename, up.upload_date, up.completion_percentage,
                   u.username, u.role
            FROM user_profiles up
            JOIN users u ON up.user_id = u.id
            ORDER BY up.updated_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        profiles = []
        for row in rows:
            profiles.append({
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "email": row[3],
                "experience": json.loads(row[4]) if row[4] else [],
                "skills": json.loads(row[5]) if row[5] else [],
                "location": row[6],
                "resume_filename": row[7],
                "upload_date": row[8],
                "completion_percentage": row[9] if row[9] is not None else 0,
                "username": row[10],
                "role": row[11]
            })
        return profiles
    except Exception as e:
        print(f"❌ Error fetching all user profiles: {e}")
        return []
 