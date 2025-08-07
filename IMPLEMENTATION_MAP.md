# LLMinate Dashboard Implementation Map

## Overview
Create two high-level dashboards (Main CISO Dashboard & User-Info Dashboard) that receive real-time data through a single WebSocket connection (`ws://scanllmai.com/ws/guardrails/`) using message types for routing.

## Project Structure
```
/LLMinate/
├── src/
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── MainDashboard.jsx       # CISO Executive Dashboard
│   │   │   └── UserDashboard.jsx       # User Analytics Dashboard
│   │   ├── shared/
│   │   │   ├── WebSocketProvider.jsx   # WebSocket connection management
│   │   │   ├── Charts/                 # Recharts components
│   │   │   └── UI/                     # MUI-based components
│   │   └── user/
│   │       ├── UserList.jsx            # Main user list view
│   │       └── UserDetail.jsx          # Individual user drill-down
│   ├── services/
│   │   ├── websocketService.js         # WebSocket message handling
│   │   └── dataProcessing.js           # Data transformation utilities
│   ├── hooks/
│   │   ├── useWebSocket.js             # WebSocket custom hook
│   │   └── useRealTimeData.js          # Data fetching hooks
│   └── utils/
│       ├── riskCalculation.js          # Risk scoring algorithms
│       └── dataFormatting.js           # Data formatting utilities
```

---

## Phase 1: Backend Database Restructuring ✅

### 1.1 New Database Tables
**Status: [✅] Completed** 
**Estimated Time: 4-6 hours**
**Completion Date: 2025-08-07**
**Notes: Successfully created all 5 new tables with indexes and migration tracking**

#### Tables to Create:
```sql
-- Daily aggregated metrics for CISO dashboard trends
CREATE TABLE daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_hour TIMESTAMP NOT NULL, -- Hourly granularity
    total_requests INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,
    allowed_requests INTEGER DEFAULT 0,
    data_exfiltration_attempts INTEGER DEFAULT 0,
    prompt_injection_attempts INTEGER DEFAULT 0,
    toxicity_triggers INTEGER DEFAULT 0,
    top_blocking_reasons_json TEXT, -- JSON array
    avg_response_time REAL DEFAULT 0.0,
    risk_score INTEGER DEFAULT 0, -- 0-100 calculated score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date_hour)
);

-- User aggregated metrics for User-Info dashboard
CREATE TABLE user_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    ip_address TEXT,
    email TEXT,
    hostname TEXT, -- From reverse DNS lookup
    department TEXT, -- Future: from LDAP/AD
    risk_score INTEGER DEFAULT 0, -- 0-100 calculated
    total_requests INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,
    blocked_percentage REAL DEFAULT 0.0,
    last_active_timestamp TIMESTAMP,
    top_violated_categories_json TEXT, -- JSON object
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, ip_address)
);

-- Provider performance metrics
CREATE TABLE provider_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    date_hour TIMESTAMP NOT NULL,
    total_requests INTEGER DEFAULT 0,
    blocked_responses INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0.0,
    error_rate REAL DEFAULT 0.0,
    estimated_cost REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_name, date_hour)
);

-- Sensitive data detection breakdown
CREATE TABLE sensitive_data_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL, -- 'API_KEY', 'CREDIT_CARD', 'EMAIL', etc.
    date_hour TIMESTAMP NOT NULL,
    detection_count INTEGER DEFAULT 0,
    last_detected_timestamp TIMESTAMP,
    severity_level TEXT DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(data_type, date_hour)
);

-- User detailed activity for drill-down (privacy-safe)
CREATE TABLE user_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    ip_address TEXT,
    timestamp TIMESTAMP NOT NULL,
    status TEXT NOT NULL, -- 'ALLOWED', 'BLOCKED'
    blocked_reason TEXT,
    prompt_context_fingerprint TEXT, -- JSON: length, keywords, language, etc.
    model_used TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    provider TEXT,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Implementation Steps:
1. **Create migration script** - `backend/migrations/add_dashboard_tables.py`
2. **Update AnalyticsService** - Add methods for new tables
3. **Test table creation** - Ensure no conflicts with existing schema
4. **Create indexes** - Optimize for dashboard queries

**Edge Cases to Handle:**
- Table already exists (IF NOT EXISTS)
- Data type mismatches
- Foreign key constraints with existing tables
- Migration rollback capability

**Testing:**
- [ ] Tables create successfully
- [ ] Indexes are properly set
- [ ] No conflicts with existing data
- [ ] Performance test with sample data

---

### 1.2 Background Aggregation Service  
**Status: [✅] Completed**
**Estimated Time: 8-10 hours**
**Completion Date: 2025-08-07**
**Notes: Comprehensive service with risk scoring, DNS caching, and data retention policies. Includes user feedback improvements.**

#### Service Implementation:
Create `backend/app/services/data_aggregation_service.py`:

```python
class DataAggregationService:
    def __init__(self):
        self.db = get_database_connection()
        self.dns_cache = {}  # IP -> hostname cache
        
    async def run_periodic_aggregation(self):
        """Main aggregation loop - runs every 5-15 minutes"""
        while True:
            try:
                await self.aggregate_daily_summary()
                await self.aggregate_user_summary()
                await self.aggregate_provider_summary()
                await self.aggregate_sensitive_data_summary()
                await self.process_user_activity_logs()
                await self.cleanup_old_data()
                
                await asyncio.sleep(900)  # 15 minutes
            except Exception as e:
                logger.error(f"Aggregation failed: {e}")
                await asyncio.sleep(300)  # 5 minutes retry
                
    async def aggregate_daily_summary(self):
        """Calculate hourly/daily metrics from raw requests"""
        # Implementation details...
        
    async def calculate_risk_score(self, data: dict) -> int:
        """Risk scoring algorithm (0-100)"""
        # Weights as specified:
        # 40% - Data exfiltration attempts
        # 30% - Prompt injection severity  
        # 20% - Overall blocked requests
        # 10% - Guardrail effectiveness trend
        
    async def perform_reverse_dns(self, ip_address: str) -> str:
        """Cached reverse DNS lookup"""
        # Implementation with caching...
