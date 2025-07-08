# Visual Studio Code Setup Guide - Educational Services Website

## 📦 Export Package Contents

This export package (`educational-services-website-v1.1.3-vscode-export.zip`) contains the complete Educational Services Flask application with all recent updates, including the terminology change from "Response Time" to "Estimated Time".

## 🚀 Quick Setup Instructions

### 1. Extract and Open in VS Code
```bash
# Extract the zip file
unzip educational-services-website-v1.1.3-vscode-export.zip

# Navigate to the project directory
cd educational-services-website-v1.1.3-vscode-export

# Open in VS Code
code .
```

### 2. Set Up Python Environment
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

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings (optional for development)
```

### 4. Initialize Database
```bash
# The database is already included, but you can reinitialize if needed
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 🔐 Default Login Credentials

### Admin Accounts
- **Username**: `john` | **Password**: `Johnston`
- **Username**: `kamila` | **Password**: `Johnston`

### Test Customer Account
- **Username**: `testcustomer` | **Password**: `password123`

## 📁 Project Structure
```
educational-services-website/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes.py            # Application routes
│   ├── config.py            # Configuration settings
│   ├── templates/           # HTML templates
│   │   ├── admin/          # Admin panel templates
│   │   ├── customer/       # Customer portal templates
│   │   ├── auth/           # Authentication templates
│   │   └── base.html       # Base template
│   └── static/             # CSS, JS, images
├── instance/
│   └── educational_service.db  # SQLite database
├── requirements.txt         # Python dependencies
├── run.py                  # Application entry point
└── Documentation files
```

## 🆕 Recent Updates (v1.2.0)

### Customer Plan Selection & Management
- **Registration Plan Selection**: Choose pricing plan during account creation
- **Plan Management Dashboard**: Complete plan management from customer dashboard
- **Visual Plan Comparison**: Side-by-side plan comparison with features
- **Instant Plan Changes**: Change plans anytime with immediate effect

### Admin Service Pricing Management
- **Dynamic Pricing Control**: Manage all service pricing from admin panel
- **Live Plan Editor**: Create/edit plans with real-time preview
- **Popular Plan Control**: Mark plans as "Most Popular" with badges
- **Active/Inactive Plans**: Control plan visibility without deletion

### Key Features
- **Admin Portal**: Complete request management with pricing and estimated time tracking
- **Customer Portal**: Request submission, tracking, pricing approval, and plan management
- **Dynamic Pricing System**: Admin-controlled pricing with customer plan selection
- **Time Management**: Estimated completion times with deadline tracking
- **Bootstrap UI**: Responsive, modern interface with interactive plan cards

## 🛠️ VS Code Extensions (Recommended)

Install these extensions for the best development experience:

1. **Python** (Microsoft)
2. **Flask Snippets** (cstrap)
3. **Jinja** (wholroyd)
4. **HTML CSS Support** (ecmel)
5. **Bootstrap 5 Quick Snippets** (AnbuselvanRocky)
6. **SQLite Viewer** (qwtel)

## 🐛 Debugging in VS Code

### Launch Configuration
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask App",
            "type": "python",
            "request": "launch",
            "program": "run.py",
            "env": {
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

### Settings Configuration
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "files.associations": {
        "*.html": "jinja-html"
    },
    "emmet.includeLanguages": {
        "jinja-html": "html"
    }
}
```

## 📊 Database Management

### View Database in VS Code
1. Install **SQLite Viewer** extension
2. Open `instance/educational_service.db`
3. Explore tables: `user`, `service_request`

### Reset Database (if needed)
```bash
# Delete existing database
rm instance/educational_service.db

# Recreate with sample data
python -c "
from app import create_app, db
from app.models import User, ServiceRequest
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()
with app.app_context():
    db.create_all()
    
    # Create admin users
    admin1 = User(username='john', email='john@admin.com', 
                  password_hash=generate_password_hash('Johnston'), 
                  role='admin', full_name='John Admin')
    admin2 = User(username='kamila', email='kamila@admin.com', 
                  password_hash=generate_password_hash('Johnston'), 
                  role='admin', full_name='Kamila Admin')
    
    # Create test customer
    customer = User(username='testcustomer', email='test@customer.com',
                   password_hash=generate_password_hash('password123'),
                   role='customer', full_name='Test Customer')
    
    db.session.add_all([admin1, admin2, customer])
    db.session.commit()
    print('Database initialized successfully!')
"
```

## 🔧 Development Tips

### Hot Reload
The application runs in debug mode by default, so changes to Python files will automatically reload the server.

### Template Changes
HTML template changes are reflected immediately without server restart.

### CSS/JS Changes
Static file changes may require a browser refresh (Ctrl+F5).

## 📚 Additional Documentation

- `README.md` - Complete project overview
- `CHANGELOG.md` - Version history and updates
- `TERMINOLOGY_UPDATE.md` - Details about recent terminology changes
- `PROJECT_SUMMARY.md` - Technical implementation details
- `BUGFIX_SUMMARY.md` - Bug fixes and improvements

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Check if `instance/` directory exists
3. **Port Conflicts**: Change port in `run.py` if 5000 is occupied
4. **Template Errors**: Verify Jinja2 syntax in HTML files

### Getting Help
- Check the documentation files included in the package
- Review the Flask and Bootstrap documentation
- Use VS Code's integrated terminal for debugging

## ✅ Testing the Application

### Basic Application Testing
1. **Start the application**: `python run.py`
2. **Open browser**: Navigate to `http://localhost:5000`
3. **Test admin login**: Use john/Johnston credentials
4. **Test customer features**: Register a new customer or use test account
5. **Verify terminology**: Check that "Estimated Time" appears throughout the interface

### New Features Testing (v1.2.0)

#### Customer Plan Selection & Management
1. **Registration with Plan Selection**:
   - Go to `/auth/register`
   - Fill out registration form
   - Select a pricing plan from the visual cards
   - Complete registration and login

2. **Customer Dashboard Plan Display**:
   - Login as customer
   - Verify current plan is displayed on dashboard
   - Click "Manage Plan" link

3. **Plan Management**:
   - Navigate to "My Plan" from customer menu
   - View current plan details
   - Select a different plan
   - Confirm plan change
   - Verify immediate update

#### Admin Service Pricing Management
1. **Access Pricing Management**:
   - Login as admin (john/Johnston)
   - Go to Admin Panel → Service Pricing
   - View all pricing plans

2. **Edit Pricing Plans**:
   - Click "Edit Plan" on any pricing plan
   - Modify plan details (name, price, features)
   - Use live preview to see changes
   - Save changes

3. **Create New Plans**:
   - Click "Add New Plan"
   - Fill out plan details
   - Add features (one per line)
   - Set display order and popularity
   - Save new plan

4. **Verify Dynamic Updates**:
   - Make changes to pricing plans
   - Visit `/services` page
   - Verify changes appear immediately
   - Test customer registration to see updated plans

### Database Testing
1. **Plan Relationships**:
   - Verify customers have selected plans
   - Check plan changes are saved
   - Ensure inactive plans are hidden

2. **Data Integrity**:
   - Test plan deletion (should prevent if customers assigned)
   - Verify plan validation during selection
   - Check default plan assignment

The application is ready for comprehensive development and testing in Visual Studio Code!