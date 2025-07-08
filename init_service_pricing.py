#!/usr/bin/env python3
"""
Initialize service pricing data in the database
"""

from app import create_app, db
from app.models import ServicePricing
import json

def init_service_pricing():
    """Initialize service pricing with default data"""
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if pricing data already exists
        if ServicePricing.query.first():
            print("Service pricing data already exists. Skipping initialization.")
            return
        
        # Default pricing plans
        pricing_plans = [
            {
                'plan_name': 'Basic',
                'price': '$25',
                'price_period': '/hour',
                'description': 'Perfect for individual students seeking quality tutoring support',
                'features': json.dumps([
                    'One-on-one tutoring',
                    'Flexible scheduling',
                    'Progress tracking',
                    'Email support'
                ]),
                'is_popular': False,
                'display_order': 1,
                'button_text': 'Get Started',
                'button_link': None
            },
            {
                'plan_name': 'Premium',
                'price': '$40',
                'price_period': '/hour',
                'description': 'Our most popular plan with expert tutors and premium features',
                'features': json.dumps([
                    'Expert tutors',
                    'Priority scheduling',
                    'Custom materials',
                    '24/7 support',
                    'Progress reports'
                ]),
                'is_popular': True,
                'display_order': 2,
                'button_text': 'Get Started',
                'button_link': None
            },
            {
                'plan_name': 'Enterprise',
                'price': 'Custom',
                'price_period': '',
                'description': 'Tailored solutions for institutions and large groups',
                'features': json.dumps([
                    'Group sessions',
                    'Institutional support',
                    'Custom curriculum',
                    'Dedicated manager',
                    'Analytics dashboard'
                ]),
                'is_popular': False,
                'display_order': 3,
                'button_text': 'Contact Sales',
                'button_link': 'mailto:sales@eduservices.com'
            }
        ]
        
        # Add pricing plans to database
        for plan_data in pricing_plans:
            pricing = ServicePricing(**plan_data)
            db.session.add(pricing)
        
        db.session.commit()
        print(f"Successfully initialized {len(pricing_plans)} service pricing plans!")
        
        # Display created plans
        plans = ServicePricing.query.order_by(ServicePricing.display_order).all()
        print("\nCreated pricing plans:")
        for plan in plans:
            popular = " (Most Popular)" if plan.is_popular else ""
            print(f"- {plan.plan_name}: {plan.price}{plan.price_period}{popular}")

if __name__ == '__main__':
    init_service_pricing()