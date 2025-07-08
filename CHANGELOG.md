# Changelog - Educational Services Website

## Version 1.1.0 - Pricing System Implementation

### 🆕 New Features

#### Admin Pricing Management
- **Hourly Rate Setting**: Administrators can now set custom hourly rates for each service request
- **Time Estimation**: Estimated hours can be set in 0.5-hour increments (0.5, 1.0, 1.5, 2.0, etc.)
- **Automatic Price Calculation**: Total price is automatically calculated based on hours × hourly rate
- **Pricing Notes**: Administrators can add detailed notes explaining pricing structure
- **Pricing Status Tracking**: Monitor which requests have pricing set and customer approval status

#### Customer Pricing Features
- **Transparent Pricing Display**: Customers see detailed breakdown of estimated hours, hourly rate, and total cost
- **Pricing Approval System**: Customers must approve pricing quotes before work can proceed
- **Pricing Status Indicators**: Clear visual indicators show pricing approval status
- **Cost Visibility**: Pricing information integrated into all customer dashboards and views

#### Database Enhancements
- **New Pricing Fields**: Added estimated_hours, hourly_rate, total_price to ServiceRequest model
- **Approval Tracking**: Added pricing_approved boolean field
- **Pricing Notes**: Added pricing_notes field for admin explanations
- **Automatic Calculations**: Built-in methods for price calculations and formatting

#### UI/UX Improvements
- **Enhanced Admin Interface**: Updated admin request management with pricing controls
- **Customer Approval Interface**: New pricing approval workflow for customers
- **Pricing Display**: Consistent pricing display across all tables and dashboards
- **Status Indicators**: Visual indicators for pricing approval status

### 🔧 Technical Updates
- **Model Methods**: Added helper methods for price formatting and calculations
- **Route Enhancements**: Updated admin routes to handle pricing data
- **New Customer Route**: Added pricing approval endpoint
- **Template Updates**: Enhanced all relevant templates with pricing information

### 📊 Dashboard Updates
- **Admin Dashboard**: Added pricing columns to request tables
- **Customer Dashboard**: Integrated pricing information and approval status
- **Request Details**: Enhanced detail views with comprehensive pricing information
- **Request Lists**: Added pricing columns to all request listing tables

---

## Version 1.0.0 - Initial Release

### ✅ Core Features
- Complete authentication system with admin and customer roles
- Admin panel with dashboard, request management, and customer management
- Customer portal with request submission, tracking, and profile management
- Bootstrap-based responsive design
- SQLAlchemy database with User and ServiceRequest models
- Flask-Login session management
- Comprehensive documentation and setup instructions

---

---

## Version 1.1.3 - Terminology Update

### 🔄 Changes
- **Terminology Update**: Changed "Response Time" to "Estimated Time" throughout the application
- **Method Renaming**: Updated model methods for better clarity:
  - `get_formatted_response_time()` → `get_formatted_estimated_time()`
  - `is_response_overdue()` → `is_estimated_time_overdue()`
- **UI Updates**: Updated all template headers, labels, and form fields
- **Admin Interface**: Updated section headers and management terminology
- **Customer Interface**: Improved clarity with "Expected Completion Time" terminology

### 🛠️ Technical Improvements
- Enhanced code readability with clearer method names
- Improved user experience with more intuitive terminology
- Maintained full backward compatibility with existing database schema
- Updated documentation to reflect terminology changes

---

---

## Version 1.2.0 - Customer Plan Selection and Management

### 🆕 New Features

#### Customer Plan Selection
- **Registration Plan Selection**: Customers can now choose their pricing plan during account registration
- **Visual Plan Cards**: Interactive plan selection with attractive card-based interface
- **Popular Plan Pre-selection**: Most popular plan is automatically selected during registration
- **Plan Validation**: Ensures selected plans are valid and active

#### Customer Plan Management
- **My Plan Dashboard**: Comprehensive plan management interface accessible from customer dashboard
- **Current Plan Display**: Customer dashboard shows current plan with pricing information
- **Plan Comparison**: Side-by-side comparison of all available plans
- **Easy Plan Changes**: One-click plan switching with confirmation dialog
- **Instant Updates**: Plan changes take effect immediately

#### Admin Service Pricing Management
- **Dynamic Pricing Control**: Admins can manage all service pricing from admin panel
- **Plan Creation/Editing**: Create, edit, and delete pricing plans with live preview
- **Feature Management**: Add/edit feature lists for each pricing plan
- **Popular Plan Control**: Mark plans as "Most Popular" with special badges
- **Active/Inactive Plans**: Control which plans are visible to customers

### 🔄 Database Enhancements
- **User-Plan Relationship**: Added selected_plan_id field to User model
- **Plan Helper Methods**: Added methods for plan name and price display
- **Service Pricing Model**: Comprehensive model for managing pricing plans
- **JSON Feature Storage**: Flexible feature list storage with JSON support

### 🎨 UI/UX Improvements
- **Interactive Plan Cards**: Click-to-select plan cards with visual feedback
- **Responsive Design**: All new interfaces work on mobile and desktop
- **Plan Status Indicators**: Clear visual indicators for current and popular plans
- **Navigation Updates**: Added "My Plan" to customer navigation menu

### 🛠️ Technical Updates
- **New Routes**: Added customer plan management and admin pricing routes
- **Template Enhancements**: New templates for plan selection and management
- **Form Validation**: Comprehensive validation for plan selection and changes
- **Database Migration**: Automatic database updates with new schema

---

**Current Version**: 1.2.0
**Release Date**: June 2025
**Compatibility**: Python 3.8+, Flask 2.3.3