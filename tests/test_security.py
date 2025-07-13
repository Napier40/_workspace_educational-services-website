import pytest
from app import create_app
from app.security import sanitize_input, is_safe_url

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

def test_sanitize_input(app):
    with app.app_context():
        assert sanitize_input('<script>alert("xss")</script>') == ''
        assert sanitize_input('test') == 'test'
        assert sanitize_input(None) == ''

def test_is_safe_url(app):
    with app.test_request_context('/'):
        assert is_safe_url('http://localhost:5000/test') == True
        assert is_safe_url('https://example.com/test') == False
        assert is_safe_url('/test') == True
        assert is_safe_url(None) == False
