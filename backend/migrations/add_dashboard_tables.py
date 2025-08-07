"""
Database Migration: Add Dashboard Optimization Tables
Creates new tables for high-performance dashboard queries as defined in IMPLEMENTATION_MAP.md

Migration adds:
- daily_summary: Hourly/daily aggregated metrics for CISO dashboard
- user_summary: User-level aggregations for User-Info dashboard  
- provider_summary: Provider performance metrics
- sensitive_data_summary: Sensitive data type breakdown
- user_activity_log: Privacy-safe detailed user logs
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DashboardTablesMigration:
    """Migration to create optimized dashboard tables"""
    
    def __init__(self, db_path: str = "user_data/ai_safety_analytics.db"):
        self.db_path = Path(db_path)
        self.migration_name = "add_dashboard_tables_v1"
        
    def run_migration(self) -> bool:
        """Execute the migration"""
        try:
            logger.info(f"Starting migration: {self.migration_name}")
            
            if self._migration_already_applied():
                logger.info(f"Migration {self.migration_name} already applied, skipping")
                return True
                
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    self._create_migration_tracking_table(conn)
                    self._create_daily_summary_table(conn)
                    self._create_user_summary_table(conn)
                    self._create_provider_summary_table(conn)
                    self._create_sensitive_data_summary_table(conn)
                    self._create_user_activity_log_table(conn)
                    self._create_indexes(conn)
                    self._record_migration_success(conn)
                    
                    conn.execute("COMMIT")
                    logger.info(f"Migration {self.migration_name} completed successfully")
                    return True
                    
                except Exception as e:
                    conn.execute("ROLLBACK")
                    logger.error(f"Migration {self.migration_name} failed: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to run migration {self.migration_name}: {e}")
            return False
    
    def _migration_already_applied(self) -> bool:
        """Check if migration was already applied"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='migration_history'
                """)
                
                if not cursor.fetchone():
                    return False
                    
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM migration_history 
                    WHERE migration_name = ? AND success = 1
                """, (self.migration_name,))
                
                return cursor.fetchone()[0] > 0
                
        except Exception:
            return False
    
    def _create_migration_tracking_table(self, conn):
        """Create table to track migrations"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """)
    
    def _create_daily_summary_table(self, conn):
        """Create daily_summary table for CISO dashboard trends"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_hour TIMESTAMP NOT NULL,
                total_requests INTEGER DEFAULT 0,
                blocked_requests INTEGER DEFAULT 0,
                allowed_requests INTEGER DEFAULT 0,
                data_exfiltration_attempts INTEGER DEFAULT 0,
                prompt_injection_attempts INTEGER DEFAULT 0,
                toxicity_triggers INTEGER DEFAULT 0,
                top_blocking_reasons_json TEXT,
                avg_response_time REAL DEFAULT 0.0,
                risk_score INTEGER DEFAULT 0,
                guardrail_effectiveness_rate REAL DEFAULT 0.0,
                unique_users INTEGER DEFAULT 0,
                unique_ips INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date_hour)
            )
        """)
        
        logger.info("Created daily_summary table")
    
    def _create_user_summary_table(self, conn):
        """Create user_summary table for User-Info dashboard"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_identifier TEXT NOT NULL,
                ip_address TEXT,
                email TEXT,
                hostname TEXT,
                department TEXT,
                risk_score INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                blocked_requests INTEGER DEFAULT 0,
                allowed_requests INTEGER DEFAULT 0,
                blocked_percentage REAL DEFAULT 0.0,
                last_active_timestamp TIMESTAMP,
                top_violated_categories_json TEXT,
                violation_severity_avg REAL DEFAULT 0.0,
                request_frequency_score INTEGER DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_identifier, ip_address)
            )
        """)
        
        logger.info("Created user_summary table")
    
    def _create_provider_summary_table(self, conn):
        """Create provider_summary table for provider analysis"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS provider_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_name TEXT NOT NULL,
                date_hour TIMESTAMP NOT NULL,
                total_requests INTEGER DEFAULT 0,
                blocked_responses INTEGER DEFAULT 0,
                allowed_responses INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0,
                error_rate REAL DEFAULT 0.0,
                estimated_cost REAL DEFAULT 0.0,
                tokens_input_total INTEGER DEFAULT 0,
                tokens_output_total INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider_name, date_hour)
            )
        """)
        
        logger.info("Created provider_summary table")
    
    def _create_sensitive_data_summary_table(self, conn):
        """Create sensitive_data_summary table for data type breakdown"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensitive_data_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                date_hour TIMESTAMP NOT NULL,
                detection_count INTEGER DEFAULT 0,
                last_detected_timestamp TIMESTAMP,
                severity_level TEXT DEFAULT 'MEDIUM',
                confidence_avg REAL DEFAULT 0.0,
                unique_users_affected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(data_type, date_hour)
            )
        """)
        
        logger.info("Created sensitive_data_summary table")
    
    def _create_user_activity_log_table(self, conn):
        """Create user_activity_log table for detailed user drill-down"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_identifier TEXT NOT NULL,
                ip_address TEXT,
                timestamp TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                blocked_reason TEXT,
                prompt_context_fingerprint TEXT,
                model_used TEXT,
                provider TEXT,
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                response_time_ms INTEGER DEFAULT 0,
                session_id TEXT,
                guardrail_confidence_avg REAL DEFAULT 0.0,
                violation_severity TEXT DEFAULT 'LOW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("Created user_activity_log table")
    
    def _create_indexes(self, conn):
        """Create performance indexes for new tables"""
        
        # Indexes for daily_summary
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_summary_date_hour ON daily_summary(date_hour)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_summary_risk_score ON daily_summary(risk_score)")
        
        # Indexes for user_summary  
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_summary_identifier ON user_summary(user_identifier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_summary_ip ON user_summary(ip_address)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_summary_risk_score ON user_summary(risk_score)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_summary_last_active ON user_summary(last_active_timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_summary_blocked_pct ON user_summary(blocked_percentage)")
        
        # Indexes for provider_summary
        conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_summary_provider_date ON provider_summary(provider_name, date_hour)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_provider_summary_date ON provider_summary(date_hour)")
        
        # Indexes for sensitive_data_summary
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sensitive_data_type_date ON sensitive_data_summary(data_type, date_hour)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sensitive_data_date ON sensitive_data_summary(date_hour)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sensitive_data_severity ON sensitive_data_summary(severity_level)")
        
        # Indexes for user_activity_log
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_identifier ON user_activity_log(user_identifier)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity_log(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_status ON user_activity_log(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_ip ON user_activity_log(ip_address)")
        # Composite index for user-specific queries (as per feedback)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_user_ip_composite ON user_activity_log(user_identifier, ip_address)")
        
        logger.info("Created performance indexes for new tables")
    
    def _record_migration_success(self, conn):
        """Record successful migration"""
        conn.execute("""
            INSERT INTO migration_history (migration_name, success) 
            VALUES (?, 1)
        """, (self.migration_name,))
    
    def rollback_migration(self) -> bool:
        """Rollback the migration (drop created tables)"""
        try:
            logger.info(f"Rolling back migration: {self.migration_name}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Drop tables in reverse order of dependencies
                    tables_to_drop = [
                        "user_activity_log",
                        "sensitive_data_summary", 
                        "provider_summary",
                        "user_summary",
                        "daily_summary"
                    ]
                    
                    for table in tables_to_drop:
                        conn.execute(f"DROP TABLE IF EXISTS {table}")
                        logger.info(f"Dropped table: {table}")
                    
                    # Update migration history
                    conn.execute("""
                        UPDATE migration_history 
                        SET success = 0, error_message = 'Manually rolled back'
                        WHERE migration_name = ?
                    """, (self.migration_name,))
                    
                    conn.execute("COMMIT")
                    logger.info(f"Migration {self.migration_name} rolled back successfully")
                    return True
                    
                except Exception as e:
                    conn.execute("ROLLBACK")
                    logger.error(f"Rollback failed: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to rollback migration {self.migration_name}: {e}")
            return False

def run_migration(db_path: Optional[str] = None) -> bool:
    """Run the dashboard tables migration"""
    if db_path is None:
        db_path = "user_data/ai_safety_analytics.db"
    
    migration = DashboardTablesMigration(db_path)
    return migration.run_migration()

def rollback_migration(db_path: Optional[str] = None) -> bool:
    """Rollback the dashboard tables migration"""
    if db_path is None:
        db_path = "user_data/ai_safety_analytics.db"
    
    migration = DashboardTablesMigration(db_path)
    return migration.rollback_migration()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
        sys.exit(0 if success else 1)
    else:
        success = run_migration()
        sys.exit(0 if success else 1)