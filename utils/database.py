import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


def get_connection():
    conn = sqlite3.connect("resume_analyzer.db")
    conn.row_factory = sqlite3.Row  # lets you access columns by name, e.g. row['email']
    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            date_joined TEXT
        )
    """)

    # Analyses table with user_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.close()


def register_user(name, email, password):
    hashed = generate_password_hash(password)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, password, date_joined)
            VALUES (?, ?, ?, ?)
        """, (name, email, hashed, datetime.now().strftime("%d %b %Y")))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        return user
    return None


def save_analysis(user_id, resume_filename, ats_score, matched_skills, missing_skills):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analyses
        (user_id, resume_filename, ats_score, matched_skills, missing_skills, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        resume_filename,
        ats_score,
        ", ".join(matched_skills),
        ", ".join(missing_skills),
        datetime.now().strftime("%d %b %Y, %I:%M %p")
    ))
    conn.commit()
    conn.close()


def get_all_analyses(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_password(email, new_password):
    hashed = generate_password_hash(new_password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def check_email_exists(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user is not None


def get_dashboard_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE user_id=?", (user_id,))
    total = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(ats_score) FROM analyses WHERE user_id=?", (user_id,))
    highest = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(ats_score) FROM analyses WHERE user_id=?", (user_id,))
    average = cursor.fetchone()[0] or 0

    cursor.execute("SELECT * FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 3", (user_id,))
    recent = cursor.fetchall()

    conn.close()
    return {
        "total": total,
        "highest": round(highest, 1),
        "average": round(average, 1),
        "recent": recent
    }