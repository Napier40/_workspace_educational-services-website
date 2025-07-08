# Educational Services Website

A full-stack Python Flask web application for educational services with admin and customer login facilities, built with Bootstrap CSS framework.

## Features

### Admin Features
- **Admin Dashboard**: Overview of all service requests, customer statistics, and system metrics
- **Request Management**: View, update, and manage all customer service requests
- **Customer Management**: View all registered customers and their request history
- **Status Updates**: Update request status, priority, and add admin notes
- **Pricing Management**: Set hourly rates and estimated hours for service requests
- **Pricing Approval**: Track customer approval status for pricing quotes
- **Estimated Time Management**: Set estimated completion times in days and hours
- **Deadline Tracking**: Automatic calculation of completion deadlines and overdue alerts

### Customer Features
- **Customer Dashboard**: Personal overview of submitted requests, account information, and current plan
- **Plan Selection**: Choose pricing plan during registration with visual plan comparison
- **Plan Management**: View current plan, compare options, and change plans anytime from dashboard
- **Service Requests**: Submit new educational service requests with detailed descriptions
- **Request Tracking**: View status and progress of all submitted requests
- **Profile Management**: Update personal information and change password
- **Pricing Review**: View and approve pricing quotes from administrators
- **Cost Transparency**: See detailed breakdown of hourly rates and total costs

### Authentication System
- **Secure Login**: Password hashing with Werkzeug security
- **Role-based Access**: Separate admin and customer interfaces
- **Session Management**: Secure session handling with Flask-Login
- **User Registration**: New customer registration with validation

## Technology Stack

- **Backend**: Python Flask 2.3.3
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Bootstrap 5.3.0 with custom CSS
- **Authentication**: Flask-Login with password hashing
- **Forms**: Flask-WTF for form handling and validation

## Project Structure

```
educational-services/
├── app/
│   ├── __init__.py              # Flask app initialization
│   ├── config.py                # Application configuration
│   ├── models.py                # Database models (User, ServiceRequest)
│   ├── routes.py                # All application routes and blueprints
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Custom CSS styles
│   │   ├── images/              # Static images
│   │   └── js/                  # JavaScript files
│   └── templates/
│       ├── base.html            # Base template with navigation
│       ├── index.html           # Homepage
│       ├── about.html           # About page
│       ├── services.html        # Services page
│       ├── auth/
│       │   ├── login.html       # Login page
│       │   └── register.html    # Registration page
│       ├── admin/
│       │   ├── dashboard.html   # Admin dashboard
│       │   ├── requests.html    # Request management
│       │   ├── request_detail.html # Individual request details
│       │   └── customers.html   # Customer management
│       └── customer/
│           ├── dashboard.html   # Customer dashboard
│           ├── new_request.html # New request form
│           ├── my_requests.html # Customer's requests
│           ├── request_detail.html # Request details
│           └── profile.html     # Profile management
├── requirements.txt             # Python dependencies
├── run.py                      # Application entry point
└── README.md                   # This file
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

5. **Access the application**:
   - Open your web browser and go to `http://localhost:33993`

## Default Admin Accounts

The application comes with two pre-configured admin accounts:

| Username | Password | Role  |
|----------|----------|-------|
| john     | Johnston | Admin |
| kamila   | Johnston | Admin |

## Usage Guide

### For Customers:
1. **Register**: Create a new account using the registration form
2. **Login**: Sign in with your credentials
3. **Submit Requests**: Use the "New Request" feature to submit educational service requests
4. **Track Progress**: Monitor your requests through the dashboard and "My Requests" page
5. **Update Profile**: Manage your account information and change password

### For Admins:
1. **Login**: Use the provided admin credentials (john/Johnston or kamila/Johnston)
2. **Dashboard**: View system overview and recent activity
3. **Manage Requests**: Review, update status, and add notes to customer requests
4. **Customer Management**: View all registered customers and their activity
5. **Request Processing**: Update request status from pending → in progress → completed

