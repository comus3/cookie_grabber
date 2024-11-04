import pytest
from app import users_collection

def test_get_nonexistent_user(client):
    response = client.get('/send/999')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

def test_invalid_email(client):
    invalid_email_data = {
        "user_id": 1,
        "email": "invalid_email_format"
    }
    response = client.post('/email', data=invalid_email_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
