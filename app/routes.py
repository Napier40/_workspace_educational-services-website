import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
# from werkzeug.security import check_password_hash # Unused in this file directly
from app.models import (db, User, ServiceRequest, ServicePricing, PasswordResetToken, 
                        Payment, CustomerAccount, BusinessExpense, ExpenseCategory, 
                        TaxRecord, FinancialSummary, FileUpload, Notification)
from app.security import (log_login_attempt, is_ip_rate_limited, # validate_password_strength removed
                         send_password_reset_email, send_email_verification, sanitize_input, is_safe_url)
from app import limiter, socketio
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
import json
import csv
from io import StringIO

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)
customer_bp = Blueprint('customer', __name__)

# Main routes
@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/services')
def services():
    # Get active pricing plans for display
    pricing_plans = ServicePricing.query.filter_by(is_active=True).order_by(ServicePricing.display_order).all()
    return render_template('services.html', pricing_plans=pricing_plans)

@main_bp.route('/set_language/<language>')
def set_language(language):
    """Set the user's preferred language"""
    if language in ['en', 'pl']:
        session['language'] = language
    return redirect(request.referrer or url_for('main.index'))

@main_bp.route('/test_translation')
def test_translation():
    """Test route to verify translations are working"""
    from flask_babel import gettext
    test_strings = {
        'home': gettext('Home'),
        'about': gettext('About'),
        'services': gettext('Services'),
        'login': gettext('Login'),
        'current_locale': session.get('language', 'en')
    }
    return f"<h1>Translation Test</h1><pre>{test_strings}</pre>"

