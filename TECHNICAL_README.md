# Technical Implementation Guide

Comprehensive technical documentation for the AI Safety System with KPMG Analytics Integration.

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Frontend (React + TypeScript)                │
│                         Port 3000                              │
├─────────────────────────────────────────────────────────────────┤
│  • Provider Management  • Analytics Dashboard                  │
│  • Guardrails Config   • Testing Playground                   │
│  • Real-time Monitor   • System Health                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8001)                    │
├─────────────────────────────────────────────────────────────────┤
│  Analytics Middleware                                          │
│  ├── Request Capture        ├── Performance Metrics           │
│  ├── Response Analysis      ├── Privacy Protection            │
│  └── Real-time Logging      └── Error Handling                │
├─────────────────────────────────────────────────────────────────┤
│  Core Services                                                 │
│  ├── Provider Service       ├── Detection Service             │
│  ├── Analytics Service      ├── Chat Service                  │
│  ├── Export Scheduler       └── Config Service                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ML Detection Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   Toxicity   │ │     PII      │ │   Prompt     │            │
│  │  Detection   │ │  Detection   │ │  Injection   │            │
│  │   (BERT)     │ │   (spaCy)    │ │  (Patterns)  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Hate Speech  │ │    Bias      │ │   Privacy    │            │
│  │ Detection    │ │  Detection   │ │  Detection   │            │
│  │  (Ensemble)  │ │ (Patterns)   │ │ (Ensemble)   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   KPMG Analytics System                        │
├─────────────────────────────────────────────────────────────────┤
│  SQLite Database                                               │
│  ├── User Analytics Table   ├── Export Log Table              │
│  ├── Performance Indexes    ├── Real-time Counters            │
│  └── Privacy Protection     └── Data Retention                │
├─────────────────────────────────────────────────────────────────┤
│  Export Scheduler (5min intervals)                            │
│  ├── JSON Generation        ├── Secure Transmission           │
│  ├── HMAC Signatures        ├── Offline Queuing               │
│  └── Retry Mechanism        └── Audit Logging                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Backend Implementation

### FastAPI Application Structure
```python
# app/main.py - Main application with lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize ML models, services, analytics
    yield
    # Shutdown: Cleanup resources, stop scheduler

app = FastAPI(lifespan=lifespan)
app.add_middleware(AnalyticsMiddleware)
app.add_middleware(ChatAnalyticsMiddleware)
```

### Core Services

#### Analytics Service (`app/services/analytics_service.py`)
```python
class AnalyticsService:
    """Enterprise-grade analytics with SQLite + pandas"""
    
    def __init__(self, db_path: str = "user_data/ai_safety_analytics.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self._init_database()
    
    async def record_user_request(
        self, user_ip: str, request_id: str, prompt: str,
        response: Optional[str], guardrail_results: Dict,
        performance_metrics: Dict, session_id: Optional[str] = None
    ) -> bool:
        """Record comprehensive user interaction data"""
        
    def generate_dashboard_export(self) -> Dict[str, Any]:
        """Generate multi-timeframe analytics for KPMG"""
```

#### Export Scheduler (`app/services/export_scheduler.py`)
```python
class ExportScheduler:
    """Automated 5-minute KPMG exports with retry logic"""
    
    async def _perform_export(self) -> bool:
        # Generate analytics export
        export_data = analytics_service.generate_dashboard_export()
        
        # Save locally
        await self._save_export_file(export_data, filename)
        
        # Transmit to KPMG with HMAC signature
        success = await self._transmit_to_kpmg(payload)
        
        # Queue for retry if failed
        if not success:
            await self._queue_for_offline_processing(payload)
```

#### Provider Service (`app/services/provider_service.py`)
```python
class ProviderService:
    """Multi-provider LLM management"""
    
    def __init__(self):
        self.providers = {
            "openai": Provider(id="openai", port=8891, ...),
            "anthropic": Provider(id="anthropic", port=8892, ...),
            "google": Provider(id="google", port=8893, ...),
            "ollama": Provider(id="ollama", port=8895, ...)
        }
    
    async def test_connection(self, provider_id: str) -> bool:
        """Test provider connectivity and authentication"""
```

