import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta # Added import
from flask import Flask, request, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail # Changed from flask_mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_moment import Moment
from flask_babel import Babel, gettext, ngettext, _
from markupsafe import Markup
from app.config import Config
from app.models import db

login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
moment = Moment()
babel = Babel()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)

    # Configure Logging
    if not app.debug and not app.testing: # Don't configure file logging if debug or testing
        log_dir = os.path.dirname(app.config['LOG_FILE_PATH'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = RotatingFileHandler(
            app.config['LOG_FILE_PATH'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(app.config['LOG_LEVEL'])

        # Remove default Flask handler if it exists
        if app.logger.hasHandlers():
            app.logger.handlers.clear()

        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('Application logging configured to file.')

    csrf.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    limiter.init_app(app)
    
    login_manager.init_app(app)
    
    # Configure Babel locale selector
    def get_locale():
        # Check if language is set in session
        if 'language' in session:
            return session['language']
        
        # Check if language is provided in URL parameter
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
            return session['language']
        
        # Fall back to browser's preferred language
        return request.accept_languages.best_match(['en', 'pl']) or 'en'
    
    # Initialize Babel with locale selector
    babel.init_app(app, locale_selector=get_locale)
    
    # Make get_locale and translation function available in templates
    @app.context_processor
    def inject_locale():
        from flask_babel import gettext
        return dict(get_locale=get_locale, _=gettext)
    
    # Add built-in functions to template context
    @app.context_processor
    def inject_builtins():
        return dict(int=int, str=str, float=float, len=len, datetime=datetime, timedelta=timedelta)
    
    # The 'Markup' class is already imported at the top of the file.
    # from markupsafe import Markup # This local import is redundant
    @app.template_filter('nl2br_safe')
    def nl2br_safe_filter(text):
        """Convert newlines to HTML line breaks and mark as safe"""
        if text is None:
            return ''
        return Markup(text.replace('\n', '<br>\n'))
    
    # login_manager configuration (Flask-Moment setup will be handled by its init_app and template includes)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
        return response
    
    # Add custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks"""
        if text is None:
            return ''
        return Markup(text.replace('\n', '<br>\n'))
    
    # Register blueprints
    from app.routes import main_bp, auth_bp, admin_bp, customer_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    
    # Create database tables and default users
    with app.app_context():
        db.create_all()

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Important: rollback the session in case of a DB error that caused the 500
        # This prevents the session from remaining in a broken state.
        db.session.rollback()
        return render_template('errors/500.html'), 500
        
        # Create default admin users if they don't exist
        from werkzeug.security import generate_password_hash
        admin_users = [
            {'username': 'john', 'email': 'john@admin.com', 'first_name': 'John', 'last_name': 'Admin'},
            {'username': 'kamila', 'email': 'kamila@admin.com', 'first_name': 'Kamila', 'last_name': 'Admin'}
        ]
        
        from app.models import User
        for admin_data in admin_users:
            existing_user = User.query.filter_by(username=admin_data['username']).first()
            if not existing_user:
                admin_user = User(
                    username=admin_data['username'],
                    email=admin_data['email'],
                    first_name=admin_data['first_name'],
                    last_name=admin_data['last_name'],
                    role='admin'
                )
                admin_user.set_password('Johnston')
                db.session.add(admin_user)
        
        db.session.commit()

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        # Important: rollback the session in case of a DB error that caused the 500
        # This prevents the session from remaining in a broken state.
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app