from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, case, desc # Removed unused 'and_', 'or_'
import secrets
import re

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # 'admin' or 'customer'
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100))
    
    # Relationship with service requests
    service_requests = db.relationship('ServiceRequest', foreign_keys='ServiceRequest.customer_id', backref='customer', lazy=True)
    
    # Selected pricing plan
    selected_plan_id = db.Column(db.Integer, db.ForeignKey('service_pricing.id'), nullable=True)
    selected_plan = db.relationship('ServicePricing', backref='customers', lazy=True)
    
    def set_password(self, password):
        ph = PasswordHasher()
        self.password_hash = ph.hash(password)
    
    def check_password(self, password):
        ph = PasswordHasher()
        try:
            ph.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_plan_name(self):
        """Get the name of the selected plan"""
        if self.selected_plan:
            return self.selected_plan.plan_name
        return "No Plan Selected"
    
    def get_plan_price(self):
        """Get the price of the selected plan"""
        if self.selected_plan:
            return f"{self.selected_plan.price}{self.selected_plan.price_period}"
        return "N/A"
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until:
            return datetime.now(timezone.utc) < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Max attempts from config
            self.lock_account()
    
    def reset_failed_login(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.last_login = datetime.now(timezone.utc)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        errors = []
        config = current_app.config

        min_length = config.get('PASSWORD_MIN_LENGTH', 8)
        require_uppercase = config.get('PASSWORD_REQUIRE_UPPERCASE', True)
        require_lowercase = config.get('PASSWORD_REQUIRE_LOWERCASE', True)
        require_numbers = config.get('PASSWORD_REQUIRE_NUMBERS', True)
        require_special = config.get('PASSWORD_REQUIRE_SPECIAL', True)

        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    def generate_email_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if self.email_verification_token == token:
            self.email_verified = True
            self.email_verification_token = None
            return True
        return False
    
    @classmethod
    def get_top_customers_by_conversions(cls, limit=10):
        """Get top customers by conversion rate (completed/total requests)"""
        return db.session.query(
            cls,
            (func.sum(case((ServiceRequest.status == 'completed', 1), else_=0)) / func.count(ServiceRequest.id) * 100).label('conversion_rate'),
            func.sum(case((ServiceRequest.status == 'completed', ServiceRequest.total_price), else_=0)).label('total_value')
        ).join(ServiceRequest).filter(cls.role == 'customer').group_by(cls.id).order_by(desc('conversion_rate'), desc('total_value')).limit(limit).all()
    
    @classmethod
    def get_top_customers_by_requests(cls, limit=10):
        """Get top customers by total number of requests"""
        customers = db.session.query(
            cls,
            func.count(ServiceRequest.id).label('request_count'),
            func.sum(ServiceRequest.total_price).label('total_value'),
            func.count(
                func.nullif(ServiceRequest.status != 'completed', True)
            ).label('completed_count')
        ).join(
            ServiceRequest, cls.id == ServiceRequest.customer_id
        ).filter(
            cls.role == 'customer'
        ).group_by(cls.id).order_by(
            func.count(ServiceRequest.id).desc()
        ).limit(limit).all()
        
        return customers

    def __repr__(self):
        return f'<User {self.id}>'

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'cancelled'
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    # due_date = db.Column(db.DateTime) # Removed as unused and superseded by new deadline fields
    notes = db.Column(db.Text)
    
    # Pricing fields
    estimated_hours = db.Column(db.Float, default=0.0)  # Hours in 0.5 increments
    hourly_rate = db.Column(db.Float, default=0.0)  # Rate per hour
    total_price = db.Column(db.Float, default=0.0)  # Calculated total price
    pricing_approved = db.Column(db.Boolean, default=False)  # Customer approval status
    pricing_notes = db.Column(db.Text)  # Admin notes about pricing
    
    # Estimated time fields
    estimated_response_days = db.Column(db.Integer, default=0)  # Days to complete task
    estimated_response_hours = db.Column(db.Integer, default=0)  # Additional hours (0-23)
    response_deadline = db.Column(db.DateTime, nullable=True)  # Calculated deadline for completion (made nullable for clarity)
    response_time_notes = db.Column(db.Text)  # Admin notes about estimated time

    # New deadline fields
    customer_proposed_deadline = db.Column(db.DateTime, nullable=True) # Proposed by customer
    admin_set_deadline = db.Column(db.DateTime, nullable=True) # Set by admin, official deadline
    
    # Relationship with assigned admin
    assigned_admin = db.relationship('User', foreign_keys=[assigned_admin_id])
    
    def calculate_total_price(self):
        """Calculate total price based on hours and rate"""
        if self.estimated_hours and self.hourly_rate:
            self.total_price = self.estimated_hours * self.hourly_rate
        return self.total_price
    
    def get_formatted_price(self):
        """Return formatted price string"""
        return f"${self.total_price:.2f}" if self.total_price else "$0.00"
    
    def get_formatted_rate(self):
        """Return formatted hourly rate string"""
        return f"${self.hourly_rate:.2f}/hr" if self.hourly_rate else "$0.00/hr"
    
    def calculate_response_deadline(self):
        """Calculate completion deadline based on estimated days and hours"""
        if self.estimated_response_days or self.estimated_response_hours:
            from datetime import timedelta
            total_hours = (self.estimated_response_days * 24) + (self.estimated_response_hours or 0)
            self.response_deadline = self.created_at + timedelta(hours=total_hours)
        return self.response_deadline
    
    def get_formatted_estimated_time(self):
        """Return formatted estimated time string"""
        if self.estimated_response_days or self.estimated_response_hours:
            days = self.estimated_response_days or 0
            hours = self.estimated_response_hours or 0
            
            if days > 0 and hours > 0:
                return f"{days} day{'s' if days != 1 else ''}, {hours} hour{'s' if hours != 1 else ''}"
            elif days > 0:
                return f"{days} day{'s' if days != 1 else ''}"
            elif hours > 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
        return "Not set"
    
    def is_estimated_time_overdue(self):
        """Check if estimated time is overdue"""
        if self.response_deadline and self.status in ['pending', 'in_progress']:
            return datetime.now(timezone.utc) > self.response_deadline
        return False
    
    def get_priority_score(self):
        """Calculate priority score for sorting (higher = more urgent)"""
        score = 0
        
        # Status priority (completed = 0, others get points)
        status_scores = {
            'pending': 100,
            'in_progress': 200,
            'under_review': 150,
            'completed': 0
        }
        score += status_scores.get(self.status, 50)
        
        # Overdue requests get highest priority
        if self.is_estimated_time_overdue():
            score += 500
        
        # Older requests get higher priority
        if self.created_at:
            days_old = (datetime.now(timezone.utc) - self.created_at).days
            score += min(days_old * 10, 200)  # Cap at 200 points
        
        # Total price priority (higher cost = higher priority)
        if self.total_price:
            score += min(self.total_price / 10, 100)  # Cap at 100 points
        
        return score
    
    @classmethod
    def get_outstanding_by_priority(cls):
        """Get outstanding requests ordered by priority"""
        outstanding = cls.query.filter(cls.status != 'completed').all()
        return sorted(outstanding, key=lambda x: x.get_priority_score(), reverse=True)
    
    @classmethod
    def get_income_report(cls, period='monthly', year=None, month=None):
        """Get income report for specified period"""
        if not year:
            year = datetime.now(timezone.utc).year
        
        if period == 'weekly':
            # Group by week
            results = db.session.query(
                func.extract('week', cls.created_at).label('period'),
                func.sum(cls.total_price).label('total_income'),
                func.count(cls.id).label('request_count')
            ).filter(
                cls.status == 'completed',
                cls.total_price > 0,
                func.extract('year', cls.created_at) == year
            ).group_by(func.extract('week', cls.created_at)).all()
            
        elif period == 'monthly':
            # Group by month
            results = db.session.query(
                func.extract('month', cls.created_at).label('period'),
                func.sum(cls.total_price).label('total_income'),
                func.count(cls.id).label('request_count')
            ).filter(
                cls.status == 'completed',
                cls.total_price > 0,
                func.extract('year', cls.created_at) == year
            ).group_by(func.extract('month', cls.created_at)).all()
            
        elif period == 'yearly':
            # Group by year
            results = db.session.query(
                func.extract('year', cls.created_at).label('period'),
                func.sum(cls.total_price).label('total_income'),
                func.count(cls.id).label('request_count')
            ).filter(
                cls.status == 'completed',
                cls.total_price > 0
            ).group_by(func.extract('year', cls.created_at)).all()
        
        return results
    
    @classmethod
    def get_conversion_rates(cls):
        """Calculate conversion rates from estimates to completed tasks"""
        total_requests = cls.query.count()
        completed_requests = cls.query.filter(cls.status == 'completed').count()
        
        # Requests with estimates
        estimated_requests = cls.query.filter(cls.total_price > 0).count()
        completed_estimated = cls.query.filter(
            cls.status == 'completed',
            cls.total_price > 0
        ).count()
        
        return {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'overall_conversion_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0,
            'estimated_requests': estimated_requests,
            'completed_estimated': completed_estimated,
            'estimate_conversion_rate': (completed_estimated / estimated_requests * 100) if estimated_requests > 0 else 0
        }

    def get_total_payments(self, status='approved'):
        """Get total payments for this request"""
        return Payment.get_request_total_payments(self.id, status)
    
    def get_outstanding_amount(self):
        """Get outstanding amount for this request"""
        if self.total_price and self.total_price > 0:
            paid_amount = self.get_total_payments('approved')
            return max(0, self.total_price - paid_amount)
        return 0.0
    
    def get_formatted_outstanding_amount(self):
        """Return formatted outstanding amount string"""
        return f"${self.get_outstanding_amount():.2f}"
    
    def is_fully_paid(self):
        """Check if request is fully paid"""
        return self.get_outstanding_amount() <= 0
    
    def get_payment_status(self):
        """Get payment status for this request"""
        if not self.total_price or self.total_price <= 0:
            return 'no_charge'
        elif self.is_fully_paid():
            return 'paid'
        elif self.get_total_payments('approved') > 0:
            return 'partial'
        else:
            return 'unpaid'
    
    @property
    def payment_status(self):
        """
        Property to get the current payment status for this service request.
        Aligns with the logic of get_payment_status() method.
        """
        if not self.total_price or self.total_price <= 0:
            return 'no_payment_required' # Or 'no_charge' to match get_payment_status()
        
        if self.is_fully_paid(): # is_fully_paid correctly uses get_outstanding_amount()
            return 'paid'
        
        # Check for any pending payments if not fully paid
        pending_payment = Payment.query.filter_by(
            service_request_id=self.id,
            status='pending'
        ).first()
        if pending_payment:
            return 'pending'

        # Check if partially paid
        if self.get_total_payments('approved') > 0:
            return 'partial' # Added partial state consistent with get_payment_status()

        return 'unpaid'
    
    @property
    def is_paid(self):
        """Check if this service request has been fully paid for."""
        # This will now correctly reflect full payment due to payment_status change
        return self.payment_status == 'paid'

    # Removed unused final_cost property
    # @property
    # def final_cost(self):
    #     """Alias for total_price to maintain compatibility."""
    #     return self.total_price

    def get_payment_status_badge_class(self):
        """Return Bootstrap badge class for payment status"""
        status_classes = {
            'paid': 'success',
            'partial': 'warning', 
            'unpaid': 'danger',
            'no_charge': 'secondary'
        }
        return status_classes.get(self.get_payment_status(), 'secondary')
    
    def get_payment_status_text(self):
        """Return human-readable payment status"""
        status_text = {
            'paid': 'Fully Paid',
            'partial': 'Partially Paid',
            'unpaid': 'Unpaid',
            'no_charge': 'No Charge'
        }
        return status_text.get(self.get_payment_status(), 'Unknown')

    def __repr__(self):
        return f'<ServiceRequest {self.title}>'


class ServicePricing(db.Model):
    """Model for managing service pricing tiers displayed on the services page"""
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(50), nullable=False)  # Basic, Premium, Enterprise
    price = db.Column(db.String(20), nullable=False)  # $25, $40, Custom
    price_period = db.Column(db.String(20), default='/hour')  # /hour, /month, etc.
    description = db.Column(db.Text)  # Brief description of the plan
    features = db.Column(db.Text)  # JSON string of features list
    is_popular = db.Column(db.Boolean, default=False)  # Mark as "Most Popular"
    is_active = db.Column(db.Boolean, default=True)  # Enable/disable plan
    display_order = db.Column(db.Integer, default=0)  # Order of display
    button_text = db.Column(db.String(50), default='Get Started')  # Button text
    button_link = db.Column(db.String(100))  # Custom button link (optional)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def get_features_list(self):
        """Return features as a list. Expects features to be a valid JSON string."""
        if self.features:
            import json # Keep local import for clarity or move to top if used elsewhere in class
            try:
                return json.loads(self.features)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to decode features JSON for ServicePricing ID {self.id}: {e}. Features string: '{self.features}'")
                return [] # Return empty list or handle error as appropriate
        return []
    
    def set_features_list(self, features_list):
        """Set features from a list"""
        import json
        if isinstance(features_list, list):
            self.features = json.dumps(features_list)
        else:
            self.features = features_list
    
    def __repr__(self):
        return f'<ServicePricing {self.plan_name}>'


class PasswordResetToken(db.Model):
    """Model for password reset tokens"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref='password_reset_tokens')
    
    def __init__(self, user_id, expiry_hours=1):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.used and datetime.now(timezone.utc) < self.expires_at
    
    def use_token(self):
        """Mark token as used"""
        self.used = True
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from database"""
        expired_tokens = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.now(timezone.utc)
        ).all()
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        return len(expired_tokens)
    
    def __repr__(self):
        return f'<PasswordResetToken for user {self.user_id}>'


class LoginAttempt(db.Model):
    """Model for tracking login attempts"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    username = db.Column(db.String(80))
    success = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_agent = db.Column(db.String(500))
    
    @staticmethod
    def log_attempt(ip_address, username, success, user_agent=None):
        """Log a login attempt"""
        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            success=success,
            user_agent=user_agent
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt
    
    @staticmethod
    def get_recent_failed_attempts(ip_address, minutes=15):
        """Get recent failed attempts from IP"""
        since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at > since
        ).count()
    
    def __repr__(self):
        return f'<LoginAttempt {self.username} from {self.ip_address}>'


class Payment(db.Model):
    """Model for tracking customer payments"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'credit_card', 'bank_transfer', 'paypal', 'cash', 'check'
    payment_reference = db.Column(db.String(200))  # Transaction ID, check number, etc.
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)
    processed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_notes = db.Column(db.Text)
    customer_notes = db.Column(db.Text)
    
    # Relationships
    customer = db.relationship('User', foreign_keys=[customer_id], backref='payments')
    service_request = db.relationship('ServiceRequest', backref='payments')
    processed_by = db.relationship('User', foreign_keys=[processed_by_id])
    
    def approve_payment(self, admin_user, notes=None):
        """Approve the payment"""
        self.status = 'approved'
        self.processed_at = datetime.now(timezone.utc)
        self.processed_by_id = admin_user.id
        if notes:
            self.admin_notes = notes
    
    def reject_payment(self, admin_user, notes=None):
        """Reject the payment"""
        self.status = 'rejected'
        self.processed_at = datetime.now(timezone.utc)
        self.processed_by_id = admin_user.id
        if notes:
            self.admin_notes = notes
    
    def get_formatted_amount(self):
        """Return formatted amount string"""
        return f"${self.amount:.2f}"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        return status_classes.get(self.status, 'secondary')
    
    @classmethod
    def get_customer_total_payments(cls, customer_id, status='approved'):
        """Get total approved payments for a customer"""
        total = db.session.query(func.sum(cls.amount)).filter(
            cls.customer_id == customer_id,
            cls.status == status
        ).scalar()
        return total or 0.0
    
    @classmethod
    def get_request_total_payments(cls, request_id, status='approved'):
        """Get total approved payments for a specific request"""
        total = db.session.query(func.sum(cls.amount)).filter(
            cls.service_request_id == request_id,
            cls.status == status
        ).scalar()
        return total or 0.0
    
    @classmethod
    def get_pending_payments(cls):
        """Get all pending payments for admin review"""
        return cls.query.filter(cls.status == 'pending').order_by(cls.submitted_at.desc()).all()
    
    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount} - {self.status}>'


