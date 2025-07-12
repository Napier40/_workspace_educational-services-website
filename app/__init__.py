import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta
from flask import Flask, request, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail
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
    if not app.debug and not app.testing:
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
        if 'language' in session:
            return session['language']
        
        if request.args.get('lang'):
            session['language'] = request.args.get('lang')
            return session['language']
        
        return request.accept_languages.best_match(['en', 'pl']) or 'en'
    
    babel.init_app(app, locale_selector=get_locale)
    
    @app.context_processor
    def inject_locale():
        from flask_babel import gettext
        return dict(get_locale=get_locale, _=gettext)
    
    @app.context_processor
    def inject_builtins():
        return dict(int=int, str=str, float=float, len=len, datetime=datetime, timedelta=timedelta)
    
    @app.template_filter('nl2br_safe')
    def nl2br_safe_filter(text):
        if text is None:
            return ''
        return Markup(text.replace('\n', '<br>\n'))
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
        return response
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
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
        # Admin user seeding is now handled by the 'flask seed' CLI command

    # Register CLI commands
    from . import cli
    cli.init_app(app)

    # Error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app
