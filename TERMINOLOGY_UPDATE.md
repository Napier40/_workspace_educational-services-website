# Terminology Update: Response Time → Estimated Time

## Overview
Updated all references from "Response Time" to "Estimated Time" throughout the application to better reflect the nature of the time estimates provided to customers.

## Changes Made

### Database Model (app/models.py)
- Updated comments in ServiceRequest model to use "estimated time" terminology
- Updated method docstrings:
  - `calculate_response_deadline()` → Updated docstring to reference "completion deadline"
  - `get_formatted_response_time()` → Renamed to `get_formatted_estimated_time()`
  - `is_response_overdue()` → Renamed to `is_estimated_time_overdue()`

### Routes (app/routes.py)
- Updated comments in admin request update handler
- Changed "Handle response time updates" → "Handle estimated time updates"
- Changed "Calculate response deadline" → "Calculate completion deadline"
- Removed duplicate code sections

### Templates Updated
1. **Admin Templates:**
   - `admin/dashboard.html` - Updated table headers and method calls
   - `admin/requests.html` - Updated table headers and method calls
   - `admin/request_detail.html` - Updated section headers, labels, and placeholders

2. **Customer Templates:**
   - `customer/dashboard.html` - Updated table headers and method calls
   - `customer/my_requests.html` - Updated table headers and method calls
   - `customer/request_detail.html` - Updated section headers and method calls

### Specific Changes
- Table headers: "Response Time" → "Estimated Time"
- Section headers: "Response Time Management" → "Estimated Time Management"
- Form labels: "Response Time Notes" → "Estimated Time Notes"
- Display text: "Expected Response Time" → "Expected Completion Time"
- Method calls updated to use new method names
- Placeholder text updated to reflect new terminology

## Database Schema
No database schema changes were required as the underlying field names remain the same for backward compatibility.

## Testing
- Application tested and confirmed working correctly
- All pages load successfully
- Terminology consistently updated throughout the interface
- No functional changes to the application logic

## Version
This update maintains full backward compatibility while improving the user-facing terminology for better clarity.