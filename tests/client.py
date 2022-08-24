import json

import pytest

from application import application


@pytest.fixture
def client_fixture():
    app = application
    app.testing = True

    client = app.test_client()

    data = {
        "customer_id": "202787",
        "username": "shahv_test",
        "password": "Abcd@1243",
        "keep": "true"
    }

    response = client.post('/auth/signin', data=json.dumps(data), headers={'Content-Type': 'application/json'})

    with app.test_request_context(
            environ_base={'HTTP_X_LSO_AUTHORIZATION': f"Bearer {response.json['data']['AccessToken']}"}):
        yield client
