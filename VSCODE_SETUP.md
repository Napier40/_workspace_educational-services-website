# Visual Studio Code Setup Guide

## 🚀 Quick Setup for Visual Studio Code

### 1. Extract and Open Project
1. Extract the `educational-services-website-v1.1.zip` file
2. Open Visual Studio Code
3. File → Open Folder → Select the extracted `educational-services-website` folder

### 2. Python Environment Setup
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

### 3. Run the Application
```bash
python run.py
```

### 4. Access the Application
- **Local URL**: http://localhost:52675
- **Admin Login**: john / Johnston or kamila / Johnston
- **Customer**: Register a new account

## 🔧 Recommended VS Code Extensions

### Essential Extensions
- **Python** (Microsoft) - Python language support
- **Flask Snippets** - Flask code snippets
- **Jinja** - Jinja2 template syntax highlighting
- **SQLite Viewer** - View SQLite database files
- **HTML CSS Support** - Enhanced HTML/CSS support

### Optional Extensions
- **GitLens** - Enhanced Git capabilities
- **Prettier** - Code formatting
- **Auto Rename Tag** - HTML tag renaming
- **Bracket Pair Colorizer** - Bracket highlighting
- **Material Icon Theme** - Better file icons

## 📁 Project Structure in VS Code

```
educational-services-website/
├── 📁 app/                    # Main application package
│   ├── 📄 __init__.py        # Flask app factory
│   ├── 📄 config.py          # Configuration settings
│   ├── 📄 models.py          # Database models with pricing
│   ├── 📄 routes.py          # All routes and blueprints
│   ├── 📁 static/css/        # Custom CSS styling
│   └── 📁 templates/         # HTML templates
│       ├── 📁 admin/         # Admin panel templates
│       ├── 📁 auth/          # Authentication templates
│       └── 📁 customer/      # Customer portal templates
├── 📄 requirements.txt       # Python dependencies
├── 📄 run.py                # Application entry point
├── 📄 README.md             # Comprehensive documentation
└── 📄 CHANGELOG.md          # Version history
```

## 🛠 Development Workflow

### 1. Database Management
```bash
# Delete database to reset (if needed)
rm -f instance/educational_service.db

# Database will be recreated automatically on next run
python run.py
```

### 2. Making Changes
- **Models**: Edit `app/models.py` for database changes
- **Routes**: Edit `app/routes.py` for new endpoints
- **Templates**: Edit files in `app/templates/` for UI changes
- **Styling**: Edit `app/static/css/style.css` for custom styles

### 3. Testing Features
- **Admin Features**: Login with john/Johnston or kamila/Johnston
- **Customer Features**: Register a new customer account
- **Pricing System**: Test admin pricing setup and customer approval

## 🎯 Key Features to Test

### Admin Pricing Management
1. Login as admin (john/Johnston)
2. Go to Admin Dashboard → Service Requests
3. Click on any request to view details
4. Set estimated hours (0.5 hour increments)
5. Set hourly rate
6. Add pricing notes
7. Update the request

### Customer Pricing Approval
1. Register as a new customer
2. Submit a service request
3. Wait for admin to set pricing (or login as admin to set it)
4. View the pricing in customer dashboard
5. Click on request to see pricing details
6. Approve the pricing

### Database Schema
- **Users**: Authentication, roles, personal info
- **ServiceRequests**: Requests with pricing fields
  - `estimated_hours`: Float (0.5 increments)
  - `hourly_rate`: Float (dollars per hour)
  - `total_price`: Float (calculated automatically)
  - `pricing_approved`: Boolean (customer approval)
  - `pricing_notes`: Text (admin explanations)

## 🐛 Troubleshooting

### Common Issues
1. **Port in use**: Change port in `run.py`
2. **Database errors**: Delete `instance/educational_service.db` and restart
3. **Template errors**: Check file paths are relative to templates folder
4. **Import errors**: Ensure virtual environment is activated

### Debug Mode
- Debug mode is enabled by default in `run.py`
- Flask debugger will show detailed error information
- Check terminal output for error messages

## 📚 Documentation Files
- **README.md**: Complete setup and usage guide
- **PROJECT_SUMMARY.md**: Feature overview and highlights
- **CHANGELOG.md**: Version history and updates
- **VSCODE_SETUP.md**: This setup guide

---

**Ready to develop!** 🎉
Your educational services website with pricing system is ready for development in Visual Studio Code.