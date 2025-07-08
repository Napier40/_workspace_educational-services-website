#!/usr/bin/env python3
"""
Create sample data for testing the reporting system
"""
from app import create_app
from app.models import db, User, ServiceRequest, ServicePricing
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample data for testing reports"""
    app = create_app()
    
    with app.app_context():
        print("Creating sample data for reporting system...")
        
        # Create sample customers if they don't exist
        sample_customers = [
            {'username': 'alice_student', 'email': 'alice@student.com', 'first_name': 'Alice', 'last_name': 'Johnson'},
            {'username': 'bob_learner', 'email': 'bob@learner.com', 'first_name': 'Bob', 'last_name': 'Smith'},
            {'username': 'carol_academic', 'email': 'carol@academic.com', 'first_name': 'Carol', 'last_name': 'Davis'},
            {'username': 'david_scholar', 'email': 'david@scholar.com', 'first_name': 'David', 'last_name': 'Wilson'},
            {'username': 'emma_pupil', 'email': 'emma@pupil.com', 'first_name': 'Emma', 'last_name': 'Brown'},
        ]
        
        customers = []
        for customer_data in sample_customers:
            existing_customer = User.query.filter_by(username=customer_data['username']).first()
            if not existing_customer:
                customer = User(
                    username=customer_data['username'],
                    email=customer_data['email'],
                    first_name=customer_data['first_name'],
                    last_name=customer_data['last_name'],
                    role='customer',
                    email_verified=True
                )
                customer.set_password('password123')
                db.session.add(customer)
                customers.append(customer)
                print(f"Created customer: {customer_data['username']}")
            else:
                customers.append(existing_customer)
                print(f"Customer already exists: {customer_data['username']}")
        
        db.session.commit()
        
        # Create sample service requests with various statuses and dates
        service_types = ['Tutoring', 'Assignment Help', 'Exam Preparation', 'Research Assistance', 'Writing Support']
        statuses = ['pending', 'in_progress', 'under_review', 'completed']
        
        # Create requests from different time periods
        base_date = datetime.utcnow()
        
        sample_requests = []
        for i in range(50):  # Create 50 sample requests
            customer = random.choice(customers)
            service_type = random.choice(service_types)
            status = random.choice(statuses)
            
            # Create requests from the past 6 months
            days_ago = random.randint(1, 180)
            created_date = base_date - timedelta(days=days_ago)
            
            # Set estimated hours and rate (some requests won't have estimates)
            estimated_hours = None
            hourly_rate = None
            total_price = None
            if random.random() > 0.3:  # 70% of requests have estimates
                estimated_hours = random.uniform(1, 20)
                hourly_rate = random.uniform(25, 75)
                total_price = estimated_hours * hourly_rate
            
            # Set response deadline
            response_deadline = created_date + timedelta(days=random.randint(1, 14))
            
            request = ServiceRequest(
                title=f"{service_type} Request #{i+1}",
                description=f"Sample {service_type.lower()} request for testing purposes.",
                service_type=service_type,
                customer_id=customer.id,
                status=status,
                estimated_hours=estimated_hours or 0.0,
                hourly_rate=hourly_rate or 0.0,
                total_price=total_price or 0.0,
                estimated_response_days=random.randint(1, 7),
                estimated_response_hours=random.randint(1, 24),
                response_deadline=response_deadline,
                due_date=response_deadline,
                created_at=created_date,
                updated_at=created_date
            )
            
            # If completed, set completion date
            if status == 'completed':
                completion_date = created_date + timedelta(days=random.randint(1, 10))
                request.updated_at = completion_date
            
            sample_requests.append(request)
            db.session.add(request)
        
        db.session.commit()
        print(f"Created {len(sample_requests)} sample service requests")
        
        # Update some requests to be overdue for testing
        overdue_count = 0
        for request in sample_requests[:10]:  # Make first 10 requests overdue
            if request.status in ['pending', 'in_progress']:
                request.response_deadline = datetime.utcnow() - timedelta(days=random.randint(1, 5))
                overdue_count += 1
        
        db.session.commit()
        print(f"Made {overdue_count} requests overdue for testing")
        
        print("Sample data creation completed!")
        print("\nSummary:")
        print(f"- Customers: {len(customers)}")
        print(f"- Service Requests: {len(sample_requests)}")
        print(f"- Completed Requests: {len([r for r in sample_requests if r.status == 'completed'])}")
        print(f"- Requests with Estimates: {len([r for r in sample_requests if r.total_price > 0])}")
        print(f"- Overdue Requests: {overdue_count}")

if __name__ == '__main__':
    create_sample_data()