### Database Schema

#### User Analytics Table
```sql
CREATE TABLE user_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_ip TEXT NOT NULL,
    request_id TEXT UNIQUE NOT NULL,
    prompt_hash TEXT NOT NULL,        -- SHA-256 for privacy
    response_hash TEXT,               -- SHA-256 for privacy
    status TEXT NOT NULL,             -- 'allowed', 'blocked', 'error'
    blocked_by TEXT,                  -- Which guardrail blocked it
    
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
);

CREATE INDEX idx_timestamp ON user_analytics(timestamp);
CREATE INDEX idx_user_ip ON user_analytics(user_ip);
CREATE INDEX idx_status ON user_analytics(status);
```

### ML Detection Pipeline

#### Model Manager (`app/models/model_manager.py`)
```python
class ModelManager:
    """ML model lifecycle management"""
    
    async def initialize(self, load_detectors: List[str]):
        """Load specified ML models with enterprise optimization"""
        for detector in load_detectors:
            await self.load_detector(detector)
    
    async def load_detector(self, detector_name: str):
        """Load and optimize specific detector model"""
        model = await detector_models.load_model(detector_name)
        self.models[detector_name] = model
        self.apply_enterprise_optimization(detector_name)
```

#### Detection Service (`app/services/detection_service.py`)
```python
class DetectionService:
    """Coordinated multi-detector analysis"""
    
    async def run_detection(
        self, text: str, enabled_detectors: List[str], 
        detector_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run enabled detectors on input text"""
        results = {}
        
        for detector in enabled_detectors:
            if detector in self.model_manager.models:
                result = await self._run_single_detector(detector, text, config)
                results[detector] = result
        
        return self._aggregate_results(results)
```

### Middleware Implementation

#### Analytics Middleware (`app/middleware/analytics_middleware.py`)
```python
class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Real-time request/response capture"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Extract request metadata
        user_ip = self._get_client_ip(request)
        request_body = await self._extract_request_body(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Record analytics asynchronously
        await self._record_analytics(
            request_id, user_ip, request_body, 
            response_data, response_time_ms
        )
        
        return response
```

## 🎨 Frontend Implementation

### React Application Structure
```typescript
// src/App.tsx - Main application with provider routing
function App() {
  return (
    <Router>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <Box sx={{ display: 'flex', minHeight: '100vh' }}>
          <AppTabs />
          <MainContent />
        </Box>
      </ThemeProvider>
    </Router>
  );
}
```

### Key Components

#### Provider Management (`src/components/providers/ProvidersConfig.tsx`)
```typescript
const ProvidersConfig: React.FC = () => {
  const { 
    providers, loading, updateProvider, 
    testConnection, enableProvider 
  } = useProviders();
  
  return (
    <Grid container spacing={3}>
      {Object.values(providers).map(provider => (
        <ProviderCard 
          key={provider.id}
          provider={provider}
          onUpdate={updateProvider}
          onTest={testConnection}
        />
      ))}
    </Grid>
  );
};
```

#### Analytics Dashboard (`src/components/analytics/AnalyticsOverview.tsx`)
```typescript
const AnalyticsOverview: React.FC = () => {
  const analytics = useAnalytics();
  
  return (
    <Box>
      <RealTimeStats stats={analytics.stats} />
      <GuardrailPerformance metrics={analytics.guardrails} />
      <ProviderHealth providers={analytics.providers} />
      <ExportStatus scheduler={analytics.exportStatus} />
    </Box>
  );
};
```

### Custom Hooks