```

#### Integration Points:
1. **Startup Integration** - Add to `backend/app/main.py` lifespan
2. **Error Handling** - Comprehensive logging and recovery
3. **Performance Monitoring** - Track aggregation performance
4. **Manual Triggers** - API endpoint to force aggregation

**Edge Cases to Handle:**
- Database connection failures during aggregation
- Partial data corruption in raw tables
- DNS lookup timeouts/failures
- Memory management for large datasets
- Concurrent access to raw data during aggregation

**Testing:**
- [ ] Aggregation runs without errors
- [ ] Calculated metrics match expected values
- [ ] Performance under load (simulate 1M+ records)
- [ ] Recovery from database failures
- [ ] DNS caching works correctly

---

## Phase 2: WebSocket Message Routing System ✅

### 2.1 WebSocket Message Types
**Status: [ ] Not Started**
**Estimated Time: 3-4 hours**

#### Message Structure:
```javascript
// Outbound message types (Backend -> Frontend)
{
  "type": "main_dashboard_update",
  "timestamp": "2025-08-07T16:00:00Z",
  "data": {
    "executive_summary": {
      "risk_score": 85,
      "risk_level": "HIGH",
      "active_threats": [
        {"type": "Prompt Injection", "count": 45, "confidence": 94.2},
        {"type": "PII Leakage", "count": 23, "confidence": 97.8},
        {"type": "Toxicity", "count": 12, "confidence": 89.1}
      ],
      "data_exfiltration_attempts": 23,
      "guardrail_effectiveness": {
        "trend": "declining", // "improving", "stable", "declining"
        "current_rate": 94.5
      }
    },
    "charts_data": {
      "guardrail_trend": [...],
      "sensitive_data_breakdown": [...],
      "provider_analysis": [...]
    },
    "top_risk_entities": [...]
  }
}

{
  "type": "user_dashboard_update", 
  "timestamp": "2025-08-07T16:00:00Z",
  "data": {
    "users_list": [
      {
        "user_id": "user1@corp.com",
        "hostname": "DEV-PC-01.corp.net",
        "risk_score": 92,
        "total_requests": 1402,
        "blocked_percentage": 18.0,
        "last_active": "2025-08-07T15:55:00Z"
      }
    ],
    "overview_stats": {
      "total_users": 156,
      "high_risk_users": 12,
      "avg_risk_score": 34.5
    }
  }
}

{
  "type": "user_detail_response",
  "user_id": "user1@corp.com",
  "data": {
    "profile": {
      "user_id": "user1@corp.com",
      "department": "Engineering",
      "risk_score": 92,
      "top_violated_policy": "PII Detection (45%)"
    },
    "activity_timeline": [...],
    "violated_categories": {...},
    "detailed_logs": [...]
  }
}

// Inbound message types (Frontend -> Backend)
{
  "type": "request_user_detail",
  "user_id": "user1@corp.com"
}

