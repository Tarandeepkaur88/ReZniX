import os
import psycopg2
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            date_joined TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            resume_filename TEXT,
            ats_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def register_user(name, email, password):
    hashed = generate_password_hash(password)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password, date_joined)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed, datetime.now().strftime("%d %b %Y")))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        conn.close()
        return False

def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user[3], password):
        return user
    return None

def save_analysis(user_id, resume_filename, ats_score, matched_skills, missing_skills):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analyses
        (user_id, resume_filename, ats_score, matched_skills, missing_skills, date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        resume_filename,
        ats_score,
        ", ".join(matched_skills),
        ", ".join(missing_skills),
        datetime.now().strftime("%d %b %Y, %I:%M %p")
    ))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_analyses(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM analyses WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def update_password(email, new_password):
    hashed = generate_password_hash(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    if user:
        cursor.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (hashed, email)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    cursor.close()
    conn.close()
    return False

def check_email_exists(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

def get_dashboard_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM analyses WHERE user_id=%s",
        (user_id,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT MAX(ats_score) FROM analyses WHERE user_id=%s",
        (user_id,)
    )
    highest = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT AVG(ats_score) FROM analyses WHERE user_id=%s",
        (user_id,)
    )
    average = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT * FROM analyses WHERE user_id=%s ORDER BY id DESC LIMIT 3",
        (user_id,)
    )
    recent = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "total": total,
        "highest": round(float(highest), 1),
        "average": round(float(average), 1),
        "recent": recent
    }