class CustomerAccount(db.Model):
    """Model for tracking customer account balances and totals"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    total_billed = db.Column(db.Float, default=0.0)  # Total amount billed to customer
    total_paid = db.Column(db.Float, default=0.0)    # Total amount paid by customer
    outstanding_balance = db.Column(db.Float, default=0.0)  # Amount still owed
    last_payment_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    customer = db.relationship('User', backref=db.backref('account', uselist=False))
    
    def update_totals(self):
        """Update account totals based on service requests and payments"""
        # Calculate total billed from completed service requests
        total_billed = db.session.query(func.sum(ServiceRequest.total_price)).filter(
            ServiceRequest.customer_id == self.customer_id,
            ServiceRequest.status == 'completed',
            ServiceRequest.total_price > 0
        ).scalar() or 0.0
        
        # Calculate total paid from approved payments
        total_paid = Payment.get_customer_total_payments(self.customer_id, 'approved')
        
        # Update totals
        self.total_billed = total_billed
        self.total_paid = total_paid
        self.outstanding_balance = total_billed - total_paid
        
        # Update last payment date
        last_payment = Payment.query.filter(
            Payment.customer_id == self.customer_id,
            Payment.status == 'approved'
        ).order_by(Payment.processed_at.desc()).first()
        
        if last_payment:
            self.last_payment_date = last_payment.processed_at
    
    def get_formatted_total_billed(self):
        """Return formatted total billed string"""
        return f"${self.total_billed:.2f}"
    
    def get_formatted_total_paid(self):
        """Return formatted total paid string"""
        return f"${self.total_paid:.2f}"
    
    def get_formatted_outstanding_balance(self):
        """Return formatted outstanding balance string"""
        return f"${self.outstanding_balance:.2f}"
    
    def has_outstanding_balance(self):
        """Check if customer has outstanding balance"""
        return self.outstanding_balance > 0
    
    @classmethod
    def get_or_create_account(cls, customer_id):
        """Get existing account or create new one for customer"""
        account = cls.query.filter_by(customer_id=customer_id).first()
        if not account:
            account = cls(customer_id=customer_id)
            db.session.add(account)
            db.session.commit()
        return account
    
    def __repr__(self):
        return f'<CustomerAccount {self.customer_id}: Balance ${self.outstanding_balance:.2f}>'


class ExpenseCategory(db.Model):
    """Business expense categories for tax deduction tracking"""
    __tablename__ = 'expense_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_tax_deductible = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    expenses = db.relationship('BusinessExpense', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'
    
    @classmethod
    def get_active_categories(cls):
        """Get all active expense categories"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()