{
  "type": "dashboard_config",
  "dashboard": "main", // or "user"
  "update_frequency": 15 // seconds
}
```

#### Backend WebSocket Handler Updates:
Update `backend/app/services/dashboard_websocket.py`:

```python
class DashboardWebSocketManager:
    async def handle_message(self, websocket: WebSocket, message: dict):
        msg_type = message.get("type")
        
        if msg_type == "request_user_detail":
            await self.send_user_detail(websocket, message["user_id"])
        elif msg_type == "dashboard_config":
            await self.update_client_config(websocket, message)
        # ... other handlers
            
    async def broadcast_main_dashboard(self):
        """Push main dashboard data to all connected clients"""
        data = await self.aggregation_service.get_main_dashboard_data()
        message = {
            "type": "main_dashboard_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        await self.broadcast_to_dashboard_clients(message, "main")
```

**Edge Cases to Handle:**
- Invalid message format
- Unknown message types
- Client disconnection during message processing
- Message queuing when client temporarily disconnected
- Rate limiting for user detail requests

**Testing:**
- [ ] All message types route correctly
- [ ] Invalid messages handled gracefully
- [ ] Client connection/disconnection works
- [ ] Message queuing works under load
- [ ] Rate limiting prevents abuse

---

## Phase 3: Frontend LLMinate Application ✅

### 3.1 Project Setup
**Status: [ ] Not Started**
**Estimated Time: 2-3 hours**

#### Setup Steps:
1. **Create React App**:
```bash
cd /Users/udsy/PycharmProjects/KPMG/NemoGaurdrails-Local-LLM-Web-Version
npx create-react-app LLMinate
cd LLMinate
```

2. **Install Dependencies**:
```bash
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material @mui/x-charts  
npm install recharts
# Note: No need for 'ws' - React uses native WebSocket API
```

3. **Configure Theme** - Adapt from existing `frontend/src/theme.js`
4. **Setup Router** - React Router for dashboard navigation

**Edge Cases to Handle:**
- Dependency version conflicts
- Theme compatibility issues
- Build configuration conflicts

**Testing:**
- [ ] Application builds successfully
- [ ] MUI theme applies correctly
- [ ] Router navigation works
- [ ] No console errors on startup

---

### 3.2 WebSocket Service Implementation
**Status: [ ] Not Started**
**Estimated Time: 4-5 hours**

#### WebSocket Service:
Create `LLMinate/src/services/websocketService.js`:

```javascript
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.messageHandlers = new Map();
    this.isConnected = false;
    this.reconnectInterval = 5000; // 5 seconds
  }

  connect(url = 'ws://scanllmai.com/ws/guardrails/') {
    try {
      this.ws = new WebSocket(url);
      
      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('Connected to WebSocket');
        this.onConnectionChange?.(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Invalid message format:', error);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.onConnectionChange?.(false);
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to connect:', error);
      this.attemptReconnect();
    }
  }

  handleMessage(message) {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message.data, message);
    } else {
      console.warn(`No handler for message type: ${message.type}`);
    }
  }

  subscribe(messageType, handler) {
    this.messageHandlers.set(messageType, handler);
  }

  send(message) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message queued');
      // Implement message queuing here
    }
  }

  // Specific methods for dashboard requests
  requestUserDetail(userId) {
    this.send({
      type: 'request_user_detail',
      user_id: userId
    });
  }

  configureDashboard(dashboard, updateFrequency) {
    this.send({
      type: 'dashboard_config',
      dashboard,
      update_frequency: updateFrequency
    });
  }
}

