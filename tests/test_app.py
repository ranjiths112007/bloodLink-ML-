import os
import tempfile

import pytest

import app as bloodlink_app


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    old = bloodlink_app.DB_PATH
    bloodlink_app.DB_PATH = path
    bloodlink_app.init_db(seed_demo=True)
    bloodlink_app.app.config['TESTING'] = True
    with bloodlink_app.app.test_client() as c:
        yield c
    bloodlink_app.DB_PATH = old
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    body = response.get_json()
    assert body['status'] == 'ok'
    assert body['donor_count'] > 0


def test_invalid_request_is_rejected(client):
    response = client.post('/api/requests', json={'blood_group': 'X+', 'lat': 13, 'lon': 80})
    assert response.status_code == 400
    assert response.get_json()['error']['code'] == 'INVALID_BLOOD_GROUP'


def test_invalid_location_is_rejected(client):
    response = client.post('/api/requests', json={'blood_group': 'O+', 'lat': 999, 'lon': 80})
    assert response.status_code == 400
    assert response.get_json()['error']['code'] == 'INVALID_LOCATION'
