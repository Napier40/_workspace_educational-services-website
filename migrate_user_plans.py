#!/usr/bin/env python3
"""
Add selected_plan_id column to User table
"""

from app import create_app, db
from app.models import User, ServicePricing

def migrate_user_plans():
    """Add selected_plan_id column to existing users"""
    app = create_app()
    
    with app.app_context():
        # Create tables with new schema
        db.create_all()
        
        # Get the Basic plan as default for existing users
        basic_plan = ServicePricing.query.filter_by(plan_name='Basic').first()
        
        if basic_plan:
            # Update existing users without a selected plan to use Basic plan
            users_without_plan = User.query.filter_by(selected_plan_id=None).all()
            
            for user in users_without_plan:
                user.selected_plan_id = basic_plan.id
                print(f"Assigned Basic plan to user: {user.username}")
            
            db.session.commit()
            print(f"Successfully updated {len(users_without_plan)} users with Basic plan")
        else:
            print("Warning: Basic plan not found. Users will have no default plan.")
        
        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_user_plans()