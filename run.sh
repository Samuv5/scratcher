#!/bin/bash
# SCRATCHER - Quick start
# Usage: ./run.sh

cd "$(dirname "$0")"

# Activate venv and start server
source venv/bin/activate
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

echo "Starting Scratcher at http://localhost:8000"
echo "Logs: server.log"
echo "Stop: Ctrl+C"

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
