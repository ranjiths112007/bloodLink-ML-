import tempfile
from auth_store import AuthStore


def test_register_and_authenticate():
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        store = AuthStore(f.name)
        user = store.register('user@example.com', 'strong-password', 'donor', 'Test Donor')
        assert user['role'] == 'donor'
        assert store.authenticate('user@example.com', 'strong-password')['user_id'] == user['user_id']
        assert store.authenticate('user@example.com', 'wrong-password') is None


def test_duplicate_email_rejected():
    with tempfile.NamedTemporaryFile(suffix='.db') as f:
        store = AuthStore(f.name)
        store.register('user@example.com', 'strong-password', 'patient', 'Patient')
        try:
            store.register('USER@example.com', 'strong-password', 'patient', 'Patient Two')
            assert False
        except ValueError as exc:
            assert 'already exists' in str(exc)
