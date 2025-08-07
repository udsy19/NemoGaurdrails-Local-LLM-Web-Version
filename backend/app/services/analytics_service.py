"""
Comprehensive Analytics Service for KPMG Dashboard Integration
Implements the analytics system as defined in IMPLEMENTATION_FEASIBILITY_AND_STRATEGY.md
This replaces the in-memory analytics with SQLite-based persistent storage for enterprise-grade data collection.
"""
import sqlite3
import hashlib
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict
import threading
import os
from enum import Enum

logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    """Request status enumeration for analytics tracking"""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class UserAnalyticsEntry:
    """Data structure for user analytics as defined in the strategy document"""
    timestamp: str
    user_ip: str
    request_id: str
    prompt_hash: str
    response_hash: Optional[str]
    status: str  # 'allowed', 'blocked', 'error'
    blocked_by: Optional[str]
    
    # Guardrail Scores and Confidences (6 guardrails)
    toxicity_score: float = 0.0
    toxicity_confidence: float = 0.0
    pii_detected: bool = False
    pii_confidence: float = 0.0
    prompt_injection_score: float = 0.0
    prompt_injection_confidence: float = 0.0
    hate_speech_score: float = 0.0
    hate_speech_confidence: float = 0.0
    bias_score: float = 0.0
    bias_confidence: float = 0.0
    privacy_score: float = 0.0
    privacy_confidence: float = 0.0
    
    # Performance Metrics
    response_time_ms: int = 0
    provider_used: Optional[str] = None
    model_used: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    session_id: Optional[str] = None

