import os
from datetime import timedelta

# Import base config to potentially inherit from if needed, or just redefine
# from app.config import Config

class TestConfig:
    TESTING = True
    DEBUG = False  # Keep Flask's debug mode off for tests unless specifically needed for a test

    # Use an in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF protection is often disabled for testing forms directly,
    # as handling CSRF tokens can complicate test client requests.
    # Specific tests for CSRF can enable it if needed.
    WTF_CSRF_ENABLED = False
    # Faster hashing for tests if bcrypt is used (not directly here, but good practice)
    # BCRYPT_LOG_ROUNDS = 4

    # Secret key for session management in tests
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pytest-secret-key-for-testing')

    # Ensure mail doesn't actually send during tests and uses an in-memory backend
    MAIL_BACKEND = 'locmem' # Flask-Mailman uses this for in-memory
    MAIL_SUPPRESS_SEND = True # Common for Flask-Mail, check Flask-Mailman equivalent if needed

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False # Assuming Flask-Limiter might check this or similar

    # Default login status for tests (can be overridden)
    LOGIN_DISABLED = False # For Flask-Login, if we want to disable login for some tests

    # Set a specific log level for testing, or disable file logging if preferred
    LOG_LEVEL = 'DEBUG' # Or 'ERROR' to keep logs quiet unless errors occur
    # To prevent file logging during tests, the app factory can check for TESTING config.
    # The current app factory in __init__.py already skips file logging if app.testing is True.

    # Ensure password reset tokens expire quickly or have a predictable value for tests
    PASSWORD_RESET_TOKEN_EXPIRY = timedelta(seconds=5)

    # Other test-specific settings
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Password policies can be relaxed for easier test user creation if needed,
    # but generally better to test with production-like policies.
    PASSWORD_MIN_LENGTH = 6 # Example: Relaxed for tests
    PASSWORD_REQUIRE_UPPERCASE = False
    PASSWORD_REQUIRE_LOWERCASE = False
    PASSWORD_REQUIRE_NUMBERS = False
    PASSWORD_REQUIRE_SPECIAL = False

# To use this config, the app factory will need to be able to load it,
# typically by passing the class or its path.
# Example modification in create_app(config_class=Config):
# if config_class is None:
#     config_class = os.environ.get('FLASK_APP_CONFIG', Config) # or some logic
# app.config.from_object(config_class)
