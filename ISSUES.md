# NemoGuardrails System Issues & Bug Report

## 📋 Overview

This document contains a comprehensive list of 47 identified issues, edge cases, and potential bugs found in the NemoGuardrails codebase through systematic analysis. Issues are prioritized by severity and impact on system functionality.

**Last Updated**: July 31, 2025  
**Analysis Coverage**: Backend (Python/FastAPI), Frontend (React/TypeScript), Configuration, Scripts

---

## 🚨 CRITICAL PRIORITY (Fix Immediately)

### 1. Provider Service Race Condition
- **File**: `/backend/app/services/provider_service.py:516-580`
- **Issue**: Multiple async tasks can simultaneously start/stop the same provider server
- **Impact**: Port conflicts, zombie processes, corrupted provider state
- **Root Cause**: `_start_provider_server()` and `_stop_provider_server()` lack proper locking mechanisms
- **Fix Effort**: High (2-3 days)
- **Workaround**: Restart backend if providers get stuck

### 2. Provider State Desynchronization 
- **File**: `/frontend/src/hooks/useProviders.ts:183-219`
- **Issue**: Frontend immediately updates UI state before backend confirmation
- **Impact**: UI shows provider as enabled when backend failed to start it (same as dropdown issue)
- **Root Cause**: Optimistic updates without proper rollback mechanism
- **Fix Effort**: Medium (1-2 days)
- **Workaround**: Refresh page after provider operations

### 3. API Key Logging Security Risk
- **File**: `/backend/app/services/provider_service.py:462-473`
- **Issue**: API key updates might be logged in debug mode
- **Impact**: Credential exposure in logs - SECURITY VULNERABILITY
- **Root Cause**: Debug logging includes sensitive configuration data
- **Fix Effort**: Low (2-4 hours)
- **Workaround**: Disable debug logging in production

### 4. Model Manager Detector Loading Race
- **File**: `/backend/app/models/model_manager.py:70-115`
- **Issue**: Concurrent detector loading can cause memory corruption
- **Impact**: Detector failures, inconsistent state, memory leaks
- **Root Cause**: Multiple requests can trigger `load_detector()` simultaneously without locks
- **Fix Effort**: Medium (1-2 days)
- **Workaround**: Avoid rapid detector enable/disable operations

---

## ⚠️ HIGH PRIORITY (Fix This Sprint)

### 5. Chat Service Session Collision
- **File**: `/backend/app/services/chat_service.py:48-56`
- **Issue**: Session initialization race when multiple messages arrive simultaneously
- **Impact**: Lost messages, corrupted chat history, session confusion
- **Root Cause**: Session creation not atomic
- **Fix Effort**: Medium (1 day)

### 6. Detector Config Drift
- **File**: `/frontend/src/hooks/useApi.ts:116-127`
- **Issue**: Frontend detector config diverges from backend reality
- **Impact**: Detectors thought to be enabled may actually be disabled
- **Root Cause**: No state reconciliation mechanism
- **Fix Effort**: Medium (1-2 days)

### 7. Model Manager State Inconsistency
- **File**: `/backend/app/models/model_manager.py:317-321`
- **Issue**: Active detectors set can differ from actually loaded detectors
- **Impact**: Runtime failures when trying to use "active" but unloaded detectors
- **Root Cause**: State tracking inconsistency
- **Fix Effort**: Medium (1 day)

### 8. Detector Status UI Mismatch
- **File**: `/frontend/src/hooks/useApi.ts:116-127`
- **Issue**: Frontend shows detectors as enabled when backend hasn't confirmed loading
- **Impact**: Users think detectors are running when they're actually failed
- **Root Cause**: Same optimistic update pattern as provider dropdown
- **Fix Effort**: Medium (1-2 days)

### 9. Model Loading State Confusion
- **File**: `/frontend/src/App.tsx:302-304`
- **Issue**: UI shows models as "available" based on static list, not actual backend state
- **Impact**: Users select models that aren't actually loaded
- **Root Cause**: Frontend assumes backend state without verification
- **Fix Effort**: Medium (1 day)

### 10. CORS Wildcard Configuration
- **File**: `/backend/app/main.py:596-608`
- **Issue**: CORS allows "*" which is overly permissive
- **Impact**: Potential CSRF attacks - SECURITY VULNERABILITY
- **Root Cause**: Development CORS settings in production
- **Fix Effort**: Low (1 hour)

---

## 🔧 MEDIUM PRIORITY (Fix Next Sprint)

