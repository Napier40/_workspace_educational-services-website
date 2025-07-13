import pytest
from app import create_app, db
from app.models import User, ServiceRequest, ServicePricing
from flask import url_for

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
    db.drop_all()

def test_index(client):
    response = client.get(url_for('main.index'))
    assert response.status_code == 200

def test_about(client):
    response = client.get(url_for('main.about'))
    assert response.status_code == 200

def test_services(client):
    response = client.get(url_for('main.services'))
    assert response.status_code == 200

def test_register(client):
    response = client.get(url_for('auth.register'))
    assert response.status_code == 200

def test_login(client):
    response = client.get(url_for('auth.login'))
    assert response.status_code == 200

def test_admin_dashboard_unauthorized(client):
    response = client.get(url_for('admin.dashboard'))
    assert response.status_code == 302

def test_customer_dashboard_unauthorized(client):
    response = client.get(url_for('customer.dashboard'))
    assert response.status_code == 302
