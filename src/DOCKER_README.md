# Django Warehouse Management System - Docker Setup

**Quick Start Guide**

```bash
cd src
docker-compose build
docker-compose up
# Access at: http://localhost:8000
# Admin at: http://localhost:8000/admin
```

**Automated Features**:
✅ Database migrations run automatically
✅ Static files collected automatically
✅ PostgreSQL database ready to use
✅ Environment variables configured

This guide provides comprehensive instructions for setting up and running the Django Warehouse Management System using Docker.

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
- **Admin Interface**: http://localhost:8000/admin
- **PostgreSQL Database**: localhost:5432 (username: warehouse_user, password: warehouse_password)

**Note**: Database migrations are now automated! The entrypoint script will automatically:
1. Wait for PostgreSQL to be ready
2. Run all database migrations
3. Collect static files
4. Start the application

### 3. Create Superuser (Optional)

#### Interactive Method (Recommended)
```bash
docker-compose exec web python manage.py createsuperuser
```
This will prompt you to enter:
- Username
- Email address
- Password (twice for confirmation)

#### Non-interactive Method
```bash
docker-compose exec web python manage.py createsuperuser --noinput --username admin --email admin@example.com
```
Then set the password:
```bash
docker-compose exec web python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(username='admin'); user.set_password('your_secure_password'); user.save()"
```

#### Automated Superuser Creation (Advanced)
To automatically create a superuser on container startup, you can modify the `entrypoint.sh` script. Add this before the `exec "$@"` line:

```bash
# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')).exists():
    User.objects.create_superuser(
        username=os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin'),
        email=os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com'),
        password=os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin')
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
"
```

Then add these environment variables to your `.env` file:
```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your_secure_password
```

**Security Note**: For production, use strong credentials and consider using secrets management.

## Common Commands

### Start the containers
```bash
docker-compose up
```

### Start in detached mode
```bash
docker-compose up -d
```

### Stop the containers
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs
```

### Run management commands
```bash
docker-compose exec web python manage.py [command]
```

### Rebuild containers
```bash
docker-compose build --no-cache
docker-compose up
```

## Environment Variables

The application uses the following environment variables (configured in `.env`):

- `DEBUG`: Set to `1` for development, `0` for production
- `SECRET_KEY`: Django secret key
- `DJANGO_ALLOWED_HOSTS`: Allowed host names
- `DB_NAME`: PostgreSQL database name
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_HOST`: Database host (use `db` for Docker)
- `DB_PORT`: Database port

## Database Configuration

The application uses PostgreSQL in Docker. The database credentials are:

- **Database Name**: warehouse_db
- **Username**: warehouse_user
- **Password**: warehouse_password
- **Host**: db (Docker service name)
- **Port**: 5432

## Development Workflow

1. Make changes to your code
2. The application will automatically reload (thanks to the volume mount)
3. Run migrations if you changed models:
   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate
   ```

## Windows-Specific Considerations

### Docker Desktop for Windows
- Ensure you have **Docker Desktop for Windows** installed with **WSL 2** enabled
- WSL 2 provides better performance and compatibility for Linux containers

### File Permissions
- Windows file permissions are handled differently than Linux
- The entrypoint script has executable permissions set in the Dockerfile

### Volume Mounting
- File changes on Windows may take slightly longer to sync to containers
- Use WSL 2 for best performance with volume mounting

### Command Line Interface
- Use **PowerShell** or **Windows Terminal** for best Docker experience
- All commands in this guide work in both PowerShell and CMD

### Common Windows Issues

#### Docker Desktop not starting
- Ensure Hyper-V is enabled in Windows Features
- Restart Docker Desktop if you get connection errors

#### File permission errors
```bash
# If you get permission errors, try:
docker-compose down -v
docker system prune -a
docker-compose up --build
```

#### Slow performance
- Allocate more resources to WSL 2 in Docker Desktop settings
- Ensure your project is in a WSL 2 accessible location (not deep in Windows directories)

## Troubleshooting

### Database connection issues
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify environment variables in `.env` file

### Port conflicts
- If port 8000 or 5432 are already in use, change them in `docker-compose.yml`

### Missing dependencies
- Ensure all packages in `requirements.txt` are installed in the container
- Rebuild if you add new dependencies: `docker-compose build`

## Production Deployment

For production deployment:

1. Set `DEBUG=0` in `.env`
2. Use a proper `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` with your domain
4. Set up proper database backups
5. Consider using a production-ready web server like Nginx
6. Use environment variables for sensitive data