### 11. Missing Network Timeout Recovery
- **File**: `/frontend/src/services/api.ts:18-24`
- **Issue**: 30-second timeout but no retry logic for transient failures
- **Impact**: Users see errors for temporary network issues
- **Root Cause**: No retry mechanism implemented
- **Fix Effort**: Low (4-6 hours)

### 12. Provider Test Connection False Positives
- **File**: `/backend/app/services/provider_service.py:171-207`
- **Issue**: Connection test passes but actual generation fails
- **Impact**: Users think provider works but chat fails silently
- **Root Cause**: Test only checks API endpoints, not actual generation
- **Fix Effort**: Medium (1 day)

### 13. Chat Service Exception Swallowing
- **File**: `/backend/app/services/chat_service.py:202-210`
- **Issue**: Detection errors are caught but processing continues with stale state
- **Impact**: Users receive responses that bypassed safety checks
- **Root Cause**: Overly broad exception handling
- **Fix Effort**: Medium (1 day)

### 14. WebSocket Service Memory Leak
- **File**: `/frontend/src/services/websocket.ts:178-199`
- **Issue**: Simulated log generation intervals never get cleared
- **Impact**: Memory usage grows indefinitely
- **Root Cause**: Missing cleanup in component unmount
- **Fix Effort**: Low (2-4 hours)

### 15. Provider Server Cleanup Failure
- **File**: `/backend/app/services/provider_service.py:582-616`
- **Issue**: Server tasks may not be properly cancelled on shutdown
- **Impact**: Zombie processes consuming ports and resources
- **Root Cause**: Incomplete async task cleanup
- **Fix Effort**: Medium (1 day)

### 16. Model Cache Unbounded Growth
- **File**: `/backend/app/models/model_manager.py:393-417`
- **Issue**: GPU accelerator cache has no size limits or eviction policy
- **Impact**: Memory exhaustion over time
- **Root Cause**: No cache management strategy
- **Fix Effort**: Medium (1 day)

### 17. Missing Session ID Validation
- **File**: `/backend/app/services/chat_service.py:44-46`
- **Issue**: No validation of session ID format or length
- **Impact**: Potential storage issues or injection attacks
- **Root Cause**: Missing input validation
- **Fix Effort**: Low (2-4 hours)

### 18. Provider Port Range Validation
- **File**: `/backend/app/services/provider_service.py:353-359`
- **Issue**: Port scanning doesn't validate against reserved/system ports
- **Impact**: Potential conflicts with system services
- **Root Cause**: No port range restrictions
- **Fix Effort**: Low (2-4 hours)

### 19. Detector Config Type Safety
- **File**: `/backend/app/models/model_manager.py:323-327`
- **Issue**: Detector config updates lack type checking
- **Impact**: Runtime errors from malformed configuration
- **Root Cause**: Dynamic configuration without validation
- **Fix Effort**: Medium (1 day)

### 20. Session ID Predictability
- **File**: `/backend/app/services/chat_service.py:45-46`
- **Issue**: UUID4 session IDs could be more secure for sensitive deployments
- **Impact**: Potential session hijacking in high-security environments
- **Root Cause**: Standard UUID4 instead of cryptographically secure tokens
- **Fix Effort**: Low (2-4 hours)

### 21. WebSocket Fallback Logic Missing
- **File**: `/frontend/src/services/websocket.ts:22-43`
- **Issue**: No graceful fallback when WebSocket connection fails
- **Impact**: Real-time features completely break
- **Root Cause**: No fallback to polling when WebSocket unavailable
- **Fix Effort**: Medium (1 day)

### 22. Backend Health Check False Positives
- **File**: `/backend/app/main.py:669-741`
- **Issue**: Health endpoint returns "healthy" even when critical components fail
- **Impact**: Load balancers don't properly route traffic
- **Root Cause**: Health check doesn't validate all critical services
- **Fix Effort**: Medium (1 day)

### 23. Incomplete Cleanup on Shutdown
- **File**: `/backend/app/main.py:270-289`
- **Issue**: Not all background tasks are properly cancelled
- **Impact**: Resource leaks, corrupted state on restart
- **Root Cause**: Missing cleanup handlers for all async tasks
- **Fix Effort**: Medium (1 day)

### 24. Startup Order Dependencies
- **File**: `/backend/app/main.py:142-267`
- **Issue**: Service initialization order is fragile
- **Impact**: Random startup failures depending on timing
- **Root Cause**: Services have undocumented dependencies
- **Fix Effort**: Medium (1-2 days)

