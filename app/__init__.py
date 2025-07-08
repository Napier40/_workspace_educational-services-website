from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
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

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
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
        return dict(int=int, str=str, float=float, len=len)
    
    # Add custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks"""
        if text is None:
            return ''
        return text.replace('\n', '<br>\n')
    
    # Mark the filter as safe for HTML output
    from markupsafe import Markup
    @app.template_filter('nl2br_safe')
    def nl2br_safe_filter(text):
        """Convert newlines to HTML line breaks and mark as safe"""
        if text is None:
            return ''
        return Markup(text.replace('\n', '<br>\n'))
    
    # Add moment-like function for date formatting
    from datetime import datetime
    
    class MomentJS:
        def __init__(self, timestamp=None):
            if timestamp is None:
                self.timestamp = datetime.utcnow()
            else:
                self.timestamp = timestamp
                
        def format(self, format_string):
            """Simple date formatting - convert moment.js format to Python strftime"""
            # Convert common moment.js formats to Python strftime
            format_map = {
                'MMMM Do YYYY, h:mm:ss a': '%B %d %Y, %I:%M:%S %p',
                'MMMM YYYY': '%B %Y',
                'YYYY-MM-DD': '%Y-%m-%d',
                'MM/DD/YYYY': '%m/%d/%Y',
                'DD/MM/YYYY': '%d/%m/%Y'
            }
            
            python_format = format_map.get(format_string, format_string)
            return self.timestamp.strftime(python_format)
    
    # Add moment function to template globals
    app.jinja_env.globals['moment'] = lambda timestamp=None: MomentJS(timestamp)
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
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
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
    
    return app