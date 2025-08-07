"""
Background Data Aggregation Service for Dashboard Optimization
Processes raw analytics data into optimized tables for high-performance dashboard queries.

This service runs periodically to:
1. Aggregate raw user_analytics data into summary tables
2. Calculate risk scores using the specified algorithm
3. Perform reverse DNS lookups for hostnames
4. Generate prompt context fingerprints for privacy-safe logging
5. Clean up old data according to retention policies

Implementation follows IMPLEMENTATION_MAP.md specifications.
"""

import sqlite3
import asyncio
import logging
import json
import socket
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import threading
import hashlib
import statistics

logger = logging.getLogger(__name__)

@dataclass
class RiskWeights:
    """Risk scoring weights as defined in implementation map"""
    data_exfiltration: float = 0.4    # 40% - PII/Privacy triggers
    prompt_injection: float = 0.3     # 30% - Direct AI attacks  
    blocked_requests: float = 0.2     # 20% - General threat activity
    guardrail_effectiveness: float = 0.1  # 10% - Declining effectiveness

class DataAggregationService:
    """
    Background service for aggregating analytics data into dashboard-optimized tables.
    Implements the aggregation strategy defined in IMPLEMENTATION_MAP.md.
    """
    
    def __init__(self, db_path: str = "user_data/ai_safety_analytics.db"):
        self.db_path = Path(db_path)
        self._lock = threading.Lock()
        self.risk_weights = RiskWeights()
        self.dns_cache = {}  # IP -> hostname cache
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        logger.info(f"Data aggregation service initialized with database: {self.db_path}")
    
    async def start_periodic_aggregation(self, interval_minutes: int = 15):
        """Start the background aggregation loop"""
        if self.is_running:
            logger.warning("Aggregation service is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting periodic aggregation with {interval_minutes}-minute intervals")
        
        while self.is_running and not self._stop_event.is_set():
            try:
                await self.run_full_aggregation()
                
                # Wait for the specified interval or until stop event
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), 
                        timeout=interval_minutes * 60
                    )
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue to next iteration
                    
            except Exception as e:
                logger.error(f"Aggregation cycle failed: {e}")
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=300)  # 5 min retry
                    break
                except asyncio.TimeoutError:
                    pass
        
        self.is_running = False
        logger.info("Periodic aggregation stopped")
    
    async def stop_aggregation(self):
        """Stop the background aggregation service"""
        if self.is_running:
            logger.info("Stopping aggregation service...")
            self.is_running = False
            self._stop_event.set()
    
    async def run_full_aggregation(self):
        """Run complete aggregation cycle"""
        start_time = datetime.now()
        logger.info("Starting full aggregation cycle")
        
        try:
            await self.aggregate_daily_summary()
            await self.aggregate_user_summary()
            await self.aggregate_provider_summary()
            await self.aggregate_sensitive_data_summary()
            await self.process_user_activity_logs()
            await self.cleanup_old_data()
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Aggregation cycle completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Full aggregation failed: {e}")
            raise
    
    async def aggregate_daily_summary(self):
        """Aggregate hourly/daily metrics for CISO dashboard"""
        logger.debug("Aggregating daily summary data")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get the latest aggregated hour to avoid reprocessing
                cursor = conn.execute("""
                    SELECT MAX(date_hour) as last_hour 
                    FROM daily_summary
                """)
                result = cursor.fetchone()
                last_hour = result['last_hour'] if result and result['last_hour'] else '2000-01-01 00:00:00'
                
                # Aggregate data by hour for the last 7 days (but only new hours)
                cursor = conn.execute("""
                    SELECT 
                        datetime(datetime(timestamp), 'start of hour') as hour,
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_requests,
                        SUM(CASE WHEN status = 'allowed' THEN 1 ELSE 0 END) as allowed_requests,
                        SUM(CASE WHEN pii_detected = 1 OR privacy_score > 0.5 THEN 1 ELSE 0 END) as data_exfiltration_attempts,
                        SUM(CASE WHEN prompt_injection_score > 0.5 THEN 1 ELSE 0 END) as prompt_injection_attempts,
                        SUM(CASE WHEN toxicity_score > 0.5 THEN 1 ELSE 0 END) as toxicity_triggers,
                        AVG(response_time_ms) as avg_response_time,
                        COUNT(DISTINCT user_ip) as unique_users,
                        COUNT(DISTINCT user_ip) as unique_ips
                    FROM user_analytics 
                    WHERE datetime(timestamp) >= datetime('now', '-7 days')
                      AND datetime(datetime(timestamp), 'start of hour') > ?
                    GROUP BY hour
                    ORDER BY hour
                """, (last_hour,))
                
                hourly_data = cursor.fetchall()
                
                for row in hourly_data:
                    # Calculate risk score for this hour
                    risk_score = self._calculate_hourly_risk_score(dict(row))
                    
                    # Get top blocking reasons for this hour
                    blocking_reasons = self._get_top_blocking_reasons(conn, row['hour'])
                    
                    # Calculate guardrail effectiveness
                    effectiveness_rate = self._calculate_guardrail_effectiveness(dict(row))
                    
                    # Insert/update daily summary
                    conn.execute("""
                        INSERT OR REPLACE INTO daily_summary (
                            date_hour, total_requests, blocked_requests, allowed_requests,
                            data_exfiltration_attempts, prompt_injection_attempts, toxicity_triggers,
                            top_blocking_reasons_json, avg_response_time, risk_score,
                            guardrail_effectiveness_rate, unique_users, unique_ips, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        row['hour'], row['total_requests'], row['blocked_requests'], 
                        row['allowed_requests'], row['data_exfiltration_attempts'],
                        row['prompt_injection_attempts'], row['toxicity_triggers'],
                        json.dumps(blocking_reasons), row['avg_response_time'] or 0,
                        risk_score, effectiveness_rate, row['unique_users'], row['unique_ips']
                    ))
                
                logger.info(f"Processed {len(hourly_data)} hourly summaries")
                
        except Exception as e:
            logger.error(f"Failed to aggregate daily summary: {e}")
            raise
    
    async def aggregate_user_summary(self):
        """Aggregate user-level metrics for User-Info dashboard"""
        logger.debug("Aggregating user summary data")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user aggregations from the last 30 days
                cursor = conn.execute("""
                    SELECT 
                        COALESCE(session_id, user_ip) as user_identifier,
                        user_ip,
                        COUNT(*) as total_requests,
                        SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_requests,
                        SUM(CASE WHEN status = 'allowed' THEN 1 ELSE 0 END) as allowed_requests,
                        MAX(datetime(timestamp)) as last_active_timestamp,
                        AVG(CASE WHEN status = 'blocked' THEN 
                            (toxicity_score + pii_confidence + prompt_injection_score + 
                             hate_speech_score + bias_score + privacy_score) / 6.0 
                            ELSE 0 END) as violation_severity_avg,
                        MIN(datetime(timestamp)) as first_seen
                    FROM user_analytics 
                    WHERE datetime(timestamp) >= datetime('now', '-30 days')
                    GROUP BY user_identifier, user_ip
                    HAVING total_requests > 0
                """)
                
                user_data = cursor.fetchall()
                
                for row in user_data:
                    user_dict = dict(row)
                    
                    # Calculate user risk score
                    risk_score = self._calculate_user_risk_score(user_dict)
                    
                    # Calculate blocked percentage
                    blocked_percentage = (user_dict['blocked_requests'] / user_dict['total_requests']) * 100
                    
                    # Get top violated categories for this user
                    violated_categories = self._get_user_violated_categories(
                        conn, user_dict['user_identifier']
                    )
                    
                    # Calculate request frequency score (requests per day)
                    days_active = max(1, (datetime.now() - datetime.fromisoformat(user_dict['first_seen'])).days)
                    frequency_score = min(100, int(user_dict['total_requests'] / days_active * 10))
                    
                    # Get/cache hostname via reverse DNS
                    hostname = await self._get_cached_hostname(user_dict['user_ip'])
                    
                    # Insert/update user summary
                    conn.execute("""
                        INSERT OR REPLACE INTO user_summary (
                            user_identifier, ip_address, hostname, risk_score, 
                            total_requests, blocked_requests, allowed_requests, blocked_percentage,
                            last_active_timestamp, top_violated_categories_json, 
                            violation_severity_avg, request_frequency_score, 
                            first_seen, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        user_dict['user_identifier'], user_dict['user_ip'], hostname, 
                        risk_score, user_dict['total_requests'], user_dict['blocked_requests'],
                        user_dict['allowed_requests'], blocked_percentage, 
                        user_dict['last_active_timestamp'], json.dumps(violated_categories),
                        user_dict['violation_severity_avg'] or 0, frequency_score,
                        user_dict['first_seen']
                    ))
                
                logger.info(f"Processed {len(user_data)} user summaries")
                
        except Exception as e:
            logger.error(f"Failed to aggregate user summary: {e}")
            raise
    
    async def aggregate_provider_summary(self):
        """Aggregate provider performance metrics"""
        logger.debug("Aggregating provider summary data")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get latest aggregated hour for each provider
                cursor = conn.execute("""
                    SELECT provider_name, MAX(date_hour) as last_hour
                    FROM provider_summary
                    GROUP BY provider_name
                """)
                provider_last_hours = {row['provider_name']: row['last_hour'] 
                                     for row in cursor.fetchall()}
                
                # Get all providers from raw data
                cursor = conn.execute("""
                    SELECT DISTINCT provider_used 
                    FROM user_analytics 
                    WHERE provider_used IS NOT NULL
                      AND datetime(timestamp) >= datetime('now', '-7 days')
                """)
                providers = [row[0] for row in cursor.fetchall()]
                
                for provider in providers:
                    last_hour = provider_last_hours.get(provider, '2000-01-01 00:00:00')
                    
                    # Aggregate by hour for this provider
                    cursor = conn.execute("""
                        SELECT 
                            datetime(datetime(timestamp), 'start of hour') as hour,
                            COUNT(*) as total_requests,
                            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_responses,
                            SUM(CASE WHEN status = 'allowed' THEN 1 ELSE 0 END) as allowed_responses,
                            AVG(response_time_ms) as avg_response_time,
                            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
                            SUM(tokens_input) as tokens_input_total,
                            SUM(tokens_output) as tokens_output_total,
                            COUNT(DISTINCT user_ip) as unique_users
                        FROM user_analytics 
                        WHERE provider_used = ?
                          AND datetime(timestamp) >= datetime('now', '-7 days')
                          AND datetime(datetime(timestamp), 'start of hour') > ?
                        GROUP BY hour
                        ORDER BY hour
                    """, (provider, last_hour))
                    
                    hourly_provider_data = cursor.fetchall()
                    
                    for row in hourly_provider_data:
                        error_rate = (row['error_count'] / row['total_requests']) if row['total_requests'] > 0 else 0
                        estimated_cost = self._estimate_provider_cost(provider, row['tokens_input_total'], row['tokens_output_total'])
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO provider_summary (
                                provider_name, date_hour, total_requests, blocked_responses,
                                allowed_responses, avg_response_time, error_rate, estimated_cost,
                                tokens_input_total, tokens_output_total, unique_users
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            provider, row['hour'], row['total_requests'], row['blocked_responses'],
                            row['allowed_responses'], row['avg_response_time'] or 0, error_rate,
                            estimated_cost, row['tokens_input_total'], row['tokens_output_total'],
                            row['unique_users']
                        ))
                    
                    if hourly_provider_data:
                        logger.debug(f"Processed {len(hourly_provider_data)} hours for provider {provider}")
                
        except Exception as e:
            logger.error(f"Failed to aggregate provider summary: {e}")
            raise
    
    async def aggregate_sensitive_data_summary(self):
        """Aggregate sensitive data type breakdown"""
        logger.debug("Aggregating sensitive data summary")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Define data types based on guardrail triggers
                data_types = [
                    ('PII_DETECTION', 'pii_detected = 1'),
                    ('CREDIT_CARD', 'pii_detected = 1 AND pii_confidence > 0.8'),
                    ('EMAIL_ADDRESS', 'pii_detected = 1 AND pii_confidence > 0.6'),
                    ('API_KEYS', 'privacy_score > 0.7'),
                    ('TOXIC_CONTENT', 'toxicity_score > 0.5'),
                    ('PROMPT_INJECTION', 'prompt_injection_score > 0.5'),
                    ('HATE_SPEECH', 'hate_speech_score > 0.5'),
                    ('BIAS_CONTENT', 'bias_score > 0.5')
                ]
                
                for data_type, condition in data_types:
                    # Get latest aggregated hour for this data type
                    cursor = conn.execute("""
                        SELECT MAX(date_hour) as last_hour
                        FROM sensitive_data_summary 
                        WHERE data_type = ?
                    """, (data_type,))
                    result = cursor.fetchone()
                    last_hour = result['last_hour'] if result and result['last_hour'] else '2000-01-01 00:00:00'
                    
                    # Aggregate hourly detections for this data type
                    cursor = conn.execute(f"""
                        SELECT 
                            datetime(datetime(timestamp), 'start of hour') as hour,
                            COUNT(*) as detection_count,
                            MAX(datetime(timestamp)) as last_detected_timestamp,
                            AVG(CASE 
                                WHEN {condition.split(' AND ')[0]} THEN 
                                    CASE 
                                        WHEN ? = 'PII_DETECTION' THEN pii_confidence
                                        WHEN ? = 'TOXIC_CONTENT' THEN toxicity_confidence
                                        WHEN ? = 'PROMPT_INJECTION' THEN prompt_injection_confidence
                                        WHEN ? = 'HATE_SPEECH' THEN hate_speech_confidence
                                        WHEN ? = 'BIAS_CONTENT' THEN bias_confidence
                                        ELSE privacy_confidence
                                    END
                                ELSE 0 
                            END) as confidence_avg,
                            COUNT(DISTINCT user_ip) as unique_users_affected
                        FROM user_analytics 
                        WHERE {condition}
                          AND datetime(timestamp) >= datetime('now', '-7 days')
                          AND datetime(datetime(timestamp), 'start of hour') > ?
                        GROUP BY hour
                        HAVING detection_count > 0
                        ORDER BY hour
                    """, (data_type, data_type, data_type, data_type, data_type, last_hour))
                    
                    detections = cursor.fetchall()
                    
                    for row in detections:
                        severity_level = self._determine_severity_level(data_type, row['confidence_avg'])
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO sensitive_data_summary (
                                data_type, date_hour, detection_count, last_detected_timestamp,
                                severity_level, confidence_avg, unique_users_affected
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data_type, row['hour'], row['detection_count'],
                            row['last_detected_timestamp'], severity_level,
                            row['confidence_avg'] or 0, row['unique_users_affected']
                        ))
                    
                    if detections:
                        logger.debug(f"Processed {len(detections)} detection hours for {data_type}")
                
        except Exception as e:
            logger.error(f"Failed to aggregate sensitive data summary: {e}")
            raise
    
    async def process_user_activity_logs(self):
        """Process detailed user activity logs with prompt context fingerprints"""
        logger.debug("Processing user activity logs")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get latest processed log entry
                cursor = conn.execute("""
                    SELECT MAX(id) as last_processed_id
                    FROM user_activity_log
                """)
                result = cursor.fetchone()
                last_id = result[0] if result and result[0] else 0
                
                # Get new raw analytics entries to process
                cursor = conn.execute("""
                    SELECT 
                        id, user_ip, timestamp, status, blocked_by,
                        prompt_hash, response_hash, model_used, provider_used,
                        tokens_input, tokens_output, response_time_ms, session_id,
                        toxicity_score, toxicity_confidence, pii_detected, pii_confidence,
                        prompt_injection_score, prompt_injection_confidence,
                        hate_speech_score, hate_speech_confidence,
                        bias_score, bias_confidence, privacy_score, privacy_confidence
                    FROM user_analytics 
                    WHERE id > ?
                      AND datetime(timestamp) >= datetime('now', '-30 days')
                    ORDER BY id
                    LIMIT 1000
                """, (last_id,))
                
                raw_entries = cursor.fetchall()
                
                for entry in raw_entries:
                    # Create prompt context fingerprint (privacy-safe)
                    fingerprint = self._create_prompt_fingerprint(entry)
                    
                    # Calculate average guardrail confidence
                    confidences = [
                        entry[5] if entry[5] else 0,  # toxicity_confidence  
                        entry[7] if entry[7] else 0,  # pii_confidence
                        entry[9] if entry[9] else 0,  # prompt_injection_confidence
                        entry[11] if entry[11] else 0, # hate_speech_confidence
                        entry[13] if entry[13] else 0, # bias_confidence
                        entry[15] if entry[15] else 0  # privacy_confidence
                    ]
                    avg_confidence = statistics.mean([c for c in confidences if c > 0]) if any(confidences) else 0
                    
                    # Determine violation severity
                    violation_severity = self._determine_violation_severity(entry)
                    
                    # Get user identifier (prefer session_id over IP)
                    user_identifier = entry[7] if entry[7] else entry[1]  # session_id or user_ip
                    
                    # Insert activity log entry
                    conn.execute("""
                        INSERT OR IGNORE INTO user_activity_log (
                            user_identifier, ip_address, timestamp, status, blocked_reason,
                            prompt_context_fingerprint, model_used, provider, tokens_input,
                            tokens_output, response_time_ms, session_id, guardrail_confidence_avg,
                            violation_severity
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user_identifier, entry[1], entry[2], entry[3], entry[4],
                        json.dumps(fingerprint), entry[5], entry[6], entry[7], entry[8],
                        entry[9] or 0, entry[7], avg_confidence, violation_severity
                    ))
                
                if raw_entries:
                    logger.info(f"Processed {len(raw_entries)} user activity log entries")
                
        except Exception as e:
            logger.error(f"Failed to process user activity logs: {e}")
            raise
    
    async def cleanup_old_data(self):
        """Clean up old data according to retention policies"""
        logger.debug("Cleaning up old data")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clean up old raw analytics (keep 30 days)
                cursor = conn.execute("""
                    DELETE FROM user_analytics 
                    WHERE datetime(timestamp) < datetime('now', '-30 days')
                """)
                raw_deleted = cursor.rowcount
                
                # Clean up old activity logs (keep 30 days)
                cursor = conn.execute("""
                    DELETE FROM user_activity_log 
                    WHERE datetime(timestamp) < datetime('now', '-30 days')
                """)
                activity_deleted = cursor.rowcount
                
                # Clean up old daily summaries (keep 1 year)
                cursor = conn.execute("""
                    DELETE FROM daily_summary 
                    WHERE datetime(date_hour) < datetime('now', '-1 year')
                """)
                daily_deleted = cursor.rowcount
                
                # Clean up old provider summaries (keep 3 months)
                cursor = conn.execute("""
                    DELETE FROM provider_summary 
                    WHERE datetime(date_hour) < datetime('now', '-3 months')
                """)
                provider_deleted = cursor.rowcount
                
                # Clean up old sensitive data summaries (keep 6 months)  
                cursor = conn.execute("""
                    DELETE FROM sensitive_data_summary 
                    WHERE datetime(date_hour) < datetime('now', '-6 months')
                """)
                sensitive_deleted = cursor.rowcount
                
                # Update user summaries - remove users inactive for >90 days
                cursor = conn.execute("""
                    DELETE FROM user_summary 
                    WHERE datetime(last_active_timestamp) < datetime('now', '-90 days')
                """)
                user_deleted = cursor.rowcount
                
                if any([raw_deleted, activity_deleted, daily_deleted, provider_deleted, sensitive_deleted, user_deleted]):
                    logger.info(f"Cleanup completed: raw={raw_deleted}, activity={activity_deleted}, "
                              f"daily={daily_deleted}, provider={provider_deleted}, "
                              f"sensitive={sensitive_deleted}, user={user_deleted} records deleted")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise
    
    def _calculate_hourly_risk_score(self, hourly_data: Dict) -> int:
        """Calculate risk score for an hour using the defined algorithm"""
        total = hourly_data['total_requests']
        if total == 0:
            return 0
            
        # Normalize metrics to 0-100 scale
        data_exfiltration_score = min(100, (hourly_data['data_exfiltration_attempts'] / total) * 500)
        prompt_injection_score = min(100, (hourly_data['prompt_injection_attempts'] / total) * 400)  
        blocked_requests_score = min(100, (hourly_data['blocked_requests'] / total) * 200)
        
        # For now, assume stable effectiveness (can be improved with historical data)
        effectiveness_score = 0  # No decline detected
        
        # Apply weights and calculate final score
        risk_score = (
            data_exfiltration_score * self.risk_weights.data_exfiltration +
            prompt_injection_score * self.risk_weights.prompt_injection +
            blocked_requests_score * self.risk_weights.blocked_requests +
            effectiveness_score * self.risk_weights.guardrail_effectiveness
        )
        
        return int(min(100, max(0, risk_score)))
    
    def _calculate_user_risk_score(self, user_data: Dict) -> int:
        """Calculate user-specific risk score"""
        total = user_data['total_requests']
        blocked = user_data['blocked_requests']
        
        if total == 0:
            return 0
            
        # Base score on blocked percentage
        blocked_percentage = (blocked / total) * 100
        
        # Violation severity factor
        severity_factor = (user_data['violation_severity_avg'] or 0) * 100
        
        # Frequency factor (higher activity = potentially higher risk)
        frequency_factor = min(100, user_data.get('request_frequency_score', 0))
        
        # Weighted risk calculation for users
        user_risk = (
            blocked_percentage * 0.5 +      # 50% weight on block rate
            severity_factor * 0.3 +         # 30% weight on severity
            (frequency_factor / 10) * 0.2   # 20% weight on frequency (normalized)
        )
        
        return int(min(100, max(0, user_risk)))
    
    def _calculate_guardrail_effectiveness(self, hourly_data: Dict) -> float:
        """Calculate guardrail effectiveness rate for the hour"""
        total = hourly_data['total_requests']
        if total == 0:
            return 100.0
            
        # Simple effectiveness: percentage of total requests that were properly processed
        # (not errored out due to guardrail failures)
        allowed = hourly_data['allowed_requests']
        blocked = hourly_data['blocked_requests'] 
        processed = allowed + blocked
        
        return (processed / total) * 100.0 if total > 0 else 100.0
    
    def _get_top_blocking_reasons(self, conn, hour: str) -> List[Dict]:
        """Get top blocking reasons for a specific hour"""
        cursor = conn.execute("""
            SELECT blocked_by, COUNT(*) as count
            FROM user_analytics 
            WHERE datetime(datetime(timestamp), 'start of hour') = ?
              AND status = 'blocked'
              AND blocked_by IS NOT NULL
            GROUP BY blocked_by
            ORDER BY count DESC
            LIMIT 5
        """, (hour,))
        
        return [{'reason': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def _get_user_violated_categories(self, conn, user_identifier: str) -> Dict:
        """Get top violated categories for a specific user"""
        cursor = conn.execute("""
            SELECT 
                SUM(CASE WHEN toxicity_score > 0.5 THEN 1 ELSE 0 END) as toxicity,
                SUM(CASE WHEN pii_detected = 1 THEN 1 ELSE 0 END) as pii,
                SUM(CASE WHEN prompt_injection_score > 0.5 THEN 1 ELSE 0 END) as prompt_injection,
                SUM(CASE WHEN hate_speech_score > 0.5 THEN 1 ELSE 0 END) as hate_speech,
                SUM(CASE WHEN bias_score > 0.5 THEN 1 ELSE 0 END) as bias,
                SUM(CASE WHEN privacy_score > 0.5 THEN 1 ELSE 0 END) as privacy
            FROM user_analytics 
            WHERE (session_id = ? OR user_ip = ?)
              AND status = 'blocked'
              AND datetime(timestamp) >= datetime('now', '-30 days')
        """, (user_identifier, user_identifier))
        
        result = cursor.fetchone()
        if result:
            categories = {
                'toxicity': result[0],
                'pii': result[1], 
                'prompt_injection': result[2],
                'hate_speech': result[3],
                'bias': result[4],
                'privacy': result[5]
            }
            # Return only categories with violations
            return {k: v for k, v in categories.items() if v > 0}
        
        return {}
    
    async def _get_cached_hostname(self, ip_address: str) -> Optional[str]:
        """Get hostname via cached reverse DNS lookup"""
        if ip_address in self.dns_cache:
            return self.dns_cache[ip_address]
        
        try:
            # Perform reverse DNS lookup with timeout
            hostname = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, socket.gethostbyaddr, ip_address
                ),
                timeout=2.0
            )
            hostname = hostname[0] if hostname else None
            
            # Cache the result
            self.dns_cache[ip_address] = hostname
            
            # Limit cache size
            if len(self.dns_cache) > 1000:
                # Remove oldest entries (simple approach)
                keys_to_remove = list(self.dns_cache.keys())[:100]
                for key in keys_to_remove:
                    del self.dns_cache[key]
            
            return hostname
            
        except (socket.herror, socket.gaierror, asyncio.TimeoutError, OSError):
            # Cache failed lookups as None to avoid repeated attempts
            self.dns_cache[ip_address] = None
            return None
    
    def _estimate_provider_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on provider and token usage"""
        # Simple cost estimation - can be enhanced with real pricing
        cost_per_1k_tokens = {
            'openai': 0.03,
            'anthropic': 0.015,
            'ollama': 0.0,  # Local models
            'local': 0.0,
        }
        
        rate = cost_per_1k_tokens.get(provider.lower(), 0.01)  # Default rate
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * rate
    
    def _determine_severity_level(self, data_type: str, confidence: float) -> str:
        """Determine severity level based on data type and confidence"""
        if confidence >= 0.8:
            return 'HIGH'
        elif confidence >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _create_prompt_fingerprint(self, entry) -> Dict:
        """Create privacy-safe prompt context fingerprint"""
        # Extract basic metrics from the prompt hash (can't recover original text)
        prompt_hash = entry[5]  # prompt_hash field
        
        # Calculate approximate length from hash (this is just an example)
        # In reality, you'd need to store length separately or use a different approach
        estimated_length = len(prompt_hash) * 8 if prompt_hash else 0
        
        # Determine language and content type from guardrail scores
        has_code = entry[13] > 0 or entry[15] > 0  # bias or privacy scores might indicate code
        is_toxic = entry[4] > 0.3  # toxicity_score
        has_pii = entry[6]  # pii_detected
        
        fingerprint = {
            'length_estimate': estimated_length,
            'has_code': has_code,
            'is_toxic': is_toxic,
            'has_pii': has_pii,
            'language': 'unknown',  # Could be enhanced with language detection
            'hash_prefix': prompt_hash[:8] if prompt_hash else None
        }
        
        return fingerprint
    
    def _determine_violation_severity(self, entry) -> str:
        """Determine overall violation severity for an entry"""
        if entry[3] != 'blocked':  # status
            return 'NONE'
        
        # Get max confidence score across all guardrails
        max_confidence = max([
            entry[5] if entry[5] else 0,   # toxicity_confidence
            entry[7] if entry[7] else 0,   # pii_confidence  
            entry[9] if entry[9] else 0,   # prompt_injection_confidence
            entry[11] if entry[11] else 0, # hate_speech_confidence
            entry[13] if entry[13] else 0, # bias_confidence
            entry[15] if entry[15] else 0  # privacy_confidence
        ])
        
        if max_confidence >= 0.8:
            return 'HIGH'
        elif max_confidence >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'