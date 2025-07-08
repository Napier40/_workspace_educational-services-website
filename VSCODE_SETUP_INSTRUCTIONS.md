# Visual Studio Code Setup Instructions

## Educational Services Flask Application

This document provides comprehensive instructions for setting up and running the Educational Services Flask application in Visual Studio Code.

## Prerequisites

- Python 3.8 or higher
- Visual Studio Code
- Git (optional, for version control)

## Quick Start

1. **Open the Project**
   - Open Visual Studio Code
   - File → Open Workspace from File
   - Select `educational-services.code-workspace`

2. **Install Recommended Extensions**
   - VS Code will prompt you to install recommended extensions
   - Click "Install All" or install individually:
     - Python
     - Jinja
     - Black Formatter
     - Flake8
     - Tailwind CSS IntelliSense

3. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Run security features migration
   python migrate_security_features.py
   
   # Run payment system migration
   python migrate_payment_system.py
   
   # Create sample data (optional)
   python create_sample_data.py
   python create_sample_payments.py
   ```

5. **Run the Application**
   ```bash
   python run.py
   ```
   
   Or use VS Code's built-in debugger:
   - Press F5 or go to Run → Start Debugging
   - Select "Flask App" configuration

## Project Structure

```
educational-services/
├── app/                          # Main application package
│   ├── __init__.py              # App factory
│   ├── models.py                # Database models
│   ├── routes.py                # Application routes
│   ├── security.py              # Security utilities
│   ├── config.py                # Configuration
│   ├── templates/               # Jinja2 templates
│   │   ├── admin/              # Admin templates
│   │   ├── customer/           # Customer templates
│   │   ├── auth/               # Authentication templates
│   │   └── base.html           # Base template
│   └── static/                  # Static files
│       ├── css/                # Stylesheets
│       ├── js/                 # JavaScript files
│       └── images/             # Images
├── instance/                    # Instance-specific files
│   └── educational_service.db   # SQLite database
├── .vscode/                     # VS Code configuration
│   ├── settings.json           # Workspace settings
│   ├── launch.json             # Debug configurations
│   └── tasks.json              # Task definitions
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── *.py                        # Migration and utility scripts
```

## Features Overview

### Core Features
- **User Authentication**: Registration, login, password recovery
- **Service Requests**: Customer request management system
- **Admin Dashboard**: Comprehensive admin controls
- **Dynamic Pricing**: Flexible service pricing management
- **Customer Plans**: Multiple subscription tiers

### Security Features
- **Password Recovery**: Secure token-based password reset
- **Rate Limiting**: Login attempt protection
- **CSRF Protection**: Cross-site request forgery prevention
- **Password Hashing**: Secure password storage
- **Session Management**: Secure user sessions

### Reporting System
- **Outstanding Tasks**: Priority-ordered task management
- **Income Reports**: Weekly, monthly, yearly analytics
- **Conversion Analytics**: Customer conversion tracking
- **Top Customers**: Performance-based customer ranking
- **Printable Reports**: Professional report generation

### Payment System
- **Customer Payments**: Payment submission interface
- **Admin Management**: Payment approval/rejection system
- **Balance Tracking**: Real-time outstanding balance calculation
- **Payment History**: Complete audit trail
- **Payment Analytics**: Financial reporting and insights

## Development Workflow

### Running the Application

1. **Development Mode** (with debugging):
   ```bash
   python run.py
   ```
   - Access at: http://localhost:5000
   - Debug mode enabled
   - Auto-reload on file changes

2. **Using VS Code Debugger**:
   - Set breakpoints in your code
   - Press F5 to start debugging
   - Use the Debug Console for interactive debugging

### Database Management

1. **View Database**:
   - Use SQLite browser or VS Code SQLite extension
   - Database location: `instance/educational_service.db`

2. **Reset Database**:
   ```bash
   # Delete existing database
   rm instance/educational_service.db
   
   # Run migrations
   python migrate_security_features.py
   python migrate_payment_system.py
   
   # Create sample data
   python create_sample_data.py
   python create_sample_payments.py
   ```

### Testing

1. **Manual Testing**:
   - Use demo credentials provided on login page
   - Admin accounts: john/Johnston, kamila/Johnston
   - Register new customer accounts for testing

2. **Feature Testing**:
   - Test all authentication flows
   - Create and manage service requests
   - Test payment submission and approval
   - Generate and view reports

## Configuration

### Environment Variables
Create a `.env` file in the root directory:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/educational_service.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Application Settings
Edit `app/config.py` to modify:
- Database settings
- Mail configuration
- Security settings
- Rate limiting parameters

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure virtual environment is activated
   - Verify all dependencies are installed: `pip install -r requirements.txt`

2. **Database Errors**:
   - Run migration scripts in order
   - Check database file permissions
   - Verify SQLite installation

3. **Template Errors**:
   - Check Jinja2 syntax in templates
   - Verify template inheritance structure
   - Ensure all required context variables are passed

4. **Static Files Not Loading**:
   - Check static file paths in templates
   - Verify Flask static folder configuration
   - Clear browser cache

### Debug Tips

1. **Use VS Code Debugger**:
   - Set breakpoints in Python code
   - Inspect variables and call stack
   - Step through code execution

2. **Check Application Logs**:
   - Monitor console output for errors
   - Use Flask's debug mode for detailed error pages

3. **Database Debugging**:
   - Use SQLite browser to inspect database state
   - Check foreign key relationships
   - Verify data integrity

## Production Deployment

### Security Considerations
- Change default secret key
- Use environment variables for sensitive data
- Enable HTTPS
- Configure proper database permissions
- Set up proper logging

### Performance Optimization
- Use production WSGI server (Gunicorn, uWSGI)
- Configure database connection pooling
- Enable static file caching
- Optimize database queries

## Support

For issues or questions:
1. Check this documentation
2. Review error logs and console output
3. Test with sample data
4. Verify configuration settings

## Demo Credentials

### Admin Accounts
- **Username**: john, **Password**: Johnston
- **Username**: kamila, **Password**: Johnston

### Customer Testing
- Register new customer accounts through the registration page
- Use different plan types to test functionality
- Submit service requests to test the workflow

---

**Note**: This application is configured for development use. For production deployment, additional security and performance configurations are required.