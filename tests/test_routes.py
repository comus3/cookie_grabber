import pytest
from flask import url_for
from app import users_collection, email_history_collection

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_get_statistics(client):
    response = client.get('/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert "total_users" in data
    assert "average_time_of_visit" in data

def test_save_user(client):
    new_user = {"name": "Jane Doe", "email": "jane@example.com"}
    response = client.post('/save', json=new_user)
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "success"
    assert "user_data" in data

def test_delete_user(client):
    # Ajouter un utilisateur de test
    new_user = {"id": 1, "name": "User to delete"}
    users_collection.insert_one(new_user)
    
    # Essayer de le supprimer
    response = client.delete('/delete/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"

    # Essayer de supprimer un utilisateur inexistant
    response = client.delete('/delete/2')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

def test_email_sending(client):
    test_email = {
        "user_id": 1,
        "email": "test@example.com"
    }
    response = client.post('/email', data=test_email)
    assert response.status_code == 200

def test_location_distribution(client):
    response = client.get('/location-distribution')
    assert response.status_code == 200
    data = response.get_json()
    assert "locations" in data

def test_search_users(client):
    # Ajouter des utilisateurs pour les tests
    users_collection.insert_many([
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"}
    ])
    
    response = client.get('/search-users?name=Alice')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Alice'