export default new WebSocketService();
```

**Edge Cases to Handle:**
- WebSocket connection failures
- Message parsing errors
- Reconnection logic
- Message queuing during disconnection
- Handler registration/deregistration
- Memory leaks from event listeners

**Testing:**
- [ ] Connection establishment works
- [ ] Reconnection works after network failure
- [ ] Message routing works correctly
- [ ] Error handling prevents crashes
- [ ] Memory management (no leaks)
- [ ] Message queuing during disconnection

---

### 3.3 Main CISO Dashboard
**Status: [ ] Not Started**
**Estimated Time: 12-15 hours**

#### Component Structure:
Create `LLMinate/src/components/dashboard/MainDashboard.jsx`:

```jsx
import React, { useState, useEffect, useMemo } from 'react';
import {
  Grid, Card, CardContent, Typography, Box,
  Alert, Chip, LinearProgress
} from '@mui/material';
import {
  TrendingUp, Security, Warning, Assessment
} from '@mui/icons-material';
import {
  LineChart, BarChart, PieChart, 
  ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts';
import websocketService from '../../services/websocketService';

const MainDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState(false);

  useEffect(() => {
    // Subscribe to main dashboard updates
    websocketService.subscribe('main_dashboard_update', (data) => {
      setDashboardData(data);
      setLoading(false);
    });

    websocketService.onConnectionChange = setConnectionStatus;
    websocketService.connect();
    websocketService.configureDashboard('main', 15); // 15-second updates

    return () => {
      // Cleanup subscriptions
    };
  }, []);

  const riskColor = useMemo(() => {
    if (!dashboardData?.executive_summary) return 'info';
    const risk = dashboardData.executive_summary.risk_score;
    if (risk >= 70) return 'error';
    if (risk >= 40) return 'warning';
    return 'success';
  }, [dashboardData]);

  if (loading) {
    return <LoadingDashboard />;
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Connection Status Alert */}
      {!connectionStatus && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          WebSocket disconnected - Dashboard may show stale data
        </Alert>
      )}

      {/* Executive Risk Summary */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Executive Risk Score
              </Typography>
              <Box display="flex" alignItems="center">
                <Typography
                  variant="h2"
                  color={`${riskColor}.main`}
                  fontWeight="bold"
                >
                  {dashboardData?.executive_summary?.risk_score || 0}
                </Typography>
                <Chip
                  label={dashboardData?.executive_summary?.risk_level || 'LOW'}
                  color={riskColor}
                  sx={{ ml: 2 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top 3 Active Threats
              </Typography>
              {dashboardData?.executive_summary?.active_threats?.map((threat, index) => (
                <ThreatItem key={index} threat={threat} rank={index + 1} />
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Key Metrics Row */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Data Exfiltration Attempts"
            value={dashboardData?.executive_summary?.data_exfiltration_attempts || 0}
            icon={<Security />}
            color="error"
          />
        </Grid>
        {/* More metric cards... */}
      </Grid>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Guardrail Effectiveness Trend
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dashboardData?.charts_data?.guardrail_trend || []}>
                    <XAxis dataKey="time" />
                    <YAxis />
                    <CartesianGrid strokeDasharray="3 3" />
                    <Tooltip />
                    {/* Chart components... */}
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detected Sensitive Data by Type
              </Typography>
              <Box height={300}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    {/* Pie chart implementation... */}
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bottom Row - Risk Entities and Provider Analysis */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <TopRiskEntities entities={dashboardData?.top_risk_entities || []} />
        </Grid>

        <Grid item xs={12} md={6}>
          <ProviderAnalysisTable data={dashboardData?.charts_data?.provider_analysis || []} />
        </Grid>
      </Grid>
    </Box>
  );
};
```

#### Key Features to Implement:
1. **Executive Risk Summary** - Color-coded risk score (0-100)
2. **Top 3 Active Threats** - Real-time threat list
3. **Data Exfiltration Counter** - Prominent PII/Privacy triggers
4. **Interactive Charts** - Recharts with time range selection
5. **Deep Forensics** - Clickable entities for detailed views
6. **Real-time Updates** - WebSocket-driven data refresh

**Edge Cases to Handle:**
- Missing or null data fields
- Chart rendering with empty datasets
- Websocket disconnection during use
- Invalid chart data formats
- Large dataset performance
- Browser memory management

**Testing:**
- [ ] Dashboard renders without errors
- [ ] Charts display correctly with sample data
- [ ] WebSocket updates refresh display
- [ ] Error handling for malformed data
- [ ] Performance with large datasets
- [ ] Responsive design works on all screen sizes

---

### 3.4 User-Info Dashboard
**Status: [ ] Not Started**
**Estimated Time: 10-12 hours**

#### Component Structure:

1. **UserList.jsx** - Main user list view
2. **UserDetail.jsx** - Individual user drill-down
3. **UserDashboard.jsx** - Container component

```jsx
// UserDashboard.jsx
const UserDashboard = () => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [overviewStats, setOverviewStats] = useState({});

  useEffect(() => {
    websocketService.subscribe('user_dashboard_update', (data) => {
      setUsers(data.users_list);
      setOverviewStats(data.overview_stats);
    });

    websocketService.subscribe('user_detail_response', (data, fullMessage) => {
      if (fullMessage.user_id === selectedUser?.user_id) {
        setSelectedUser({
          ...selectedUser,
          detailData: data
        });
      }
    });
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      {/* Overview Dashboard */}
      <UserOverviewDashboard stats={overviewStats} />

      {/* User List */}
      <UserList 
        users={users} 
        onUserSelect={(user) => {
          setSelectedUser(user);
          websocketService.requestUserDetail(user.user_id);
        }}
        selectedUserId={selectedUser?.user_id}
      />

      {/* User Detail Drawer */}
      {selectedUser && (
        <UserDetailDrawer
          user={selectedUser}
          open={Boolean(selectedUser)}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </Box>
  );
};
```

#### Key Features:
1. **Sortable User List** - Risk score, activity, blocked %
2. **User Detail Drawer** - Slides out from right
3. **Activity Timeline Chart** - User's request patterns
4. **Violation Breakdown** - Donut chart of violation categories
5. **Detailed Activity Log** - Table with prompt fingerprints
6. **Export Functionality** - CSV export for analysts

**Edge Cases to Handle:**
- Large user lists (virtualization)
- User detail loading states
- Drawer performance with large datasets
- Sort/filter performance
- Export timeout for large datasets

**Testing:**
- [ ] User list loads and displays correctly
- [ ] Sorting and filtering work
- [ ] User detail drawer opens/closes
- [ ] Activity timeline renders correctly
- [ ] Export functionality works
- [ ] Performance with 1000+ users

---

## Phase 4: Advanced Features & Testing ✅

### 4.1 Risk Calculation Engine
**Status: [ ] Not Started**
**Estimated Time: 3-4 hours**

#### Algorithm Implementation:
Create `LLMinate/src/utils/riskCalculation.js`:

```javascript
export class RiskCalculator {
  static calculateExecutiveRiskScore(data) {
    const weights = {
      dataExfiltration: 0.4,      // 40%
      promptInjection: 0.3,       // 30%
      blockedRequests: 0.2,       // 20%
      guardrailTrend: 0.1         // 10%
    };

    // Normalize each metric to 0-100 scale
    const dataExfiltrationScore = Math.min(100, 
      (data.dataExfiltrationAttempts / data.totalRequests) * 500
    );

    const promptInjectionScore = Math.min(100,
      (data.promptInjectionAttempts / data.totalRequests) * 400
    );

    const blockedRequestsScore = Math.min(100,
      (data.blockedRequests / data.totalRequests) * 200
    );

    const trendScore = data.guardrailTrendSlope < 0 ? 100 : 0;

    const riskScore = Math.round(
      (dataExfiltrationScore * weights.dataExfiltration) +
      (promptInjectionScore * weights.promptInjection) +
      (blockedRequestsScore * weights.blockedRequests) +
      (trendScore * weights.guardrailTrend)
    );

    return Math.min(100, Math.max(0, riskScore));
  }

  static calculateUserRiskScore(userData) {
    // User-specific risk calculation
    // Based on: blocked percentage, violation severity, frequency
    const blockedPercentage = (userData.blockedRequests / userData.totalRequests) * 100;
    const violationSeverity = this.calculateViolationSeverity(userData.violationTypes);
    const frequencyScore = this.calculateFrequencyScore(userData.requestPattern);

    return Math.min(100, Math.max(0, 
      (blockedPercentage * 0.5) + 
      (violationSeverity * 0.3) + 
      (frequencyScore * 0.2)
    ));
  }
}
```

**Testing:**
- [ ] Risk scores calculate correctly
- [ ] Edge cases (division by zero, null values)
- [ ] Score ranges stay within 0-100
- [ ] Performance with large datasets

---

### 4.2 Comprehensive Testing Strategy
**Status: [ ] Not Started**
**Estimated Time: 8-10 hours**

#### Test Categories:

1. **Unit Tests**:
   - Risk calculation algorithms
   - Data processing utilities
   - WebSocket message handlers
   - Chart data transformations

2. **Integration Tests**:
   - WebSocket connection flow
   - Database aggregation service
   - Frontend-backend message flow
   - Chart rendering with real data

3. **Performance Tests**:
   - WebSocket under high message volume
   - Dashboard rendering with large datasets
   - Database aggregation performance
   - Memory usage over extended periods

4. **Edge Case Tests**:
   - Network disconnection/reconnection
   - Malformed WebSocket messages
   - Empty/null datasets
   - Browser refresh during active connection
   - Concurrent user detail requests

#### Test Implementation:
```bash
# Backend tests
cd backend
python -m pytest tests/test_aggregation_service.py -v
python -m pytest tests/test_websocket_routing.py -v

# Frontend tests  
cd LLMinate
npm test -- --coverage
npm run test:integration
```

**Testing Checklist:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Performance benchmarks met
- [ ] Edge cases handled gracefully
- [ ] No memory leaks detected
- [ ] Cross-browser compatibility verified

---

### 4.3 Production Deployment Checklist
**Status: [ ] Not Started**
**Estimated Time: 2-3 hours**

#### Deployment Requirements:
1. **Environment Configuration**:
   - WebSocket URL configuration
   - Database connection settings
   - Logging configuration
   - Error tracking setup

2. **Performance Optimization**:
   - Build optimization
   - Code splitting
   - Lazy loading for heavy components
   - WebSocket connection pooling

3. **Security Measures**:
   - WebSocket authentication
   - Rate limiting
   - Input validation
   - XSS protection

4. **Monitoring & Alerts**:
   - WebSocket connection monitoring
   - Dashboard performance metrics
   - Error rate tracking
   - Database performance monitoring

**Deployment Checklist:**
- [ ] Environment variables configured
- [ ] Build process optimized
- [ ] Security measures implemented
- [ ] Monitoring tools configured
- [ ] Performance benchmarks met
- [ ] Rollback plan prepared

---

## Implementation Timeline

### Week 1: Backend Foundation
- **Days 1-2**: Database restructuring & new tables
- **Days 3-5**: Background aggregation service
- **Days 6-7**: WebSocket message routing system

### Week 2: Frontend Development  
- **Days 1-2**: Project setup & WebSocket service
- **Days 3-5**: Main CISO Dashboard implementation
- **Days 6-7**: User-Info Dashboard implementation

### Week 3: Advanced Features & Testing
- **Days 1-2**: Risk calculation engine & advanced features
- **Days 3-5**: Comprehensive testing & bug fixes
- **Days 6-7**: Production deployment & monitoring

---

## Risk Mitigation Strategies

### Technical Risks:
1. **WebSocket Connection Stability**
   - **Mitigation**: Robust reconnection logic, message queuing
   
2. **Database Performance Under Load**
   - **Mitigation**: Proper indexing, query optimization, connection pooling
   
3. **Frontend Performance with Large Datasets**
   - **Mitigation**: Virtualization, pagination, lazy loading

### Business Risks:
1. **Data Privacy Concerns**
   - **Mitigation**: Prompt context fingerprinting, data retention policies
   
2. **Dashboard Accuracy**
   - **Mitigation**: Comprehensive testing, data validation, audit trails

---

## Success Metrics

### Performance Metrics:
- Dashboard load time < 2 seconds
- WebSocket message latency < 100ms
- Database aggregation time < 5 minutes
- Support for 100+ concurrent users

### Functional Metrics:
- All risk calculations accurate to ±5%
- 99.9% WebSocket uptime
- Zero data loss during network interruptions
- All edge cases handled gracefully

---

## Notes & Decisions Log

### Technical Decisions:
1. **Single WebSocket Connection**: Chosen for simplicity and reduced infrastructure overhead
2. **MUI + Recharts**: Maintains consistency with existing frontend
3. **SQLite with New Tables**: Balances performance with operational simplicity
4. **Pre-computed Aggregations**: Essential for dashboard responsiveness

### Open Questions:
1. **User Authentication Integration**: How to integrate with existing auth system?
2. **Data Retention Policies**: Specific compliance requirements?
3. **Alert Thresholds**: What risk scores should trigger alerts?
4. **Export Formats**: Besides CSV, what other formats needed?

---

## Implementation Status Tracking

| Phase | Component | Status | Completion Date | Notes |
|-------|-----------|--------|-----------------|-------|
| 1.1 | Database Tables | ⏳ Not Started | | |
| 1.2 | Aggregation Service | ⏳ Not Started | | |
| 2.1 | WebSocket Routing | ⏳ Not Started | | |
| 3.1 | Project Setup | ⏳ Not Started | | |
| 3.2 | WebSocket Service | ⏳ Not Started | | |
| 3.3 | Main Dashboard | ⏳ Not Started | | |
| 3.4 | User Dashboard | ⏳ Not Started | | |
| 4.1 | Risk Engine | ⏳ Not Started | | |
| 4.2 | Testing | ⏳ Not Started | | |
| 4.3 | Deployment | ⏳ Not Started | | |

**Legend**: ✅ Complete | 🔄 In Progress | ⏳ Not Started | ❌ Blocked

---

*Last Updated: 2025-08-07*
*Next Review Date: TBD*