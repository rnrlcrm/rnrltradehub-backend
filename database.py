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

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/rnrltradehub"
)

# Log database configuration (without credentials)
if "postgresql" in DATABASE_URL:
    logger.info("Database: PostgreSQL")
elif "sqlite" in DATABASE_URL:
    logger.info("Database: SQLite")
else:
    logger.info("Database: %s", DATABASE_URL.split(":")[0])

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
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: %s", str(e))
        db.rollback()
        raise
    finally:
        db.close()
