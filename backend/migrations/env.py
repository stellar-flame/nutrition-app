from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.connection import Base
from database.models import UserModel, MealModel  # Import all models here
target_metadata = Base.metadata

# Get database URL from environment variable
from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# If no DATABASE_URL, construct from individual components (for AWS setup)
if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT") 
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    
    if all([DB_HOST, DB_PORT, DB_USER, DB_NAME]):
        # URL encode the password to handle special characters
        encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        # Add SSL requirement for AWS RDS
        ssl_param = "?sslmode=require" if ".amazonaws.com" in DB_HOST else ""
        DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}{ssl_param}"
    else:
        # Default for local development
        DATABASE_URL = "postgresql://localhost/nutrition_app"
elif DATABASE_URL.startswith("postgres://"):
    # Heroku/Vercel style URLs need to be adapted for SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

config.set_main_option("sqlalchemy.url", "driver://user:pass@localhost/dbname")

# Override with actual database URL at runtime
def get_database_url():
    """Get the actual database URL, handling AWS environment variables"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    # If no DATABASE_URL, construct from individual components (for AWS setup)
    if not DATABASE_URL:
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT") 
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_NAME = os.getenv("DB_NAME")
        
        if all([DB_HOST, DB_PORT, DB_USER, DB_NAME]):
            # URL encode the password to handle special characters
            encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
            DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        else:
            # Default for local development
            DATABASE_URL = "postgresql://localhost/nutrition_app"
    elif DATABASE_URL.startswith("postgres://"):
        # Heroku/Vercel style URLs need to be adapted for SQLAlchemy
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    return DATABASE_URL

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy import create_engine
    
    # Use our database URL instead of config
    database_url = get_database_url()
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
