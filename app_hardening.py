"""Production safety helpers for Flask."""
import os
import time
from collections import defaultdict, deque
from functools import wraps
from flask import jsonify, request

_REQUEST_LOG = defaultdict(deque)
WINDOW_SECONDS = int(os.getenv("BLOODLINK_RATE_WINDOW_SECONDS", "60"))
MAX_REQUESTS = int(os.getenv("BLOODLINK_RATE_LIMIT", "120"))


def client_key():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


def rate_limit(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        now = time.time(); q = _REQUEST_LOG[client_key()]
        while q and now - q[0] >= WINDOW_SECONDS: q.popleft()
        if len(q) >= MAX_REQUESTS:
            response = jsonify({"error":{"code":"RATE_LIMITED","message":"Too many requests. Please try again shortly."}})
            response.status_code = 429
            response.headers["Retry-After"] = str(WINDOW_SECONDS)
            return response
        q.append(now)
        return fn(*args, **kwargs)
    return wrapped


def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(self), microphone=(), camera=()")
    if os.getenv("BLOODLINK_ENV", "development") == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
