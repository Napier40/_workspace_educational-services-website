# Educational Services Flask Application v2.0.0 - VS Code Setup Guide

## Overview
This is the **Enhanced Educational Services Flask Application v2.0.0** - a complete upgrade from v1.4.0 with added internationalization support and optimized VS Code integration. This maintains all the professional features and modular architecture from v1.4.0 while adding dual-language support and enhanced development tools.

## What's New in v2.0.0
- ✅ **Dual Language Support** - English/Polish internationalization with Flask-Babel
- ✅ **Enhanced VS Code Integration** - Improved debugging, tasks, and workspace configuration
- ✅ **All v1.4.0 Features Preserved** - Complete payment system, reporting, security features
- ✅ **Professional Modular Architecture** - Maintained from v1.4.0 with blueprints and organized structure
- ✅ **Advanced Development Tools** - Enhanced debugging configurations and task automation

## Core Features (Preserved from v1.4.0)
- **Complete User Management System** - Registration, authentication, role-based access
- **Advanced Service Request System** - Customer requests with admin approval workflow
- **Full Payment Processing System** - Complete payment system with approval/rejection capabilities
- **Comprehensive Admin Dashboard** - User management, request approval, payment processing
- **Advanced Customer Dashboard** - Service requests, payments, account overview, reporting
- **Security Features** - CSRF protection, rate limiting, password hashing, audit logging
- **Reporting System** - Outstanding tasks, income reports, conversion analytics, top customers
- **Professional UI/UX** - Bootstrap-based responsive design with modern styling

## Quick Start Guide

### Prerequisites
- Python 3.8 or higher
- Visual Studio Code
- Git (optional, for version control)

### Step 1: Setup Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database and Sample Data
```bash
# Create sample data (includes users, service requests, payments)
python create_sample_data.py

# Create additional payment data
python create_sample_payments.py

# Run security migrations
python migrate_security_features.py

# Run payment system migrations
python migrate_payment_system.py
```

### Step 4: Compile Translations
```bash
pybabel compile -d translations
```

### Step 5: Run the Application
```bash
python run.py
```

The application will be available at: `http://localhost:5000`

## VS Code Development Features

### Debug Configurations
- **Flask Development Server**: Run with debugging enabled (F5)
- **Flask Production Mode**: Test production configuration
- **Python: Current File**: Debug individual Python files
- **Database Migration**: Debug database migration scripts
- **Create Sample Data**: Debug sample data creation

### Tasks Available (Ctrl+Shift+P → Tasks: Run Task)
- **Install Dependencies**: Install all required packages
- **Run Flask App**: Start the development server
- **Create Sample Data**: Generate test data
- **Create Sample Payments**: Generate payment test data
- **Database Migration - Security**: Run security feature migrations
- **Database Migration - Payment System**: Run payment system migrations

### Enhanced VS Code Settings
- **Python Environment**: Automatic virtual environment detection
- **Jinja2 Support**: Template syntax highlighting and completion
- **Flask Integration**: Optimized for Flask development
- **Code Quality**: Pylint integration with Flask-specific rules
- **Auto-formatting**: Black formatter integration

## Application Architecture

```
educational_services_v2/
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── babel.cfg                # Babel configuration for i18n
├── app/                     # Main application package
│   ├── __init__.py          # Application factory with Babel integration
│   ├── config.py            # Configuration settings
│   ├── models.py            # Database models (7 tables)
│   ├── routes.py            # Application routes (4 blueprints)
│   ├── security.py          # Security utilities
│   ├── static/              # CSS, JS, images
│   └── templates/           # Jinja2 templates (30+ files)
├── translations/            # Internationalization
│   ├── en/LC_MESSAGES/      # English translations
│   └── pl/LC_MESSAGES/      # Polish translations
├── instance/                # Database and instance files
├── .vscode/                 # VS Code configuration
│   ├── settings.json        # Workspace settings
│   ├── launch.json          # Debug configurations
│   └── tasks.json           # Task definitions
└── [Migration Scripts]      # Database migration utilities
```