class AnalyticsService:
    """
    Enterprise-grade analytics service implementing the KPMG dashboard data collection strategy.
    Features:
    - SQLite database with privacy protection (SHA-256 hashing)
    - Real-time data collection with comprehensive metrics
    - Multi-timeframe aggregation (1h, 6h, 12h, 24h, 3d, 1w)
    - JSON export for KPMG dashboard
    - Thread-safe operations with connection pooling
    - Data retention management
    """
    
    def __init__(self, db_path: str = "user_data/ai_safety_analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
        
        # In-memory counters for real-time stats (performance optimization)
        self.total_requests = 0
        self.blocked_requests = 0
        self.allowed_requests = 0
        self.error_requests = 0
        
        logger.info(f"Enterprise analytics service initialized with SQLite database at {self.db_path}")
        
    def _init_database(self):
        """Initialize SQLite database with the comprehensive schema from strategy document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create main analytics table with comprehensive schema
                conn.execute("""
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
                """)
                
                # Create export tracking table
                conn.execute("""
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
                """)
                
                # Create performance indexes for fast queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON user_analytics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_user_ip ON user_analytics(user_ip)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON user_analytics(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_provider ON user_analytics(provider_used)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON user_analytics(session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_blocked_by ON user_analytics(blocked_by)")
                
                # Enable WAL mode for better concurrent performance
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                
                logger.info(f"Analytics database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
            raise
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Create SHA-256 hash for privacy protection"""
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _extract_guardrail_scores(self, guardrail_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract guardrail scores from analysis results"""
        scores = {}
        
        # Map legacy detector names to standard names
        detector_mapping = {
            'toxicity': 'toxicity',
            'pii': 'pii', 
            'prompt_injection': 'prompt_injection',
            'hate_speech': 'hate_speech',
            'bias': 'bias',
            'privacy': 'privacy',
            'spam': 'hate_speech',  # Map spam to hate_speech category
            'topic': 'bias',  # Map topic classification to bias category
            'fact_check': 'privacy'  # Map fact check to privacy category
        }
        
        # Initialize all scores to 0
        for standard_name in detector_mapping.values():
            scores[f"{standard_name}_score"] = 0.0
            scores[f"{standard_name}_confidence"] = 0.0
            if standard_name == 'pii':
                scores["pii_detected"] = False
        
        # Define non-detector keys to ignore (control/status keys)
        ignored_keys = {
            'blocked', 'error', 'status_code', 'timestamp', 'session_id', 
            'message_id', 'request_id', 'success', 'warnings', 'metadata',
            'summary', 'detectors_used', 'blocking_reasons', 'text_length',
            'detector_config'
        }
        
        # Extract scores for each guardrail
        for detector_name, result in guardrail_results.items():
            # Skip non-detector keys
            if detector_name in ignored_keys:
                continue
                
            # Get standard name
            standard_name = detector_mapping.get(detector_name, detector_name)
            
            # Skip if this detector name is not in our mapping and doesn't look like a detector
            if detector_name not in detector_mapping and not any(
                detector in detector_name.lower() 
                for detector in ['toxicity', 'pii', 'prompt', 'hate', 'bias', 'privacy', 'spam', 'topic', 'fact']
            ):
                continue
            
            if isinstance(result, dict):
                score = float(result.get('score', 0.0))
                confidence = float(result.get('confidence', 0.0))
                
                # Use maximum score if multiple detectors map to same category
                scores[f"{standard_name}_score"] = max(scores[f"{standard_name}_score"], score)
                scores[f"{standard_name}_confidence"] = max(scores[f"{standard_name}_confidence"], confidence)
                
                # Special handling for PII detection (boolean)
                if standard_name == 'pii':
                    detected = bool(result.get('detected', False) or result.get('has_pii', False))
                    scores["pii_detected"] = scores["pii_detected"] or detected
                    
            elif isinstance(result, (bool, int, float)):
                # Handle simple score values
                score = float(result)
                scores[f"{standard_name}_score"] = max(scores[f"{standard_name}_score"], score)
        
        return scores
    
    async def record_user_request(
        self,
        user_ip: str,
        request_id: str,
        prompt: str,
        response: Optional[str],
        guardrail_results: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Record a user request with comprehensive analytics data.
        Implements privacy protection through content hashing.
        """
        try:
            # Hash sensitive content for privacy
            prompt_hash = self._hash_content(prompt)
            response_hash = self._hash_content(response) if response else None
            
            # Extract guardrail scores
            guardrail_scores = self._extract_guardrail_scores(guardrail_results)
            
            # Determine status and blocking reason
            status = "allowed"
            blocked_by = None
            
            if guardrail_results.get('blocked', False):
                status = "blocked"
                blocked_by = guardrail_results.get('blocked_by', 'unknown')
                # Try to extract blocking reason from results
                for detector, result in guardrail_results.items():
                    if isinstance(result, dict) and result.get('blocked', False):
                        blocked_by = detector
                        break
            elif guardrail_results.get('error', False):
                status = "error"
            
            # Count tokens (estimate if not provided)
            tokens_input = int(performance_metrics.get('tokens_input', len(prompt.split()) if prompt else 0))
            tokens_output = int(performance_metrics.get('tokens_output', len(response.split()) if response else 0))
            
            # Create analytics entry
            entry = UserAnalyticsEntry(
                timestamp=datetime.utcnow().isoformat(),
                user_ip=user_ip,
                request_id=request_id,
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                status=status,
                blocked_by=blocked_by,
                
                # Guardrail scores (ensure all fields exist)
                toxicity_score=guardrail_scores.get('toxicity_score', 0.0),
                toxicity_confidence=guardrail_scores.get('toxicity_confidence', 0.0),
                pii_detected=guardrail_scores.get('pii_detected', False),
                pii_confidence=guardrail_scores.get('pii_confidence', 0.0),
                prompt_injection_score=guardrail_scores.get('prompt_injection_score', 0.0),
                prompt_injection_confidence=guardrail_scores.get('prompt_injection_confidence', 0.0),
                hate_speech_score=guardrail_scores.get('hate_speech_score', 0.0),
                hate_speech_confidence=guardrail_scores.get('hate_speech_confidence', 0.0),
                bias_score=guardrail_scores.get('bias_score', 0.0),
                bias_confidence=guardrail_scores.get('bias_confidence', 0.0),
                privacy_score=guardrail_scores.get('privacy_score', 0.0),
                privacy_confidence=guardrail_scores.get('privacy_confidence', 0.0),
                
                # Performance metrics
                response_time_ms=int(performance_metrics.get('response_time_ms', 0)),
                provider_used=performance_metrics.get('provider_used'),
                model_used=performance_metrics.get('model_used'),
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                session_id=session_id
            )
            
            # Insert into database (thread-safe)
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Convert entry to dict and insert
                    entry_dict = asdict(entry)
                    
                    # Remove any unknown fields that might cause issues
                    expected_fields = {
                        'timestamp', 'user_ip', 'request_id', 'prompt_hash', 'response_hash',
                        'status', 'blocked_by', 'toxicity_score', 'toxicity_confidence',
                        'pii_detected', 'pii_confidence', 'prompt_injection_score',
                        'prompt_injection_confidence', 'hate_speech_score', 'hate_speech_confidence',
                        'bias_score', 'bias_confidence', 'privacy_score', 'privacy_confidence',
                        'response_time_ms', 'provider_used', 'model_used', 'tokens_input',
                        'tokens_output', 'session_id'
                    }
                    filtered_dict = {k: v for k, v in entry_dict.items() if k in expected_fields}
                    
                    columns = ', '.join(filtered_dict.keys())
                    placeholders = ', '.join(['?' for _ in filtered_dict])
                    
                    conn.execute(
                        f"INSERT INTO user_analytics ({columns}) VALUES ({placeholders})",
                        list(filtered_dict.values())
                    )
                    
                # Update in-memory counters for real-time stats
                self.total_requests += 1
                if status == "blocked":
                    self.blocked_requests += 1
                elif status == "allowed":
                    self.allowed_requests += 1
                elif status == "error":
                    self.error_requests += 1
                    
            logger.debug(f"Recorded analytics for request {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record analytics for request {request_id}: {e}")
            return False
    
    def _get_timeframe_data(self, hours: int) -> pd.DataFrame:
        """Get data for a specific timeframe using pandas for efficient analysis"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        query = """
            SELECT * FROM user_analytics 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=[cutoff_str])
    
    def _generate_timeframe_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for a timeframe"""
        if df.empty:
            return {
                "total_requests": 0,
                "blocked_requests": 0,
                "block_rate": 0.0,
                "unique_users": 0,
                "avg_response_time_ms": 0,
                "total_tokens_input": 0,
                "total_tokens_output": 0,
                "avg_tokens_per_request": 0.0
            }
        
        total_requests = len(df)
        blocked_requests = len(df[df['status'] == 'blocked'])
        block_rate = blocked_requests / total_requests if total_requests > 0 else 0.0
        unique_users = df['user_ip'].nunique()
        avg_response_time = df['response_time_ms'].mean()
        total_tokens_input = df['tokens_input'].sum()
        total_tokens_output = df['tokens_output'].sum()
        avg_tokens_per_request = (total_tokens_input + total_tokens_output) / total_requests if total_requests > 0 else 0.0
        
        return {
            "total_requests": total_requests,
            "blocked_requests": blocked_requests,
            "block_rate": round(block_rate, 3),
            "unique_users": unique_users,
            "avg_response_time_ms": round(avg_response_time, 2) if pd.notna(avg_response_time) else 0,
            "total_tokens_input": int(total_tokens_input),
            "total_tokens_output": int(total_tokens_output),
            "avg_tokens_per_request": round(avg_tokens_per_request, 2)
        }
    
    def _generate_guardrail_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive guardrail effectiveness analysis based on blocking reasons"""
        guardrails = ['toxicity', 'pii', 'prompt_injection', 'hate_speech', 'bias', 'privacy']
        analysis = {}
        
        # Get blocked requests to analyze blocking reasons
        blocked_df = df[df['status'] == 'blocked'].copy()
        total_requests = len(df)
        total_blocked = len(blocked_df)
        
        for guardrail in guardrails:
            # Count triggers based on blocking reasons (more accurate than score columns)
            if guardrail == 'toxicity':
                # Look for toxicity-related blocking reasons
                toxicity_pattern = r'(?i)toxic|toxicity|offensive|inappropriate|harmful'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(toxicity_pattern, na=False)])
            elif guardrail == 'pii':
                # Look for PII-related blocking reasons
                pii_pattern = r'(?i)pii|personal|private|phone|email|address'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(pii_pattern, na=False)])
            elif guardrail == 'prompt_injection':
                # Look for prompt injection related blocking reasons
                injection_pattern = r'(?i)prompt.injection|injection|malicious.prompt'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(injection_pattern, na=False)])
            elif guardrail == 'hate_speech':
                # Look for hate speech related blocking reasons
                hate_pattern = r'(?i)hate|discrimination|bias|racist|sexist'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(hate_pattern, na=False)])
            elif guardrail == 'bias':
                # Look for bias related blocking reasons
                bias_pattern = r'(?i)bias|unfair|discriminat'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(bias_pattern, na=False)])
            elif guardrail == 'privacy':
                # Look for privacy related blocking reasons
                privacy_pattern = r'(?i)privacy|confidential|sensitive'
                triggers = len(blocked_df[blocked_df['blocked_by'].str.contains(privacy_pattern, na=False)])
            else:
                triggers = 0
            
            # Calculate effectiveness based on actual blocking data
            score_col = f"{guardrail}_score"
            confidence_col = f"{guardrail}_confidence"
            
            # Use score columns if available, otherwise estimate based on triggers
            if score_col in df.columns and confidence_col in df.columns:
                avg_confidence = df[confidence_col].mean() if confidence_col in df.columns else 0.0
                max_score = df[score_col].max() if not df[score_col].empty else 0.0
                total_analyzed = len(df[df[score_col] > 0.0]) if len(df[df[score_col] > 0.0]) > 0 else total_requests
            else:
                # Estimate based on blocking patterns
                avg_confidence = 0.8 if triggers > 0 else 0.0
                max_score = 0.95 if triggers > 0 else 0.0
                total_analyzed = total_requests
            
            # Calculate effectiveness percentage
            effectiveness = (triggers / total_analyzed * 100) if total_analyzed > 0 else 0.0
            
            analysis[guardrail] = {
                "triggers": triggers,
                "avg_confidence": round(avg_confidence, 3) if pd.notna(avg_confidence) else 0.0,
                "max_score": round(max_score, 3) if pd.notna(max_score) else 0.0,
                "total_analyzed": total_analyzed,
                "effectiveness_percentage": round(effectiveness, 1)
            }
        
        return analysis
    
    async def get_content_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Get real content analysis data from stored analytics"""
        try:
            # Get data from the last N hours
            df = self._get_timeframe_data(hours)
            
            if df.empty:
                return {
                    "common_words": {},
                    "language_distribution": {"English": 100},
                    "content_categories": {}
                }
            
            # Analyze actual prompt content for common words (if available)
            common_words = {}
            if 'prompt' in df.columns:
                # Simple word frequency analysis
                all_text = ' '.join(df['prompt'].dropna().astype(str).str.lower())
                # Remove common words and get flagged content indicators
                flagged_words = ['inappropriate', 'spam', 'toxic', 'offensive', 'harassment', 
                               'hate', 'abuse', 'threat', 'discrimination', 'violence']
                for word in flagged_words:
                    count = all_text.count(word)
                    if count > 0:
                        common_words[word] = count
            
            # Get language distribution (simplified - mostly English for now)
            language_distribution = {"English": 100}
            
            # Get content categories based on guardrail triggers
            content_categories = {}
            guardrails = ['toxicity', 'pii', 'prompt_injection', 'hate_speech', 'bias', 'privacy']
            
            for guardrail in guardrails:
                score_col = f"{guardrail}_score"
                if score_col in df.columns:
                    # Count how many times this guardrail was triggered
                    if guardrail == 'pii':
                        count = len(df[df.get('pii_detected', False) == True])
                    else:
                        count = len(df[df[score_col] > 0.5])
                    
                    if count > 0:
                        content_categories[guardrail.replace('_', ' ').title()] = count
            
            return {
                "common_words": common_words,
                "language_distribution": language_distribution,
                "content_categories": content_categories
            }
            
        except Exception as e:
            from app.utils.logger import app_logger
            app_logger.error(f"Error generating content analysis: {e}")
            return {
                "common_words": {},
                "language_distribution": {"English": 100},
                "content_categories": {}
            }
    
    def _generate_user_activity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive per-user activity analysis"""
        user_activity = {}
        
        for user_ip in df['user_ip'].unique():
            user_data = df[df['user_ip'] == user_ip]
            
            total_requests = len(user_data)
            blocked_requests = len(user_data[user_data['status'] == 'blocked'])
            avg_response_time = user_data['response_time_ms'].mean()
            total_tokens = user_data['tokens_input'].sum() + user_data['tokens_output'].sum()
            
            # Find most common blocking guardrail
            blocked_data = user_data[user_data['status'] == 'blocked']
            top_blocked_guardrail = blocked_data['blocked_by'].mode().iloc[0] if not blocked_data.empty and not blocked_data['blocked_by'].mode().empty else None
            
            # Session analysis
            unique_sessions = user_data['session_id'].nunique() if 'session_id' in user_data.columns else 1
            
            # Risk assessment
            block_rate = blocked_requests / total_requests if total_requests > 0 else 0.0
            risk_score = block_rate * 100
            if total_requests > 50:  # High volume user
                risk_score += 10
            if unique_sessions > 5:  # Multiple sessions
                risk_score += 5
            risk_score = min(100, risk_score)
            
            user_activity[user_ip] = {
                "total_requests": total_requests,
                "blocked_requests": blocked_requests,
                "block_rate": round(block_rate * 100, 1),
                "avg_response_time": round(avg_response_time, 2) if pd.notna(avg_response_time) else 0,
                "total_tokens": int(total_tokens),
                "unique_sessions": unique_sessions,
                "top_blocked_guardrail": top_blocked_guardrail,
                "risk_score": round(risk_score, 1),
                "first_seen": user_data['timestamp'].min(),
                "last_seen": user_data['timestamp'].max()
            }
        
        return user_activity
    
    def _generate_provider_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive provider performance analysis"""
        provider_performance = {}
        
        for provider in df['provider_used'].dropna().unique():
            provider_data = df[df['provider_used'] == provider]
            
            requests = len(provider_data)
            avg_response_time = provider_data['response_time_ms'].mean()
            blocked_requests = len(provider_data[provider_data['status'] == 'blocked'])
            error_requests = len(provider_data[provider_data['status'] == 'error'])
            total_tokens = provider_data['tokens_input'].sum() + provider_data['tokens_output'].sum()
            
            # Model usage breakdown
            model_usage = provider_data['model_used'].value_counts().to_dict()
            
            provider_performance[provider] = {
                "requests": requests,
                "avg_response_time": round(avg_response_time, 2) if pd.notna(avg_response_time) else 0,
                "blocked_requests": blocked_requests,
                "error_requests": error_requests,
                "block_rate": round(blocked_requests / requests * 100, 1) if requests > 0 else 0,
                "error_rate": round(error_requests / requests * 100, 1) if requests > 0 else 0,
                "total_tokens": int(total_tokens),
                "avg_tokens_per_request": round(total_tokens / requests, 1) if requests > 0 else 0,
                "models_used": model_usage
            }
        
        return provider_performance
    
    def _generate_alerts(self, summary: Dict[str, Any], guardrail_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent alerts based on configurable thresholds"""
        alerts = []
        
        # High block rate alert
        if summary["block_rate"] > 0.3:  # More than 30% blocked
            alerts.append({
                "type": "high_block_rate",
                "severity": "warning" if summary["block_rate"] < 0.5 else "critical",
                "message": f"Block rate elevated: {summary['block_rate']*100:.1f}%",
                "threshold": 0.3,
                "current": summary["block_rate"],
                "impact": "High blocking may indicate aggressive guardrails or attack patterns"
            })
        
        # High response time alert
        if summary["avg_response_time_ms"] > 2000:  # More than 2 seconds
            alerts.append({
                "type": "high_response_time",
                "severity": "warning" if summary["avg_response_time_ms"] < 5000 else "critical",
                "message": f"Average response time elevated: {summary['avg_response_time_ms']:.0f}ms",
                "threshold": 2000,
                "current": summary["avg_response_time_ms"],
                "impact": "Slow responses may affect user experience"
            })
        
        # High token usage alert
        total_tokens = summary["total_tokens_input"] + summary["total_tokens_output"]
        if total_tokens > 100000:  # High token usage
            alerts.append({
                "type": "high_token_usage",
                "severity": "info",
                "message": f"High token usage detected: {total_tokens:,} tokens",
                "threshold": 100000,
                "current": total_tokens,
                "impact": "Monitor for cost implications"
            })
        
        # Guardrail-specific alerts
        for guardrail, analysis in guardrail_analysis.items():
            if analysis["triggers"] > 10:  # More than 10 triggers
                alerts.append({
                    "type": f"guardrail_{guardrail}_active",
                    "severity": "info",
                    "message": f"{guardrail.title()} guardrail highly active: {analysis['triggers']} triggers",
                    "threshold": 10,
                    "current": analysis["triggers"],
                    "impact": f"Monitor {guardrail} patterns for potential threats"
                })
        
        return alerts
    
    def generate_dashboard_export(self) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard export for KPMG.
        Implements multi-timeframe analysis as defined in strategy document.
        """
        try:
            timeframes = {
                "1h": 1,
                "6h": 6,
                "12h": 12,
                "24h": 24,
                "3d": 72,
                "1w": 168
            }
            
            export_data = {
                "export_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "export_version": "1.0",
                    "time_ranges": list(timeframes.keys()),
                    "database_path": str(self.db_path),
                    "system_info": {
                        "total_records": self._get_total_records(),
                        "database_size_mb": self._get_database_size_mb()
                    }
                },
                "time_ranges": {}
            }
            
            # Generate analysis for each timeframe
            for timeframe_name, hours in timeframes.items():
                try:
                    df = self._get_timeframe_data(hours)
                    
                    summary = self._generate_timeframe_summary(df)
                    guardrail_analysis = self._generate_guardrail_analysis(df)
                    user_activity = self._generate_user_activity(df)
                    provider_performance = self._generate_provider_performance(df)
                    alerts = self._generate_alerts(summary, guardrail_analysis)
                    
                    export_data["time_ranges"][timeframe_name] = {
                        "summary": summary,
                        "guardrail_analysis": guardrail_analysis,
                        "user_activity": user_activity,
                        "provider_performance": provider_performance,
                        "alerts": alerts,
                        "data_points": len(df)
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to generate analysis for timeframe {timeframe_name}: {e}")
                    export_data["time_ranges"][timeframe_name] = {
                        "error": str(e),
                        "data_points": 0
                    }
            
            # Log successful export
            self._log_export("dashboard_export", 168, len(export_data["time_ranges"]))
            
            logger.info("Dashboard export generated successfully")
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to generate dashboard export: {e}")
            self._log_export("dashboard_export", 168, 0, success=False, error_message=str(e))
            return {
                "export_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "export_version": "1.0",
                    "error": str(e)
                },
                "time_ranges": {}
            }
    
    def _get_total_records(self) -> int:
        """Get total number of records in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM user_analytics")
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    def _get_database_size_mb(self) -> float:
        """Get database file size in MB"""
        try:
            if self.db_path.exists():
                size_bytes = self.db_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except Exception:
            return 0.0
    
    def _log_export(self, export_type: str, timeframe_hours: int, records_count: int, 
                   success: bool = True, error_message: Optional[str] = None):
        """Log export operations for audit trail"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO export_log 
                    (export_timestamp, export_type, timeframe_hours, records_count, success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    datetime.utcnow().isoformat(),
                    export_type,
                    timeframe_hours,
                    records_count,
                    success,
                    error_message
                ])
        except Exception as e:
            logger.error(f"Failed to log export: {e}")
    
    def cleanup_old_data(self, retention_days: int = 7):
        """Clean up data older than retention period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
            cutoff_str = cutoff_time.isoformat()
            
            deleted_count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_analytics WHERE timestamp < ?", [cutoff_str])
                deleted_count = cursor.rowcount
                
                # Clean old export logs too
                cursor.execute("DELETE FROM export_log WHERE export_timestamp < ?", [cutoff_str])
            
            # Vacuum in separate connection to avoid transaction issues
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                
            logger.info(f"Cleaned up {deleted_count} old analytics records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics for monitoring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total records
                cursor.execute("SELECT COUNT(*) FROM user_analytics")
                total_records = cursor.fetchone()[0]
                
                # Get oldest and newest records
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM user_analytics")
                oldest, newest = cursor.fetchone()
                
                # Get records by status
                cursor.execute("SELECT status, COUNT(*) FROM user_analytics GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Get top providers
                cursor.execute("""
                    SELECT provider_used, COUNT(*) as count 
                    FROM user_analytics 
                    WHERE provider_used IS NOT NULL 
                    GROUP BY provider_used 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_providers = dict(cursor.fetchall())
                
                # Get database file size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "total_records": total_records,
                    "oldest_record": oldest,
                    "newest_record": newest,
                    "status_breakdown": status_counts,
                    "top_providers": top_providers,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "realtime_counters": {
                        "total_requests": self.total_requests,
                        "blocked_requests": self.blocked_requests,
                        "allowed_requests": self.allowed_requests,
                        "error_requests": self.error_requests
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def export_user_data(self, user_ip: str, timeframe_hours: int = 168) -> Dict[str, Any]:
        """Export all data for a specific user (for data sovereignty compliance)"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
            cutoff_str = cutoff_time.isoformat()
            
            query = """
                SELECT * FROM user_analytics 
                WHERE user_ip = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=[user_ip, cutoff_str])
            
            if df.empty:
                return {"user_ip": user_ip, "message": "No data found for this user"}
            
            # Convert to user-friendly format
            user_data = {
                "user_ip": user_ip,
                "data_export_timestamp": datetime.utcnow().isoformat(),
                "timeframe_hours": timeframe_hours,
                "total_requests": len(df),
                "blocked_requests": len(df[df['status'] == 'blocked']),
                "allowed_requests": len(df[df['status'] == 'allowed']),
                "error_requests": len(df[df['status'] == 'error']),
                "first_request": df['timestamp'].min(),
                "last_request": df['timestamp'].max(),
                "requests": df.to_dict('records')
            }
            
            # Log the export for compliance
            self._log_export(f"user_data_export_{user_ip}", timeframe_hours, len(df))
            
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to export user data for {user_ip}: {e}")
            return {"user_ip": user_ip, "error": str(e)}
    
    # Backward compatibility methods for existing code
    def track_request(self, ip_address: str, user_agent: str, message: str, 
                     status: str, blocking_reasons: List[str] = None,
                     detection_results: Dict[str, Any] = None,
                     response_time_ms: float = 0.0, provider: str = None,
                     model: str = None, session_id: str = None) -> str:
        """Backward compatibility wrapper for track_request"""
        request_id = f"req_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Convert to new format
        guardrail_results = detection_results or {}
        if blocking_reasons:
            guardrail_results['blocked'] = True
            guardrail_results['blocked_by'] = blocking_reasons[0] if blocking_reasons else 'unknown'
        
        performance_metrics = {
            'response_time_ms': response_time_ms,
            'provider_used': provider,
            'model_used': model
        }
        
        # Use asyncio to run the async method
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, schedule as task
                asyncio.create_task(self.record_user_request(
                    ip_address, request_id, message, None, 
                    guardrail_results, performance_metrics, session_id
                ))
            else:
                loop.run_until_complete(self.record_user_request(
                    ip_address, request_id, message, None,
                    guardrail_results, performance_metrics, session_id
                ))
        except Exception as e:
            logger.error(f"Failed to track request: {e}")
        
        return request_id
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for dashboard"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "allowed_requests": self.allowed_requests,
            "error_requests": self.error_requests,
            "block_rate": (self.blocked_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "database_stats": self.get_database_stats()
        }

    def get_analytics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        try:
            # Get recent data for specified timeframe
            df = self._get_timeframe_data(hours)
            
            if df.empty:
                return {
                    "total_requests": 0,
                    "blocked_requests": 0,
                    "block_rate": 0.0,
                    "unique_users": 0,
                    "avg_response_time": 0,
                    "guardrails_analysis": {},
                    "top_blocked_reasons": []
                }
            
            # Generate summary
            summary = self._generate_timeframe_summary(df)
            guardrail_analysis = self._generate_guardrail_analysis(df)
            
            # Top blocking reasons
            blocked_df = df[df['status'] == 'blocked']
            top_blocked_reasons = []
            if not blocked_df.empty:
                blocked_reasons = blocked_df['blocked_by'].value_counts().head(5)
                top_blocked_reasons = [
                    {"reason": reason, "count": int(count)} 
                    for reason, count in blocked_reasons.items()
                ]
            
            return {
                **summary,
                "guardrails_analysis": guardrail_analysis,
                "top_blocked_reasons": top_blocked_reasons
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "block_rate": (self.blocked_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
                "unique_users": 0,
                "avg_response_time": 0,
                "guardrails_analysis": {},
                "top_blocked_reasons": [],
                "error": str(e)
            }

# Global analytics service instance
analytics_service = AnalyticsService()