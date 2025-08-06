# COMPREHENSIVE REBUILD DOCUMENTATION: KPMG NemoGuardrails AI Safety System

## Table of Contents
1. [Application Architecture Overview](#application-architecture-overview)
2. [Backend Services & APIs](#backend-services--apis)
3. [Frontend Components & State Management](#frontend-components--state-management)
4. [Database Schemas & Data Models](#database-schemas--data-models)
5. [Configuration Files & Environment Setup](#configuration-files--environment-setup)
6. [Build Processes & Deployment](#build-processes--deployment)
7. [Dependencies & Versions](#dependencies--versions)
8. [Integration Patterns](#integration-patterns)
9. [State Management & Local Storage](#state-management--local-storage)
10. [API Endpoints & Request/Response Formats](#api-endpoints--requestresponse-formats)
11. [Real-time Features & WebSocket Implementation](#real-time-features--websocket-implementation)
12. [Security & Guardrails Logic](#security--guardrails-logic)
13. [Analytics & Monitoring Systems](#analytics--monitoring-systems)
14. [Provider Integrations](#provider-integrations)
15. [Testing Frameworks](#testing-frameworks)
16. [Known Issues & Bugs](#known-issues--bugs)

---

## 1. Application Architecture Overview

### System Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    KPMG AI SAFETY SYSTEM                        │
│                                                                 │
│ ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐ │
│ │   React Frontend │    │  FastAPI Backend │    │   SQLite DB   │ │
│ │   (Port 3000)    │◄──►│   (Port 8001)    │◄──►│   Analytics   │ │
│ │                 │    │                 │    │               │ │
│ │ • Modern UI     │    │ • 6 ML Detectors│    │ • Request     │ │
│ │ • Provider Mgmt │    │ • Guardrails    │    │   Tracking    │ │
│ │ • Real-time Logs│    │ • Analytics     │    │ • KPMG Export │ │
│ │ • Testing Suite │    │ • Provider APIs │    │ • Privacy     │ │
│ └─────────────────┘    └─────────────────┘    │   Protection  │ │
│                                               └───────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                  EXTERNAL INTEGRATIONS                      │ │
│ │                                                             │ │
│ │ OpenAI ◄─┐  Anthropic ◄─┐  Google ◄─┐  Ollama ◄─┐         │ │
│ │ GPT-4     │  Claude       │  Gemini   │  Local     │         │ │
│ │ GPT-3.5   │  Opus/Sonnet  │  Pro      │  Llama     │         │ │
│ └───────────┴───────────────┴───────────┴────────────┘         │ │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components
1. **Frontend (React + TypeScript)**
   - Modern chat interface with real-time updates
   - Provider configuration and management
   - Guardrails configuration dashboard
   - Analytics and monitoring views
   - Advanced testing playground
   - GPU acceleration controls
   - Documentation system

2. **Backend (FastAPI + Python 3.13)**
   - Multi-stage ML detection pipeline
   - Provider management system
   - Analytics collection service
   - Real-time health monitoring
   - Self-healing mechanisms
   - Circuit breaker patterns
   - Performance optimization

3. **Database (SQLite)**
   - User request tracking with privacy protection (SHA-256 hashing)
   - KPMG analytics export system
   - Performance metrics storage
   - Export audit trails

4. **ML Detection System**
   - 6 ML-based safety detectors
   - Enterprise-mode permanent model loading
   - CPU-optimized inference
   - Configurable thresholds
   - Real-time processing

---

## 2. Backend Services & APIs

### Main Application (`/backend/app/main.py`)

**Key Features:**
- **Lifespan Management**: Comprehensive startup/shutdown with resource management
- **Health Monitoring**: Multi-component health checks with diagnostics
- **Request Logging**: Enhanced logging with categorization and performance tracking
- **Real-time Logs**: In-memory log storage for frontend consumption
- **WebSocket Support**: Chat interface with WebSocket endpoint
- **Error Handling**: Global exception handlers with correlation IDs

**Critical Implementation Details:**
```python
# Global instances (EXACTLY as implemented)
model_manager: ModelManager = None
detection_service: DetectionService = None
chat_service: ChatService = None
config_service: ConfigService = None

# System logs storage for real-time monitoring
system_logs = []

def add_system_log(level: str, source: str, message: str):
    """Add a log entry to system logs for real-time monitoring"""
    log_entry = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "level": level,
        "source": source,
        "message": message
    }
    system_logs.append(log_entry)
    # Keep only last 100 logs
    if len(system_logs) > 100:
        system_logs.pop(0)
```

**Port Configuration:**
- **Backend Port**: 8001 (configurable via uvicorn.run)
- **CORS Origins**: `["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000", "http://127.0.0.1:3000"]`

### Chat Service (`/backend/app/services/chat_service.py`)

**Functionality:**
- Message processing through safety pipeline
- Session management with detector configurations
- Chat history storage and retrieval
- Provider integration (with fallback to Ollama)
- Real-time analytics tracking

**Critical Methods:**
```python
async def process_message(
    self,
    message: str,
    detector_config: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    provider_id: Optional[str] = None
) -> Dict[str, Any]
```

**Session Management:**
- In-memory session storage: `self.chat_history = {}`
- Session-specific detector configs: `self.session_configs = {}`
- Unique session IDs generated with UUID

### Model Manager (`/backend/app/models/model_manager.py`)

**Enterprise Mode Features:**
- **Permanent Model Loading**: All detectors loaded at startup and kept in memory
- **CPU Optimization**: Models moved to CPU with evaluation mode
- **Concurrent Processing**: Semaphore-limited concurrent detections (max 6)
- **Performance Monitoring**: Request tracking and timeout handling (30-second SLA)

**Available Detectors:**
```python
self.available_detectors = {
    'toxicity': ToxicityDetector,
    'pii': PIIDetector,
    'prompt_injection': PromptInjectionDetector,
    'topic': TopicDetector,
    'fact_check': FactCheckDetector,
    'spam': SpamDetector
}
```

**Default Thresholds (Adjusted for Usability):**
```python
self.detector_configs = {
    'toxicity': {'threshold': 0.85},      # Increased from 0.7
    'pii': {'sensitivity': 0.6},          # Reduced from 0.8
    'prompt_injection': {'threshold': 0.7}, # Increased from 0.5
    'topic': {'threshold': 0.85},         # Increased from 0.7
    'fact_check': {'threshold': 0.6},     # Increased from 0.5
    'spam': {'threshold': 0.75}           # Increased from 0.6
}
```

### Analytics Service (`/backend/app/services/analytics_service.py`)

**Database Schema:**
```sql
CREATE TABLE IF NOT EXISTS user_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_ip TEXT NOT NULL,
    request_id TEXT UNIQUE NOT NULL,
    prompt_hash TEXT NOT NULL,
    response_hash TEXT,
    status TEXT NOT NULL,
    blocked_by TEXT,
    
    -- 6 Guardrail Scores and Confidences
    toxicity_score REAL DEFAULT 0.0,
    toxicity_confidence REAL DEFAULT 0.0,
    pii_detected BOOLEAN DEFAULT FALSE,
    pii_confidence REAL DEFAULT 0.0,
    prompt_injection_score REAL DEFAULT 0.0,
    prompt_injection_confidence REAL DEFAULT 0.0,
    hate_speech_score REAL DEFAULT 0.0,
    hate_speech_confidence REAL DEFAULT 0.0,
    bias_score REAL DEFAULT 0.0,
    bias_confidence REAL DEFAULT 0.0,
    privacy_score REAL DEFAULT 0.0,
    privacy_confidence REAL DEFAULT 0.0,
    
    -- Performance Metrics
    response_time_ms INTEGER DEFAULT 0,
    provider_used TEXT,
    model_used TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    session_id TEXT
)
```

**Privacy Protection:**
- All prompts and responses are SHA-256 hashed before storage
- User IPs tracked for analytics but content is anonymized
- 7-day retention policy (configurable)

**KPMG Export System:**
- **Export Interval**: Every 5 minutes
- **Export Format**: JSON with comprehensive analytics
- **Timeframes**: 1h, 6h, 12h, 24h, 3d, 1w analysis
- **Export Location**: `/backend/user_data/exports/`

### Provider Service (`/backend/app/services/provider_service.py`)

**Supported Providers:**
1. **OpenAI** (Port 8002)
   - Models: GPT-4, GPT-3.5-turbo
   - API Key required
   - Connection testing with LLM generation

2. **Anthropic** (Port 8003)
   - Models: Claude 3 Opus, Sonnet, Haiku
   - API Key required

3. **Google** (Port 8004)
   - Models: Gemini Pro, Gemini Vision
   - API Key required

4. **Ollama** (Port 11434)
   - Local models: Llama 2, Code Llama, Mistral
   - No API key required
   - Direct integration

5. **Azure OpenAI** (Port 8005)
   - Enterprise OpenAI integration
   - Endpoint, API version, deployment name configuration

**Port Conflict Management:**
- Automatic port availability checking
- Force port option for conflict resolution
- Next available port selection

---

## 3. Frontend Components & State Management

### Main Application (`/frontend/src/App.tsx`)

**State Management:**
```typescript
// Core state
const [message, setMessage] = useState('');
const [activeTab, setActiveTab] = useState<'chat' | 'models' | 'terminal' | 'guardrails' | 'providers' | 'analytics' | 'testing' | 'hardware' | 'docs'>(loadActiveTab);
const [selectedProvider, setSelectedProvider] = useState<string>(loadSelectedProvider);

// localStorage Integration
const loadActiveTab = () => {
  try {
    const saved = localStorage.getItem('app_active_tab');
    if (saved && ['chat', 'models', 'terminal', 'guardrails', 'providers', 'analytics', 'testing', 'hardware', 'docs'].includes(saved)) {
      return saved;
    }
  } catch (error) {
    console.error('Failed to load active tab from localStorage:', error);
  }
  return 'chat';
};
```

**Key Features:**
- Tab persistence in localStorage
- Provider selection with validation
- Auto-scroll chat with multiple fallback strategies
- Real-time log streaming
- Model management (download, delete, search)
- System status monitoring

### Chat Interface (`/frontend/src/components/chat/ModernChatInterface.tsx`)

**Props Interface:**
```typescript
interface ModernChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, provider: string, detectorConfig: DetectorConfig) => void;
  isLoading: boolean;
  disabled: boolean;
  detectorConfig: DetectorConfig;
  onDetectorConfigChange: (config: DetectorConfig) => void;
  onClearHistory: () => void;
  availableProviders: Provider[];
  selectedProvider: string;
  onProviderChange: (providerId: string) => void;
  onNavigateToProviders: () => void;
  onNavigateToGuardrails: () => void;
}
```

### API Service (`/frontend/src/services/api.ts`)

**Core Configuration:**
```typescript
constructor(baseURL: string = 'http://localhost:8000') {  // BUG: Should be 8001
  this.baseURL = baseURL;
  this.client = axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
```

**Key Methods:**
- `sendMessage()`: Chat message processing with 60-second timeout
- `getDetectors()`: Detector status and configuration
- `getHealth()`: System health monitoring
- `getChatHistory()`: Session history retrieval
- Provider management APIs
- Testing and diagnostics APIs

### Custom Hooks

**useApi Hook (`/frontend/src/hooks/useApi.ts`):**
```typescript
export const useApi = () => {
  const [isConnected, setIsConnected] = useState(false);
  // Connection monitoring with periodic health checks
}

export const useSystemHealth = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  // Real-time health status updates
}

export const useDetectors = () => {
  const [detectors, setDetectors] = useState<DetectorInfo[]>([]);
  // Detector management and configuration
}
```

---

## 4. Database Schemas & Data Models

### SQLite Database Location
**Path**: `/backend/user_data/ai_safety_analytics.db`

### User Analytics Table
```sql
CREATE TABLE IF NOT EXISTS user_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_ip TEXT NOT NULL,
    request_id TEXT UNIQUE NOT NULL,
    prompt_hash TEXT NOT NULL,
    response_hash TEXT,
    status TEXT NOT NULL,
    blocked_by TEXT,
    
    -- 6 Guardrail Scores and Confidences
    toxicity_score REAL DEFAULT 0.0,
    toxicity_confidence REAL DEFAULT 0.0,
    pii_detected BOOLEAN DEFAULT FALSE,
    pii_confidence REAL DEFAULT 0.0,
    prompt_injection_score REAL DEFAULT 0.0,
    prompt_injection_confidence REAL DEFAULT 0.0,
    hate_speech_score REAL DEFAULT 0.0,
    hate_speech_confidence REAL DEFAULT 0.0,
    bias_score REAL DEFAULT 0.0,
    bias_confidence REAL DEFAULT 0.0,
    privacy_score REAL DEFAULT 0.0,
    privacy_confidence REAL DEFAULT 0.0,
    
    -- Performance Metrics
    response_time_ms INTEGER DEFAULT 0,
    provider_used TEXT,
    model_used TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    session_id TEXT
)
```

### Export Log Table
```sql
CREATE TABLE IF NOT EXISTS export_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_timestamp TEXT NOT NULL,
    export_type TEXT NOT NULL,
    timeframe_hours INTEGER,
    records_count INTEGER,
    file_path TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
)
```

### Database Optimization
```sql
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_timestamp ON user_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_ip ON user_analytics(user_ip);
CREATE INDEX IF NOT EXISTS idx_status ON user_analytics(status);
CREATE INDEX IF NOT EXISTS idx_provider ON user_analytics(provider_used);
CREATE INDEX IF NOT EXISTS idx_session ON user_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_blocked_by ON user_analytics(blocked_by);

-- WAL mode for better concurrent performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

### Data Models (Python)
```python
@dataclass
class UserAnalyticsEntry:
    timestamp: str
    user_ip: str
    request_id: str
    prompt_hash: str
    response_hash: Optional[str]
    status: str  # 'allowed', 'blocked', 'error'
    blocked_by: Optional[str]
    
    # Guardrail Scores
    toxicity_score: float = 0.0
    toxicity_confidence: float = 0.0
    pii_detected: bool = False
    pii_confidence: float = 0.0
    # ... (6 total guardrail types)
    
    # Performance Metrics
    response_time_ms: int = 0
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    session_id: Optional[str] = None
```

---

## 5. Configuration Files & Environment Setup

### Backend Configuration (`/backend/configs/app_config.yml`)
```yaml
app:
  debug: false
  graceful_degradation_enabled: true
  health_monitoring_enabled: true
  name: AI Safety System
  resilience_enabled: true
  version: 2.0.0

detectors:
  toxicity:
    enabled: true
    model: martin-ha/toxic-comment-model
    threshold: 0.85  # Increased to reduce false positives
  pii:
    enabled: false
    model: en_core_web_sm
    sensitivity: 0.6  # Reduced to be less aggressive
  prompt_injection:
    enabled: false
    threshold: 0.5
  # ... other detectors

models:
  ollama:
    base_url: http://localhost:11434
    default_model: llama3.1:8b
    timeout: 120

api:
  cors_origins:
  - http://localhost:8501
  - http://127.0.0.1:8501
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

### Frontend Environment (`.env`)
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Backend Environment Variables
```bash
# Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

# KPMG Integration
KPMG_DASHBOARD_ENDPOINT=https://your-kpmg-endpoint.com/api/v1/ingest
KPMG_CLIENT_ID=your-client-id
KPMG_JWT_TOKEN=your-jwt-token
EXPORT_INTERVAL_MINUTES=5
```

---

## 6. Build Processes & Deployment

### Startup Script (`/start_react_app.sh`)
```bash
#!/bin/bash

echo "🌐 Starting AI Safety System - React Version with Enhanced ML"

# Dependency checking
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found!"
    exit 1
fi

# Install dependencies
python3 -m pip install -r backend/requirements.txt --quiet
cd frontend && npm install --legacy-peer-deps --silent && cd ..

# Port cleanup
EXISTING_PID_8001=$(lsof -ti:8001 2>/dev/null || true)
if [ ! -z "$EXISTING_PID_8001" ]; then
    kill $EXISTING_PID_8001 2>/dev/null
fi

# Start backend
(cd backend && PYTHONPATH=. python3 -c "
import uvicorn
from app.main import app
uvicorn.run(app, host='0.0.0.0', port=8001, reload=False)
") &
BACKEND_PID=$!

# Start frontend
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > frontend/.env
(cd frontend && export BROWSER=none && npm start) &
FRONTEND_PID=$!
```

### Backend Startup Process
1. **Dependency Loading**: Model manager initialization with all 6 detectors
2. **Service Initialization**: Chat service, detection service, config service
3. **Analytics Setup**: SQLite database initialization and export scheduler
4. **Health Monitoring**: Component health checkers registration
5. **Provider Services**: Multi-provider system initialization
6. **Performance Systems**: Self-healing and monitoring activation

### Frontend Build Process
1. **Dependencies**: React 19.1.0, TypeScript, Material-UI
2. **Development Server**: Port 3000 with hot reload
3. **Build Output**: Static files for production deployment
4. **Environment Configuration**: Backend URL injection

---

## 7. Dependencies & Versions

### Backend Dependencies (`/backend/requirements.txt`)
```
# Core FastAPI and server
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
websockets>=12.0
pydantic[email]>=2.5.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
pyyaml>=6.0.1
requests>=2.31.0
httpx>=0.25.2
aiohttp>=3.9.0
aiofiles>=23.2.0

# Data processing (Python 3.13 compatible)
numpy>=1.26.0
pandas>=2.1.0
scikit-learn>=1.3.0
scipy>=1.11.0

# AI/ML Dependencies
torch>=2.1.0
transformers>=4.35.0
sentence-transformers>=2.2.0
spacy>=3.7.0
tokenizers>=0.15.0
huggingface-hub>=0.19.0
safetensors>=0.4.0
datasets>=2.14.0

# Logging and monitoring
loguru>=0.7.0
prometheus-client>=0.19.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
```

### Frontend Dependencies (`/frontend/package.json`)
```json
{
  "dependencies": {
    "@emotion/react": "^11.14.0",
    "@emotion/styled": "^11.14.1",
    "@mui/icons-material": "^7.2.0",
    "@mui/material": "^7.2.0",
    "@testing-library/dom": "^10.4.0",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.126",
    "@types/react": "^19.1.8",
    "@types/react-dom": "^19.1.6",
    "@types/react-syntax-highlighter": "^15.5.13",
    "@types/recharts": "^1.8.29",
    "axios": "^1.10.0",
    "framer-motion": "^12.23.0",
    "lucide-react": "^0.525.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "react-hot-toast": "^2.5.2",
    "react-scripts": "5.0.1",
    "react-syntax-highlighter": "^15.6.1",
    "recharts": "^3.0.2",
    "socket.io-client": "^4.8.1",
    "typescript": "^4.9.5",
    "web-vitals": "^2.1.4"
  }
}
```

---

## 8. Integration Patterns

### Backend-Frontend Communication
**Base URL Configuration:**
```typescript
// Frontend service - BUG: Wrong default port
constructor(baseURL: string = 'http://localhost:8000') // Should be 8001
```
**Issue**: Default base URL in frontend service is port 8000, but backend runs on 8001. This is overridden by environment variable but represents a configuration inconsistency.

### Provider Integration Pattern
```python
# Provider Service Pattern
class Provider:
    def __init__(self, id: str, name: str, port: int):
        self.id = id
        self.name = name 
        self.port = port
        self.status = ProviderStatus.DISCONNECTED
        
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        # Connection testing with timeout
        
    async def generate_response(self, messages: List[Dict]) -> Dict:
        # Provider-specific response generation
```

### Analytics Middleware Integration
```python
# Request interception for analytics
class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics and record analytics
        await self._record_analytics(...)
```

---

## 9. State Management & Local Storage

### Frontend State Persistence
```typescript
// Active tab persistence
const loadActiveTab = () => {
  try {
    const saved = localStorage.getItem('app_active_tab');
    return saved || 'chat';
  } catch (error) {
    console.error('Failed to load active tab from localStorage:', error);
    return 'chat';
  }
};

// Provider selection persistence  
const loadSelectedProvider = () => {
  try {
    const saved = localStorage.getItem('selected_provider');
    return saved || '';
  } catch (error) {
    console.error('Failed to load selected provider:', error);
    return '';
  }
};
```

**localStorage Keys Used:**
- `app_active_tab`: Main application tab selection
- `selected_provider`: User's preferred AI provider
- `guardrails_config`: Guardrails configuration (full detector objects)
- `provider_configs`: Provider API keys and settings
- `guardrails_tab_selection`: Guardrails configuration tab index

### Session Management
```python
# Backend session storage (in-memory)
class ChatService:
    def __init__(self):
        self.chat_history = {}  # session_id -> messages
        self.session_configs = {}  # session_id -> detector_config
```

### Real-time State Updates
```typescript
// Hooks for real-time data
export const useRealTimeLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await apiService.get('/api/logs');
        setLogs(response.data);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    }, 1000); // 1-second polling
    
    return () => clearInterval(interval);
  }, []);
  
  return { logs };
};
```

---

## 10. API Endpoints & Request/Response Formats

### Core Chat API
**Endpoint**: `POST /api/chat/message`
**Request Format**:
```json
{
  "message": "Hello, how are you?",
  "detector_config": {
    "toxicity": {
      "enabled": true,
      "threshold": 0.85
    }
  },
  "session_id": "session_123",
  "provider_id": "openai"
}
```

**Response Format**:
```json
{
  "response": "I'm doing well, thank you!",
  "blocked": false,
  "blocking_reasons": [],
  "session_id": "session_123",
  "message_id": "msg_456",
  "timestamp": "2025-08-05T10:30:00Z",
  "input_analysis": {
    "toxicity": {
      "blocked": false,
      "confidence": 0.1,
      "reason": "Content appears safe"
    }
  },
  "output_analysis": {
    "toxicity": {
      "blocked": false,
      "confidence": 0.05,
      "reason": "Response is appropriate"
    }
  }
}
```

### Provider Management API
**Endpoint**: `GET /api/providers/`
**Response Format**:
```json
{
  "providers": {
    "openai": {
      "id": "openai",
      "name": "OpenAI",
      "display_name": "OpenAI GPT",
      "port": 8002,
      "enabled": true,
      "status": "connected",
      "api_key": "sk-***",
      "models": [
        {
          "id": "gpt-4",
          "name": "GPT-4",
          "description": "Most capable model"
        }
      ]
    }
  },
  "stats": {
    "total_providers": 5,
    "enabled": 2,
    "connected": 1
  }
}
```

### Health Check API
**Endpoint**: `GET /health`
**Response Format**:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "detectors_available": ["toxicity", "pii", "prompt_injection"],
  "detectors_status": {
    "toxicity": true,
    "pii": false,
    "prompt_injection": true
  },
  "ollama_connected": true,
  "nemo_guardrails": true,
  "system_health": {
    "overall_status": "healthy",
    "components": [
      {
        "name": "model_manager",
        "status": "healthy",
        "response_time": 15.2,
        "error": null
      }
    ],
    "timestamp": "2025-08-05T10:30:00Z"
  }
}
```

### Analytics Export API
**Endpoint**: `GET /api/analytics/export/dashboard`
**Response Format**: See sample_kpmg_analytics_dashboard.json for complete structure

---

## 11. Real-time Features & WebSocket Implementation

### WebSocket Chat Interface
**Endpoint**: `ws://localhost:8001/ws/chat`

**Connection Handling**:
```python
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    app_logger.info("WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "chat_message":
                message = data.get("message", "")
                detector_config = data.get("detector_config", {})
                
                response = await chat_service.process_message(message, detector_config)
                await websocket.send_json(response)
                
    except WebSocketDisconnect:
        app_logger.info("WebSocket connection closed")
```

### Real-time Log Streaming
**Endpoint**: `GET /api/logs`
**Frontend Implementation**:
```typescript
export const useRealTimeLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch('http://localhost:8001/api/logs');
        const newLogs = await response.json();
        setLogs(newLogs);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    };
    
    // Poll every second for real-time updates
    const interval = setInterval(fetchLogs, 1000);
    fetchLogs(); // Initial fetch
    
    return () => clearInterval(interval);
  }, []);
  
  return { logs };
};
```

### System Status Updates
Real-time status updates are implemented through periodic polling rather than WebSocket due to the architecture. The frontend polls health endpoints every few seconds to maintain current status.

---

## 12. Security & Guardrails Logic

### ML-Based Detection Pipeline

**6 Safety Detectors:**
1. **Toxicity Detection**
   - Model: `martin-ha/toxic-comment-model` (BERT-based)
   - Threshold: 0.85 (increased to reduce false positives)
   - CPU optimized for enterprise load

2. **PII Detection**
   - Model: spaCy `en_core_web_sm` + pattern matching
   - Sensitivity: 0.6 (reduced from 0.8 to be less aggressive)
   - Detects: emails, phone numbers, SSNs, addresses

3. **Prompt Injection Detection**
   - Pattern-based analysis with ML scoring
   - Threshold: 0.7 (increased from 0.5 for better accuracy)
   - Detects: system prompt attempts, jailbreaking

4. **Topic Classification**
   - Model: `all-MiniLM-L6-v2`
   - Threshold: 0.85 (increased to be less sensitive)
   - Restricted topic detection

5. **Fact Check Detection**
   - Threshold: 0.6 (increased from 0.5)
   - Claims verification flags

6. **Spam Detection**
   - Threshold: 0.75 (increased from 0.6)
   - Repetitive content and spam patterns

### Guardrails Manager Implementation
```python
class GuardrailsManager:
    def __init__(self, model_manager, detection_service=None):
        self.use_phase4_pipeline = True  # Multi-stage pipeline
        self.phase4_pipeline = None
        
    async def process_message(self, message: str, detector_config: Optional[Dict[str, Any]] = None):
        # Phase 4: Use multi-stage pipeline if available
        if self.use_phase4_pipeline and self.phase4_pipeline:
            return await self._process_with_phase4_pipeline(message, detector_config)
        
        # Fallback to traditional processing
        return await self._process_with_traditional_guardrails(message)
```

### Enterprise Security Features
```python
# Enterprise-mode detector loading
async def load_detector(self, detector_name: str, force_load: bool = False):
    # For enterprise deployment - load model immediately and keep it loaded
    await detector_instance.load_model()
    
    # Optimize for CPU to handle enterprise load efficiently
    detector_instance.model = detector_instance.model.to(torch.device("cpu"))
    detector_instance.model.eval()  # Set to evaluation mode
    
    detector_instance._enterprise_mode = True  # Mark as enterprise mode
```

### Privacy Protection
```python
@staticmethod
def _hash_content(content: str) -> str:
    """Create SHA-256 hash for privacy protection"""
    if not content:
        return ""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

All user prompts and AI responses are hashed before database storage to protect privacy while maintaining analytics capabilities.

---

## 13. Analytics & Monitoring Systems

### KPMG Analytics Integration

**Export Scheduler**:
```python
# Automated exports every 5 minutes
EXPORT_INTERVAL_MINUTES = 5

# Export format for KPMG dashboard
export_data = {
    "export_metadata": {
        "generated_at": datetime.utcnow().isoformat(),
        "export_version": "1.0",
        "time_ranges": ["1h", "6h", "12h", "24h", "3d", "1w"]
    },
    "time_ranges": {
        # Comprehensive analysis for each timeframe
    }
}
```

**Export Location**: `/backend/user_data/exports/dashboard_YYYY-MM-DD_HH-MM.json`

### Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.performance_stats = {
            "cpu_inference_times": [],
            "gpu_inference_times": [],
            "memory_usage": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_events": 0
        }
```

### Health Monitoring System
```python
# Component health checkers
system_health_monitor.register_checker(
    "ollama_client",
    _check_ollama_health,
    timeout=10.0
)

system_health_monitor.register_checker(
    "model_manager", 
    _check_model_manager_health,
    timeout=5.0
)
```

### Alert System
```python
def _generate_alerts(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts = []
    
    # High block rate alert
    if summary["block_rate"] > 0.3:  # More than 30% blocked
        alerts.append({
            "type": "high_block_rate",
            "severity": "warning" if summary["block_rate"] < 0.5 else "critical",
            "message": f"Block rate elevated: {summary['block_rate']*100:.1f}%"
        })
```

### Self-Healing System
The application includes self-healing mechanisms for:
- Automatic connection reset
- Memory cleanup
- Performance optimization
- Circuit breaker recovery

---

## 14. Provider Integrations

### OpenAI Integration
```python
class OpenAIProvider(Provider):
    def __init__(self):
        super().__init__("openai", "OpenAI", 8002)
        self.models = [
            {"id": "gpt-4", "name": "GPT-4", "description": "Most capable model"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Fast and efficient"}
        ]
        self.requires_api_key = True
```

### Anthropic Integration
```python
class AnthropicProvider(Provider):
    def __init__(self):
        super().__init__("anthropic", "Anthropic", 8003)
        self.models = [
            {"id": "claude-3-opus", "name": "Claude 3 Opus"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku"}
        ]
```

### Ollama Integration (Local Models)
```python
class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        
    async def generate(self, model: str, prompt: str):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        # Direct HTTP API integration
```

### Provider Connection Testing
```python
async def test_provider_connection(self, provider_id: str) -> Tuple[bool, Optional[str]]:
    """Test connection to a provider with LLM generation test"""
    provider = self.get_provider(provider_id)
    
    # Basic connection test
    connection_success = await provider.test_connection()
    
    # LLM generation test
    if connection_success:
        test_prompt = "Hello! Please respond with 'Connection test successful'"
        response = await provider.generate_response([{"role": "user", "content": test_prompt}])
        return response is not None, None
    
    return False, "Connection failed"
```

---

## 15. Testing Frameworks

### Backend Testing
**Framework**: pytest with asyncio support
**Test Files**:
- `/backend/test_api_integration.py`
- `/backend/test_config_respect.py`
- `/backend/test_endpoints.py`
- `/backend/test_functionality.py`
- `/backend/test_guardrails.py`
- `/backend/test_providers.py`

**Example Test Structure**:
```python
@pytest.mark.asyncio
async def test_detector_functionality():
    model_manager = ModelManager()
    await model_manager.initialize()
    
    # Test toxicity detection
    result = await model_manager.detect("You are amazing!", "toxicity")
    assert result["result"]["score"] < 0.5
```

### Frontend Testing
**Framework**: React Testing Library + Jest
**Configuration**:
```json
"scripts": {
  "test": "react-scripts test",
}
```

**Testing Libraries**:
- `@testing-library/react`: Component testing
- `@testing-library/user-event`: User interaction simulation
- `@testing-library/jest-dom`: Enhanced assertions

### Integration Testing
**Manual Testing Scripts**:
```bash
# Backend health check
curl http://localhost:8001/health

# Provider test
curl http://localhost:8001/api/providers/

# Analytics health
curl http://localhost:8001/api/analytics/health
```

---

## 16. Known Issues & Bugs

### Configuration Inconsistencies
1. **Port Mismatch**: Frontend API service defaults to port 8000, but backend runs on 8001
   - **Location**: `/frontend/src/services/api.ts` line 16
   - **Fix**: Change default from 8000 to 8001
   - **Current Workaround**: Environment variable override

### Model Loading Issues
2. **NeMo Guardrails Fallback**: 
   - **Issue**: Application falls back to simple guardrails when NeMo is unavailable
   - **Location**: `/backend/app/main.py` lines 51-57
   - **Impact**: Reduced functionality without proper NeMo installation

### Frontend State Management
3. **localStorage Error Handling**:
   - **Issue**: Multiple try-catch blocks for localStorage operations
   - **Location**: Throughout `/frontend/src/App.tsx`
   - **Impact**: Potential state loss in private browsing mode

### Database Schema Issues
4. **Export Log Foreign Key**:
   - **Issue**: No foreign key relationship between user_analytics and export_log
   - **Location**: `/backend/app/services/analytics_service.py`
   - **Impact**: Potential data integrity issues

### Performance Issues
5. **Real-time Log Polling**:
   - **Issue**: Frontend polls logs every second, potentially causing performance issues
   - **Location**: `/frontend/src/hooks/useRealTime.ts`
   - **Impact**: Increased network traffic and CPU usage

### Provider Management
6. **Port Conflict Resolution**:
   - **Issue**: Force port option doesn't gracefully handle conflicts
   - **Location**: `/backend/app/services/provider_service.py`
   - **Impact**: Potential service startup failures

### Analytics Middleware
7. **Response Body Extraction**:
   - **Issue**: Middleware cannot properly extract response bodies in production
   - **Location**: `/backend/app/middleware/analytics_middleware.py` lines 154-158
   - **Impact**: Incomplete analytics data collection

### WebSocket Implementation
8. **Error Handling in WebSocket**:
   - **Issue**: WebSocket errors not properly propagated to frontend
   - **Location**: `/backend/app/main.py` WebSocket endpoint
   - **Impact**: Silent failures in real-time chat

### Memory Management
9. **Model Cleanup in Enterprise Mode**:
   - **Issue**: Cleanup method preserves models in enterprise mode but doesn't clear all resources
   - **Location**: `/backend/app/models/model_manager.py` lines 391-418
   - **Impact**: Potential memory leaks in long-running deployments

### Build Process
10. **Dependency Installation Order**:
    - **Issue**: npm install uses --legacy-peer-deps flag due to React 19 compatibility issues
    - **Location**: `/start_react_app.sh` line 33
    - **Impact**: Potential security vulnerabilities from legacy dependency resolution

---

## Rebuild Instructions

To rebuild this application exactly as it exists (including bugs):

1. **Environment Setup**:
   - Python 3.13+
   - Node.js 18+
   - 8GB+ RAM

2. **Backend Setup**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install --legacy-peer-deps
   ```

4. **Configuration**:
   - Copy all configuration files exactly as shown
   - Set environment variables for provider API keys
   - Ensure SQLite database directory exists

5. **Startup**:
   ```bash
   chmod +x start_react_app.sh
   ./start_react_app.sh
   ```

6. **Database Initialization**:
   - SQLite database auto-creates on first request
   - Analytics tables initialize automatically
   - Export directory creates automatically

This documentation captures the exact state of the application, including all architectural decisions, implementation details, configuration inconsistencies, and known issues that would be required to rebuild the system identically.

## Project Directory Structure

```
KPMG/NemoGaurdrails-Local-LLM-Web-Version/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI application entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── providers.py                 # Provider management endpoints
│   │   │   └── analytics_endpoints.py       # Analytics API endpoints
│   │   ├── guardrails/
│   │   │   ├── __init__.py
│   │   │   ├── guardrails_manager.py        # Core guardrails processing
│   │   │   ├── detectors/                   # Individual detector implementations
│   │   │   ├── ensemble/                    # Ensemble detection methods
│   │   │   ├── optimization/                # Performance optimization
│   │   │   └── pipeline/                    # Multi-stage pipeline
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── analytics_middleware.py      # Request analytics collection
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── model_manager.py             # ML model management
│   │   │   └── detector_models.py           # Detector data models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── analytics_service.py         # KPMG analytics integration
│   │   │   ├── chat_service.py              # Chat message processing
│   │   │   ├── detection_service.py         # Detection orchestration
│   │   │   ├── provider_service.py          # Multi-provider management
│   │   │   ├── export_scheduler.py          # Automated data exports
│   │   │   └── traffic_router.py            # Load balancing
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── gpu_accelerator.py           # GPU optimization utilities
│   ├── configs/
│   │   └── app_config.yml                   # Application configuration
│   ├── requirements.txt                     # Python dependencies
│   └── user_data/                           # Runtime data storage
│       ├── ai_safety_analytics.db           # SQLite analytics database
│       └── exports/                         # KPMG export files
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── analytics/
│   │   │   │   ├── AnalyticsOverview.tsx
│   │   │   │   └── GuardrailAnalyticsDashboard.tsx
│   │   │   ├── chat/
│   │   │   │   └── ModernChatInterface.tsx
│   │   │   ├── common/
│   │   │   │   ├── LoadingSpinner.tsx
│   │   │   │   └── TabPanel.tsx
│   │   │   ├── docs/                        # Documentation system
│   │   │   ├── distributed/
│   │   │   │   └── DistributedProcessing.tsx
│   │   │   ├── gpu/
│   │   │   │   └── GPUAcceleration.tsx
│   │   │   ├── guardrails/
│   │   │   │   └── GuardrailsConfig.tsx
│   │   │   ├── providers/
│   │   │   │   ├── ProvidersConfig.tsx
│   │   │   │   └── PortConflictDialog.tsx
│   │   │   └── testing/
│   │   │       └── AdvancedTestingPlayground.tsx
│   │   ├── hooks/
│   │   │   ├── useApi.ts                    # Core API integration hooks
│   │   │   ├── useProviders.ts              # Provider management hooks
│   │   │   └── useRealTime.ts               # Real-time data hooks
│   │   ├── services/
│   │   │   ├── api.ts                       # Axios API client
│   │   │   ├── ollama.ts                    # Ollama service integration
│   │   │   └── ollamaDownload.ts            # Model download service
│   │   ├── themes/
│   │   │   └── darkTheme.ts                 # Material-UI dark theme
│   │   ├── types/
│   │   │   └── index.ts                     # TypeScript type definitions
│   │   ├── App.tsx                          # Main React application
│   │   ├── index.tsx                        # React DOM entry point
│   │   └── index.css                        # Global styles
│   ├── package.json                         # Node.js dependencies
│   ├── tsconfig.json                        # TypeScript configuration
│   └── .env                                 # Environment variables
├── logs/
│   ├── backend.log                          # Backend application logs
│   └── frontend.log                         # Frontend build logs
├── sample_kpmg_analytics_dashboard.json     # Sample analytics export
├── start_react_app.sh                       # Application startup script
├── REBUILD_DOCUMENTATION.md                 # This documentation
├── TECHNICAL_README.md                      # Technical overview
├── README.md                                # Project README
└── various test and configuration files
```

This documentation provides everything needed to rebuild the KPMG NemoGuardrails AI Safety System exactly as it currently exists, including all features, bugs, and architectural decisions.