### 25. Direct Service Dependencies
- **File**: `/backend/app/main.py:56-61`
- **Issue**: Global service instances create tight coupling
- **Impact**: Difficult testing, circular dependencies
- **Root Cause**: Services directly reference each other
- **Fix Effort**: High (3-5 days)

### 26. Frontend State Management Chaos
- **File**: Multiple components in `/frontend/src/components/`
- **Issue**: No centralized state management, multiple sources of truth
- **Impact**: State synchronization nightmares
- **Root Cause**: No state management framework (Redux/Zustand)
- **Fix Effort**: High (1-2 weeks)

### 27. In-Memory Session Storage
- **File**: `/backend/app/services/chat_service.py:15-16`
- **Issue**: Chat history stored in memory without persistence
- **Impact**: Data loss on restart, memory growth
- **Root Cause**: No persistent storage for sessions
- **Fix Effort**: Medium (2-3 days)

### 28. No Graceful Degradation State Persistence
- **File**: `/backend/app/main.py:323-373`
- **Issue**: Degradation state is lost on restart
- **Impact**: Service doesn't remember why it was degraded
- **Root Cause**: Degradation state not persisted
- **Fix Effort**: Medium (1-2 days)

### 29. Provider Configuration Drift
- **File**: `/backend/app/services/provider_service.py:461-487`
- **Issue**: API key changes aren't persisted across restarts
- **Impact**: Users must re-enter credentials after restart
- **Root Cause**: Configuration only stored in memory
- **Fix Effort**: Medium (1-2 days)

### 30. Provider Integration Test Gaps
- **File**: `/backend/app/services/provider_service.py:209-281`
- **Issue**: Provider tests only check API endpoints, not actual generation
- **Impact**: Providers show as "working" but fail during real use
- **Root Cause**: Shallow integration testing
- **Fix Effort**: Medium (2-3 days)

### 31. Detector Loading Inefficiency
- **File**: `/backend/app/models/model_manager.py:117-170`
- **Issue**: Models loaded synchronously, blocking other operations
- **Impact**: Long initialization times, poor user experience
- **Root Cause**: Synchronous model loading
- **Fix Effort**: Medium (1-2 days)

### 32. Environment-Specific Configuration Issues
- **File**: `/backend/configs/app_config.yml:14-27`
- **Issue**: No environment-specific config override mechanism
- **Impact**: Deployment complexity, configuration drift
- **Root Cause**: Single configuration file for all environments
- **Fix Effort**: Medium (1-2 days)

### 33. Port Conflict Resolution Strategy
- **File**: `/backend/app/services/provider_service.py:421-459`
- **Issue**: Port conflict resolution is complex and error-prone
- **Impact**: Provider startup failures in containerized environments
- **Root Cause**: Complex port management logic
- **Fix Effort**: High (2-3 days)

---

## 📝 LOW PRIORITY (Fix When Time Permits)

### 34. Default Config Overwrite
- **File**: `/backend/configs/app_config.yml:32-53`
- **Issue**: Some detectors are disabled by default but code assumes they're enabled
- **Impact**: Inconsistent behavior between fresh installs and configured systems
- **Root Cause**: Configuration vs code assumptions mismatch
- **Fix Effort**: Low (2-4 hours)

### 35. Environment Variable Priority
- **File**: `/frontend/src/hooks/useProviders.ts:46`
- **Issue**: Hardcoded backend URL takes precedence over environment variables
- **Impact**: Deployment configuration issues
- **Root Cause**: Hardcoded fallback overrides env vars
- **Fix Effort**: Low (1 hour)

### 36. Optimistic UI Updates Without Rollback
- **File**: `/frontend/src/hooks/useProviders.ts:194-206`
- **Issue**: Multiple places update UI optimistically but don't handle failures properly
- **Impact**: Confusing user experience
- **Root Cause**: Pattern repeated across multiple components
- **Fix Effort**: Medium (1-2 days)

### 37. Loading State Inconsistencies
- **File**: `/frontend/src/App.tsx:154-198`
- **Issue**: Loading states don't consistently reflect actual backend operations
- **Impact**: Users see "loaded" states for failed operations
- **Root Cause**: Loading state not properly synchronized
- **Fix Effort**: Low (4-6 hours)

### 38. Missing Critical Error Alerts
- **File**: `/backend/app/main.py:258-266`
- **Issue**: Initialization failures are logged but don't trigger alerts
- **Impact**: Silent failures in production environments
- **Root Cause**: No alerting system for critical errors
- **Fix Effort**: Medium (1 day)

