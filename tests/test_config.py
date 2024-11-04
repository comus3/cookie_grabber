import pytest
from app import app, db, users_collection, email_history_collection

@pytest.fixture
def client():
    """
    Configure the Flask test client and test database.
    """
    app.config['TESTING'] = True
    app.config['MONGO_DBNAME'] = 'test_cookie_awareness'  # Nom de la DB de test
    app.config['MAIL_SUPPRESS_SEND'] = True  # Évite l'envoi réel des emails pendant les tests

    with app.test_client() as client:
        yield client

    # Nettoyage de la DB après chaque test
    db.drop_collection(users_collection)
    db.drop_collection(email_history_collection)