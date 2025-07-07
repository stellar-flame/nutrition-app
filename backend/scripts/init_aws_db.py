#!/usr/bin/env python3
"""
AWS Database Initialization Script

This script initializes the AWS RDS database by running Alembic migrations
using AWS environment configuration. Can accept credentials as arguments
or from .env.aws file.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import subprocess

def load_aws_env(args=None):
    """Load AWS environment variables from args or .env.aws"""
    if args and args.db_host:
        # Use command line arguments
        os.environ["DB_HOST"] = args.db_host
        os.environ["DB_PORT"] = str(args.db_port) if args.db_port else "5432"
        os.environ["DB_USER"] = args.db_user
        os.environ["DB_PASSWORD"] = args.db_password
        os.environ["DB_NAME"] = args.db_name
        print("✅ Loaded AWS environment from command line arguments")
    else:
        # Fall back to .env.aws file
        aws_env_path = Path(__file__).parent.parent / '.env.aws'
        if not aws_env_path.exists():
            print("❌ .env.aws file not found and no arguments provided!")
            sys.exit(1)
        
        load_dotenv(aws_env_path, override=True)
        print("✅ Loaded AWS environment configuration from .env.aws")

def test_connection():
    """Test connection to AWS RDS"""
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    
    print(f"🔍 Testing connection to AWS RDS:")
    print(f"   Host: {db_host}")
    print(f"   Database: {db_name}")
    print(f"   User: {db_user}")
    
    # Construct DATABASE_URL with SSL for AWS RDS
    db_password = os.getenv("DB_PASSWORD")
    db_port = os.getenv("DB_PORT")
    # URL encode the password to handle special characters
    encoded_password = quote_plus(db_password) if db_password else ""
    database_url = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text('SELECT version()'))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL Version: {version}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def run_migrations():
    """Run Alembic migrations"""
    print("\n🚀 Running Alembic migrations...")
    
    try:
        # Run alembic upgrade head
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
        else:
            print("❌ Migration failed!")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    return True

def verify_tables():
    """Verify that tables were created"""
    print("\n🔍 Verifying database tables...")
    
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    
    database_url = f"postgresql://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}?sslmode=require"
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            print("📋 Created tables:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Check Alembic version (only if table exists)
            try:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'alembic_version' AND table_schema = 'public'
                """))
                if result.fetchone():
                    result = conn.execute(text('SELECT version_num FROM alembic_version'))
                    version = result.fetchone()
                    if version:
                        print(f"✅ Alembic version: {version[0]}")
                else:
                    print("⚠️  No alembic_version table found")
            except Exception as e:
                print(f"⚠️  Could not check Alembic version: {e}")
            
            return len(tables) > 0
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Initialize AWS RDS database')
    parser.add_argument('--db-host', help='Database host')
    parser.add_argument('--db-port', type=int, default=5432, help='Database port')
    parser.add_argument('--db-user', help='Database user')
    parser.add_argument('--db-password', help='Database password')
    parser.add_argument('--db-name', help='Database name')
    parser.add_argument('--auto-confirm', action='store_true', 
                       help='Skip confirmation prompt (for CI/CD)')
    
    args = parser.parse_args()
    
    print("🏗️  AWS Database Initialization Script")
    print("=" * 50)
    
    # Load AWS environment
    load_aws_env(args)
    
    # Test connection
    if not test_connection():
        print("\n❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Confirm before proceeding (skip in auto mode)
    if not args.auto_confirm:
        response = input("\n⚠️  This will run migrations on AWS RDS. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    else:
        print("\n🤖 Auto-confirm enabled, proceeding with migrations...")
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Migration failed")
        sys.exit(1)
    
    # Verify tables
    if verify_tables():
        print("\n🎉 AWS database initialization completed successfully!")
    else:
        print("\n⚠️  Migration completed but table verification failed")

if __name__ == "__main__":
    main()
