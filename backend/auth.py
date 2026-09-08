# backend/auth.py
"""
Authentication module for the RAG Research Agent.

Design decisions:
- Uses the same SQLite connection pattern as db.py (get_connection() + raw SQL).
- Passwords hashed with bcrypt directly (bcrypt >= 4.0 — passlib is incompatible
  with bcrypt >= 4.0 due to its internal wrap-bug detection using a 73-byte test
  string that bcrypt now rejects. Using bcrypt directly avoids this entirely.)
- JWTs signed with HS256 using SECRET_KEY from environment.
- User IDs are UUIDs stored as TEXT (consistent with session_id pattern).
- This module has NO dependency on the existing messages/session code —
  it is purely additive.
"""

import os
import uuid
import logging
import bcrypt
import jwt

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, field_validator

from backend.db import get_connection

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Security configuration (read from environment — never hardcoded)
# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


# ─────────────────────────────────────────────────────────────────────────────
# Password hashing (bcrypt directly — compatible with bcrypt >= 4.0)
# ─────────────────────────────────────────────────────────────────────────────
def _hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (cost factor 12)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request / response models
# ─────────────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    """Request body for POST /auth/register."""
    name: str
    email: str
    password: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty.")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("A valid email address is required.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v


class UserLogin(BaseModel):
    """Request body for POST /auth/login."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_normalise(cls, v: str) -> str:
        return v.strip().lower()


class TokenResponse(BaseModel):
    """Response body for register and login endpoints."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


class UserInfo(BaseModel):
    """Response body for GET /auth/me."""
    user_id: str
    name: str
    email: str


# ─────────────────────────────────────────────────────────────────────────────
# Database helpers — users table
# ─────────────────────────────────────────────────────────────────────────────
def create_users_table() -> None:
    """
    Create the users table in the existing SQLite database.

    Called from db.init_db() so both tables are initialised together
    at application startup. Idempotent (IF NOT EXISTS).
    """
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                email      TEXT NOT NULL UNIQUE,
                password   TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)
        conn.commit()
    finally:
        conn.close()


def _get_user_by_email(email: str) -> Optional[dict]:
    """Fetch a user row by email. Returns None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, email, password FROM users WHERE email = ?",
            (email.strip().lower(),),
        ).fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()


def create_user(name: str, email: str, password: str) -> dict:
    """
    Hash the password and insert a new user row.

    Returns the new user dict (without the password hash).
    Raises ValueError on duplicate email.
    """
    email = email.strip().lower()

    if _get_user_by_email(email):
        raise ValueError("An account with this email already exists.")

    user_id = str(uuid.uuid4())
    hashed = _hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (id, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name.strip(), email, hashed, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    return {"user_id": user_id, "name": name.strip(), "email": email}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Verify email + password.

    Returns the user dict (without password hash) if credentials are valid,
    or None if the email doesn't exist or the password is wrong.

    NOTE: We return the same None for both bad email AND bad password to
    prevent user-enumeration attacks. We still run bcrypt.checkpw on a
    dummy hash when the user doesn't exist to keep timing consistent.
    """
    user = _get_user_by_email(email)
    if user is None:
        # Constant-time dummy check so attackers can't use timing to enumerate users
        _verify_password(password, "$2b$12$abcdefghijklmnopqrstuvuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
        return None

    if not _verify_password(password, user["password"]):
        return None

    return {"user_id": user["id"], "name": user["name"], "email": user["email"]}


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ─────────────────────────────────────────────────────────────────────────────
def create_access_token(user_id: str, email: str, name: str) -> str:
    """
    Create a signed JWT containing the user's identity.

    The token expires after JWT_EXPIRE_HOURS (default 24h).
    SECRET_KEY must be set in the environment.
    """
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Add it to your .env file before running the server."
        )

    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT.

    Returns the payload dict on success.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set.")
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