class BusinessExpense(db.Model):
    """Track business expenses for tax calculations"""
    __tablename__ = 'business_expense'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    receipt_filename = db.Column(db.String(255))  # For receipt storage
    is_tax_deductible = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    created_by = db.relationship('User', backref='expenses_created')
    
    def get_formatted_amount(self):
        """Return formatted amount string"""
        return f"${self.amount:.2f}"
    
    # Removed get_formatted_date(), as templates now use Flask-Moment for expense_date
    
    @classmethod
    def get_total_expenses(cls, start_date=None, end_date=None, tax_deductible_only=False):
        """Get total expenses for a period"""
        query = cls.query
        
        if start_date:
            query = query.filter(cls.expense_date >= start_date)
        if end_date:
            query = query.filter(cls.expense_date <= end_date)
        if tax_deductible_only:
            query = query.filter(cls.is_tax_deductible == True)
            
        result = query.with_entities(func.sum(cls.amount)).scalar()
        return result or 0.0
    
    @classmethod
    def get_expenses_by_category(cls, start_date=None, end_date=None):
        """Get expenses grouped by category"""
        query = db.session.query(
            ExpenseCategory.name,
            func.sum(cls.amount).label('total_amount'),
            func.count(cls.id).label('expense_count')
        ).join(ExpenseCategory).group_by(ExpenseCategory.name)
        
        if start_date:
            query = query.filter(cls.expense_date >= start_date)
        if end_date:
            query = query.filter(cls.expense_date <= end_date)
            
        return query.all()


