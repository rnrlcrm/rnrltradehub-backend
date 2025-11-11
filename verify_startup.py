#!/usr/bin/env python3
"""
Startup Verification Script for RNRL TradeHub Backend.

This script verifies that the FastAPI application can be imported and configured correctly.
Use this to debug deployment issues.

Usage:
    python verify_startup.py
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_imports():
    """Verify all required modules can be imported."""
    logger.info("Verifying imports...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        import passlib
        import pydantic
        logger.info("✓ All required packages are installed")
        return True
    except ImportError as e:
        logger.error("✗ Import error: %s", e)
        return False


def verify_app():
    """Verify the FastAPI app can be imported and is configured correctly."""
    logger.info("Verifying FastAPI application...")
    try:
        from main import app
        logger.info("✓ App imported successfully")
        logger.info("  - App title: %s", app.title)
        logger.info("  - Framework: FastAPI")
        logger.info("  - Total routes: %d", len(app.routes))
        
        # Check for critical endpoints
        routes = [route.path for route in app.routes]
        critical_endpoints = ['/health', '/', '/docs']
        
        for endpoint in critical_endpoints:
            if endpoint in routes:
                logger.info("  ✓ %s endpoint found", endpoint)
            else:
                logger.warning("  ✗ %s endpoint not found", endpoint)
                
        return True
    except Exception as e:
        logger.error("✗ Failed to import app: %s", e)
        import traceback
        traceback.print_exc()
        return False


def verify_database_config():
    """Verify database configuration."""
    logger.info("Verifying database configuration...")
    try:
        from database import DATABASE_URL
        logger.info("✓ Database URL configured")
        # Don't log the actual URL as it may contain credentials
        if "postgresql" in DATABASE_URL:
            logger.info("  - Database type: PostgreSQL")
        elif "sqlite" in DATABASE_URL:
            logger.info("  - Database type: SQLite")
        else:
            logger.info("  - Database type: %s", DATABASE_URL.split(":")[0])
        return True
    except Exception as e:
        logger.error("✗ Database configuration error: %s", e)
        return False


def verify_environment():
    """Verify environment variables."""
    import os
    logger.info("Verifying environment...")
    
    port = os.environ.get("PORT", "8080")
    logger.info("  - PORT: %s", port)
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        logger.info("  ✓ DATABASE_URL is set")
    else:
        logger.warning("  ✗ DATABASE_URL not set (using default)")
    
    return True


def main():
    """Run all verification checks."""
    logger.info("="*60)
    logger.info("RNRL TradeHub Backend - Startup Verification")
    logger.info("="*60)
    
    checks = [
        ("Imports", verify_imports),
        ("Environment", verify_environment),
        ("Database Config", verify_database_config),
        ("FastAPI App", verify_app),
    ]
    
    results = []
    for name, check in checks:
        logger.info("")
        result = check()
        results.append((name, result))
    
    logger.info("")
    logger.info("="*60)
    logger.info("Verification Summary")
    logger.info("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info("%s: %s", name, status)
        if not result:
            all_passed = False
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("✓ All checks passed - Application is ready to start")
        logger.info("")
        logger.info("To start the server:")
        logger.info("  python main.py")
        logger.info("or")
        logger.info("  python -m uvicorn main:app --host 0.0.0.0 --port 8080")
        return 0
    else:
        logger.error("✗ Some checks failed - Please fix the issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
