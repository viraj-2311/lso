import json

from tests.client import client_fixture

headers = {
    'Content-Type': 'application/json'
}


def test_login_without_credentials(client_fixture):
    data = {}

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials, Please try again.'


def test_login_with_wrong_customer_id(client_fixture):
    data = {
        "customer_id": "202777",
        "username": "shahv_test",
        "password": "Abcd@1243",
        "keep": "true"
    }

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials.'


def test_login_with_wrong_username(client_fixture):
    data = {
        "customer_id": "202787",
        "username": "shahv_testt",
        "password": "Abcd@1243",
        "keep": "true"
    }

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials.'


def test_login_with_wrong_password(client_fixture):
    data = {
        "customer_id": "202787",
        "username": "shahv_test",
        "password": "Abcd@1245",
        "keep": "true"
    }

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 400
    assert response.json['status'] == 'error'
    assert response.json['message'] == 'Invalid User Credentials.'


def test_login_with_keep_true(client_fixture):
    data = {
        "customer_id": "202787",
        "username": "shahv_test",
        "password": "Abcd@1243",
        "keep": "true"
    }

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert response.json['message'] == 'Sign in'
    assert len(response.json['data'].get('RefreshToken', '')) != 0


def test_login_with_keep_false(client_fixture):
    data = {
        "customer_id": "202787",
        "username": "shahv_test",
        "password": "Abcd@1243",
        "keep": "false"
    }

    response = client_fixture.post('/auth/signin', data=json.dumps(data), headers=headers)

    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert response.json['message'] == 'Sign in'
    assert len(response.json['data'].get('RefreshToken', '')) == 0