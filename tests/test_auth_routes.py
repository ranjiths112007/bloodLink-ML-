import os
import tempfile
import pytest
import app as bloodlink_app


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix='.db'); os.close(fd)
    old = bloodlink_app.DB_PATH
    bloodlink_app.DB_PATH = path
    bloodlink_app.init_db(seed_demo=False)
    with bloodlink_app.app.test_client() as c:
        yield c
    bloodlink_app.DB_PATH = old
    os.remove(path)


def test_register_login_logout(client):
    r = client.post('/api/auth/register', json={'email':'a@example.com','password':'strong-password','role':'patient','display_name':'Patient'})
    assert r.status_code == 201
    assert client.get('/api/auth/me').get_json()['user']['role'] == 'patient'
    assert client.post('/api/auth/logout').status_code == 200
    assert client.get('/api/auth/me').get_json()['user'] is None
    r = client.post('/api/auth/login', json={'email':'a@example.com','password':'strong-password'})
    assert r.status_code == 200


def test_patient_can_create_request(client):
    client.post('/api/auth/register', json={'email':'p@example.com','password':'strong-password','role':'patient','display_name':'Patient'})
    r = client.post('/api/requests', json={'blood_group':'O+','lat':13.08,'lon':80.27,'max_distance':20,'urgency':'high'})
    assert r.status_code == 201


def test_unauthenticated_request_is_rejected(client):
    r = client.post('/api/requests', json={'blood_group':'O+','lat':13.08,'lon':80.27})
    assert r.status_code == 401
