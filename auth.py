"""Minimal production-oriented authentication helpers.

This module intentionally keeps authentication provider-agnostic. For a real
regulated deployment, use a managed identity provider and never store raw
passwords. The API can use these helpers for local/demo accounts.
"""
import hashlib
import hmac
import os


def hash_password(password: str, salt: str | None = None) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return f"pbkdf2_sha256$310000${salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (AttributeError, ValueError, TypeError):
        return False


def normalize_role(role: str) -> str:
    role = str(role or "").strip().lower()
    if role not in {"donor", "patient", "hospital", "admin"}:
        raise ValueError("Role must be donor, patient, hospital, or admin")
    return role
