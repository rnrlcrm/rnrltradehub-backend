#!/bin/bash
# Quick Deployment Script for RNRL TradeHub Backend
# This script helps deploy to the correct Cloud Run service

set -e

echo "============================================================"
echo "RNRL TradeHub Backend - Deployment Script"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}✗ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ gcloud CLI found${NC}"

# Run verification
echo ""
echo "Running pre-deployment verification..."
if python verify_startup.py > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Startup verification passed${NC}"
else
    echo -e "${RED}✗ Startup verification failed${NC}"
    echo "Run 'python verify_startup.py' for details"
    exit 1
fi

# Ask which service to deploy to
echo ""
echo "Which service would you like to deploy to?"
echo ""
echo "1) erp-nonprod-backend (Fixes the 404 issue, recommended)"
echo "2) rnrltradehub-nonprod (Alternative service)"
echo ""
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        SERVICE_NAME="erp-nonprod-backend"
        CONFIG_FILE="cloudbuild.yaml"
        ;;
    2)
        SERVICE_NAME="rnrltradehub-nonprod"
        CONFIG_FILE="cloudbuild-rnrltradehub.yaml"
        ;;
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Deploying to: $SERVICE_NAME${NC}"
echo -e "${YELLOW}Using config: $CONFIG_FILE${NC}"
echo ""

# Confirm deployment
read -p "Continue with deployment? [y/N]: " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "Starting deployment..."
echo "============================================================"

# Deploy using Cloud Build
if gcloud builds submit --config=$CONFIG_FILE; then
    echo ""
    echo "============================================================"
    echo -e "${GREEN}✓ Deployment successful!${NC}"
    echo "============================================================"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=us-central1 \
        --format='value(status.url)' 2>/dev/null || echo "")
    
    if [ -n "$SERVICE_URL" ]; then
        echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
        echo ""
        echo "Testing endpoints..."
        echo ""
        
        # Test health endpoint
        echo "1. Testing /health..."
        if curl -s -f "$SERVICE_URL/health" > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓ /health is responding${NC}"
            curl -s "$SERVICE_URL/health" | python -m json.tool 2>/dev/null || echo ""
        else
            echo -e "   ${RED}✗ /health is not responding${NC}"
        fi
        
        echo ""
        echo "2. Testing / ..."
        if curl -s -f "$SERVICE_URL/" > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓ / is responding${NC}"
        else
            echo -e "   ${RED}✗ / is not responding${NC}"
        fi
        
        echo ""
        echo "3. Testing /docs..."
        if curl -s -I "$SERVICE_URL/docs" | grep -q "200 OK"; then
            echo -e "   ${GREEN}✓ /docs is accessible${NC}"
            echo -e "   Visit: ${GREEN}$SERVICE_URL/docs${NC}"
        else
            echo -e "   ${RED}✗ /docs is not accessible${NC}"
        fi
        
        echo ""
        echo "============================================================"
        echo "Next Steps:"
        echo "============================================================"
        echo "1. Update frontend API_BASE_URL to: $SERVICE_URL"
        echo "2. Test critical API endpoints"
        echo "3. Monitor logs: gcloud run services logs read $SERVICE_NAME --region=us-central1"
        echo ""
    fi
else
    echo ""
    echo "============================================================"
    echo -e "${RED}✗ Deployment failed${NC}"
    echo "============================================================"
    echo ""
    echo "Check the error messages above and try again."
    echo "For troubleshooting, see: DEPLOYMENT_TROUBLESHOOTING.md"
    exit 1
fi
