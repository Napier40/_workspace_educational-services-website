import pytest
from app.models import User, ServiceRequest, Payment # Add other models as you test them
from app import db as _db # Use the db instance from app, aliased to avoid conflict if needed

def test_new_user_creation(session):
    """Test creating a new User instance and saving to DB."""
    user = User(
        username="john_doe",
        email="john.doe@example.com",
        first_name="John",
        last_name="Doe",
        role="customer"
    )
    user.set_password("SecurePassword123!")

    session.add(user)
    session.commit()

    retrieved_user = User.query.filter_by(username="john_doe").first()
    assert retrieved_user is not None
    assert retrieved_user.email == "john.doe@example.com"
    assert retrieved_user.first_name == "John"
    assert retrieved_user.role == "customer"
    assert retrieved_user.id is not None

def test_user_password_hashing(session):
    """Test password hashing and checking."""
    user = User(
        username="jane_doe",
        email="jane.doe@example.com",
        first_name="Jane",
        last_name="Doe"
    )
    password = "AnotherSecurePassword@2024"
    user.set_password(password)

    session.add(user)
    session.commit()

    assert user.password_hash is not None
    assert user.password_hash != password # Ensure it's hashed
    assert user.check_password(password) is True
    assert user.check_password("WrongPassword") is False

def test_user_default_role_is_customer(session):
    """Test that a new user defaults to 'customer' role if not specified."""
    user = User(
        username="default_user",
        email="default@example.com",
        first_name="Default",
        last_name="User"
    )
    user.set_password("DefaultPass1!")
    # Not setting user.role explicitly

    session.add(user)
    session.commit()

    retrieved_user = User.query.filter_by(username="default_user").first()
    assert retrieved_user.role == "customer"

def test_user_is_admin_method(session):
    """Test the is_admin() method on the User model."""
    customer_user = User(username="cust", email="c@e.com", first_name="C", last_name="U", role="customer")
    customer_user.set_password("p")

    admin_user = User(username="adm", email="a@e.com", first_name="A", last_name="D", role="admin")
    admin_user.set_password("p")

    session.add_all([customer_user, admin_user])
    session.commit()

    assert customer_user.is_admin() is False
    assert admin_user.is_admin() is True

def test_user_password_strength_validation_configurable(app, new_user):
    """Test that password strength validation uses app config."""
    # This test relies on the app fixture to ensure config is loaded.
    # We'll test one aspect: min_length.
    # The TestConfig in conftest.py sets PASSWORD_MIN_LENGTH = 6 (example)

    # Temporarily override config for this test if needed, or ensure TestConfig is used.
    # For this test, we assume TestConfig with relaxed password rules is active.
    # If TestConfig had strict rules, this test would need to reflect that.

    # Check against TestConfig's relaxed policy (PASSWORD_MIN_LENGTH = 6)
    short_password_errors = User.validate_password_strength("Short1!") # 7 chars
    assert not any("at least 6 characters long" in e for e in short_password_errors)
    assert not any("at least 8 characters long" in e for e in short_password_errors) # Default if config not read

    # Test a password that would fail the default (8 chars) but pass the test config (6 chars)
    # and meets other criteria from TestConfig (all False for require_*)
    valid_short_password = "Test1" # 5 chars

    # Update TestConfig to reflect relaxed rules for this specific test case
    original_min_length = app.config.get('PASSWORD_MIN_LENGTH')
    original_req_upper = app.config.get('PASSWORD_REQUIRE_UPPERCASE')
    original_req_lower = app.config.get('PASSWORD_REQUIRE_LOWERCASE')
    original_req_numbers = app.config.get('PASSWORD_REQUIRE_NUMBERS')
    original_req_special = app.config.get('PASSWORD_REQUIRE_SPECIAL')

    app.config['PASSWORD_MIN_LENGTH'] = 5
    app.config['PASSWORD_REQUIRE_UPPERCASE'] = False # Assuming TestConfig has these False
    app.config['PASSWORD_REQUIRE_LOWERCASE'] = False
    app.config['PASSWORD_REQUIRE_NUMBERS'] = False
    app.config['PASSWORD_REQUIRE_SPECIAL'] = False

    errors = User.validate_password_strength(valid_short_password)
    assert not errors, f"Validation errors for '{valid_short_password}': {errors}"

    # Restore original config values to avoid affecting other tests
    app.config['PASSWORD_MIN_LENGTH'] = original_min_length
    app.config['PASSWORD_REQUIRE_UPPERCASE'] = original_req_upper
    app.config['PASSWORD_REQUIRE_LOWERCASE'] = original_req_lower
    app.config['PASSWORD_REQUIRE_NUMBERS'] = original_req_numbers
    app.config['PASSWORD_REQUIRE_SPECIAL'] = original_req_special


# --- Basic ServiceRequest Model Test ---
def test_new_service_request(session, new_user):
    """Test creating a new ServiceRequest."""
    customer = new_user(username="service_customer", email="sc@example.com")

    sr = ServiceRequest(
        title="Test Service Request",
        description="This is a test description.",
        service_type="Mathematics",
        priority="medium",
        customer_id=customer.id # or customer=customer
    )
    session.add(sr)
    session.commit()

    retrieved_sr = ServiceRequest.query.filter_by(title="Test Service Request").first()
    assert retrieved_sr is not None
    assert retrieved_sr.customer == customer
    assert retrieved_sr.status == "pending" # Default status
    assert retrieved_sr.total_price == 0.0 # Default

# --- Placeholder for Payment Model Test ---
def test_new_payment(session, new_user, test_service_request): # Assuming a test_service_request fixture
    """Test creating a new Payment."""
    customer = new_user(username="payment_customer", email="pc@example.com")
    # service_request = test_service_request(customer=customer) # This fixture would need to be created

    # For now, create a simple SR for the payment test
    service_request = ServiceRequest(title="SR for Payment", description="Desc", service_type="Test", customer=customer, total_price=100.0)
    session.add(service_request)
    session.commit()

    payment = Payment(
        customer_id=customer.id,
        service_request_id=service_request.id,
        amount=50.0,
        payment_method="credit_card",
        status="pending"
    )
    session.add(payment)
    session.commit()

    retrieved_payment = Payment.query.filter_by(amount=50.0).first()
    assert retrieved_payment is not None
    assert retrieved_payment.customer == customer
    assert retrieved_payment.service_request == service_request
    assert retrieved_payment.status == "pending"

# It's good practice to create more specific fixtures for related models,
# e.g., a fixture that creates a ServiceRequest with a customer.
@pytest.fixture
def test_service_request(session, new_user):
    def _test_service_request(customer=None, **kwargs):
        if customer is None:
            customer = new_user()

        sr_data = {
            "title": kwargs.get("title", "Default SR Title"),
            "description": kwargs.get("description", "Default SR Desc"),
            "service_type": kwargs.get("service_type", "General"),
            "customer_id": customer.id,
            "total_price": kwargs.get("total_price", 0.0)
        }
        sr = ServiceRequest(**sr_data)
        session.add(sr)
        session.commit()
        return sr
    return _test_service_request
