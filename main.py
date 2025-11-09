"""
RNRL TradeHub Backend API - Non-Production Environment.

This module provides a FastAPI-based backend service for the RNRL TradeHub
non-production environment. It includes CORS middleware configuration and
basic health check endpoints.

Security Note:
- CORS is configured with wildcard origins for non-prod testing.
  In production, restrict to specific domains.
- Host binding to 0.0.0.0 is required for containerized deployments.
"""
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="RNRL TradeHub NonProd API")

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


@app.get("/")
async def root():
    """
    Root endpoint providing API status.

    Returns:
        dict: A message indicating the API is running.
    """
    return {"message": "RNRL TradeHub NonProd API is running!"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and orchestration.

    This endpoint is used by Cloud Run and other services to verify
    that the application is running and responsive.

    Returns:
        dict: Health status information.
    """
    return {
        "status": "healthy",
        "service": "rnrltradehub-nonprod",
        "version": "1.0.0"
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
