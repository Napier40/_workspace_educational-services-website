import pytest
from app import create_app, db as _db
from app.models import User, ServiceRequest, Payment, CustomerAccount, ServicePricing # Import other models as needed
from tests.config_test import TestConfig

@pytest.fixture(scope='session')
def app():
    """
    Session-wide test Flask application.
    """
    app = create_app(config_class=TestConfig)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    yield app # The app is yielded for use in tests

    ctx.pop() # Clean up the context


@pytest.fixture(scope='session')
def db(app):
    """
    Session-wide test database.
    """
    _db.app = app # Associate db with the app directly for create_all/drop_all
    with app.app_context(): # Ensure operations are within app context
        _db.create_all()

    yield _db

    # Explicitly drop all tables if you want a clean slate for the next session
    # For in-memory SQLite, this might not be strictly necessary as it's recreated,
    # but good practice for other DBs or if session scope is changed.
    # _db.drop_all() # Commented out for now, as in-memory SQLite is fresh each session.


@pytest.fixture(scope='function') # Use 'function' scope for clean DB per test
def session(db):
    """
    Rolls back the database session after each test, ensuring test isolation.
    This is preferred over db.drop_all() for function-scoped tests with SQLite.
    For other DBs, a transaction-based approach might be better.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    # For Flask-SQLAlchemy 3.x, db.session is already a scoped_session.
    # We can use nested transactions for test isolation.

    # Start a transaction
    db.session.begin_nested()

    yield db.session # Tests will use the existing db.session

    # Rollback the transaction after the test
    db.session.rollback()
    # No need to remove or close the connection here, as Flask-SQLAlchemy manages the session scope.


@pytest.fixture
def client(app):
    """
    A test client for the app.
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    A test runner for the app's Click commands.
    """
    return app.test_cli_runner()

# Example utility fixture to create a user
@pytest.fixture
def new_user(session):
    def _new_user(username="testuser", email="test@example.com", password="TestPassword123!", role="customer", **kwargs):
        user = User(
            username=username,
            email=email,
            first_name=kwargs.get('first_name', 'Test'),
            last_name=kwargs.get('last_name', 'User'),
            role=role
        )
        user.set_password(password)
        if kwargs.get('is_active', True):
            user.is_active = True
        if kwargs.get('email_verified', True):
            user.email_verified = True

        session.add(user)
        session.commit()
        return user
    return _new_user

# Example utility fixture for an admin user
@pytest.fixture
def admin_user(new_user):
    return new_user(username="adminuser", email="admin@example.com", role="admin")

# Add more model creation fixtures as needed (e.g., for ServiceRequest, etc.)