## Testing Credentials

### Admin Accounts
- **Username**: john, **Password**: Johnston
- **Username**: kamila, **Password**: Johnston

### Customer Testing
- Register new customer accounts through the registration system
- Multiple existing customer accounts with payment history available

## Database Information
- **Database Type**: SQLite
- **Location**: `instance/educational_services.db`
- **Tables**: 7 tables with comprehensive relationships
- **Sample Data**: 100+ records across all entities
  - Users (admin and customers)
  - Service requests with varied statuses
  - Payments with approval workflow
  - Customer accounts with payment history
  - Security audit logs
  - Password reset tokens

## Language Support
- **Default Language**: English
- **Available Languages**: English (en), Polish (pl)
- **Language Switching**: Available in navigation with `/set_language/<lang>` route
- **Translation Management**: 
  ```bash
  # Extract new translatable strings
  pybabel extract -F babel.cfg -k _l -o messages.pot .
  
  # Update existing translations
  pybabel update -i messages.pot -d translations
  
  # Compile translations
  pybabel compile -d translations
  ```

## Security Features (Enhanced from v1.4.0)
- **CSRF Protection**: All forms protected with Flask-WTF
- **Rate Limiting**: Login attempts and form submissions limited
- **Password Security**: Secure password storage with Werkzeug
- **Session Management**: Secure session handling with internationalization
- **Input Validation**: Comprehensive form validation
- **Audit Logging**: Complete user action tracking
- **IP-based Security**: Rate limiting and monitoring

## Development Tips

### Running in Debug Mode
- Use F5 in VS Code to start with debugging enabled
- Automatic reloading on code changes
- Detailed error messages with Flask-Babel integration
- Interactive debugger

### Database Management
- Use migration scripts to update database schema
- Database file located at `instance/educational_services.db`
- Use SQLite browser tools to inspect database contents
- Sample data scripts available for testing

### Adding New Features
1. Create new routes in appropriate blueprint files (`app/routes.py`)
2. Add corresponding templates in the templates directory
3. Update models if database changes are needed (`app/models.py`)
4. Add translations for new text strings
5. Test with both languages (English/Polish)

### Translation Workflow
1. Mark translatable strings with `_()` function
2. Extract strings: `pybabel extract -F babel.cfg -k _l -o messages.pot .`
3. Update translations: `pybabel update -i messages.pot -d translations`
4. Edit `.po` files with translations
5. Compile: `pybabel compile -d translations`

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Run migration scripts in order
3. **Translation Issues**: Compile translations with `pybabel compile -d translations`
4. **Port Already in Use**: Change port in `run.py` or kill existing process

### VS Code Specific Issues
1. **Python Interpreter**: Ensure VS Code is using the virtual environment interpreter
2. **Debugging**: Check that launch configurations point to correct files
3. **Extensions**: Install recommended Python, Flask, and Jinja2 extensions

## Production Deployment Notes
- Set `FLASK_ENV=production` in environment variables
- Use a production WSGI server like Gunicorn
- Configure proper database (PostgreSQL/MySQL) for production
- Set up proper logging and monitoring
- Configure SSL/HTTPS
- Set strong SECRET_KEY in production
- Compile translations for production deployment

## Migration from v1.4.0
This v2.0.0 maintains full compatibility with v1.4.0 data and features while adding:
- Internationalization support
- Enhanced VS Code integration
- Improved development workflow
- Additional debugging capabilities

All existing v1.4.0 functionality is preserved and enhanced.

## Support and Documentation
- All major bugs from v1.4.0 have been preserved as fixed
- Comprehensive error handling implemented
- Full internationalization support added
- Production-ready security features maintained
- Complete payment processing system enhanced
- Professional modular architecture preserved

This application represents the evolution of the Educational Services platform with enhanced international support and development tools while maintaining all the robust features developed in previous versions.