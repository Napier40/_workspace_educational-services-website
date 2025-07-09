"""
Security utilities and helpers
"""
from flask import request, flash, current_app
# Removed: from flask_mail import Message
from app import mail
from app.models import LoginAttempt, PasswordResetToken, User, db
from datetime import datetime
import re


def log_login_attempt(username, success):
    """Log login attempt with IP and user agent"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    LoginAttempt.log_attempt(
        ip_address=ip_address,
        username=username,
        success=success,
        user_agent=user_agent
    )


def is_ip_rate_limited(ip_address, max_attempts=10, window_minutes=15):
    """Check if IP address is rate limited"""
    failed_attempts = LoginAttempt.get_recent_failed_attempts(ip_address, window_minutes)
    return failed_attempts >= max_attempts


# def validate_password_strength(password): # Removed, use User.validate_password_strength directly
#     """Validate password meets security requirements"""
#     return User.validate_password_strength(password)


def send_password_reset_email(user, token):
    """Send password reset email"""
    try:
        subject = 'Password Reset Request - Educational Services'
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        recipients = [user.email]
        reset_url = request.url_root.rstrip('/') + f'/auth/reset_password/{token.token}'
        
        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user.first_name},</p>
            <p>You have requested to reset your password for your Educational Services account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_url}</p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Educational Services Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hello {user.first_name},
        
        You have requested to reset your password for your Educational Services account.
        
        Please visit the following link to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        Educational Services Team
        """
        
        mail.send_mail(
            subject=subject,
            message=text_body,
            from_email=sender,
            recipient_list=recipients,
            html_message=html_body
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email: {str(e)}")
        return False


def send_email_verification(user):
    """Send email verification email"""
    try:
        token = user.generate_email_verification_token()
        db.session.commit()
        
        subject = 'Verify Your Email - Educational Services'
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        recipients = [user.email]
        verify_url = request.url_root.rstrip('/') + f'/auth/verify_email/{token}'
        
        html_body = f"""
        <html>
        <body>
            <h2>Welcome to Educational Services!</h2>
            <p>Hello {user.first_name},</p>
            <p>Thank you for registering with Educational Services. Please verify your email address to complete your registration.</p>
            <p>Click the link below to verify your email:</p>
            <p><a href="{verify_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verify_url}</p>
            <p>If you did not create this account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Educational Services Team</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to Educational Services!
        
        Hello {user.first_name},
        
        Thank you for registering with Educational Services. Please verify your email address to complete your registration.
        
        Please visit the following link to verify your email:
        {verify_url}
        
        If you did not create this account, please ignore this email.
        
        Best regards,
        Educational Services Team
        """
        
        mail.send_mail(
            subject=subject,
            message=text_body,
            from_email=sender,
            recipient_list=recipients,
            html_message=html_body
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email verification: {str(e)}")
        return False


def sanitize_input(input_string, max_length=None):
    """Sanitize user input"""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(input_string))
    
    # Limit length if specified
    if max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def is_safe_url(target):
    """Check if redirect URL is safe"""
    if not target:
        return False
    
    # Only allow relative URLs or URLs to the same host
    if target.startswith('/'):
        return True
    
    from urllib.parse import urlparse
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc