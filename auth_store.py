"""SQLite-backed demo identity store.

For production, replace this with a managed identity provider, but keep the
same role and authorization boundaries. No raw passwords are stored.
"""
import sqlite3
from auth import hash_password, normalize_role, verify_password


class AuthStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        conn = self._connect()
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('donor','patient','hospital','admin')),
            display_name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.commit(); conn.close()

    def register(self, email, password, role, display_name):
        email = str(email or '').strip().lower()
        if '@' not in email or len(email) > 254:
            raise ValueError('A valid email is required')
        role = normalize_role(role)
        display_name = str(display_name or '').strip()
        if not 2 <= len(display_name) <= 100:
            raise ValueError('display_name must contain 2-100 characters')
        encoded = hash_password(password)
        conn = self._connect()
        try:
            cur = conn.execute('INSERT INTO users(email,password_hash,role,display_name) VALUES(?,?,?,?)', (email, encoded, role, display_name))
            conn.commit()
            return {'user_id': cur.lastrowid, 'email': email, 'role': role, 'display_name': display_name}
        except sqlite3.IntegrityError:
            raise ValueError('An account with this email already exists')
        finally:
            conn.close()

    def authenticate(self, email, password):
        conn = self._connect()
        row = conn.execute('SELECT * FROM users WHERE email=? AND is_active=1', (str(email or '').strip().lower(),)).fetchone()
        conn.close()
        if not row or not verify_password(password, row['password_hash']):
            return None
        return {'user_id': row['user_id'], 'email': row['email'], 'role': row['role'], 'display_name': row['display_name']}
