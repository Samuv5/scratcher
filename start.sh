#!/bin/bash

# ============================================
# SCRATCHER - Startup Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
CLIENT_DIR="$PROJECT_DIR/client"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  SCRATCHER - CV Optimizer${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be available
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $name...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $name is ready${NC}"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e "${RED}✗ $name did not respond after $max_attempts seconds${NC}"
    return 1
}

# 1. Check/Create virtual environment
echo -e "${BLUE}[1/5] Setting up virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# 2. Install/Check Python dependencies
echo -e "${BLUE}[2/5] Checking Python dependencies...${NC}"
cd "$PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
fastapi>=0.100.0
uvicorn>=0.23.0
pdfminer.six>=20221101
requests>=2.28.0
beautifulsoup4>=4.11.0
python-multipart>=0.0.6
EOF
fi

pip install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}✓ Python dependencies ready${NC}"

# 3. Check LM Studio
echo -e "${BLUE}[3/5] Checking LM Studio...${NC}"
if check_port 1234; then
    echo -e "${GREEN}✓ LM Studio is running on port 1234${NC}"
else
    echo -e "${YELLOW}⚠ LM Studio not detected on port 1234${NC}"
    echo -e "${YELLOW}  Make sure LM Studio is running with the nvidia/nemotron-3-nano-4b model${NC}"
    echo -e "${YELLOW}  Press Enter to continue anyway...${NC}"
    read
fi

# 4. Rebuild frontend (optional)
echo -e "${BLUE}[4/5] Checking frontend...${NC}"
if [ "$1" == "--rebuild" ] || [ ! -d "$CLIENT_DIR/dist" ]; then
    echo -e "${YELLOW}Building frontend...${NC}"
    cd "$CLIENT_DIR"
    npm install --silent 2>/dev/null
    npm run build
    cd "$PROJECT_DIR"
    echo -e "${GREEN}✓ Frontend built${NC}"
else
    echo -e "${GREEN}✓ Frontend already built (use --rebuild to rebuild)${NC}"
fi

# 5. Start FastAPI server
echo -e "${BLUE}[5/5] Starting Scratcher server...${NC}"

# Kill previous process if exists
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Check if port 8000 is free
if check_port 8000; then
    echo -e "${YELLOW}Port 8000 in use, waiting...${NC}"
    pkill -f "uvicorn main:app" 2>/dev/null || true
    sleep 2
fi

cd "$PROJECT_DIR"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
sleep 2
if check_port 8000; then
    echo -e "${GREEN}✓ Server started successfully${NC}"
else
    echo -e "${RED}✗ Error starting server${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  SCRATCHER is ready!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "  ${BLUE}URL: http://localhost:8000${NC}"
echo -e "  ${BLUE}Logs: tail -f server.log${NC}"
echo -e "  ${BLUE}Stop: pkill -f 'uvicorn main:app'${NC}"
echo ""
echo -e "  Model: ${YELLOW}nvidia/nemotron-3-nano-4b${NC}"
echo -e "  Timeout: ${YELLOW}300s${NC}"
echo ""

# Open browser (optional)
if command -v xdg-open > /dev/null 2>&1; then
    xdg-open http://localhost:8000 2>/dev/null &
elif command -v open > /dev/null 2>&1; then
    open http://localhost:8000 2>/dev/null &
fi

# Keep the script running
echo -e "${GREEN}Press Ctrl+C to stop the server${NC}"
wait $SERVER_PID
