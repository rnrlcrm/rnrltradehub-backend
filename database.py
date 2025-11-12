"""
Database configuration and session management.

This module provides database connection and session management using SQLAlchemy.
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

# Get database configuration from environment variables
# Priority: DATABASE_URL > individual DB_* variables > default localhost
db_host = os.getenv("DB_HOST", "").strip()
db_name = os.getenv("DB_NAME", "").strip()
db_user = os.getenv("DB_USER", "").strip()
db_password = os.getenv("DB_PASSWORD", "").strip()
db_port = os.getenv("DB_PORT", "5432").strip()

# Build DATABASE_URL based on available environment variables
database_url_env = os.getenv("DATABASE_URL", "").strip()
if database_url_env:
    # Use DATABASE_URL if explicitly provided and not empty
    DATABASE_URL = database_url_env
elif db_host and db_name and db_user and db_password:
    # Build from individual components (all must be non-empty)
    # Check if DB_HOST is a Cloud SQL Unix socket path
    if db_host.startswith("/cloudsql/"):
        # Cloud SQL Unix socket connection format
        # Format: postgresql+psycopg2://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        # Standard TCP connection format
        DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
else:
    # Default for local development
    DATABASE_URL = "postgresql+psycopg2://user:password@localhost:5432/rnrltradehub"
    logger.warning(
        "Database configuration incomplete. Using default localhost connection. "
        "Please set DATABASE_URL or all of (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) "
        "environment variables with non-empty values."
    )

# Log database configuration (without credentials)
logger.info("---- DATABASE DEBUG START ----")
logger.info(f"DB_HOST: {db_host}")
logger.info(f"DB_NAME: {db_name}")
logger.info(f"DB_USER: {db_user}")
logger.info(f"DB_PORT: {db_port}")
logger.info(f"Using Cloud SQL socket: {'/cloudsql/' in db_host}")
logger.info(f"Final DATABASE_URL (masked): {DATABASE_URL.replace(db_password, '***') if db_password else DATABASE_URL}")
logger.info("---- DATABASE DEBUG END ----")

if "postgresql" in DATABASE_URL:
    logger.info("Database: PostgreSQL")
elif "sqlite" in DATABASE_URL:
    logger.info("Database: SQLite")
elif "mysql" in DATABASE_URL:
    logger.info("Database: MySQL")
else:
    logger.info("Database: Other")

# Create SQLAlchemy engine with robust configuration
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,  # 10 second timeout for connections
        } if "postgresql" in DATABASE_URL else {},
        echo=False  # Set to True for SQL query logging (debugging)
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error("Failed to create database engine: %s", str(e))
    # Create a fallback engine with NullPool for better error handling
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    This function is used as a dependency in FastAPI routes to provide
    a database session that is automatically closed after the request.

    Yields:
        Session: SQLAlchemy database session.
    
    Raises:
        HTTPException: If database connection cannot be established.
    """
    from fastapi import HTTPException
    
    try:
        db = SessionLocal()
    except Exception as e:
        logger.error("Failed to create database session: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable. Please try again later."
        )
    
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()
