import sqlite3
import hashlib
import secrets
import re
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "promptwise.db"


@contextmanager
def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        310000
    ).hex()
    return salt, hashed


def verify_password(password, salt, stored_hash):
    _, candidate = hash_password(password, salt)
    return secrets.compare_digest(candidate, stored_hash)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                email TEXT UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                original TEXT NOT NULL,
                optimized TEXT NOT NULL,
                framework TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_user
            ON prompts(user_id)
        """)


def create_user(display_name, username, email, password):
    display_name = (display_name or "").strip()
    username = (username or "").strip()
    email = (email or "").strip().lower() or None

    if not display_name or not username or not password:
        return False, "Please complete all required fields."

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
        return False, "Username can contain letters, numbers, dots, underscores and hyphens."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "Please enter a valid email address."

    salt, password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users
                (display_name, username, email, password_salt, password_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (display_name, username, email, salt, password_hash))

        return True, "Account created successfully."

    except sqlite3.IntegrityError:
        return False, "That username or email is already registered."

    except sqlite3.Error:
        return False, "Unable to create the account. Please try again."


def verify_user(username, password):
    username = (username or "").strip()

    if not username or not password:
        return None

    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM users
            WHERE username = ? COLLATE NOCASE
        """, (username,)).fetchone()

    if not row:
        return None

    if not verify_password(
        password,
        row["password_salt"],
        row["password_hash"]
    ):
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "email": row["email"]
    }


def save_prompt(user_id, original, optimized, framework):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO prompts (user_id, original, optimized, framework)
            VALUES (?, ?, ?, ?)
        """, (user_id, original, optimized, framework))


def list_prompts(user_id):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, original, optimized, framework, created_at
            FROM prompts
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    return [dict(row) for row in rows]


def delete_prompt(user_id, prompt_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM prompts
            WHERE id = ? AND user_id = ?
        """, (prompt_id, user_id))


def get_stats(user_id):
    with get_connection() as conn:
        count = conn.execute("""
            SELECT COUNT(*) AS total
            FROM prompts
            WHERE user_id = ?
        """, (user_id,)).fetchone()["total"]

    return {"prompts": count}
