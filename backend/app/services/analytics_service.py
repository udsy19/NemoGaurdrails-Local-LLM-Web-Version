"""
Analytics Service for tracking requests, blocks, and user activity
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import ipaddress
from enum import Enum

logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ERROR = "error"

@dataclass
class RequestEvent:
    id: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    message: str
    status: RequestStatus
    blocking_reasons: List[str]
    detection_results: Dict[str, Any]
    response_time_ms: float
    provider: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class UserSession:
    ip_address: str
    first_seen: datetime
    last_seen: datetime
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    user_agent: str
    sessions: Set[str]

@dataclass
class DetectorStats:
    name: str
    total_detections: int
    blocked_count: int
    allowed_count: int
    avg_confidence: float
    last_triggered: Optional[datetime]

@dataclass
class AnalyticsSummary:
    timeframe_hours: int
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    unique_users: int
    unique_ips: int
    top_blocking_reasons: List[Dict[str, Any]]
    detector_stats: List[DetectorStats]
    request_timeline: List[Dict[str, Any]]
    user_activity: List[Dict[str, Any]]
    geographic_data: List[Dict[str, Any]]
    error_rate: float
    avg_response_time: float

class AnalyticsService:
    """Comprehensive analytics and monitoring service"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events: deque = deque(maxlen=max_events)
        self.users: Dict[str, UserSession] = {}
        self.detector_stats: Dict[str, DetectorStats] = {}
        self.lock = threading.RLock()
        
        # Real-time counters
        self.total_requests = 0
        self.blocked_requests = 0
        self.allowed_requests = 0
        self.error_requests = 0
        
        # Performance tracking
        self.response_times: deque = deque(maxlen=1000)
        
        logger.info("Analytics service initialized")
    
    def track_request(
        self,
        ip_address: str,
        user_agent: str,
        message: str,
        status: RequestStatus,
        blocking_reasons: List[str] = None,
        detection_results: Dict[str, Any] = None,
        response_time_ms: float = 0.0,
        provider: str = None,
        model: str = None,
        session_id: str = None
    ) -> str:
        """Track a new request event"""
        
        with self.lock:
            # Generate unique event ID
            event_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create event
            event = RequestEvent(
                id=event_id,
                timestamp=datetime.now(),
                ip_address=ip_address,
                user_agent=user_agent,
                message=message,
                status=status,
                blocking_reasons=blocking_reasons or [],
                detection_results=detection_results or {},
                response_time_ms=response_time_ms,
                provider=provider,
                model=model,
                session_id=session_id
            )
            
            # Add to events
            self.events.append(event)
            
            # Update counters
            self.total_requests += 1
            if status == RequestStatus.BLOCKED:
                self.blocked_requests += 1
            elif status == RequestStatus.ALLOWED:
                self.allowed_requests += 1
            elif status == RequestStatus.ERROR:
                self.error_requests += 1
            
            # Track response time
            if response_time_ms > 0:
                self.response_times.append(response_time_ms)
            
            # Update user tracking
            self._update_user_session(event)
            
            # Update detector statistics
            self._update_detector_stats(event)
            
            logger.debug(f"Tracked request {event_id} from {ip_address}: {status.value}")
            return event_id
    
    def _update_user_session(self, event: RequestEvent):
        """Update user session tracking"""
        ip = event.ip_address
        
        if ip not in self.users:
            self.users[ip] = UserSession(
                ip_address=ip,
                first_seen=event.timestamp,
                last_seen=event.timestamp,
                total_requests=0,
                blocked_requests=0,
                allowed_requests=0,
                user_agent=event.user_agent,
                sessions=set()
            )
        
        user = self.users[ip]
        user.last_seen = event.timestamp
        user.total_requests += 1
        
        if event.status == RequestStatus.BLOCKED:
            user.blocked_requests += 1
        elif event.status == RequestStatus.ALLOWED:
            user.allowed_requests += 1
        
        if event.session_id:
            user.sessions.add(event.session_id)
    
    def _is_detection_blocked(self, result):
        """Helper method to check if a detection result indicates blocking"""
        if isinstance(result, dict):
            # Check various blocking indicators
            return (
                result.get('blocked', False) or
                result.get('is_toxic', False) or
                result.get('has_pii', False) or
                result.get('is_injection', False) or
                result.get('has_restricted_topic', False) or
                result.get('is_spam', False) or
                result.get('needs_fact_check', False)
            )
        elif isinstance(result, bool):
            return result
        else:
            return False
    
    def _update_detector_stats(self, event: RequestEvent):
        """Update detector statistics"""
        if not event.detection_results:
            return
        
        # Handle different detection result formats
        detection_data = event.detection_results
        
        # If detection_results has a 'results' key, use that
        if 'results' in detection_data:
            detection_data = detection_data['results']
        
        for detector_name, result in detection_data.items():
            if detector_name not in self.detector_stats:
                self.detector_stats[detector_name] = DetectorStats(
                    name=detector_name,
                    total_detections=0,
                    blocked_count=0,
                    allowed_count=0,
                    avg_confidence=0.0,
                    last_triggered=None
                )
            
            stats = self.detector_stats[detector_name]
            stats.total_detections += 1
            
            if isinstance(result, dict):
                confidence = result.get('confidence', 0.0)
                
                # Check various blocking indicators
                blocked = (
                    result.get('blocked', False) or
                    result.get('is_toxic', False) or
                    result.get('has_pii', False) or
                    result.get('is_injection', False) or
                    result.get('has_restricted_topic', False) or
                    result.get('is_spam', False) or
                    result.get('needs_fact_check', False)
                )
                
                # Update confidence (running average)
                if stats.total_detections == 1:
                    stats.avg_confidence = confidence
                else:
                    stats.avg_confidence = (
                        (stats.avg_confidence * (stats.total_detections - 1) + confidence) / 
                        stats.total_detections
                    )
                
                if blocked:
                    stats.blocked_count += 1
                    stats.last_triggered = event.timestamp
                else:
                    stats.allowed_count += 1
            elif isinstance(result, bool):
                # Handle boolean results
                if result:
                    stats.blocked_count += 1
                    stats.last_triggered = event.timestamp
                else:
                    stats.allowed_count += 1
    
    def get_analytics_summary(self, hours: int = 24) -> AnalyticsSummary:
        """Get comprehensive analytics summary"""
        
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
            
            # Basic metrics
            total_requests = len(recent_events)
            blocked_requests = len([e for e in recent_events if e.status == RequestStatus.BLOCKED])
            allowed_requests = len([e for e in recent_events if e.status == RequestStatus.ALLOWED])
            error_requests = len([e for e in recent_events if e.status == RequestStatus.ERROR])
            
            # User metrics
            unique_ips = len(set(e.ip_address for e in recent_events))
            unique_sessions = len(set(e.session_id for e in recent_events if e.session_id))
            
            # Top blocking reasons
            blocking_reasons = defaultdict(int)
            for event in recent_events:
                if event.status == RequestStatus.BLOCKED:
                    for reason in event.blocking_reasons:
                        blocking_reasons[reason] += 1
            
            top_blocking_reasons = [
                {"reason": reason, "count": count}
                for reason, count in sorted(blocking_reasons.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Detector statistics
            detector_stats_list = []
            for detector_name, stats in self.detector_stats.items():
                # Filter for recent activity
                recent_detections = [
                    e for e in recent_events 
                    if detector_name in e.detection_results
                ]
                
                if recent_detections:
                    recent_blocked = len([
                        e for e in recent_detections
                        if self._is_detection_blocked(e.detection_results.get(detector_name, {}))
                    ])
                    
                    detector_stats_list.append(DetectorStats(
                        name=detector_name,
                        total_detections=len(recent_detections),
                        blocked_count=recent_blocked,
                        allowed_count=len(recent_detections) - recent_blocked,
                        avg_confidence=stats.avg_confidence,
                        last_triggered=stats.last_triggered
                    ))
            
            # Request timeline (hourly buckets)
            timeline = self._generate_timeline(recent_events, hours)
            
            # User activity
            user_activity = self._generate_user_activity(recent_events)
            
            # Geographic data (simplified - just top countries by IP)
            geographic_data = self._generate_geographic_data(recent_events)
            
            # Performance metrics
            error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            return AnalyticsSummary(
                timeframe_hours=hours,
                total_requests=total_requests,
                blocked_requests=blocked_requests,
                allowed_requests=allowed_requests,
                unique_users=unique_sessions,
                unique_ips=unique_ips,
                top_blocking_reasons=top_blocking_reasons,
                detector_stats=detector_stats_list,
                request_timeline=timeline,
                user_activity=user_activity,
                geographic_data=geographic_data,
                error_rate=error_rate,
                avg_response_time=avg_response_time
            )
    
    def _generate_timeline(self, events: List[RequestEvent], hours: int) -> List[Dict[str, Any]]:
        """Generate hourly timeline data"""
        timeline = []
        now = datetime.now()
        
        for i in range(hours):
            hour_start = now - timedelta(hours=i+1)
            hour_end = now - timedelta(hours=i)
            
            hour_events = [
                e for e in events 
                if hour_start <= e.timestamp < hour_end
            ]
            
            timeline.append({
                "hour": hour_start.strftime("%Y-%m-%d %H:00"),
                "timestamp": hour_start.isoformat(),
                "total_requests": len(hour_events),
                "blocked_requests": len([e for e in hour_events if e.status == RequestStatus.BLOCKED]),
                "allowed_requests": len([e for e in hour_events if e.status == RequestStatus.ALLOWED]),
                "error_requests": len([e for e in hour_events if e.status == RequestStatus.ERROR]),
                "unique_ips": len(set(e.ip_address for e in hour_events))
            })
        
        return list(reversed(timeline))
    
    def _generate_user_activity(self, events: List[RequestEvent]) -> List[Dict[str, Any]]:
        """Generate user activity summary"""
        user_stats = defaultdict(lambda: {
            "total_requests": 0,
            "blocked_requests": 0,
            "allowed_requests": 0,
            "first_seen": None,
            "last_seen": None,
            "user_agent": ""
        })
        
        for event in events:
            ip = event.ip_address
            stats = user_stats[ip]
            
            stats["total_requests"] += 1
            if event.status == RequestStatus.BLOCKED:
                stats["blocked_requests"] += 1
            elif event.status == RequestStatus.ALLOWED:
                stats["allowed_requests"] += 1
            
            if not stats["first_seen"] or event.timestamp < stats["first_seen"]:
                stats["first_seen"] = event.timestamp
            if not stats["last_seen"] or event.timestamp > stats["last_seen"]:
                stats["last_seen"] = event.timestamp
            
            if not stats["user_agent"]:
                stats["user_agent"] = event.user_agent
        
        # Convert to list and sort by request count
        activity = []
        for ip, stats in user_stats.items():
            activity.append({
                "ip_address": ip,
                "total_requests": stats["total_requests"],
                "blocked_requests": stats["blocked_requests"],
                "allowed_requests": stats["allowed_requests"],
                "block_rate": (stats["blocked_requests"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0,
                "first_seen": stats["first_seen"].isoformat() if stats["first_seen"] else None,
                "last_seen": stats["last_seen"].isoformat() if stats["last_seen"] else None,
                "user_agent": stats["user_agent"][:100]  # Truncate long user agents
            })
        
        return sorted(activity, key=lambda x: x["total_requests"], reverse=True)[:20]
    
    def _generate_geographic_data(self, events: List[RequestEvent]) -> List[Dict[str, Any]]:
        """Generate simplified geographic data"""
        # This is a simplified implementation
        # In production, you'd use a GeoIP database
        
        ip_counts = defaultdict(int)
        for event in events:
            ip_counts[event.ip_address] += 1
        
        # Classify IPs roughly
        geographic_data = []
        local_ips = 0
        external_ips = 0
        
        for ip, count in ip_counts.items():
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private or ip_obj.is_loopback:
                    local_ips += count
                else:
                    external_ips += count
            except:
                external_ips += count
        
        if local_ips > 0:
            geographic_data.append({
                "location": "Local Network",
                "country_code": "LOC",
                "request_count": local_ips,
                "percentage": (local_ips / len(events) * 100) if events else 0
            })
        
        if external_ips > 0:
            geographic_data.append({
                "location": "External",
                "country_code": "EXT",
                "request_count": external_ips,
                "percentage": (external_ips / len(events) * 100) if events else 0
            })
        
        return geographic_data
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics"""
        with self.lock:
            recent_events = [
                e for e in self.events 
                if e.timestamp >= datetime.now() - timedelta(minutes=5)
            ]
            
            return {
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "allowed_requests": self.allowed_requests,
                "error_requests": self.error_requests,
                "recent_requests_5min": len(recent_events),
                "unique_users_total": len(self.users),
                "avg_response_time": (
                    sum(self.response_times) / len(self.response_times)
                    if self.response_times else 0
                ),
                "block_rate": (
                    self.blocked_requests / self.total_requests * 100
                    if self.total_requests > 0 else 0
                ),
                "requests_per_minute": len(recent_events) / 5.0
            }
    
    def clear_old_data(self, hours: int = 168):  # Default: keep 1 week
        """Clear old data to prevent memory issues"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter events
            old_count = len(self.events)
            self.events = deque(
                (e for e in self.events if e.timestamp >= cutoff_time),
                maxlen=self.max_events
            )
            
            # Clean old users
            old_users = [
                ip for ip, user in self.users.items()
                if user.last_seen < cutoff_time
            ]
            for ip in old_users:
                del self.users[ip]
            
            logger.info(f"Cleaned analytics data: removed {old_count - len(self.events)} events and {len(old_users)} old users")
    
    def get_analytics_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics data in a format compatible with frontend"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
            
            # Convert events to dictionaries for frontend
            recent_requests = []
            for event in recent_events[-50:]:  # Get last 50 events
                recent_requests.append({
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "message": event.message,
                    "status": event.status.value,
                    "blocking_reasons": event.blocking_reasons,
                    "detection_results": event.detection_results,
                    "response_time_ms": event.response_time_ms,
                    "provider": event.provider,
                    "model": event.model
                })
            
            return {
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "allowed_requests": self.allowed_requests,
                "error_requests": self.error_requests,
                "recent_requests": recent_requests,
                "detector_performance": {
                    name: {
                        "total_detections": stats.total_detections,
                        "blocked_count": stats.blocked_count,
                        "allowed_count": stats.allowed_count,
                        "avg_confidence": stats.avg_confidence,
                        "last_triggered": stats.last_triggered.isoformat() if stats.last_triggered else None
                    } for name, stats in self.detector_stats.items()
                },
                "unique_users": len(self.users),
                "avg_response_time": (
                    sum(self.response_times) / len(self.response_times)
                    if self.response_times else 0
                ),
                "block_rate": (
                    self.blocked_requests / self.total_requests * 100
                    if self.total_requests > 0 else 0
                ),
                "last_updated": datetime.now().isoformat()
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Export analytics data to dictionary"""
        with self.lock:
            return {
                "total_events": len(self.events),
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "allowed_requests": self.allowed_requests,
                "error_requests": self.error_requests,
                "unique_users": len(self.users),
                "detector_stats": {
                    name: asdict(stats) for name, stats in self.detector_stats.items()
                },
                "last_updated": datetime.now().isoformat()
            }
    
    def export_comprehensive_data(self, hours: int = 24) -> Dict[str, Any]:
        """Export comprehensive analytics data that can rebuild the entire dashboard"""
        with self.lock:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=hours)
            recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
            
            # Get comprehensive analytics summary
            summary = self.get_analytics_summary(hours)
            realtime_stats = self.get_real_time_stats()
            
            # Export all individual events with complete data
            events_data = []
            for event in recent_events:
                events_data.append({
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "message": event.message,
                    "status": event.status.value,
                    "blocking_reasons": event.blocking_reasons,
                    "detection_results": event.detection_results,
                    "response_time_ms": event.response_time_ms,
                    "provider": event.provider,
                    "model": event.model,
                    "session_id": event.session_id
                })
            
            # Export detailed user sessions
            user_sessions_data = []
            for ip, user_session in self.users.items():
                user_sessions_data.append({
                    "ip_address": ip,
                    "first_seen": user_session.first_seen.isoformat(),
                    "last_seen": user_session.last_seen.isoformat(),
                    "total_requests": user_session.total_requests,
                    "blocked_requests": user_session.blocked_requests,
                    "allowed_requests": user_session.allowed_requests,
                    "user_agent": user_session.user_agent,
                    "sessions": list(user_session.sessions),
                    "block_rate": (user_session.blocked_requests / user_session.total_requests * 100) if user_session.total_requests > 0 else 0,
                    "session_duration": (user_session.last_seen - user_session.first_seen).total_seconds() / 3600  # hours
                })
            
            # Export detailed detector statistics
            detector_stats_data = []
            for name, stats in self.detector_stats.items():
                detector_stats_data.append({
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "total_detections": stats.total_detections,
                    "blocked_count": stats.blocked_count,
                    "allowed_count": stats.allowed_count,
                    "avg_confidence": stats.avg_confidence,
                    "last_triggered": stats.last_triggered.isoformat() if stats.last_triggered else None,
                    "block_rate": (stats.blocked_count / stats.total_detections * 100) if stats.total_detections > 0 else 0,
                    "accuracy_estimate": stats.avg_confidence * 100,
                    "effectiveness": "high" if stats.blocked_count > 0 and stats.avg_confidence > 0.7 else "medium" if stats.blocked_count > 0 else "low"
                })
            
            # Provider statistics
            provider_stats = defaultdict(lambda: {
                "total_requests": 0,
                "blocked_requests": 0,
                "allowed_requests": 0,
                "error_requests": 0,
                "response_times": [],
                "models_used": set()
            })
            
            for event in recent_events:
                if event.provider:
                    stats = provider_stats[event.provider]
                    stats["total_requests"] += 1
                    
                    if event.status == RequestStatus.BLOCKED:
                        stats["blocked_requests"] += 1
                    elif event.status == RequestStatus.ALLOWED:
                        stats["allowed_requests"] += 1
                    elif event.status == RequestStatus.ERROR:
                        stats["error_requests"] += 1
                    
                    if event.response_time_ms > 0:
                        stats["response_times"].append(event.response_time_ms)
                    
                    if event.model:
                        stats["models_used"].add(event.model)
            
            # Convert provider stats to serializable format
            provider_stats_data = []
            for provider, stats in provider_stats.items():
                avg_response_time = sum(stats["response_times"]) / len(stats["response_times"]) if stats["response_times"] else 0
                
                provider_stats_data.append({
                    "provider": provider,
                    "total_requests": stats["total_requests"],
                    "blocked_requests": stats["blocked_requests"],
                    "allowed_requests": stats["allowed_requests"],
                    "error_requests": stats["error_requests"],
                    "block_rate": (stats["blocked_requests"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0,
                    "error_rate": (stats["error_requests"] / stats["total_requests"] * 100) if stats["total_requests"] > 0 else 0,
                    "avg_response_time": avg_response_time,
                    "min_response_time": min(stats["response_times"]) if stats["response_times"] else 0,
                    "max_response_time": max(stats["response_times"]) if stats["response_times"] else 0,
                    "models_used": list(stats["models_used"])
                })
            
            # Threat intelligence - analyze blocking patterns
            threat_patterns = defaultdict(lambda: {
                "count": 0,
                "first_seen": None,
                "last_seen": None,
                "affected_ips": set(),
                "detection_methods": set()
            })
            
            for event in recent_events:
                if event.status == RequestStatus.BLOCKED:
                    for reason in event.blocking_reasons:
                        pattern = threat_patterns[reason]
                        pattern["count"] += 1
                        pattern["affected_ips"].add(event.ip_address)
                        
                        if not pattern["first_seen"] or event.timestamp < pattern["first_seen"]:
                            pattern["first_seen"] = event.timestamp
                        if not pattern["last_seen"] or event.timestamp > pattern["last_seen"]:
                            pattern["last_seen"] = event.timestamp
                        
                        # Identify which detectors triggered
                        for detector_name in event.detection_results.keys():
                            if detector_name in event.detection_results:
                                pattern["detection_methods"].add(detector_name)
            
            # Convert threat patterns to serializable format
            threat_intelligence_data = []
            for pattern, data in threat_patterns.items():
                threat_intelligence_data.append({
                    "pattern": pattern,
                    "count": data["count"],
                    "first_seen": data["first_seen"].isoformat() if data["first_seen"] else None,
                    "last_seen": data["last_seen"].isoformat() if data["last_seen"] else None,
                    "affected_ips": list(data["affected_ips"]),
                    "unique_ips": len(data["affected_ips"]),
                    "detection_methods": list(data["detection_methods"]),
                    "severity": "high" if data["count"] > 10 else "medium" if data["count"] > 5 else "low"
                })
            
            # Performance metrics over time
            performance_timeline = []
            for i in range(hours):
                hour_start = current_time - timedelta(hours=i+1)
                hour_end = current_time - timedelta(hours=i)
                
                hour_events = [e for e in recent_events if hour_start <= e.timestamp < hour_end]
                hour_response_times = [e.response_time_ms for e in hour_events if e.response_time_ms > 0]
                
                performance_timeline.append({
                    "hour": hour_start.strftime("%Y-%m-%d %H:00"),
                    "timestamp": hour_start.isoformat(),
                    "total_requests": len(hour_events),
                    "blocked_requests": len([e for e in hour_events if e.status == RequestStatus.BLOCKED]),
                    "allowed_requests": len([e for e in hour_events if e.status == RequestStatus.ALLOWED]),
                    "error_requests": len([e for e in hour_events if e.status == RequestStatus.ERROR]),
                    "unique_ips": len(set(e.ip_address for e in hour_events)),
                    "avg_response_time": sum(hour_response_times) / len(hour_response_times) if hour_response_times else 0,
                    "min_response_time": min(hour_response_times) if hour_response_times else 0,
                    "max_response_time": max(hour_response_times) if hour_response_times else 0,
                    "p95_response_time": sorted(hour_response_times)[int(len(hour_response_times) * 0.95)] if hour_response_times else 0
                })
            
            performance_timeline.reverse()  # Chronological order
            
            # System health indicators
            system_health = {
                "overall_status": "healthy" if realtime_stats["error_requests"] / realtime_stats["total_requests"] < 0.05 else "degraded" if realtime_stats["error_requests"] / realtime_stats["total_requests"] < 0.1 else "unhealthy",
                "error_rate": realtime_stats["error_requests"] / realtime_stats["total_requests"] * 100 if realtime_stats["total_requests"] > 0 else 0,
                "block_rate": realtime_stats["block_rate"],
                "avg_response_time": realtime_stats["avg_response_time"],
                "requests_per_minute": realtime_stats["requests_per_minute"],
                "unique_users_growth": len(self.users),
                "detector_health": {
                    name: {
                        "status": "active" if stats.last_triggered and (current_time - stats.last_triggered).total_seconds() < 3600 else "idle",
                        "confidence": stats.avg_confidence,
                        "effectiveness": stats.blocked_count / stats.total_detections if stats.total_detections > 0 else 0
                    }
                    for name, stats in self.detector_stats.items()
                },
                "capacity_utilization": {
                    "events_buffer": len(self.events) / self.max_events * 100,
                    "response_times_buffer": len(self.response_times) / 1000 * 100,
                    "users_tracked": len(self.users)
                }
            }
            
            # Export metadata
            export_metadata = {
                "export_timestamp": current_time.isoformat(),
                "export_timeframe_hours": hours,
                "total_events_exported": len(events_data),
                "total_users_exported": len(user_sessions_data),
                "total_detectors": len(detector_stats_data),
                "total_providers": len(provider_stats_data),
                "total_threat_patterns": len(threat_intelligence_data),
                "system_version": "1.0.0",
                "data_retention_hours": hours,
                "export_type": "comprehensive_dashboard_data"
            }
            
            return {
                # Core Analytics Data (for dashboard reconstruction)
                "analytics_summary": {
                    "timeframe_hours": summary.timeframe_hours,
                    "total_requests": summary.total_requests,
                    "blocked_requests": summary.blocked_requests,
                    "allowed_requests": summary.allowed_requests,
                    "unique_users": summary.unique_users,
                    "unique_ips": summary.unique_ips,
                    "top_blocking_reasons": summary.top_blocking_reasons,
                    "detector_stats": [
                        {
                            "name": stat.name,
                            "total_detections": stat.total_detections,
                            "blocked_count": stat.blocked_count,
                            "allowed_count": stat.allowed_count,
                            "avg_confidence": stat.avg_confidence,
                            "last_triggered": stat.last_triggered.isoformat() if stat.last_triggered else None,
                            "block_rate": (stat.blocked_count / stat.total_detections * 100) if stat.total_detections > 0 else 0
                        }
                        for stat in summary.detector_stats
                    ],
                    "request_timeline": summary.request_timeline,
                    "user_activity": summary.user_activity,
                    "geographic_data": summary.geographic_data,
                    "error_rate": summary.error_rate,
                    "avg_response_time": summary.avg_response_time
                },
                
                # Real-time Stats
                "realtime_stats": realtime_stats,
                
                # Detailed Event Data
                "events": events_data,
                
                # User Sessions
                "user_sessions": user_sessions_data,
                
                # Detector Analytics
                "detector_analytics": detector_stats_data,
                
                # Provider Performance
                "provider_performance": provider_stats_data,
                
                # Threat Intelligence
                "threat_intelligence": threat_intelligence_data,
                
                # Performance Timeline
                "performance_timeline": performance_timeline,
                
                # System Health
                "system_health": system_health,
                
                # Export Metadata
                "metadata": export_metadata
            }

# Global analytics service instance
analytics_service = AnalyticsService()