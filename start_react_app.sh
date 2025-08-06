#!/bin/bash

echo "🌐 Starting AI Safety System - React Version with Enhanced ML"
echo "=============================================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found! Please install Node.js first."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"
echo "✅ Node.js found: $(node --version)"

# Install Python dependencies
echo "📦 Installing/checking Python dependencies..."
python3 -m pip install -r backend/requirements.txt --quiet

# Install Node.js dependencies
echo "📦 Installing/checking Node.js dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies (this may take a few minutes)..."
    npm install --legacy-peer-deps --silent
else
    echo "✅ Frontend dependencies already installed"
fi
cd ..

echo "🔥 Starting enhanced backend and React frontend..."
echo ""
echo "🌐 React frontend will be available at: http://localhost:3000"
echo "🔧 Backend API will be available at: http://localhost:8001"
echo "📊 KPMG Analytics system active with 5-minute exports"
echo "🤖 Enhanced ML detection enabled (6 guardrails)"
echo "🛡️ Multi-provider management enabled"
echo "🔒 Enterprise security features active"
echo ""
echo "💡 Press Ctrl+C to stop both services"
echo "=============================================================="

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Kill any existing processes on ports 8001 and 3000
echo "🔍 Checking for existing processes on ports 8001 and 3000..."
EXISTING_PID_8001=$(lsof -ti:8001 2>/dev/null || true)
if [ ! -z "$EXISTING_PID_8001" ]; then
    echo "🛑 Killing existing process $EXISTING_PID_8001 on port 8001..."
    kill $EXISTING_PID_8001 2>/dev/null || kill -9 $EXISTING_PID_8001 2>/dev/null || true
    sleep 2
fi

EXISTING_PID_3000=$(lsof -ti:3000 2>/dev/null || true)
if [ ! -z "$EXISTING_PID_3000" ]; then
    echo "🛑 Killing existing process $EXISTING_PID_3000 on port 3000..."
    kill $EXISTING_PID_3000 2>/dev/null || kill -9 $EXISTING_PID_3000 2>/dev/null || true
    sleep 2
fi

# Set environment variables for backend
export KPMG_DASHBOARD_ENDPOINT="https://kpmg-dashboard-api.com/api/v1/client-data/ingest"
export KPMG_CLIENT_ID="ai-safety-client-001"
export EXPORT_INTERVAL_MINUTES="5"

# Start backend in background with formatted logging
echo "🚀 Starting unified AI Safety System backend on port 8001..."
(cd backend && PYTHONPATH=. python3 -c "
import uvicorn
from app.main import app
uvicorn.run(app, host='0.0.0.0', port=8001, reload=False)
" 2>&1 | while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BACKEND] $line"; done > ../logs/backend.log) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
    # Test if backend is responding
    sleep 2
    if curl -s http://localhost:8001/health >/dev/null 2>&1; then
        echo "✅ Backend is responding on port 8001"
    else
        echo "⚠️  Backend started but not responding yet (may need more time to initialize)"
    fi
else
    echo "❌ Backend failed to start. Check logs/backend.log for details."
    echo "📋 Recent backend log:"
    tail -10 logs/backend.log 2>/dev/null || echo "No log file found"
    exit 1
fi

# Ensure frontend has correct backend URL
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > frontend/.env

# Start React frontend in background
echo "🌐 Starting React frontend on port 3000..."
(cd frontend && export BROWSER=none && npm start 2>&1 | while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] [FRONTEND] $line"; done > ../logs/frontend.log) &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✅ Frontend started successfully (PID: $FRONTEND_PID)"
    echo ""
    echo "🎉 Both services are running!"
    echo "🌐 Open http://localhost:3000 in your browser"
else
    echo "❌ Frontend failed to start. Check logs/frontend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Keep script running and wait for user to stop
echo ""
echo "📝 Logs are being written to:"
echo "   - Backend: logs/backend.log (formatted with timestamps)"
echo "   - Frontend: logs/frontend.log (formatted with timestamps)"
echo "   - All requests are tracked in backend logs"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for user interrupt
wait