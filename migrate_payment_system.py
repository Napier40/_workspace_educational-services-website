#!/usr/bin/env python3
"""
Database migration script to add payment system tables
"""
import sqlite3
import os
from datetime import datetime

def migrate_payment_system():
    """Add payment system tables to existing database"""
    db_path = 'instance/educational_service.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Please ensure the application database exists.")
        return False
    
    print("Backing up existing database...")
    backup_path = f'instance/educational_service_payment_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    # Create backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating payment system tables...")
        
        # Create Payment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                service_request_id INTEGER,
                amount REAL NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                payment_reference VARCHAR(200),
                status VARCHAR(20) DEFAULT 'pending',
                submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_at DATETIME,
                processed_by_id INTEGER,
                admin_notes TEXT,
                customer_notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES user (id),
                FOREIGN KEY (service_request_id) REFERENCES service_request (id),
                FOREIGN KEY (processed_by_id) REFERENCES user (id)
            )
        ''')
        print("Created payment table")
        
        # Create CustomerAccount table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_account (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL UNIQUE,
                total_billed REAL DEFAULT 0.0,
                total_paid REAL DEFAULT 0.0,
                outstanding_balance REAL DEFAULT 0.0,
                last_payment_date DATETIME,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES user (id)
            )
        ''')
        print("Created customer_account table")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_customer ON payment(customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_request ON payment(service_request_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_status ON payment(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_account_customer ON customer_account(customer_id)')
        print("Created database indexes")
        
        # Initialize customer accounts for existing customers
        cursor.execute('''
            INSERT OR IGNORE INTO customer_account (customer_id, total_billed, total_paid, outstanding_balance)
            SELECT id, 0.0, 0.0, 0.0 FROM user WHERE role = 'customer'
        ''')
        
        # Update customer accounts with existing completed request totals
        cursor.execute('''
            UPDATE customer_account 
            SET total_billed = (
                SELECT COALESCE(SUM(total_price), 0.0) 
                FROM service_request 
                WHERE customer_id = customer_account.customer_id 
                AND status = 'completed' 
                AND total_price > 0
            ),
            outstanding_balance = (
                SELECT COALESCE(SUM(total_price), 0.0) 
                FROM service_request 
                WHERE customer_id = customer_account.customer_id 
                AND status = 'completed' 
                AND total_price > 0
            )
        ''')
        
        conn.commit()
        print("Payment system migration completed successfully!")
        
        # Show summary
        cursor.execute('SELECT COUNT(*) FROM payment')
        payment_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customer_account')
        account_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM customer_account WHERE outstanding_balance > 0')
        accounts_with_balance = cursor.fetchone()[0]
        
        print(f"\nMigration Summary:")
        print(f"- Payment records: {payment_count}")
        print(f"- Customer accounts: {account_count}")
        print(f"- Accounts with outstanding balance: {accounts_with_balance}")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_payment_system()