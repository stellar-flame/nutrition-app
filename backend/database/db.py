"""
Unified database module that automatically selects the correct connection type
based on the environment (Lambda vs local development).
"""
import os

# Use Lambda-compatible database connection if running in Lambda
if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
    from .lambda_connection import get_db, init_db, get_db_session, engine, SessionLocal, Base
else:
    from .connection import get_db, init_db, get_db_session, engine, SessionLocal, Base

# Export all the database utilities
__all__ = ['get_db', 'init_db', 'get_db_session', 'engine', 'SessionLocal', 'Base']
