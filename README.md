# Warehouse Management System

A production-grade, full-stack Warehouse Management System (WMS) built with Django and Tailwind CSS, designed for efficient digital operations across inventory, inbound, outbound, and user workflows. The system is containerized with Docker and follows modern deployment architecture.

## Features

### Core Features
- **Inventory Management**: Add, update, and delete products with fields: name, SKU, description, category, quantity and warehouse
- **Real-time Inventory Tracking**: Complete audit logs for all inventory changes
- **Search & Filtering**: By keyword, tag, category, or SKU
- **Low Stock Alerts**: Configurable thresholds with real-time notifications
- **Bulk Operations**: CSV/XLSX import/export for inventory management and adding products

### Inbound Management
- **Incoming Stock Logging**: Product, supplier, quantity, invoice/reference, received date, total value and recieved products
- **Bulk Inbound Uploads**: Via XLSX files
- **Automatic Inventory Updates**: Real-time stock level adjustments
- **Supplier Association**: Link inbound shipments to supplier records

### Outbound Management
- **Outbound Transactions**: Product, quantity, customer, reference, date and products
- **Negative Stock Prevention**: System validation to prevent invalid dispatches
- **Bulk Outbound Uploads**: Via XLSX files
- **Real-time Inventory Deduction**: Immediate stock level updates

### User & Role Management
- **Authentication & Authorization**: Django built-in Session based security
- **Role-Based Access Control**: Admin, Manager, Operator roles
- **Granular Permissions**: Read/write/delete permissions per module
- **Activity Logging**: Comprehensive audit trail of user actions
#### Permission matrix**
  **Legend:**
- **Full** = Full access
- **❌** = No access

| Feature / Function                                      | Admin | Manager | Operator |
|--------------------------------------------------------|:-----:|:-------:|:--------:|
| Authentication                                         | Login | Login   | Login    |
| Dashboard Access                                       | Full  | Full    | Full     |
| Product Management (add / edit / delete)               | Full  | Full   | ❌       |
| Warehouse Management (add / edit / delete)             | Full  | Full   | ❌       |
| Inventory Management (inbounds & outbounds)            | Full  | Full   | Full     |
| Inventory Valuation                                    | Full  | Full   | ❌       |
| Activity Reports                                       | Full  | Full   | ❌       |
| Audit Dashboard                                        | Full  | Full   | ❌       |
| Admin Control Panel                                    | Full  | Full   | ❌       |
| User Management (accept / decline user requests)       | Full  | Full   | ❌       |


### Dashboard & Insights
- **Key Statistics**: Total inventory items, inbound/outbound transactions, low stock alerts
- **Recent Activity Stream**: Real-time view of system activities
- **Transaction Volume Charts**: Daily/weekly/monthly visualizations

### Additional Features Implemented
- **Multi-Warehouse Support**: Per-warehouse quantity tracking and internal stock transfers
- **Inventory Valuation**: Product cost tracking with total stock valuation reports
- **Audit Dashboard**: Visual activity logs and frequent adjustment tracking

### Extra Feature:
- **Improved access security**: Only Admins/Managers can accept sign-in/registration requests, once accepted new users can use their sign-in details to login to the app 

## Project Structure

```
src/
├── inventory/          # Main inventory application
├── users/              # User management and authentication
├── mysite/             # Django project configuration
├── static/             # CSS/JS assets
└── templates/          # HTML templates
```

## Setup Instructions

1. **Prerequisites**:
   - Python 3.8+
   - Node.js (for frontend assets)
   - Docker (optional, for containerized deployment)

2. **Installation**:
   ```bash
   # Clone the repository
   git clone [repo-url]
   
   # create virtual envirement
   python -m venv venv_name
   venv_name\Scripts\activate
   cd Warehouse\ Management/src

   # Install Python dependencies
   pip install -r requirements.txt

   # Install Node dependencies
   npm install


3. **Docker Setup**:
   ```bash
   docker-compose up --build
   ```

## Configuration

- **Database**: SQLite/PostgreSQL
- **Environment Variables**: Configured in `.env` file
- **Tailwind CSS**: Configured in `tailwind.config.js`
- **Docker**: Containerized deployment with `docker-compose.yml`

## Technology Stack

- **Backend**: Django (Python)
- **Frontend**: Tailwind CSS + Vanilla JavaScript
- **Database**: SQLite/PostgreSQL
- **Containerization**: Docker 
- **Deployment**: [PENDING] AWS EC2 ready architecture with Nginx reverse proxy support

## Overview of how to access the app:

**Authentification**

The application doesn't support direct sign-in for new users (even admins), to enforce security and controle. Instead sign-ins are treated as registration request.
To login with Creds from Sign-in, the user request must be accepted by an Admin. Once accpeted, then the credentials can be used to login.

How to login when first running the app (No Admins registered):
 1) Enter Sign In information
 2) Create Superuser:
    * docker-compose exec web python manage.py createsuperuser
 3) Login with Superuser credentials 
 4) Navigate to Admin Controle Pannel, all the user registration requestes are found there, you can choose to accept and activate or not.
 5) Use the credentials of the accepted user to login

## Key Files

- `inventory/models.py` - Database models
- `inventory/views.py` - View logic
- `users/views.py` - Authentication and user management
- `mysite/settings.py` - Django configuration
