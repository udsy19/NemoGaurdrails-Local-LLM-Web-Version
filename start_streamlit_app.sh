#!/bin/bash

echo "🎮 Starting AI Safety System - Streamlit Version with Enhanced ML"
echo "=================================================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Install dependencies
echo "📦 Installing/checking dependencies..."
python3 -m pip install -r backend/requirements.txt --quiet
python3 -m pip install streamlit plotly psutil py-cpuinfo --quiet

echo "🔥 Starting enhanced backend and Streamlit interface..."
echo ""
echo "🌐 Streamlit will be available at: http://localhost:8501"
echo "🔧 Backend API will be available at: http://localhost:8000"
echo "📊 Analytics tracking enabled"
echo "🤖 Enhanced ML detection enabled"
echo "🛡️ Provider management enabled"
echo ""
echo "💡 Press Ctrl+C to stop both services"
echo "=================================================================="

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Kill any existing process on port 8000
echo "🔍 Checking for existing processes on port 8000..."
EXISTING_PID=$(lsof -ti:8000)
if [ ! -z "$EXISTING_PID" ]; then
    echo "🛑 Killing existing process $EXISTING_PID on port 8000..."
    kill -9 $EXISTING_PID 2>/dev/null
    sleep 2
fi

# Start backend in background with formatted logging
echo "🚀 Starting unified AI Safety System backend on port 8000..."
(cd backend && PYTHONPATH=. python3 app/main.py 2>&1 | while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BACKEND] $line"; done > ../logs/backend.log) &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
    # Test if backend is responding
    sleep 2
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        echo "✅ Backend is responding on port 8000"
    else
        echo "⚠️  Backend started but not responding yet (may need more time to initialize)"
    fi
else
    echo "❌ Backend failed to start. Check logs/backend.log for details."
    echo "📋 Recent backend log:"
    tail -10 logs/backend.log 2>/dev/null || echo "No log file found"
    exit 1
fi

# Start Streamlit with formatted logging (this will run in foreground)
echo "🎮 Starting Streamlit interface on port 8501..."
echo "📝 Streamlit logs are being written to: logs/streamlit.log"
echo "📝 Backend logs are being written to: logs/backend.log (formatted with timestamps)"
echo "📝 All requests are tracked in backend logs"
echo ""
(cd backend && streamlit run app/streamlit_app.py --server.port 8501 --server.address localhost --browser.gatherUsageStats false 2>&1 | while IFS= read -r line; do echo "[$(date '+%Y-%m-%d %H:%M:%S')] [STREAMLIT] $line"; done | tee ../logs/streamlit.log)