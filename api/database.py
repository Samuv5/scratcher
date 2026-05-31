import sqlite3
import os
import json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "scratcher.db")


def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_text TEXT NOT NULL,
            skills TEXT DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL DEFAULT 'Position',
            company TEXT DEFAULT '',
            location TEXT DEFAULT '',
            description TEXT DEFAULT '',
            requirements TEXT DEFAULT '[]',
            source TEXT DEFAULT 'manual',
            source_url TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS optimizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cv_id INTEGER REFERENCES cvs(id),
            job_id INTEGER REFERENCES jobs(id),
            job_title TEXT NOT NULL,
            original_cv TEXT NOT NULL,
            optimized_cv TEXT NOT NULL,
            template TEXT DEFAULT 'modern',
            used_ai INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# --- CV operations ---

def save_cv(filename, original_text, skills=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO cvs (filename, original_text, skills) VALUES (?, ?, ?)",
        (filename, original_text, json.dumps(skills or []))
    )
    conn.commit()
    cv_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return cv_id


def get_cv(cv_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM cvs WHERE id = ?", (cv_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_cvs(limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, filename, skills, created_at FROM cvs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Job operations ---

def save_job(title, company="", location="", description="", requirements=None, source="manual", source_url=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO jobs (title, company, location, description, requirements, source, source_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, company, location, description[:5000], json.dumps(requirements or []), source, source_url)
    )
    conn.commit()
    job_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return job_id


def get_job(job_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["requirements"] = json.loads(d["requirements"]) if isinstance(d["requirements"], str) else d["requirements"]
        return d
    return None


def get_recent_jobs(limit=20):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, company, location, source, created_at FROM jobs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Optimization operations ---

def save_optimization(cv_id, job_id, job_title, original_cv, optimized_cv, template="modern", used_ai=0):
    conn = get_db()
    conn.execute(
        "INSERT INTO optimizations (cv_id, job_id, job_title, original_cv, optimized_cv, template, used_ai) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (cv_id, job_id, job_title, original_cv, optimized_cv, template, used_ai)
    )
    conn.commit()
    opt_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return opt_id


def get_optimizations(limit=20):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, job_title, template, used_ai, created_at FROM optimizations ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_optimization(opt_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM optimizations WHERE id = ?", (opt_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# --- Settings ---

def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()
