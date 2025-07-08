#!/usr/bin/env python3
"""
Database migration script to add security features to existing database
"""
import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add security columns to existing database"""
    db_path = 'instance/educational_service.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return False
    
    print("Backing up existing database...")
    backup_path = f'instance/educational_services_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # Create backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding security columns to User table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add security columns if they don't exist
        security_columns = [
            ('failed_login_attempts', 'INTEGER DEFAULT 0'),
            ('account_locked_until', 'DATETIME'),
            ('last_login', 'DATETIME'),
            ('password_changed_at', 'DATETIME'),
            ('email_verified', 'BOOLEAN DEFAULT 0'),
            ('email_verification_token', 'VARCHAR(100)')
        ]
        
        for column_name, column_def in security_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE user ADD COLUMN {column_name} {column_def}')
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"Column {column_name} might already exist: {e}")
        
        print("Creating password_reset_token table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_token (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token VARCHAR(100) NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        
        print("Creating login_attempt table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address VARCHAR(45) NOT NULL,
                username VARCHAR(80),
                success BOOLEAN NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT
            )
        ''')
        
        # Update existing users to have email_verified = 1 (assume existing users are verified)
        cursor.execute('UPDATE user SET email_verified = 1 WHERE email_verified IS NULL OR email_verified = 0')
        
        conn.commit()
        print("Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()