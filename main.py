"""
RNRL TradeHub Backend API - Non-Production Environment.

This module provides a FastAPI-based backend service for the RNRL TradeHub
non-production environment. It includes CORS middleware configuration,
database connectivity, and API endpoints.

Security Note:
- CORS is configured with wildcard origins for non-prod testing.
  In production, restrict to specific domains.
- Host binding to 0.0.0.0 is required for containerized deployments.
"""
import os
import logging
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_db, engine, Base
from schemas import HealthCheckResponse
from routes_complete import (
    business_partner_router,
    sales_contract_router,
    cci_term_router,
    user_router,
    invoice_router,
    payment_router,
    dispute_router,
    commission_router,
    role_router,
    setting_router,
    master_data_router,
    gst_rate_router,
    location_router,
    commission_structure_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
logger.info("Creating database tables...")
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning("Could not create database tables: %s", str(e))

app = FastAPI(
    title="RNRL TradeHub NonProd API",
    description="Backend API for RNRL TradeHub CRM system",
    version="1.0.0"
)

# CORS configuration - using wildcard for non-prod environment
# TODO: In production, replace with specific allowed origins
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers for all entities
app.include_router(business_partner_router)
app.include_router(sales_contract_router)
app.include_router(cci_term_router)
app.include_router(user_router)
app.include_router(invoice_router)
app.include_router(payment_router)
app.include_router(dispute_router)
app.include_router(commission_router)
app.include_router(role_router)
app.include_router(setting_router)
app.include_router(master_data_router)
app.include_router(gst_rate_router)
app.include_router(location_router)
app.include_router(commission_structure_router)


@app.get("/")
async def root():
    """
    Root endpoint providing API status.

    Returns:
        dict: A message indicating the API is running.
    """
    return {"message": "RNRL TradeHub NonProd API is running!"}


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and orchestration.

    This endpoint is used by Cloud Run and other services to verify
    that the application is running and responsive. It also checks
    database connectivity.

    Args:
        db: Database session dependency.

    Returns:
        dict: Health status information including database status.
    """
    # Check database connectivity
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))

    return {
        "status": "healthy",
        "service": "rnrltradehub-nonprod",
        "version": "1.0.0",
        "database": db_status
    }


if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8080))
        logger.info("Starting RNRL TradeHub API on port %d", port)
        # Host 0.0.0.0 is required for Cloud Run containerized deployment
        uvicorn.run(app, host="0.0.0.0", port=port)  # nosec B104
    except Exception as e:
        logger.error("Failed to start server: %s", str(e))
        raise
