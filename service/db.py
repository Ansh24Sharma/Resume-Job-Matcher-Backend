import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime
 
# ---------- INIT ----------
def init_db():
    try:
        print("🔹 Connecting to MySQL...")
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
 
        # Users table (no changes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role ENUM('user', 'recruiter', 'admin') DEFAULT 'user'
        );
        """)
 
        # User Profiles table (no changes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            name VARCHAR(255),
            email VARCHAR(255),
            experience JSON,
            skills JSON,
            education JSON,
            location VARCHAR(255),
            resume_filename VARCHAR(255),
            resume_file_path VARCHAR(500),
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_percentage INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_completion (completion_percentage)
        );
        """)

        # Resumes table (no changes)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            name VARCHAR(255),
            description LONGTEXT,
            skills JSON,
            education JSON,
            experience JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """)
 
        # Jobs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            description LONGTEXT,
            skills JSON,
            education JSON,
            experience JSON,
            company VARCHAR(255),
            location VARCHAR(255),
            creator_email VARCHAR(255),
            job_type ENUM('full-time', 'part-time', 'internship', 'remote') NOT NULL,
            salary VARCHAR(255),
            status ENUM('active', 'closed') DEFAULT 'active',
            job_source ENUM('jobs', 'posted_jobs') NOT NULL DEFAULT 'jobs',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_creator_email (creator_email),
            INDEX idx_job_source (job_source)
        );
        """)

        # Posted Jobs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posted_jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description LONGTEXT,
            skills JSON,
            education JSON,
            experience JSON,
            company VARCHAR(255),
            location VARCHAR(255),
            creator_email VARCHAR(255),
            job_type ENUM('full-time', 'part-time', 'internship', 'remote') NOT NULL,
            salary VARCHAR(255),
            status ENUM('active', 'closed') DEFAULT 'active',
            job_source ENUM('jobs', 'posted_jobs') NOT NULL DEFAULT 'jobs',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_creator_email (creator_email),
            INDEX idx_job_source (job_source)
        );
        """)
 
        # Matches table - REMOVED status field
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            resume_id INT,
            job_id INT,
            job_source ENUM('jobs', 'posted_jobs') NOT NULL DEFAULT 'jobs',
            creator_email VARCHAR(255),
            final_score FLOAT,
            bert_score FLOAT,
            skill_score FLOAT,
            education_score FLOAT,
            experience_score FLOAT,
            save_status ENUM('saved', 'not_saved', 'applied') NOT NULL DEFAULT 'not_saved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
            INDEX idx_resume_score (resume_id, final_score DESC),
            INDEX idx_job_score (job_id, final_score DESC),
            INDEX idx_creator_email (creator_email),
            INDEX idx_job_source (job_source),
            INDEX idx_resume_job_source (resume_id, job_source),
            INDEX idx_job_source_score (job_source, final_score DESC),
            UNIQUE KEY unique_match (resume_id, job_id, job_source)
        );
        """)

        # NEW Candidates table - Central table for recruiter's candidate management
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            match_id INT NOT NULL,
            user_id INT NOT NULL,
            profile_id INT NOT NULL,
            job_id INT NOT NULL,
            job_source ENUM('jobs', 'posted_jobs') NOT NULL,
            creator_email VARCHAR(255) NOT NULL,
            status ENUM('available', 'interview_scheduled', 'under_review', 'hired', 'rejected') DEFAULT 'available',
            contacted_at TIMESTAMP NULL,
            interview_scheduled_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
            INDEX idx_creator_email (creator_email),
            INDEX idx_creator_status (creator_email, status),
            INDEX idx_match_id (match_id),
            INDEX idx_user_id (user_id),
            INDEX idx_job_source (job_source),
            INDEX idx_job_id_source (job_id, job_source),
            UNIQUE KEY unique_candidate (match_id, creator_email)
        );
        """)
 
        conn.commit()
        conn.close()
        print("✅ Database and tables initialized successfully.")
 
    except sql.Error as err:
        print(f"❌ MySQL Error: {err}")
    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")
 
 

 





