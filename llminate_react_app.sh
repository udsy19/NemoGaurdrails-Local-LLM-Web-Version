#!/bin/bash

# LLMinate Dashboard Startup Script
# Starts the React dashboard application for LLMinate Security Analytics

echo "🚀 Starting LLMinate Dashboard..."
echo "======================================"

# Check if we're in the right directory
if [ ! -d "llminate" ]; then
    echo "❌ Error: llminate directory not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Navigate to the dashboard directory
cd llminate

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
# Check if remote backend is accessible
echo "🔍 Checking Django backend server status..."
if curl -s --connect-timeout 5 http://scanllmai.com/ >/dev/null 2>&1; then
    echo "✅ Django backend server is accessible at scanllmai.com"
else
    echo "⚠️  Cannot reach Django backend at scanllmai.com"
    echo "💡 Make sure your Django backend is running with Daphne"
    echo "Press Enter to continue anyway, or Ctrl+C to exit..."
    read
fi

echo "🌐 Starting LLMinate dashboard..."
echo "Dashboard will be available at: http://localhost:3000"
echo "Django WebSocket endpoint: ws://scanllmai.com/ws/guardrails/"
echo ""
echo "Available routes:"
echo "  • Main CISO Dashboard: http://localhost:3000/main"
echo "  • User Analytics: http://localhost:3000/users"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================"

# Start the React development server
npm start