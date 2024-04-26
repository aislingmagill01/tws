import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

        
def test_login_invalid_credentials(client):
    # Simulate a POST request with valid credentials
    response = client.post('/login', data={'username': 'test_username', 'password': 'test_password'})
    assert b'Invalid username or password' in response.data  # Assuming the login route redirects to a welcome page

def test_register_new_user(client):
    # Simulate a POST request with valid new user data
    response = client.post('/register', data={'username': 'new_user', 'password': 'password123'})
    
    # Assert that the response status code is a redirection (302)
    assert response.status_code == 200
    

def test_services_route(client):
    response = client.get('/services')
    assert response.status_code == 200
    assert b'<h2>Services</h2>' in response.data
    
  