#### useProviders Hook (`src/hooks/useProviders.ts`)
```typescript
export const useProviders = () => {
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  
  const fetchProviders = useCallback(async () => {
    const response = await fetch(`${BACKEND_URL}/api/providers/`);
    const data = await response.json();
    setProviders(data.providers);
  }, []);
  
  const updateProvider = useCallback(async (
    providerId: string, config: ProviderConfig
  ) => {
    await fetch(`${BACKEND_URL}/api/providers/${providerId}/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    await fetchProviders();
  }, [fetchProviders]);
  
  return { providers, updateProvider, testConnection, enableProvider };
};
```

## 🔒 Security Implementation

### Privacy Protection
```python
# SHA-256 content hashing for privacy
def _hash_content(content: str) -> str:
    if not content:
        return ""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# Usage in analytics recording
prompt_hash = self._hash_content(prompt)
response_hash = self._hash_content(response) if response else None
```

### Secure Transmission
```python
# HMAC signature generation
def _generate_hmac_signature(self, data: str) -> str:
    if not self.config.hmac_secret:
        return ""
    
    signature = hmac.new(
        self.config.hmac_secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

# HTTPS transmission with JWT + HMAC
headers = {
    "Authorization": f"Bearer {self.config.jwt_token}",
    "X-Data-Signature": self._generate_hmac_signature(payload_json),
    "X-Client-ID": self.config.client_id,
    "X-Timestamp": datetime.utcnow().isoformat()
}
```

## 📊 KPMG Analytics Integration

### Export Data Structure
```json
{
  "export_metadata": {
    "generated_at": "2025-01-17T10:30:00Z",
    "export_version": "1.0",
    "time_ranges": ["1h", "6h", "12h", "24h", "3d", "1w"]
  },
  "time_ranges": {
    "1h": {
      "summary": {
        "total_requests": 150,
        "blocked_requests": 45,
        "block_rate": 0.30,
        "unique_users": 12,
        "avg_response_time_ms": 245
      },
      "guardrail_analysis": {
        "toxicity": {
          "triggers": 20,
          "avg_confidence": 0.85,
          "effectiveness_percentage": 95.2
        }
      },
      "user_activity": {
        "192.168.1.100": {
          "total_requests": 25,
          "blocked_requests": 8,
          "risk_score": 32.0
        }
      },
      "provider_performance": {
        "openai": {
          "requests": 80,
          "avg_response_time": 240,
          "error_rate": 0.025
        }
      },
      "alerts": [
        {
          "type": "high_block_rate",
          "severity": "warning",
          "message": "Block rate exceeded 30%",
          "threshold": 0.3,
          "current": 0.35
        }
      ]
    }
  }
}
```

### Multi-timeframe Analysis
```python
def _generate_timeframe_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary statistics using pandas"""
    if df.empty:
        return self._empty_summary()
    
    total_requests = len(df)
    blocked_requests = len(df[df['status'] == 'blocked'])
    block_rate = blocked_requests / total_requests if total_requests > 0 else 0.0
    unique_users = df['user_ip'].nunique()
    avg_response_time = df['response_time_ms'].mean()
    
    return {
        "total_requests": total_requests,
        "blocked_requests": blocked_requests,
        "block_rate": round(block_rate, 3),
        "unique_users": unique_users,
        "avg_response_time_ms": round(avg_response_time, 2)
    }
```

## ⚡ Performance Optimizations

### SQLite Optimizations
```python
# WAL mode for better concurrency
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=10000")

# Performance indexes
conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON user_analytics(timestamp)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_user_ip ON user_analytics(user_ip)")
```

### Async Processing
```python
# Non-blocking analytics recording
async def _record_analytics(self, ...):
    try:
        # Use asyncio for non-blocking database operations
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_database_write, entry)
    except Exception as e:
        logger.error(f"Analytics recording failed: {e}")
```

### Caching Strategy
```python
# In-memory counters for real-time stats
self.total_requests = 0
self.blocked_requests = 0
self.allowed_requests = 0

# Efficient DataFrame operations
df = self._get_timeframe_data(hours)
summary = self._generate_timeframe_summary(df)
```

## 🧪 Testing Framework

### Multi-level Testing Strategy

#### Level 1: Unit Tests
```python
# test_analytics_service.py
def test_record_user_request():
    service = AnalyticsService(":memory:")
    result = await service.record_user_request(
        user_ip="127.0.0.1",
        request_id="test_001",
        prompt="test prompt",
        response="test response",
        guardrail_results={"toxicity": {"score": 0.1}},
        performance_metrics={"response_time_ms": 100}
    )
    assert result == True
```

#### Level 2: Integration Tests
```python
# test_providers.py
def test_provider_connectivity():
    for provider_id in ["openai", "anthropic", "google"]:
        result = await provider_service.test_connection(provider_id)
        assert result.status in ["connected", "disconnected"]
```

#### Level 3: End-to-End Tests
```python
# test_functionality.py
def test_complete_workflow():
    # Test full request pipeline
    response = await client.post("/api/chat/completions", json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code in [200, 400]  # 400 if blocked
```

### Health Monitoring
```python
async def health_check():
    checks = {
        "database": analytics_service.get_database_stats(),
        "export_scheduler": export_scheduler.get_status(),
        "ml_models": model_manager.get_model_status(),
        "providers": provider_service.get_provider_stats()
    }
    
    overall_status = "healthy" if all(
        check.get("status") == "healthy" 
        for check in checks.values()
    ) else "unhealthy"
    
    return {"status": overall_status, "components": checks}
```

## 🚀 Deployment Considerations

### Environment Configuration
```bash
# Production environment variables
KPMG_DASHBOARD_ENDPOINT=https://prod-kpmg-api.com/v1/ingest
KPMG_CLIENT_ID=prod-client-001
KPMG_JWT_TOKEN=<production-jwt-token>
KPMG_HMAC_SECRET=<production-hmac-secret>

# Database configuration
ANALYTICS_DB_PATH=/data/ai_safety_analytics.db
ANALYTICS_RETENTION_DAYS=30

# Performance tuning
ML_BATCH_SIZE=32
ASYNC_WORKERS=4
EXPORT_INTERVAL_MINUTES=5
```

### Monitoring & Alerting
```python
# System health monitoring
system_health_monitor.register_checker("analytics_db", _check_db_health)
system_health_monitor.register_checker("export_scheduler", _check_scheduler_health)
system_health_monitor.register_checker("ml_pipeline", _check_ml_health)

# Performance monitoring
performance_monitor.track_endpoint_latency()
performance_monitor.track_memory_usage()
performance_monitor.track_error_rates()

# Alert conditions
alert_manager.add_rule("high_block_rate", threshold=0.3)
alert_manager.add_rule("slow_response_time", threshold=2000)
alert_manager.add_rule("export_failures", threshold=3)
```

## 📋 API Reference

### Complete Endpoint Documentation

#### Analytics Endpoints
```http
GET    /api/analytics/health                          # System health
GET    /api/analytics/stats                           # Real-time statistics
GET    /api/analytics/database/stats                  # Database metrics
GET    /api/analytics/export/dashboard                # Full dashboard export
GET    /api/analytics/export/timeframe/{timeframe}    # Specific timeframe
POST   /api/analytics/export/user-data                # User data export
GET    /api/analytics/export/scheduler/status         # Scheduler status
POST   /api/analytics/export/scheduler/start          # Start scheduler
POST   /api/analytics/export/scheduler/stop           # Stop scheduler
POST   /api/analytics/export/force                    # Force export
DELETE /api/analytics/data/cleanup                    # Data cleanup
```

#### Provider Endpoints
```http
GET    /api/providers/                                # List providers
GET    /api/providers/{id}                           # Get provider
PUT    /api/providers/{id}/config                    # Update config
POST   /api/providers/{id}/test-connection           # Test connection
POST   /api/providers/{id}/enable                    # Enable provider
POST   /api/providers/{id}/disable                   # Disable provider
GET    /api/providers/stats/summary                  # Provider stats
```

#### Detection Endpoints
```http
GET    /api/detectors/                               # List detectors
POST   /api/detectors/analyze                        # Analyze text
PUT    /api/detectors/config                         # Update config
GET    /api/detectors/{detector}/status              # Detector status
```

This technical documentation provides the complete implementation details for developers working on or deploying the AI Safety System with KPMG Analytics Integration.