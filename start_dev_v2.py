#!/usr/bin/env python3
"""
Enhanced Quick Start Script for Educational Services Flask Application v2.0.0
This script helps set up and run the application with internationalization support
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_virtual_environment():
    """Check if virtual environment is activated"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is activated")
        return True
    else:
        print("⚠️  Virtual environment not detected")
        print("Consider activating a virtual environment:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On macOS/Linux")
        print("  venv\\Scripts\\activate     # On Windows")
        return False

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False

def check_database():
    """Check if database exists and has data"""
    db_path = Path("instance/educational_services.db")
    if not db_path.exists():
        print("⚠️  Database not found")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        if user_count > 0:
            print(f"✅ Database found with {user_count} users")
            return True
        else:
            print("⚠️  Database exists but appears empty")
            return False
    except sqlite3.Error:
        print("⚠️  Database exists but may be corrupted")
        return False

def initialize_database():
    """Initialize the database with sample data"""
    print("\n🗄️  Initializing database...")
    
    scripts = [
        ("create_sample_data.py", "Creating sample data"),
        ("create_sample_payments.py", "Creating sample payments"),
        ("migrate_security_features.py", "Migrating security features"),
        ("migrate_payment_system.py", "Migrating payment system")
    ]
    
    for script, description in scripts:
        if Path(script).exists():
            print(f"  {description}...")
            try:
                subprocess.check_call([sys.executable, script])
            except subprocess.CalledProcessError:
                print(f"  ⚠️  Warning: {script} failed, continuing...")
        else:
            print(f"  ⚠️  {script} not found, skipping...")
    
    print("✅ Database initialization completed")
    return True

def compile_translations():
    """Compile translation files"""
    print("\n🌐 Compiling translations...")
    try:
        subprocess.check_call(["pybabel", "compile", "-d", "translations"])
        print("✅ Translations compiled successfully")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Could not compile translations (pybabel not found or failed)")
        print("Installing Babel and retrying...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Babel"])
            subprocess.check_call(["pybabel", "compile", "-d", "translations"])
            print("✅ Translations compiled successfully")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  Translation compilation failed - translations may not work properly")
            return False

def check_translations():
    """Check if translation files exist"""
    en_mo = Path("translations/en/LC_MESSAGES/messages.mo")
    pl_mo = Path("translations/pl/LC_MESSAGES/messages.mo")
    
    if en_mo.exists() and pl_mo.exists():
        print("✅ Translation files found")
        return True
    else:
        print("⚠️  Translation files missing")
        return False

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting Educational Services Flask Application v2.0.0...")
    print("=" * 70)
    print("Application will be available at: http://localhost:5000")
    print("=" * 70)
    print("\n👤 Demo Credentials:")
    print("Admin: john / Johnston")
    print("Admin: kamila / Johnston")
    print("Or register a new customer account")
    print("=" * 70)
    print("\n🌐 Language Support:")
    print("English: http://localhost:5000/set_language/en")
    print("Polish: http://localhost:5000/set_language/pl")
    print("=" * 70)
    print("\nPress Ctrl+C to stop the server")
    print("=" * 70)
    
    try:
        # Set environment variables
        os.environ["FLASK_APP"] = "run.py"
        os.environ["FLASK_ENV"] = "development"
        os.environ["FLASK_DEBUG"] = "1"
        
        subprocess.check_call([sys.executable, "run.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except subprocess.CalledProcessError:
        print("\n❌ Failed to start application")

def show_feature_summary():
    """Show summary of application features"""
    print("\n📋 Educational Services v2.0.0 Features:")
    print("=" * 50)
    print("✅ User Management & Authentication")
    print("✅ Service Request System")
    print("✅ Payment Processing System")
    print("✅ Admin Dashboard & Management")
    print("✅ Customer Dashboard & Reports")
    print("✅ Security Features & Audit Logging")
    print("✅ Dual Language Support (EN/PL)")
    print("✅ Professional Modular Architecture")
    print("✅ VS Code Integration & Debugging")
    print("✅ Comprehensive Reporting System")
    print("=" * 50)

def main():
    """Main setup and start function"""
    print("🎓 Educational Services Flask Application v2.0.0 - Enhanced Quick Start")
    print("=" * 70)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check virtual environment
    check_virtual_environment()
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)
    
    # Check and initialize database if needed
    if not check_database():
        if not initialize_database():
            print("\n❌ Database setup failed. Please check the error messages above.")
            sys.exit(1)
    
    # Check and compile translations
    if not check_translations():
        compile_translations()
    
    print("\n✅ Setup completed successfully!")
    
    # Show feature summary
    show_feature_summary()
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()