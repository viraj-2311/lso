import json

from flask.globals import request

from tests.client import client_fixture

headers = {
    'Content-Type': 'application/json'
}


def test_change_password_without_access_token(client_fixture):
    data = {}
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 500
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'InvalidTokenError'


def test_change_password_with_wrong_access_token(client_fixture):
    headers['X-LSO-Authorization'] = "WRONG ACCESS TOKEN"
    data = {}
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'TokenExpiredError'


def test_change_password_with_wrong_username(client_fixture):
    headers['X-LSO-Authorization'] = request.headers['X_LSO_AUTHORIZATION']
    data = {
        "username": "shahv_testt",
        "old_password": "Abcd@12345",
        "new_password": "Abcd@1243"
    }
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 401
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials.'


def test_change_password_with_wrong_old_password(client_fixture):
    headers['X-LSO-Authorization'] = request.headers['X_LSO_AUTHORIZATION']
    data = {
        "username": "shahv_test",
        "old_password": "Abcd@12345",
        "new_password": "Abcd@1243"
    }
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 401
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials.'


def test_change_password_with_invalid_new_password(client_fixture):
    headers['X-LSO-Authorization'] = request.headers['X_LSO_AUTHORIZATION']
    data = {
        "username": "shahv_test",
        "old_password": "Abcd@1243",
        "new_password": "abcd"
    }
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'New password must contain upper, lower, and digit and 8 characters long'


def test_change_password_with_old_and_password_same(client_fixture):
    headers['X-LSO-Authorization'] = request.headers['X_LSO_AUTHORIZATION']
    data = {
        "username": "shahv_test",
        "old_password": "Abcd@1243",
        "new_password": "Abcd@1243"
    }
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'New password must be different from current password. Please try again.'


def test_change_password_success(client_fixture):
    headers['X-LSO-Authorization'] = request.headers['X_LSO_AUTHORIZATION']
    data = {
        "username": "shahv_test",
        "old_password": "Abcd@1243",
        "new_password": "Abcd@1234"
    }
    response = client_fixture.post('auth/change_password', data=json.dumps(data), headers=headers)

    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert response.json['message'] == 'Password successfully changed.'

