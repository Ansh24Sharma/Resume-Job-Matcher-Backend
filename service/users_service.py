import MySQLdb as sql
import json
from config import DB_CONFIG
from datetime import datetime

# ---------- USER FUNCTIONS ----------
def create_user(username: str, email: str, password: str, role: str = "user"):
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (username, email, password, role))
        user_id = cursor.lastrowid
        
        # Create initial profile entry
        cursor.execute("""
            INSERT INTO user_profiles (user_id, email, name)
            VALUES (%s, %s, %s)
        """, (user_id, email, username))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
 
 
def get_user_by_username(username: str):
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        return None
    
def get_user_by_email(email: str):
    try:
        conn = sql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"❌ Error fetching user: {e}")
        return None
     