## Service Types Available

- Mathematics (Algebra, Calculus, Statistics)
- Sciences (Physics, Chemistry, Biology)
- English & Literature
- Computer Science & Programming
- Test Preparation (SAT, ACT, GRE, GMAT)
- Academic Consulting & Study Skills

## Database Schema

### User Model
- ID, Username, Email, Password (hashed)
- First Name, Last Name, Phone
- Role (admin/customer), Active Status
- Created/Updated timestamps

### ServiceRequest Model
- ID, Title, Description, Service Type
- Priority (low/medium/high), Status (pending/in_progress/completed/cancelled)
- Customer ID, Assigned Admin ID
- Created/Updated timestamps, Due Date, Admin Notes
- Pricing fields: Estimated Hours (0.5 hour increments), Hourly Rate, Total Price
- Pricing Approval Status, Pricing Notes

## Security Features

- **Password Hashing**: All passwords are securely hashed using Werkzeug
- **Session Management**: Secure session handling with Flask-Login
- **Role-based Access Control**: Separate admin and customer interfaces
- **CSRF Protection**: Forms protected with Flask-WTF
- **Input Validation**: Server-side validation for all forms

## Customization

### Styling
- Modify `app/static/css/style.css` for custom styling
- Bootstrap classes can be customized or extended
- Color scheme and branding can be updated in CSS variables

### Configuration
- Update `app/config.py` for database settings, secret keys, etc.
- Environment variables can be used for production settings

### Adding Features
- New routes can be added to `app/routes.py`
- Database models can be extended in `app/models.py`
- New templates should follow the existing structure

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use environment variables for sensitive configuration
2. **Database**: Switch from SQLite to PostgreSQL or MySQL for production
3. **Web Server**: Use Gunicorn or uWSGI with Nginx
4. **Security**: Enable HTTPS, update secret keys, configure CORS
5. **Monitoring**: Add logging and monitoring solutions

## Troubleshooting

### Common Issues:

1. **Port Already in Use**: Change the port number in `run.py`
2. **Database Errors**: Delete the database file and restart to recreate tables
3. **Template Not Found**: Ensure all template files are in the correct directories
4. **Static Files Not Loading**: Check static file paths and Flask configuration

### Development Tips:

- Enable debug mode for development (already enabled in `run.py`)
- Use Flask's built-in debugger for troubleshooting
- Check browser console for JavaScript errors
- Verify database relationships if adding new models

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support or questions:
- Check the troubleshooting section above
- Review the code comments for implementation details
- Test with the provided demo accounts

## Pricing System

### Admin Pricing Management
- **Hourly Rate Setting**: Administrators can set custom hourly rates for each service request
- **Time Estimation**: Estimated hours can be set in 0.5-hour increments (0.5, 1.0, 1.5, 2.0, etc.)
- **Automatic Calculation**: Total price is automatically calculated (hours × rate)
- **Pricing Notes**: Administrators can add notes explaining the pricing structure

### Customer Pricing Approval
- **Transparent Pricing**: Customers see detailed breakdown of hours, rate, and total cost
- **Approval Required**: Customers must approve pricing before work proceeds
- **Pricing Status**: Clear indicators show whether pricing is pending or approved
- **Cost Visibility**: All pricing information is visible in dashboards and request details

### Pricing Workflow
1. **Admin Sets Pricing**: Administrator reviews request and sets estimated hours and hourly rate
2. **Customer Notification**: Customer sees pricing information in their dashboard and request details
3. **Customer Approval**: Customer reviews and approves the pricing quote
4. **Work Proceeds**: Once approved, the service can move forward with confirmed pricing

---

**Demo URL**: https://52675-be219d74-e9af-425c-bfd6-78311b22b73a.proxy.daytona.work

**Admin Login**: john / Johnston or kamila / Johnston
**Customer**: Register a new account to test customer features