@main_bp.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
        'service_request_id': n.service_request_id
    } for n in notifications])

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', '').lower(), 80)
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        # Check IP rate limiting
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if is_ip_rate_limited(ip_address):
            flash('Too many failed login attempts. Please try again later.', 'danger')
            log_login_attempt(username, False)
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.is_account_locked():
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'warning')
            log_login_attempt(username, False)
            return render_template('auth/login.html')
        
        if user and user.check_password(password) and user.is_active:
            # Successful login
            user.reset_failed_login()
            db.session.commit()
            
            login_user(user, remember=remember)
            log_login_attempt(username, True)
            
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.dashboard'))
        else:
            # Failed login
            if user:
                user.increment_failed_login()
                db.session.commit()
            
            log_login_attempt(username, False)
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', '').lower(), 80)
        email = sanitize_input(request.form.get('email', '').lower(), 120) # Keep sanitize
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()[:50] # Remove sanitize, add strip and length limit
        last_name = request.form.get('last_name', '').strip()[:50] # Remove sanitize, add strip and length limit
        phone = sanitize_input(request.form.get('phone', ''), 20) # Keep sanitize
        selected_plan_id = request.form.get('selected_plan_id')
        
        pricing_plans = ServicePricing.query.filter_by(is_active=True).order_by(ServicePricing.display_order).all()
        
        # Enhanced validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        
        if not email or '@' not in email:
            errors.append('Please enter a valid email address')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Password strength validation
        password_errors = User.validate_password_strength(password) # Changed to User.method
        errors.extend(password_errors)
        
        if not first_name or not last_name:
            errors.append('First name and last name are required')
        
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        # Validate selected plan
        if selected_plan_id:
            selected_plan = ServicePricing.query.get(selected_plan_id)
            if not selected_plan or not selected_plan.is_active:
                errors.append('Invalid plan selected. Please choose a valid plan.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', pricing_plans=pricing_plans)
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='customer',
            selected_plan_id=int(selected_plan_id) if selected_plan_id else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send email verification
        if send_email_verification(user):
            flash('Registration successful! Please check your email to verify your account, then log in.', 'success')
        else:
            flash('Registration successful! Please log in. (Email verification temporarily unavailable)', 'success')
        
        return redirect(url_for('auth.login'))
    
    # Get active pricing plans for registration form
    pricing_plans = ServicePricing.query.filter_by(is_active=True).order_by(ServicePricing.display_order).all()
    return render_template('auth/register.html', pricing_plans=pricing_plans)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '').lower(), 120)
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.is_active:
            # Clean up old tokens for this user
            old_tokens = PasswordResetToken.query.filter_by(user_id=user.id, used=False).all()
            for token in old_tokens:
                db.session.delete(token)
            
            # Create new reset token
            reset_token = PasswordResetToken(user.id)
            db.session.add(reset_token)
            db.session.commit()
            
            # Send reset email
            if send_password_reset_email(user, reset_token):
                flash('Password reset instructions have been sent to your email address.', 'success')
            else:
                flash('Unable to send password reset email. Please try again later.', 'danger')
        else:
            # Don't reveal if email exists or not for security
            flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def reset_password(token):
    """Password reset with token"""
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Password strength validation
        password_errors = User.validate_password_strength(password) # Changed to User.method
        errors.extend(password_errors)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user = reset_token.user
        user.set_password(password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.unlock_account()  # Unlock account if it was locked
        
        # Mark token as used
        reset_token.use_token()
        
        db.session.commit()
        
        flash('Your password has been reset successfully. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    """Email verification"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if user and user.verify_email(token):
        db.session.commit()
        flash('Your email has been verified successfully!', 'success')
    else:
        flash('Invalid or expired verification link.', 'danger')
    
    return redirect(url_for('auth.login'))

# Admin routes
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get statistics
    total_requests = ServiceRequest.query.count()
    pending_requests = ServiceRequest.query.filter_by(status='pending').count()
    in_progress_requests = ServiceRequest.query.filter_by(status='in_progress').count()
    completed_requests = ServiceRequest.query.filter_by(status='completed').count()
    total_customers = User.query.filter_by(role='customer').count()
    
    # Get recent requests
    recent_requests = ServiceRequest.query.order_by(ServiceRequest.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         in_progress_requests=in_progress_requests,
                         completed_requests=completed_requests,
                         total_customers=total_customers,
                         recent_requests=recent_requests)

@admin_bp.route('/requests')
@login_required
def requests():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = ServiceRequest.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    requests = query.order_by(ServiceRequest.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('admin/requests.html', requests=requests, status_filter=status_filter)

@admin_bp.route('/request/<int:id>')
@login_required
def request_detail(id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(id)
    return render_template('admin/request_detail.html', request=service_request)

@admin_bp.route('/request/<int:id>/update', methods=['POST'])
@login_required
def update_request(id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    service_request = ServiceRequest.query.get_or_404(id)
    service_request.status = request.form['status']
    service_request.priority = request.form['priority']
    service_request.notes = request.form.get('notes', '')
    service_request.assigned_admin_id = current_user.id
    
    # Handle pricing updates
    estimated_hours = request.form.get('estimated_hours')
    hourly_rate = request.form.get('hourly_rate')
    pricing_notes = request.form.get('pricing_notes', '')
    
    if estimated_hours:
        service_request.estimated_hours = float(estimated_hours)
    if hourly_rate:
        service_request.hourly_rate = float(hourly_rate)
    
    service_request.pricing_notes = pricing_notes
    
    # Calculate total price
    if service_request.estimated_hours and service_request.hourly_rate:
        service_request.calculate_total_price()
    
    # Handle estimated time updates
    response_days = request.form.get('estimated_response_days')
    response_hours = request.form.get('estimated_response_hours')
    response_time_notes = request.form.get('response_time_notes', '')
    
    if response_days:
        service_request.estimated_response_days = int(response_days)
    if response_hours:
        service_request.estimated_response_hours = int(response_hours)
    
    service_request.response_time_notes = response_time_notes
    
    # Calculate completion deadline
    if service_request.estimated_response_days or service_request.estimated_response_hours:
        service_request.calculate_response_deadline()

    # Handle admin_set_deadline
    admin_set_deadline_str = request.form.get('admin_set_deadline')
    if admin_set_deadline_str:
        try:
            service_request.admin_set_deadline = datetime.strptime(admin_set_deadline_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid Admin Set Deadline format. Please use YYYY-MM-DD.', 'warning') # Changed to warning as it's not a critical failure for the whole update
            # Potentially log this error as well
    else:
        service_request.admin_set_deadline = None # Allow clearing the deadline
    
    db.session.commit()
    flash('Request updated successfully!', 'success')
    return redirect(url_for('admin.request_detail', id=id))

@admin_bp.route('/customers')
@login_required
def customers():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    customers = User.query.filter_by(role='customer').paginate(
        page=page, per_page=10, error_out=False)
    
    # These are used by the template for "New This Month" card
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    
    return render_template('admin/customers.html', 
                         customers=customers,
                         current_month=current_month,
                         current_year=current_year)

@admin_bp.route('/service_pricing')
@login_required
def service_pricing():
    """Admin page for managing service pricing"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    pricing_plans = ServicePricing.query.order_by(ServicePricing.display_order).all()
    return render_template('admin/service_pricing.html', pricing_plans=pricing_plans)

@admin_bp.route('/service_pricing/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service_pricing(id):
    """Edit a service pricing plan"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    pricing = ServicePricing.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update pricing plan
        pricing.plan_name = request.form.get('plan_name', '').strip()
        pricing.price = request.form.get('price', '').strip()
        pricing.price_period = request.form.get('price_period', '').strip()
        pricing.description = request.form.get('description', '').strip()
        pricing.button_text = request.form.get('button_text', 'Get Started').strip()
        pricing.button_link = request.form.get('button_link', '').strip()
        pricing.is_popular = 'is_popular' in request.form
        pricing.is_active = 'is_active' in request.form
        pricing.display_order = int(request.form.get('display_order', 0))
        
        # Handle features - convert from textarea to JSON
        features_text = request.form.get('features', '').strip()
        if features_text:
            # Split by newlines and clean up
            features_list = [f.strip() for f in features_text.split('\n') if f.strip()]
            pricing.set_features_list(features_list)
        else:
            pricing.features = None
        
        try:
            db.session.commit()
            flash(f'Pricing plan "{pricing.plan_name}" updated successfully!', 'success')
            return redirect(url_for('admin.service_pricing'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating pricing plan {pricing.id if pricing else 'new'}: {str(e)}")
            flash('Error updating pricing plan. Please check logs for details.', 'danger')
    
    # Convert features JSON back to text for editing
    features_text = ''
    if pricing.features:
        features_list = pricing.get_features_list()
        features_text = '\n'.join(features_list)
    
    return render_template('admin/edit_service_pricing.html', 
                         pricing=pricing, 
                         features_text=features_text)

@admin_bp.route('/service_pricing/new', methods=['GET', 'POST'])
@login_required
def new_service_pricing():
    """Create a new service pricing plan"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Create new pricing plan
        pricing = ServicePricing(
            plan_name=request.form.get('plan_name', '').strip(),
            price=request.form.get('price', '').strip(),
            price_period=request.form.get('price_period', '/hour').strip(),
            description=request.form.get('description', '').strip(),
            button_text=request.form.get('button_text', 'Get Started').strip(),
            button_link=request.form.get('button_link', '').strip(),
            is_popular='is_popular' in request.form,
            is_active='is_active' in request.form,
            display_order=int(request.form.get('display_order', 0))
        )
        
        # Handle features
        features_text = request.form.get('features', '').strip()
        if features_text:
            features_list = [f.strip() for f in features_text.split('\n') if f.strip()]
            pricing.set_features_list(features_list)
        
        try:
            db.session.add(pricing)
            db.session.commit()
            flash(f'Pricing plan "{pricing.plan_name}" created successfully!', 'success')
            return redirect(url_for('admin.service_pricing'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating new pricing plan: {str(e)}")
            flash('Error creating pricing plan. Please check logs for details.', 'danger')
    
    return render_template('admin/edit_service_pricing.html', pricing=None, features_text='')

@admin_bp.route('/service_pricing/delete/<int:id>', methods=['POST'])
@login_required
def delete_service_pricing(id):
    """Delete a service pricing plan"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    pricing = ServicePricing.query.get_or_404(id)
    plan_name = pricing.plan_name
    
    try:
        db.session.delete(pricing)
        db.session.commit()
        flash(f'Pricing plan "{plan_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting pricing plan {id}: {str(e)}")
        flash(f'Error deleting pricing plan "{plan_name}". Please check logs for details.', 'danger')
    
    return redirect(url_for('admin.service_pricing'))

# Customer routes
@customer_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    # Get customer's requests
    my_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).order_by(
        ServiceRequest.created_at.desc()).limit(5).all()
    
    # Get service requests that need payment (no approved payment exists)
    # from sqlalchemy import and_, not_, exists # Unused imports removed
    
    # Subquery to find service requests with approved payments
    approved_payment_subquery = db.session.query(Payment.service_request_id)\
        .filter(Payment.status == 'approved')
    
    # Get service requests without approved payments that have final costs
    unpaid_requests = ServiceRequest.query\
        .filter(ServiceRequest.customer_id == current_user.id)\
        .filter(ServiceRequest.total_price.isnot(None))\
        .filter(ServiceRequest.total_price > 0)\
        .filter(~ServiceRequest.id.in_(approved_payment_subquery))\
        .order_by(ServiceRequest.created_at.desc()).all()
    
    # Get actual pending payments for display
    pending_payments = Payment.query.join(ServiceRequest)\
        .filter(ServiceRequest.customer_id == current_user.id)\
        .filter(Payment.status == 'pending')\
        .order_by(Payment.submitted_at.desc()).all() # Corrected to submitted_at
    
    # Get statistics
    total_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).count()
    pending_requests = ServiceRequest.query.filter_by(customer_id=current_user.id, status='pending').count()
    completed_requests = ServiceRequest.query.filter_by(customer_id=current_user.id, status='completed').count()
    
    return render_template('customer/dashboard.html',
                         my_requests=my_requests,
                         total_requests=total_requests,
                         pending_requests=pending_requests,
                         completed_requests=completed_requests,
                         pending_payments=pending_payments,
                         unpaid_requests=unpaid_requests)

@customer_bp.route('/new_request', methods=['GET', 'POST'])
@login_required
def new_request():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        service_type = request.form['service_type']
        priority = request.form['priority']
        customer_proposed_deadline_str = request.form.get('customer_proposed_deadline')
        
        customer_proposed_deadline_obj = None
        if customer_proposed_deadline_str:
            try:
                customer_proposed_deadline_obj = datetime.strptime(customer_proposed_deadline_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid proposed delivery date format. Please use YYYY-MM-DD.', 'danger')
                # It might be better to return render_template here with form data preserved
                # For now, let's assume valid input or rely on browser date picker.
                # If an error occurs, it will be None and not saved.
                pass 

        service_request = ServiceRequest(
            title=title,
            description=description,
            service_type=service_type,
            priority=priority,
            customer_id=current_user.id,
            customer_proposed_deadline=customer_proposed_deadline_obj
        )
        
        db.session.add(service_request)
        db.session.commit()

        files = request.files.getlist('files')
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                file_upload = FileUpload(
                    filename=filename,
                    filepath=filepath,
                    service_request_id=service_request.id,
                    uploaded_by_id=current_user.id
                )
                db.session.add(file_upload)
        
        db.session.commit()
        
        flash('Service request submitted successfully!', 'success')
        return redirect(url_for('customer.dashboard'))
    
    return render_template('customer/new_request.html')

@customer_bp.route('/my_plan')
@login_required
def my_plan():
    """Customer plan management page"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    # Get all active pricing plans for comparison
    all_plans = ServicePricing.query.filter_by(is_active=True).order_by(ServicePricing.display_order).all()
    current_plan = current_user.selected_plan
    
    return render_template('customer/my_plan.html', 
                         current_plan=current_plan, 
                         all_plans=all_plans)

@customer_bp.route('/change_plan', methods=['POST'])
@login_required
def change_plan():
    """Change customer's selected plan"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    new_plan_id = request.form.get('new_plan_id')
    
    if not new_plan_id:
        flash('Please select a plan.', 'danger')
        return redirect(url_for('customer.my_plan'))
    
    # Validate the new plan
    new_plan = ServicePricing.query.get(new_plan_id)
    if not new_plan or not new_plan.is_active:
        flash('Invalid plan selected.', 'danger')
        return redirect(url_for('customer.my_plan'))
    
    # Check if it's the same plan
    if current_user.selected_plan_id == int(new_plan_id):
        flash('You are already on this plan.', 'info')
        return redirect(url_for('customer.my_plan'))
    
    # Update user's plan
    old_plan_name = current_user.get_plan_name()
    current_user.selected_plan_id = int(new_plan_id)
    
    try:
        db.session.commit()
        flash(f'Successfully changed from {old_plan_name} to {new_plan.plan_name} plan!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating your plan. Please try again.', 'danger')
    
    return redirect(url_for('customer.my_plan'))
    # Unreachable code removed: return render_template('customer/new_request.html')

@customer_bp.route('/my_requests')
@login_required
def my_requests():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    requests = ServiceRequest.query.filter_by(customer_id=current_user.id).order_by(
        ServiceRequest.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('customer/my_requests.html', requests=requests)

@customer_bp.route('/request/<int:id>')
@login_required
def request_detail(id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    service_request = ServiceRequest.query.filter_by(id=id, customer_id=current_user.id).first_or_404()
    return render_template('customer/request_detail.html', request=service_request)

@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.email = request.form.get('email')
        current_user.phone = request.form.get('phone', '')
        
        # Check if password is being updated
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Profile and password updated successfully!', 'success')
            else:
                flash('Current password is incorrect!', 'danger')
                return render_template('customer/profile.html')
        else:
            flash('Profile updated successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('customer.profile'))
    
    return render_template('customer/profile.html')

@customer_bp.route('/request/<int:id>/approve_pricing', methods=['POST'])
@login_required
def approve_pricing(id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    service_request = ServiceRequest.query.filter_by(id=id, customer_id=current_user.id).first_or_404()
    service_request.pricing_approved = True
    service_request.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    flash('Pricing approved successfully!', 'success')
    return redirect(url_for('customer.request_detail', id=id))


# ============================================================================
# REPORTING ROUTES
# ============================================================================

@admin_bp.route('/reports')
@login_required
def reports_dashboard():
    """Admin reports dashboard"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/reports_dashboard.html')

@admin_bp.route('/reports/outstanding-tasks')
@login_required
def outstanding_tasks_report():
    """Outstanding tasks report ordered by priority"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    outstanding_requests = ServiceRequest.get_outstanding_by_priority()
    
    return render_template('admin/outstanding_tasks_report.html', 
                         requests=outstanding_requests)

@admin_bp.route('/reports/income')
@login_required
def income_report():
    """Income reports with period filtering"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    period = request.args.get('period', 'monthly')
    year = request.args.get('year', datetime.now(timezone.utc).year, type=int)
    
    income_data = ServiceRequest.get_income_report(period=period, year=year)
    
    # Calculate totals
    total_income = sum(item.total_income or 0 for item in income_data)
    total_requests = sum(item.request_count or 0 for item in income_data)
    
    # Prepare chart data
    chart_data = {
        'labels': [],
        'income': [],
        'requests': []
    }
    
    for item in income_data:
        if period == 'weekly':
            chart_data['labels'].append(f'Week {int(item.period)}')
        elif period == 'monthly':
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            chart_data['labels'].append(month_names[int(item.period) - 1])
        else:
            chart_data['labels'].append(str(int(item.period)))
        
        chart_data['income'].append(float(item.total_income or 0))
        chart_data['requests'].append(int(item.request_count or 0))
    
    return render_template('admin/income_report.html',
                         income_data=income_data,
                         total_income=total_income,
                         total_requests=total_requests,
                         chart_data=json.dumps(chart_data),
                         period=period,
                         year=year)

@admin_bp.route('/reports/conversions')
@login_required
def conversion_report():
    """Conversion rates report"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    conversion_data = ServiceRequest.get_conversion_rates()
    
    return render_template('admin/conversion_report.html',
                         conversion_data=conversion_data)

@admin_bp.route('/reports/top-customers')
@login_required
def top_customers_report():
    """Top customers report"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    report_type = request.args.get('type', 'conversions')
    limit = request.args.get('limit', 10, type=int)
    
    if report_type == 'conversions':
        customers_data = User.get_top_customers_by_conversions(limit=limit)
        title = 'Top Customers by Conversion Rate'
    else:
        customers_data = User.get_top_customers_by_requests(limit=limit)
        title = 'Top Customers by Request Volume'
    
    return render_template('admin/top_customers_report.html',
                         customers_data=customers_data,
                         report_type=report_type,
                         title=title,
                         limit=limit)

@admin_bp.route('/reports/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports to CSV"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    output = StringIO()
    writer = csv.writer(output)
    
    if report_type == 'outstanding':
        writer.writerow(['ID', 'Title', 'Customer', 'Status', 'Priority Score', 'Created', 'Total Price', 'Overdue'])
        requests = ServiceRequest.get_outstanding_by_priority()
        for req in requests:
            writer.writerow([
                req.id,
                req.title,
                req.customer.username if req.customer else 'N/A',
                req.status,
                req.get_priority_score(),
                req.created_at.strftime('%Y-%m-%d %H:%M'),
                req.total_price or 'N/A',
                'Yes' if req.is_estimated_time_overdue() else 'No'
            ])
    
    elif report_type == 'income':
        period = request.args.get('period', 'monthly')
        year = request.args.get('year', datetime.now(timezone.utc).year, type=int)
        writer.writerow(['Period', 'Total Income', 'Request Count'])
        income_data = ServiceRequest.get_income_report(period=period, year=year)
        for item in income_data:
            writer.writerow([
                f'{period.title()} {int(item.period)}',
                item.total_income or 0,
                item.request_count or 0
            ])
    
    elif report_type == 'customers':
        report_subtype = request.args.get('type', 'conversions')
        if report_subtype == 'conversions':
            writer.writerow(['Customer', 'Email', 'Total Requests', 'Completed', 'Conversion Rate %', 'Total Value'])
            customers = User.get_top_customers_by_conversions()
            for customer_data in customers:
                writer.writerow([
                    customer_data['customer'].username,
                    customer_data['customer'].email,
                    customer_data['total_requests'],
                    customer_data['completed_requests'],
                    f"{customer_data['conversion_rate']:.1f}%",
                    f"${customer_data['total_value']:.2f}"
                ])
        else:
            writer.writerow(['Customer', 'Email', 'Total Requests', 'Completed', 'Total Value'])
            customers = User.get_top_customers_by_requests()
            for customer, request_count, total_value, completed_count in customers:
                writer.writerow([
                    customer.username,
                    customer.email,
                    request_count,
                    completed_count or 0,
                    f"${total_value or 0:.2f}"
                ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report_{datetime.now(timezone.utc).strftime("%Y%m%d")}.csv'
    
    return response


# ============================================================================
# FINANCIAL MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/finances')
@login_required
def financial_dashboard():
    """Main financial dashboard for administrators"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    from datetime import datetime, timedelta
    from calendar import monthrange
    # from app.models import FinancialSummary, TaxRecord, BusinessExpense # Removed local import
    
    # Get current month data
    now = datetime.now()
    current_summary = FinancialSummary.get_or_create_summary(now.year, now.month)
    
    # Get current month tax record
    current_tax_record = TaxRecord.get_or_create_month_record(now.year, now.month)
    current_tax_record.calculate_taxes()
    db.session.commit()
    
    # Get recent expenses
    recent_expenses = BusinessExpense.query.order_by(
        BusinessExpense.created_at.desc()
    ).limit(5).all()
    
    # Get year-to-date totals
    year_start = datetime(now.year, 1, 1).date()
    ytd_income = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'approved',
        Payment.processed_at >= year_start
    ).scalar() or 0.0
    
    ytd_expenses = BusinessExpense.get_total_expenses(year_start)
    ytd_net_income = ytd_income - ytd_expenses
    ytd_tax_liability = max(0, ytd_net_income * 0.09)
    
    # Get monthly trends (last 6 months)
    monthly_trends = []
    for i in range(6):
        month_date = now - timedelta(days=30*i)
        summary = FinancialSummary.get_or_create_summary(month_date.year, month_date.month)
        monthly_trends.append({
            'month': month_date.strftime('%b %Y'),
            'income': summary.total_income,
            'expenses': summary.total_expenses,
            'net_income': summary.net_income
        })
    
    monthly_trends.reverse()  # Show oldest to newest
    
    return render_template('admin/financial_dashboard.html',
                         current_summary=current_summary,
                         current_tax_record=current_tax_record,
                         recent_expenses=recent_expenses,
                         ytd_income=ytd_income,
                         ytd_expenses=ytd_expenses,
                         ytd_net_income=ytd_net_income,
                         ytd_tax_liability=ytd_tax_liability,
                         monthly_trends=monthly_trends)

@admin_bp.route('/finances/expenses')
@login_required
def expense_management():
    """Expense management page"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import BusinessExpense, ExpenseCategory # Removed local import
    
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', 'all')
    
    # Build query
    query = BusinessExpense.query
    if category_filter != 'all':
        query = query.filter_by(category_id=category_filter)
    
    expenses = query.order_by(BusinessExpense.expense_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter
    categories = ExpenseCategory.get_active_categories()
    
    # Get summary statistics
    total_expenses = BusinessExpense.get_total_expenses()
    monthly_expenses = BusinessExpense.get_total_expenses(
        datetime.now().replace(day=1).date()
    )
    
    return render_template('admin/expense_management.html',
                         expenses=expenses,
                         categories=categories,
                         category_filter=category_filter,
                         total_expenses=total_expenses,
                         monthly_expenses=monthly_expenses)

@admin_bp.route('/finances/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new business expense"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import BusinessExpense, ExpenseCategory # Removed local import
    
    if request.method == 'POST':
        category_id = request.form.get('category_id', type=int)
        amount = request.form.get('amount', type=float)
        description = request.form.get('description', '').strip()[:200] # Remove sanitize, add strip and length limit
        expense_date = request.form.get('expense_date')
        is_tax_deductible = bool(request.form.get('is_tax_deductible'))
        
        errors = []
        
        # Validation
        if not category_id:
            errors.append('Please select an expense category')
        if not amount or amount <= 0:
            errors.append('Please enter a valid amount')
        if not description:
            errors.append('Please enter a description')
        if not expense_date:
            errors.append('Please select an expense date')
        
        if not errors:
            try:
                expense_date_obj = datetime.strptime(expense_date, '%Y-%m-%d').date()
                
                expense = BusinessExpense(
                    category_id=category_id,
                    amount=amount,
                    description=description,
                    expense_date=expense_date_obj,
                    is_tax_deductible=is_tax_deductible,
                    created_by_id=current_user.id
                )
                
                db.session.add(expense)
                db.session.commit()
                
                flash(f'Expense of ${amount:.2f} added successfully!', 'success')
                return redirect(url_for('admin.expense_management'))
                
            except ValueError:
                errors.append('Invalid date format')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error saving expense: {str(e)}")
                errors.append('Error saving expense. Please check logs for details.')
        
        for error in errors:
            flash(error, 'danger')
    
    categories = ExpenseCategory.get_active_categories()
    return render_template('admin/add_expense.html', categories=categories)

@admin_bp.route('/finances/taxes')
@login_required
def tax_management():
    """Monthly tax management and calculation page"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import TaxRecord # Removed local import
    
    current_year = datetime.now().year
    
    # Get all tax records for current year
    tax_records = TaxRecord.query.filter_by(tax_year=current_year).order_by(
        TaxRecord.tax_month
    ).all()
    
    # Calculate taxes for each month
    for record in tax_records:
        record.calculate_taxes()
    
    db.session.commit()
    
    # Calculate annual totals
    annual_income = sum(record.gross_income for record in tax_records)
    annual_expenses = sum(record.tax_deductible_expenses for record in tax_records)
    annual_taxable_income = sum(record.taxable_income for record in tax_records)
    annual_tax_owed = sum(record.tax_owed for record in tax_records)
    annual_tax_paid = sum(record.tax_paid for record in tax_records)
    
    return render_template('admin/tax_management.html',
                         tax_records=tax_records,
                         current_year=current_year,
                         annual_income=annual_income,
                         annual_expenses=annual_expenses,
                         annual_taxable_income=annual_taxable_income,
                         annual_tax_owed=annual_tax_owed,
                         annual_tax_paid=annual_tax_paid)

@admin_bp.route('/finances/taxes/recalculate')
@login_required
def recalculate_taxes():
    """Recalculate all tax records"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import TaxRecord # Removed local import
    
    current_year = datetime.now(timezone.utc).year
    tax_records = TaxRecord.query.filter_by(tax_year=current_year).all()
    
    for record in tax_records:
        record.calculate_taxes()
        record.calculated_at = datetime.now(timezone.utc)
        record.calculated_by_id = current_user.id
    
    db.session.commit()
    
    flash('Monthly tax calculations updated successfully!', 'success')
    return redirect(url_for('admin.tax_management'))

@admin_bp.route('/finances/reports/profit-loss')
@login_required
def profit_loss_report():
    """Profit and Loss statement"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import BusinessExpense # Removed local import
    
    # Get date range from request
    year = request.args.get('year', datetime.now().year, type=int)
    period = request.args.get('period', 'annual')  # monthly, annual
    
    if period == 'annual':
        # Annual P&L
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        # Get income
        total_income = db.session.query(func.sum(Payment.amount)).filter(
            Payment.status == 'approved',
            Payment.processed_at >= start_date,
            Payment.processed_at <= end_date
        ).scalar() or 0.0
        
        # Get expenses by category
        expense_categories = BusinessExpense.get_expenses_by_category(start_date, end_date)
        total_expenses = sum(cat.total_amount for cat in expense_categories)
        
        # Calculate metrics
        gross_profit = total_income
        net_income = total_income - total_expenses
        profit_margin = (net_income / total_income * 100) if total_income > 0 else 0
        tax_liability = max(0, net_income * 0.09)
        
        return render_template('admin/profit_loss_report.html',
                             period=period,
                             year=year,
                             total_income=total_income,
                             expense_categories=expense_categories,
                             total_expenses=total_expenses,
                             gross_profit=gross_profit,
                             net_income=net_income,
                             profit_margin=profit_margin,
                             tax_liability=tax_liability)

@admin_bp.route('/finances/expense-categories')
@login_required
def expense_categories():
    """Manage expense categories"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import ExpenseCategory # Removed local import
    
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return render_template('admin/expense_categories.html', categories=categories)

@admin_bp.route('/finances/expense-categories/add', methods=['POST'])
@login_required
def add_expense_category():
    """Add new expense category"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import ExpenseCategory # Removed local import
    
    name = request.form.get('name', '').strip()[:100] # Remove sanitize
    description = request.form.get('description', '').strip()[:500] # Remove sanitize
    is_tax_deductible = bool(request.form.get('is_tax_deductible'))
    
    if name:
        # Check if category already exists
        existing = ExpenseCategory.query.filter_by(name=name).first()
        if existing:
            flash('Category with this name already exists', 'danger')
        else:
            category = ExpenseCategory(
                name=name,
                description=description,
                is_tax_deductible=is_tax_deductible
            )
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" added successfully!', 'success')
    else:
        flash('Category name is required', 'danger')
    
    return redirect(url_for('admin.expense_categories'))

@admin_bp.route('/finances/expense-categories/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_expense_category(category_id):
    """Edit expense category"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import ExpenseCategory # Removed local import
    
    category = ExpenseCategory.query.get_or_404(category_id)
    
    name = request.form.get('name', '').strip()[:100] # Remove sanitize
    description = request.form.get('description', '').strip()[:500] # Remove sanitize
    is_tax_deductible = bool(request.form.get('is_tax_deductible'))
    
    if name:
        # Check if another category with this name exists
        existing = ExpenseCategory.query.filter(
            ExpenseCategory.name == name,
            ExpenseCategory.id != category_id
        ).first()
        
        if existing:
            flash('Another category with this name already exists', 'danger')
        else:
            category.name = name
            category.description = description
            category.is_tax_deductible = is_tax_deductible
            
            db.session.commit()
            flash(f'Category "{name}" updated successfully!', 'success')
    else:
        flash('Category name is required', 'danger')
    
    return redirect(url_for('admin.expense_categories'))

@admin_bp.route('/finances/expense-categories/<int:category_id>/activate', methods=['POST'])
@login_required
def activate_expense_category(category_id):
    """Activate expense category"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import ExpenseCategory # Removed local import
    
    category = ExpenseCategory.query.get_or_404(category_id)
    category.is_active = True
    db.session.commit()
    
    flash(f'Category "{category.name}" activated successfully!', 'success')
    return redirect(url_for('admin.expense_categories'))

@admin_bp.route('/finances/expense-categories/<int:category_id>/deactivate', methods=['POST'])
@login_required
def deactivate_expense_category(category_id):
    """Deactivate expense category"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import ExpenseCategory # Removed local import
    
    category = ExpenseCategory.query.get_or_404(category_id)
    category.is_active = False
    db.session.commit()
    
    flash(f'Category "{category.name}" deactivated successfully!', 'success')
    return redirect(url_for('admin.expense_categories'))

@admin_bp.route('/finances/expenses/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete business expense"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import BusinessExpense # Removed local import
    
    expense = BusinessExpense.query.get_or_404(expense_id)
    description = expense.description
    
    db.session.delete(expense)
    db.session.commit()
    
    flash(f'Expense "{description}" deleted successfully!', 'success')
    return redirect(url_for('admin.expense_management'))

@admin_bp.route('/finances/taxes/<int:record_id>/mark-paid', methods=['POST'])
@login_required
def mark_tax_paid(record_id):
    """Mark tax record as paid"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # from app.models import TaxRecord # Removed local import
    
    record = TaxRecord.query.get_or_404(record_id)
    
    payment_amount = request.form.get('payment_amount', type=float)
    payment_date = request.form.get('payment_date')
    notes = request.form.get('notes', '').strip()[:500] # Remove sanitize
    
    if payment_amount and payment_date:
        try:
            payment_date_obj = datetime.strptime(payment_date, '%Y-%m-%d').date()
            
            record.tax_paid = payment_amount
            record.payment_date = payment_date_obj
            record.status = 'paid'
            if notes:
                record.notes = notes
            
            db.session.commit()
            
            flash(f'Tax payment of ${payment_amount:.2f} recorded for {record.get_month_name()}!', 'success')
        except ValueError:
            flash('Invalid payment date format', 'danger')
    else:
        flash('Payment amount and date are required', 'danger')
    
    return redirect(url_for('admin.tax_management'))

# ============================================================================
# PAYMENT SYSTEM ROUTES
# ============================================================================

@customer_bp.route('/payments')
@login_required
def payments():
    """Customer payments dashboard"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    # Get or create customer account
    account = CustomerAccount.get_or_create_account(current_user.id)
    account.update_totals()
    db.session.commit()
    
    # Get payment history
    payments = Payment.query.filter_by(customer_id=current_user.id).order_by(Payment.submitted_at.desc()).all()
    
    # Get service requests with outstanding balances
    outstanding_requests = ServiceRequest.query.filter(
        ServiceRequest.customer_id == current_user.id,
        ServiceRequest.status == 'completed',
        ServiceRequest.total_price > 0
    ).all()
    
    # Filter to only show requests with outstanding amounts
    outstanding_requests = [req for req in outstanding_requests if req.get_outstanding_amount() > 0]
    
    return render_template('customer/payments.html',
                         account=account,
                         payments=payments,
                         outstanding_requests=outstanding_requests)

@customer_bp.route('/make_payment', methods=['GET', 'POST'])
@login_required
def make_payment():
    """Customer make payment form"""
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        amount = request.form.get('amount', type=float)
        payment_method = sanitize_input(request.form.get('payment_method', ''), 50) # Keep sanitize
        payment_reference = request.form.get('payment_reference', '').strip()[:200] # Remove sanitize
        customer_notes = request.form.get('customer_notes', '').strip()[:500] # Remove sanitize
        service_request_id = request.form.get('service_request_id', type=int)
        
        errors = []
        
        # Validation
        if not amount or amount <= 0:
            errors.append('Please enter a valid payment amount')
        
        if not payment_method:
            errors.append('Please select a payment method')
        
        if payment_method in ['bank_transfer', 'check'] and not payment_reference:
            errors.append('Payment reference is required for this payment method')
        
        # Validate service request if specified
        service_request = None
        if service_request_id:
            service_request = ServiceRequest.query.filter_by(
                id=service_request_id,
                customer_id=current_user.id
            ).first()
            if not service_request:
                errors.append('Invalid service request selected')
            elif service_request.get_outstanding_amount() <= 0:
                errors.append('This request is already fully paid')
            elif amount > service_request.get_outstanding_amount():
                errors.append(f'Payment amount cannot exceed outstanding balance of {service_request.get_formatted_outstanding_amount()}')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Create payment record
            payment = Payment(
                customer_id=current_user.id,
                service_request_id=service_request_id,
                amount=amount,
                payment_method=payment_method,
                payment_reference=payment_reference,
                customer_notes=customer_notes,
                status='pending'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            flash('Payment submitted successfully! It will be reviewed by our admin team.', 'success')
            return redirect(url_for('customer.payments'))
    
    # Get outstanding requests for dropdown
    outstanding_requests = ServiceRequest.query.filter(
        ServiceRequest.customer_id == current_user.id,
        ServiceRequest.status == 'completed',
        ServiceRequest.total_price > 0
    ).all()
    
    # Filter to only show requests with outstanding amounts
    outstanding_requests = [req for req in outstanding_requests if req.get_outstanding_amount() > 0]
    
    return render_template('customer/make_payment.html',
                         outstanding_requests=outstanding_requests)

@admin_bp.route('/payments')
@login_required
def payments():
    """Admin payments management"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    status_filter = request.args.get('status', 'all')
    
    # Get payments based on filter
    if status_filter == 'all':
        payments = Payment.query.order_by(Payment.submitted_at.desc()).all()
    else:
        payments = Payment.query.filter_by(status=status_filter).order_by(Payment.submitted_at.desc()).all()
    
    # Get summary statistics
    pending_count = Payment.query.filter_by(status='pending').count()
    approved_count = Payment.query.filter_by(status='approved').count()
    rejected_count = Payment.query.filter_by(status='rejected').count()
    
    total_pending = db.session.query(func.sum(Payment.amount)).filter_by(status='pending').scalar() or 0
    total_approved = db.session.query(func.sum(Payment.amount)).filter_by(status='approved').scalar() or 0
    
    return render_template('admin/payments.html',
                         payments=payments,
                         status_filter=status_filter,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count,
                         total_pending=total_pending,
                         total_approved=total_approved)

@admin_bp.route('/payment/<int:payment_id>/process', methods=['POST'])
@login_required
def process_payment(payment_id):
    """Admin process payment (approve/reject)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.get_or_404(payment_id)
    action = request.form.get('action')
    admin_notes = request.form.get('admin_notes', '').strip()[:500] # Remove sanitize
    
    if action == 'approve':
        payment.approve_payment(current_user, admin_notes)
        
        # Update customer account
        account = CustomerAccount.get_or_create_account(payment.customer_id)
        account.update_totals()
        
        flash(f'Payment of {payment.get_formatted_amount()} approved successfully!', 'success')
    
    elif action == 'reject':
        payment.reject_payment(current_user, admin_notes)
        flash(f'Payment of {payment.get_formatted_amount()} rejected.', 'warning')
    
    else:
        flash('Invalid action specified.', 'danger')
        return redirect(url_for('admin.payments'))
    
    db.session.commit()
    return redirect(url_for('admin.payments'))

@admin_bp.route('/customer_accounts')
@login_required
def customer_accounts():
    """Admin customer accounts overview"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Update all customer accounts
    customers = User.query.filter_by(role='customer').all()
    for customer in customers:
        account = CustomerAccount.get_or_create_account(customer.id)
        account.update_totals()
    
    db.session.commit()
    
    # Get accounts with filters
    balance_filter = request.args.get('balance', 'all')
    
    if balance_filter == 'outstanding':
        accounts = CustomerAccount.query.filter(CustomerAccount.outstanding_balance > 0).all()
    elif balance_filter == 'paid':
        accounts = CustomerAccount.query.filter(CustomerAccount.outstanding_balance <= 0).all()
    else:
        accounts = CustomerAccount.query.all()
    
    # Sort by outstanding balance (highest first)
    accounts.sort(key=lambda x: x.outstanding_balance, reverse=True)
    
    # Calculate summary statistics
    total_outstanding = sum(acc.outstanding_balance for acc in CustomerAccount.query.all())
    total_billed = sum(acc.total_billed for acc in CustomerAccount.query.all())
    total_paid = sum(acc.total_paid for acc in CustomerAccount.query.all())
    accounts_with_balance = len([acc for acc in CustomerAccount.query.all() if acc.outstanding_balance > 0])
    
    return render_template('admin/customer_accounts.html',
                         accounts=accounts,
                         balance_filter=balance_filter,
                         total_outstanding=total_outstanding,
                         total_billed=total_billed,
                         total_paid=total_paid,
                         accounts_with_balance=accounts_with_balance)

@admin_bp.route('/customer_account/<int:customer_id>')
@login_required
def customer_account_detail(customer_id):
    """Admin view customer account details"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    customer = User.query.get_or_404(customer_id)
    if customer.role != 'customer':
        flash('Invalid customer specified.', 'danger')
        return redirect(url_for('admin.customer_accounts'))
    
    # Get or create account and update totals
    account = CustomerAccount.get_or_create_account(customer_id)
    account.update_totals()
    db.session.commit()
    
    # Get payment history
    payments = Payment.query.filter_by(customer_id=customer_id).order_by(Payment.submitted_at.desc()).all()
    
    # Get service requests
    service_requests = ServiceRequest.query.filter_by(customer_id=customer_id).order_by(ServiceRequest.created_at.desc()).all()
    
    return render_template('admin/customer_account_detail.html',
                         customer=customer,
                         account=account,
                         payments=payments,
                         service_requests=service_requests)

@admin_bp.route('/send_notification/<int:user_id>', methods=['POST'])
@login_required
def send_notification(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    message = request.form.get('message')
    service_request_id = request.form.get('service_request_id')

    if not message:
        flash('Message cannot be empty', 'danger')
        return redirect(request.referrer)

    notification = Notification(
        message=message,
        user_id=user_id,
        service_request_id=service_request_id
    )
    db.session.add(notification)
    db.session.commit()

    socketio.emit('new_notification', {'message': message}, room=str(user_id))

    flash('Notification sent successfully!', 'success')
    return redirect(request.referrer)