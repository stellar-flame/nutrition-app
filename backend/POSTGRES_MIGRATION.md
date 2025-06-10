# Health App PostgreSQL Migration Guide

This document outlines the steps taken to migrate the Health App backend from SQLite to PostgreSQL.

## Setup Instructions

### Prerequisites
- PostgreSQL installed and running
- Python 3.9+ with pip
- Required Python packages (specified in requirements.txt)

### Installation

1. Install PostgreSQL (if not already installed)
   ```
   brew install postgresql
   brew services start postgresql
   ```

2. Create a new database
   ```
   createdb health_app
   ```

3. Install Python dependencies
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables
   - Copy `.env.example` to `.env`
   - Set `DATABASE_URL` to your PostgreSQL connection string
   - Example: `DATABASE_URL=postgresql://username:password@localhost/health_app`

### Database Migration

1. Initialize the database schema
   ```
   alembic upgrade head
   ```

2. Migrate data from SQLite to PostgreSQL (if needed)
   ```
   python migrate_data.py
   ```

## Database Configuration

### Connection Settings

The application uses SQLAlchemy ORM to connect to PostgreSQL. Key configuration:

- Connection pooling enabled for production use
- Connection recycling every 5 minutes
- Pool size of 10 connections with max overflow of 20
- Environment variables for configuration

### Alembic Migrations

To create new database migrations:

1. Make changes to model definitions in `models.py`
2. Generate a migration script
   ```
   alembic revision --autogenerate -m "Description of changes"
   ```
3. Apply the migration
   ```
   alembic upgrade head
   ```

## API Endpoints

All API endpoints have been updated to use SQLAlchemy with PostgreSQL. No changes to API URLs or request/response formats were made during migration.

## Production Considerations

- Connection pooling is configured for optimal performance
- Set appropriate `DATABASE_URL` in production environment
- Consider using a managed PostgreSQL service like AWS RDS, Google Cloud SQL, or Heroku Postgres in production
