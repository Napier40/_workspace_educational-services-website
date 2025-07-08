#!/usr/bin/env python3
"""
Create sample payment data for testing the payment system
"""
from app import create_app
from app.models import db, User, ServiceRequest, Payment, CustomerAccount
from datetime import datetime, timedelta
import random

def create_sample_payments():
    """Create sample payment data for testing"""
    app = create_app()
    
    with app.app_context():
        print("Creating sample payment data...")
        
        # Get customers and completed requests
        customers = User.query.filter_by(role='customer').all()
        completed_requests = ServiceRequest.query.filter(
            ServiceRequest.status == 'completed',
            ServiceRequest.total_price > 0
        ).all()
        
        if not customers:
            print("No customers found. Please run create_sample_data.py first.")
            return
        
        if not completed_requests:
            print("No completed requests found. Please run create_sample_data.py first.")
            return
        
        print(f"Found {len(customers)} customers and {len(completed_requests)} completed requests")
        
        # Create sample payments
        payment_methods = ['credit_card', 'bank_transfer', 'paypal', 'check', 'cash']
        statuses = ['pending', 'approved', 'rejected']
        
        sample_payments = []
        
        # Create payments for some completed requests
        for request in completed_requests[:20]:  # Create payments for first 20 requests
            # Decide if this request should have payments
            if random.random() > 0.3:  # 70% chance of having payments
                total_price = request.total_price
                
                # Create 1-3 payments for this request
                num_payments = random.randint(1, 3)
                remaining_amount = total_price
                
                for i in range(num_payments):
                    if remaining_amount <= 0:
                        break
                    
                    # Calculate payment amount
                    if i == num_payments - 1:  # Last payment
                        amount = remaining_amount
                    else:
                        # Random partial payment (20-80% of remaining)
                        max_payment = remaining_amount * 0.8
                        min_payment = min(remaining_amount * 0.2, 50)
                        amount = random.uniform(min_payment, max_payment)
                    
                    amount = round(amount, 2)
                    remaining_amount -= amount
                    
                    # Create payment
                    payment_method = random.choice(payment_methods)
                    status = random.choice(statuses)
                    
                    # Generate reference based on payment method
                    payment_reference = None
                    if payment_method == 'bank_transfer':
                        payment_reference = f"TXN{random.randint(100000, 999999)}"
                    elif payment_method == 'check':
                        payment_reference = f"CHK{random.randint(1000, 9999)}"
                    elif payment_method == 'paypal':
                        payment_reference = f"PP{random.randint(10000000, 99999999)}"
                    
                    # Create payment with date in the past
                    days_ago = random.randint(1, 30)
                    submitted_date = datetime.utcnow() - timedelta(days=days_ago)
                    
                    payment = Payment(
                        customer_id=request.customer_id,
                        service_request_id=request.id,
                        amount=amount,
                        payment_method=payment_method,
                        payment_reference=payment_reference,
                        status=status,
                        submitted_at=submitted_date,
                        customer_notes=f"Payment for {request.title}" if random.random() > 0.5 else None
                    )
                    
                    # If approved, set processed date and admin
                    if status == 'approved':
                        admin = User.query.filter_by(role='admin').first()
                        if admin:
                            payment.processed_at = submitted_date + timedelta(hours=random.randint(1, 48))
                            payment.processed_by_id = admin.id
                            payment.admin_notes = "Payment verified and approved" if random.random() > 0.5 else None
                    elif status == 'rejected':
                        admin = User.query.filter_by(role='admin').first()
                        if admin:
                            payment.processed_at = submitted_date + timedelta(hours=random.randint(1, 48))
                            payment.processed_by_id = admin.id
                            payment.admin_notes = "Payment could not be verified" if random.random() > 0.5 else None
                    
                    sample_payments.append(payment)
                    db.session.add(payment)
        
        # Create some general account payments (not tied to specific requests)
        for customer in customers[:3]:  # First 3 customers get general payments
            if random.random() > 0.5:  # 50% chance
                amount = random.uniform(50, 300)
                payment_method = random.choice(payment_methods)
                status = random.choice(statuses)
                
                days_ago = random.randint(1, 60)
                submitted_date = datetime.utcnow() - timedelta(days=days_ago)
                
                payment = Payment(
                    customer_id=customer.id,
                    service_request_id=None,  # General payment
                    amount=amount,
                    payment_method=payment_method,
                    payment_reference=f"GEN{random.randint(1000, 9999)}",
                    status=status,
                    submitted_at=submitted_date,
                    customer_notes="General account payment"
                )
                
                if status == 'approved':
                    admin = User.query.filter_by(role='admin').first()
                    if admin:
                        payment.processed_at = submitted_date + timedelta(hours=random.randint(1, 48))
                        payment.processed_by_id = admin.id
                
                sample_payments.append(payment)
                db.session.add(payment)
        
        db.session.commit()
        print(f"Created {len(sample_payments)} sample payments")
        
        # Update all customer accounts
        print("Updating customer account balances...")
        for customer in customers:
            account = CustomerAccount.get_or_create_account(customer.id)
            account.update_totals()
        
        db.session.commit()
        
        # Show summary
        pending_payments = Payment.query.filter_by(status='pending').count()
        approved_payments = Payment.query.filter_by(status='approved').count()
        rejected_payments = Payment.query.filter_by(status='rejected').count()
        
        total_pending_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(status='pending').scalar() or 0
        total_approved_amount = db.session.query(db.func.sum(Payment.amount)).filter_by(status='approved').scalar() or 0
        
        accounts_with_balance = CustomerAccount.query.filter(CustomerAccount.outstanding_balance > 0).count()
        total_outstanding = db.session.query(db.func.sum(CustomerAccount.outstanding_balance)).scalar() or 0
        
        print("\nPayment System Summary:")
        print(f"- Total Payments: {len(sample_payments)}")
        print(f"- Pending Payments: {pending_payments} (${total_pending_amount:.2f})")
        print(f"- Approved Payments: {approved_payments} (${total_approved_amount:.2f})")
        print(f"- Rejected Payments: {rejected_payments}")
        print(f"- Accounts with Outstanding Balance: {accounts_with_balance}")
        print(f"- Total Outstanding Balance: ${total_outstanding:.2f}")

if __name__ == '__main__':
    create_sample_payments()