# Django Warehouse Management System

**Quick Start Guide**

```bash
cd src
docker-compose build
docker-compose up
# Access at: http://localhost:8000
```

**Automated Features**:
✅ Database migrations run automatically
✅ Static files collected automatically
✅ PostgreSQL database ready to use
✅ Environment variables configured

## Overview of how to access the app:

**Authentification**

The application doesn't support direct sign in for new users (even admins), due to security and controle pourpueses. instead sign-ins are treated as registration request.
So to be able to login after creating an account the user request must be accepted by the admin. Once accpeted, then the credentials can be used to login.

How to login when first running the app:
 1) Enter Sign In information
 2) Create superuser:
    * docker-compose exec web python manage.py createsuperuser
 3) Login with superuser credentials 
 4) Navigate to Admin Controle Pannel, all the user registration requestes are found there, you can choose to accept and activate or not.
 5) Use the credentials of the accepted user to login


## Prerequisites

- Docker installed on your system
- Docker Compose installed

## Project Structure

```
src/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env
├── requirements.txt
├── mysite/
│   ├── settings.py
│   └── ...
├── inventory/
├── users/
└── ...
```

## Setup Instructions

### 1. Build and Start the Containers

```bash
cd src
docker-compose build
docker-compose up
```

### 2. Access the Application

- **Web Application**: http://localhost:8000

**Note**: Database migrations are now automated, The entrypoint script will automatically:
1. Wait for PostgreSQL to be ready
2. Run all database migrations
3. Collect static files
4. Start the application

### 3. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```
This will prompt you to enter:
- Username
- Email address
- Password (twice for confirmation)

```


## Database Configuration

The application uses PostgreSQL in Docker. The database credentials are:

- **Database Name**: warehouse_db
- **Username**: warehouse_user
- **Password**: warehouse_password
- **Host**: db (Docker service name)
- **Port**: 5432

## Development Workflow

1. Make changes to your code
2. The application will automatically reload
3. Run migrations if you changed models:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

## Production Deployment

For production deployment:

1. Set `DEBUG=0` in `.env`
2. Use a proper `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` with your domain
5. Consider using a production-ready web server like Nginx
6. Use environment variables for sensitive data
