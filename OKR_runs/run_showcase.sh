#!/bin/bash
# Run Showcase Scripts for OKR Delivery Demonstration
# This script runs both showcase scripts to demonstrate delivery completion

set -e

echo "=========================================="
echo "OKR Delivery Showcase Runner"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENAI_API_KEY is not set${NC}"
    echo "Some tests may fail without an API key."
    echo ""
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Showcase 1: Foundational SDKs (Python SDK)${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

python3 showcase_foundational_sdk.py
SDK_RESULT=$?

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Showcase 2: AI Gateway Service${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

python3 showcase_gateway_service.py
GATEWAY_RESULT=$?

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Final Summary${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

if [ $SDK_RESULT -eq 0 ] && [ $GATEWAY_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL OKRs COMPLETE!${NC}"
    echo ""
    echo "✅ Foundational SDKs (Python SDK) Delivery: PASSED"
    echo "✅ Platform Component: AI Gateway Service Delivery: PASSED"
    echo ""
    echo "Both deliverables are working and ready for demonstration."
    exit 0
else
    echo -e "${YELLOW}⚠️  Some showcases failed${NC}"
    echo ""
    if [ $SDK_RESULT -ne 0 ]; then
        echo "❌ Foundational SDKs (Python SDK) Delivery: FAILED"
    else
        echo "✅ Foundational SDKs (Python SDK) Delivery: PASSED"
    fi
    
    if [ $GATEWAY_RESULT -ne 0 ]; then
        echo "❌ Platform Component: AI Gateway Service Delivery: FAILED"
    else
        echo "✅ Platform Component: AI Gateway Service Delivery: PASSED"
    fi
    exit 1
fi