class TaxRecord(db.Model):
    """Track monthly tax calculations and payments"""
    __tablename__ = 'tax_record'
    
    id = db.Column(db.Integer, primary_key=True)
    tax_year = db.Column(db.Integer, nullable=False)
    tax_month = db.Column(db.Integer, nullable=False)  # 1-12 for monthly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Financial calculations
    gross_income = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    tax_deductible_expenses = db.Column(db.Float, default=0.0)
    taxable_income = db.Column(db.Float, default=0.0)
    tax_rate = db.Column(db.Float, default=0.09)  # 9% default rate
    tax_owed = db.Column(db.Float, default=0.0)
    tax_paid = db.Column(db.Float, default=0.0)
    
    # Status and dates
    status = db.Column(db.String(20), default='pending')  # pending/paid/overdue
    due_date = db.Column(db.Date)
    payment_date = db.Column(db.Date)
    
    # Metadata
    calculated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    calculated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    
    # Relationships
    calculated_by = db.relationship('User', backref='tax_calculations')
    
    def calculate_taxes(self):
        """Calculate tax owed for this monthly period"""
        # Get income for the period
        self.gross_income = self._get_period_income()
        
        # Get expenses for the period
        self.total_expenses = BusinessExpense.get_total_expenses(
            self.period_start, self.period_end
        )
        self.tax_deductible_expenses = BusinessExpense.get_total_expenses(
            self.period_start, self.period_end, tax_deductible_only=True
        )
        
        # Calculate taxable income
        self.taxable_income = max(0, self.gross_income - self.tax_deductible_expenses)
        
        # Calculate tax owed
        self.tax_owed = self.taxable_income * self.tax_rate
        
        return self.tax_owed
    
    def _get_period_income(self):
        """Get total income for the tax period"""
        # Get approved payments in the period
        income = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'approved',
            Payment.processed_at >= self.period_start,
            Payment.processed_at <= self.period_end
        ).scalar()
        
        return income or 0.0
    
    def get_formatted_tax_owed(self):
        """Return formatted tax owed string"""
        return f"${self.tax_owed:.2f}"
    
    def get_formatted_taxable_income(self):
        """Return formatted taxable income string"""
        return f"${self.taxable_income:.2f}"
    
    def get_month_name(self):
        """Return month name (January 2025, etc.)"""
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        return f"{month_names[self.tax_month - 1]} {self.tax_year}"
    
    def is_overdue(self):
        """Check if tax payment is overdue"""
        if self.due_date and self.status == 'pending':
            return datetime.now(timezone.utc).date() > self.due_date
        return False
    
    @classmethod
    def get_or_create_month_record(cls, year, month):
        """Get or create tax record for a specific month"""
        record = cls.query.filter_by(tax_year=year, tax_month=month).first()
        
        if not record:
            # Calculate month dates
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            
            start_date = datetime(year, month, 1).date()
            end_date = datetime(year, month, last_day).date()
            
            # Due date is 15th of following month
            if month == 12:
                due_year = year + 1
                due_month = 1
            else:
                due_year = year
                due_month = month + 1
            
            due_date = datetime(due_year, due_month, 15).date()
            
            record = cls(
                tax_year=year,
                tax_month=month,
                period_start=start_date,
                period_end=end_date,
                due_date=due_date
            )
            
            db.session.add(record)
            db.session.commit()
        
        return record