### 39. Blocking Synchronous Operations
- **File**: `/backend/app/services/provider_service.py:296-351`
- **Issue**: Port checking and process inspection are synchronous
- **Impact**: UI freezes during provider operations
- **Root Cause**: Blocking operations in async context
- **Fix Effort**: Medium (1 day)

### 40. Excessive Real-time Polling
- **File**: `/frontend/src/hooks/useRealTime.ts:46-48`
- **Issue**: Frontend polls backend logs every 2 seconds regardless of activity
- **Impact**: Unnecessary network traffic and battery drain
- **Root Cause**: Fixed polling interval without optimization
- **Fix Effort**: Low (2-4 hours)

### 41. Chat History Linear Search
- **File**: `/backend/app/services/chat_service.py:398-411`
- **Issue**: Chat history retrieval uses linear search
- **Impact**: Performance degrades with long conversations
- **Root Cause**: No indexing for chat history
- **Fix Effort**: Low (4-6 hours)

### 42. Frontend Bootstrap Race Conditions
- **File**: `/frontend/src/App.tsx:122-127`
- **Issue**: Multiple useEffect hooks compete for initialization
- **Impact**: Inconsistent initial state
- **Root Cause**: Uncoordinated component initialization
- **Fix Effort**: Medium (1 day)

### 43. No Offline Capability
- **File**: Frontend components lack offline state handling
- **Issue**: No graceful degradation when backend is unavailable
- **Impact**: Poor user experience during network issues
- **Root Cause**: No offline state management
- **Fix Effort**: High (1-2 weeks)

### 44. Inconsistent Error Messages
- **File**: Various API endpoints and UI components
- **Issue**: Error messages vary in format and detail level
- **Impact**: Confusing user experience
- **Root Cause**: No standardized error message format
- **Fix Effort**: Medium (2-3 days)

### 45. Missing Edge Case Testing
- **File**: Various test files in `/backend/`
- **Issue**: Tests don't cover concurrent operations, resource exhaustion
- **Impact**: Edge cases discovered in production
- **Root Cause**: Insufficient test coverage
- **Fix Effort**: High (1-2 weeks)

### 46. Missing Distributed Tracing
- **File**: Request flow across services lacks correlation IDs consistency
- **Issue**: Difficult to trace requests across service boundaries
- **Impact**: Hard to debug issues in production
- **Root Cause**: No distributed tracing implementation
- **Fix Effort**: High (1-2 weeks)

### 47. Inadequate Metrics Collection
- **File**: `/backend/app/utils/performance_monitor.py` (referenced but not shown)
- **Issue**: Missing business-level metrics (success rates, detector effectiveness)
- **Impact**: Limited visibility into system health
- **Root Cause**: Monitoring focuses on technical, not business metrics
- **Fix Effort**: Medium (1 week)

---

## 📊 Issue Summary Statistics

| **Priority** | **Count** | **Estimated Fix Time** |
|-------------|-----------|------------------------|
| **Critical** | 4 issues | 1-2 weeks |
| **High** | 6 issues | 1-2 weeks |
| **Medium** | 23 issues | 4-6 weeks |
| **Low** | 14 issues | 2-4 weeks |
| **TOTAL** | **47 issues** | **8-14 weeks** |

## 🎯 Recommended Fix Order

### **Week 1: Critical Fixes**
1. API Key Logging Security Risk (2-4 hours)
2. CORS Wildcard Configuration (1 hour)
3. Provider State Desynchronization (1-2 days)
4. Provider Service Race Condition (2-3 days)

### **Week 2: High Priority State Issues**
1. Detector Status UI Mismatch (1-2 days)
2. Model Loading State Confusion (1 day)
3. Detector Config Drift (1-2 days)
4. Model Manager State Inconsistency (1 day)

### **Week 3-4: Critical Functionality**
1. Chat Service Session Collision (1 day)
2. Missing Network Timeout Recovery (4-6 hours)
3. Provider Test Connection False Positives (1 day)
4. Chat Service Exception Swallowing (1 day)

### **Ongoing: Medium Priority Fixes**
- Address medium priority issues based on user impact
- Focus on memory leaks and performance issues
- Improve error handling and validation

This prioritization ensures that critical security vulnerabilities and the most impactful user experience issues (like the provider dropdown problem) are addressed first, followed by systematic improvement of system reliability and performance.