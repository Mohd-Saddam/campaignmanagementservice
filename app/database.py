"""
Database Configuration Module

This module sets up the database connection using SQLAlchemy ORM.
It loads the database URL from environment variables and creates
the engine, session factory, and base class for models.

Performance Features:
- Connection pooling for efficient database connections
- Pool pre-ping to validate connections before use
"""

import os  # Operating system interface for environment variables
from dotenv import load_dotenv  # Load environment variables from .env file
from sqlalchemy import create_engine  # Create database engine
from sqlalchemy.ext.declarative import declarative_base  # Base class for ORM models
from sqlalchemy.orm import sessionmaker  # Session factory for database operations

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Fix for Render PostgreSQL URL (postgres:// -> postgresql://)
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine with connection pooling for performance
# pool_size: Number of connections to keep open (5 is default)
# max_overflow: Extra connections allowed beyond pool_size (10 more)
# pool_pre_ping: Test connections before using to handle stale connections
# pool_recycle: Recycle connections after 1800 seconds (30 minutes)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,  # Maintain 5 persistent connections
    max_overflow=10,  # Allow up to 10 additional connections during peak load
    pool_pre_ping=True,  # Verify connection is alive before using
    pool_recycle=1800,  # Refresh connections every 30 minutes
)

# Create session factory - sessions are used for database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models - all models inherit from this
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    
    This is used with FastAPI's dependency injection system.
    It creates a new session for each request and ensures
    the session is closed after the request is complete.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()  # Create new session
    try:
        yield db  # Provide session to the route handler
    finally:
        db.close()  # Always close session when done
