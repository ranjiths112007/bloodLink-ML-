"""Reusable role-aware application helpers for BloodLink."""
from functools import wraps
from flask import jsonify, session

ROLES = {"donor", "patient", "hospital", "admin"}


def current_user():
    return session.get("user")


def require_roles(*allowed):
    allowed = set(allowed)
    if not allowed <= ROLES:
        raise ValueError("Unknown role in authorization policy")
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error":{"code":"AUTH_REQUIRED","message":"Authentication required."}}), 401
            if user.get("role") not in allowed:
                return jsonify({"error":{"code":"FORBIDDEN","message":"This action is not available for your role."}}), 403
            return fn(*args, **kwargs)
        return wrapped
    return decorator