class Notification(db.Model):
    """Model for storing user notifications"""
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=True)

    # Relationships
    user = db.relationship('User', backref='notifications')
    service_request = db.relationship('ServiceRequest', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id}>'


class FileUpload(db.Model):
    """Model for storing uploaded files"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    service_request = db.relationship('ServiceRequest', backref='uploads')
    uploaded_by = db.relationship('User', backref='uploads')

    def __repr__(self):
        return f'<FileUpload {self.filename}>'


class FinancialSummary(db.Model):
    """Monthly financial summary for quick dashboard access"""
    __tablename__ = 'financial_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    
    # Financial totals
    total_income = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    net_income = db.Column(db.Float, default=0.0)
    tax_liability = db.Column(db.Float, default=0.0)
    
    # Metrics
    profit_margin = db.Column(db.Float, default=0.0)  # Percentage
    expense_ratio = db.Column(db.Float, default=0.0)  # Expenses/Income ratio
    
    # Metadata
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def calculate_summary(self):
        """Calculate financial summary for the month"""
        from calendar import monthrange
        
        # Get month date range
        start_date = datetime(self.year, self.month, 1).date()
        last_day = monthrange(self.year, self.month)[1]
        end_date = datetime(self.year, self.month, last_day).date()
        
        # Calculate income (approved payments)
        self.total_income = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'approved',
            Payment.processed_at >= start_date,
            Payment.processed_at <= end_date
        ).scalar() or 0.0
        
        # Calculate expenses
        self.total_expenses = BusinessExpense.get_total_expenses(start_date, end_date)
        
        # Calculate net income
        self.net_income = self.total_income - self.total_expenses
        
        # Calculate tax liability (9% of net income)
        self.tax_liability = max(0, self.net_income * 0.09)
        
        # Calculate metrics
        if self.total_income > 0:
            self.profit_margin = (self.net_income / self.total_income) * 100
            self.expense_ratio = (self.total_expenses / self.total_income) * 100
        else:
            self.profit_margin = 0.0
            self.expense_ratio = 0.0
    
    @classmethod
    def get_or_create_summary(cls, year, month):
        """Get or create financial summary for a month"""
        summary = cls.query.filter_by(year=year, month=month).first()
        
        if not summary:
            summary = cls(year=year, month=month)
            db.session.add(summary)
        
        summary.calculate_summary()
        db.session.commit()
        
        return summary