# AI Safety System with KPMG Analytics Integration

A comprehensive AI safety system with multi-provider LLM support, real-time guardrails, and enterprise analytics for KPMG dashboard integration.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- 8GB+ RAM recommended

### Installation & Setup
```bash
# Clone and setup
git clone <repository>
cd NemoGaurdrails-Local-LLM-Web-Version

# Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Return to project root
cd ..
```

### Start the System
```bash
# Single command to start both frontend and backend
./start_react_app.sh
```

Access the application at: **http://localhost:3000**

## 🎯 Core Features

### AI Safety & Guardrails
- **6 ML-based Detectors**: Toxicity, PII, Prompt Injection, Hate Speech, Bias, Privacy
- **Real-time Protection**: All AI responses filtered through safety guardrails
- **Configurable Thresholds**: Customizable sensitivity for each detector
- **Multi-stage Pipeline**: Advanced detection with confidence scoring

### Multi-Provider Support
- **OpenAI**: GPT-4, GPT-3.5-turbo with advanced reasoning
- **Anthropic**: Claude 3 models (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro and Vision models
- **Ollama**: Local models (Llama 2, Code Llama, Mistral, etc.)
- **Azure OpenAI**: Enterprise-grade OpenAI integration

### KPMG Analytics Integration
- **Real-time Data Collection**: Comprehensive user interaction tracking
- **Privacy Protection**: SHA-256 content hashing for data protection
- **5-minute Exports**: Automated JSON exports for KPMG dashboard
- **Multi-timeframe Analysis**: 1h, 6h, 12h, 24h, 3d, 1w analytics
- **SQLite Database**: Enterprise-grade local data storage

## 🔧 Configuration

### Provider Setup
1. Navigate to **Providers** tab in the web interface
2. Enable desired providers and add API keys:
   - **OpenAI**: Get key from https://platform.openai.com/api-keys
   - **Anthropic**: Get key from https://console.anthropic.com
   - **Google**: Get key from https://ai.google.dev
   - **Ollama**: No API key needed (local models)

### Environment Variables
Create `backend/.env` file:
```bash
# Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

# KPMG Integration
KPMG_DASHBOARD_ENDPOINT=https://your-kpmg-endpoint.com/api/v1/ingest
KPMG_CLIENT_ID=your-client-id
KPMG_JWT_TOKEN=your-jwt-token
```

## 📊 System Architecture

### Backend (FastAPI - Port 8001)
- **API Server**: RESTful API with automatic documentation
- **ML Pipeline**: Real-time AI safety detection
- **Analytics Engine**: SQLite-based data collection
- **Export Scheduler**: Automated KPMG data transmission

### Frontend (React - Port 3000)
- **Provider Management**: Configure and test AI providers
- **Guardrails Control**: Adjust safety thresholds
- **Analytics Dashboard**: Real-time system insights
- **Testing Playground**: Safe AI interaction testing

### Key Endpoints
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Analytics**: http://localhost:8001/api/analytics/health

## 🛡️ Security Features

### Data Protection
- **Content Hashing**: All prompts/responses hashed with SHA-256
- **Local Storage**: User data stays on local SQLite database
- **Configurable Retention**: Auto-cleanup after 7 days (configurable)
- **Audit Trail**: All exports and access logged

### Network Security
- **HTTPS Transmission**: Encrypted data to KPMG
- **JWT Authentication**: Secure API access
- **HMAC Signatures**: Data integrity verification
- **Rate Limiting**: Protection against abuse

## 🔍 Testing

### Quick Health Check
```bash
# Test backend
curl http://localhost:8001/health

# Test providers
curl http://localhost:8001/api/providers/

# Test analytics
curl http://localhost:8001/api/analytics/health
```

### Integration Testing
```bash
cd backend
python test_endpoints.py
python test_providers.py
python test_functionality.py
```

## 📈 Monitoring

### Analytics Dashboard
- **Real-time Stats**: Request counts, block rates, performance metrics
- **Guardrail Performance**: Effectiveness and confidence scores
- **Provider Health**: Connection status and response times
- **User Activity**: IP-based usage patterns (privacy-protected)

### System Health
- **Component Status**: All services monitored
- **Performance Metrics**: Response times, memory usage
- **Error Tracking**: Comprehensive error logging
- **Self-healing**: Automatic recovery mechanisms

## 🚨 Troubleshooting

### Common Issues

**"Failed to fetch" errors**
- Ensure backend is running on port 8001
- Check `frontend/.env` has `REACT_APP_BACKEND_URL=http://localhost:8001`
- Restart both frontend and backend

**Provider connection failures**
- Verify API keys are correct and active
- Check internet connectivity
- Test individual providers in the UI

**Analytics not working**
- Check analytics health: `curl http://localhost:8001/api/analytics/health`
- Verify SQLite database: `ls -la backend/user_data/`
- Review logs: `tail -f backend/logs/backend.log`

### Port Conflicts
If port conflicts occur:
```bash
# Backend on different port
cd backend
python3 -c "
import uvicorn
from app.main import app
uvicorn.run(app, host='0.0.0.0', port=8002)
"

# Update frontend config
echo "REACT_APP_BACKEND_URL=http://localhost:8002" > frontend/.env
```

## 📚 API Documentation

### Provider Management
- `GET /api/providers/` - List all providers
- `PUT /api/providers/{id}/config` - Update provider configuration
- `POST /api/providers/{id}/test-connection` - Test provider connection

### Analytics
- `GET /api/analytics/stats` - Real-time statistics
- `GET /api/analytics/export/dashboard` - Full dashboard export
- `GET /api/analytics/export/scheduler/status` - Export scheduler status

### Safety Detection
- `POST /api/chat/completions` - Process message with safety checks
- `GET /api/detectors/` - List available safety detectors
- `PUT /api/detectors/config` - Update detector configuration

## 🏢 Enterprise Features

### KPMG Integration
- **Automated Exports**: JSON data every 5 minutes
- **Comprehensive Analytics**: User activity, guardrail performance, provider metrics
- **Privacy Compliance**: Only aggregated, hashed data transmitted
- **Offline Queuing**: Reliable transmission with retry mechanism

### Scalability
- **Multi-tenant Support**: Isolated environments for different clients
- **Distributed Processing**: Horizontal scaling capabilities
- **Load Balancing**: Intelligent request distribution
- **Performance Monitoring**: Real-time system optimization

## 📞 Support

### Logs Location
- **Backend**: `backend/logs/backend.log`
- **Frontend**: Browser console
- **Analytics**: `backend/user_data/exports/`

### Health Endpoints
- **System**: http://localhost:8001/health
- **Analytics**: http://localhost:8001/api/analytics/health
- **Providers**: http://localhost:8001/api/providers/stats/summary

---

**For technical implementation details, see TECHNICAL_README.md**