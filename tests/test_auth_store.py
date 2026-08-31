import os
import tempfile
from auth_store import AuthStore


def test_register_and_authenticate():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        store = AuthStore(path)
        user = store.register('user@example.com', 'strong-password', 'donor', 'Test Donor')
        assert user['role'] == 'donor'
        assert store.authenticate('user@example.com', 'strong-password')['user_id'] == user['user_id']
        assert store.authenticate('user@example.com', 'wrong-password') is None
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_duplicate_email_rejected():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        store = AuthStore(path)
        store.register('user@example.com', 'strong-password', 'patient', 'Patient')
        try:
            store.register('USER@example.com', 'strong-password', 'patient', 'Patient Two')
            assert False
        except ValueError as exc:
            assert 'already exists' in str(exc)
    finally:
        if os.path.exists(path):
            os.remove(path)

