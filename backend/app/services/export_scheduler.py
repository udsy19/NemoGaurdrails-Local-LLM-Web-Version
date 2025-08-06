"""
Export Scheduler Service for KPMG Dashboard Integration
Implements 5-minute automated JSON export system as defined in IMPLEMENTATION_FEASIBILITY_AND_STRATEGY.md
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles
import aiohttp
import hashlib
import hmac
import os
from dataclasses import dataclass

from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

@dataclass
class ExportConfig:
    """Configuration for KPMG export system"""
    kpmg_endpoint: str = os.getenv("KPMG_DASHBOARD_ENDPOINT", "https://kpmg-dashboard-api.com/api/v1/client-data/ingest")
    client_id: str = os.getenv("KPMG_CLIENT_ID", "ai-safety-client-001")
    jwt_token: str = os.getenv("KPMG_JWT_TOKEN", "")
    hmac_secret: str = os.getenv("KPMG_HMAC_SECRET", "")
    export_interval_minutes: int = int(os.getenv("EXPORT_INTERVAL_MINUTES", "5"))
    export_directory: str = "user_data/exports"
    max_retries: int = 3
    retry_delay_seconds: int = 30
    offline_queue_max_size: int = 100

class ExportScheduler:
    """
    Automated export scheduler for KPMG dashboard integration.
    Features:
    - 5-minute automated exports
    - Secure HTTPS transmission with JWT auth
    - HMAC data integrity verification
    - Offline queuing with retry mechanism
    - Export file management and cleanup
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.export_dir = Path(self.config.export_directory)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Offline queue for failed transmissions
        self.offline_queue: list = []
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        logger.info(f"Export scheduler initialized - exports every {self.config.export_interval_minutes} minutes")
    
    def _generate_hmac_signature(self, data: str) -> str:
        """Generate HMAC-SHA256 signature for data integrity"""
        if not self.config.hmac_secret:
            return ""
        
        signature = hmac.new(
            self.config.hmac_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _create_export_filename(self, timestamp: datetime) -> str:
        """Create timestamped export filename"""
        return f"dashboard_{timestamp.strftime('%Y-%m-%d_%H-%M')}.json"
    
    async def _save_export_file(self, export_data: Dict[str, Any], filename: str) -> str:
        """Save export data to local file"""
        try:
            file_path = self.export_dir / filename
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2, default=str))
            
            logger.info(f"Export saved to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save export file {filename}: {e}")
            raise
    
    async def _prepare_kpmg_payload(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare payload for KPMG API transmission"""
        timestamp = datetime.utcnow().isoformat()
        
        payload = {
            "client_metadata": {
                "client_id": self.config.client_id,
                "timestamp": timestamp,
                "data_period": f"{self.config.export_interval_minutes}min",
                "export_version": export_data.get("export_metadata", {}).get("export_version", "1.0")
            },
            "dashboard_data": export_data
        }
        
        return payload
    
    async def _transmit_to_kpmg(self, payload: Dict[str, Any]) -> bool:
        """Securely transmit payload to KPMG dashboard API"""
        try:
            # Convert payload to JSON string for signature
            payload_json = json.dumps(payload, default=str)
            signature = self._generate_hmac_signature(payload_json)
            
            headers = {
                "Content-Type": "application/json",
                "X-Client-ID": self.config.client_id,
                "X-Timestamp": datetime.utcnow().isoformat(),
            }
            
            # Add authentication headers if configured
            if self.config.jwt_token:
                headers["Authorization"] = f"Bearer {self.config.jwt_token}"
            
            if signature:
                headers["X-Data-Signature"] = signature
            
            # Transmit with retry logic
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                for attempt in range(self.config.max_retries):
                    try:
                        async with session.post(
                            self.config.kpmg_endpoint,
                            json=payload,
                            headers=headers
                        ) as response:
                            
                            if response.status == 200:
                                result = await response.json()
                                logger.info(f"Successfully transmitted export to KPMG: {result.get('message', 'OK')}")
                                return True
                            elif response.status == 401:
                                logger.error("KPMG transmission failed: Authentication error")
                                return False  # Don't retry auth errors
                            else:
                                logger.warning(f"KPMG transmission failed (attempt {attempt + 1}): HTTP {response.status}")
                                if attempt < self.config.max_retries - 1:
                                    await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))
                    
                    except aiohttp.ClientError as e:
                        logger.warning(f"KPMG transmission network error (attempt {attempt + 1}): {e}")
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))
            
            logger.error(f"KPMG transmission failed after {self.config.max_retries} attempts")
            return False
            
        except Exception as e:
            logger.error(f"KPMG transmission error: {e}")
            return False
    
    async def _process_offline_queue(self):
        """Process queued exports that failed to transmit"""
        if not self.offline_queue:
            return
        
        logger.info(f"Processing {len(self.offline_queue)} queued exports")
        
        # Process queue (oldest first)
        processed = []
        for queued_export in self.offline_queue[:]:
            try:
                success = await self._transmit_to_kpmg(queued_export["payload"])
                if success:
                    processed.append(queued_export)
                    logger.info(f"Successfully transmitted queued export from {queued_export['timestamp']}")
                else:
                    # Stop processing if transmission is still failing
                    break
            except Exception as e:
                logger.error(f"Failed to process queued export: {e}")
                break
        
        # Remove successfully processed exports
        for export in processed:
            self.offline_queue.remove(export)
    
    async def _queue_for_offline_processing(self, payload: Dict[str, Any]):
        """Queue export for later transmission when KPMG is unavailable"""
        if len(self.offline_queue) >= self.config.offline_queue_max_size:
            # Remove oldest queued export
            removed = self.offline_queue.pop(0)
            logger.warning(f"Offline queue full - discarded export from {removed['timestamp']}")
        
        queued_export = {
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        
        self.offline_queue.append(queued_export)
        logger.info(f"Queued export for offline processing (queue size: {len(self.offline_queue)})")
    
    async def _cleanup_old_exports(self, retention_hours: int = 24):
        """Clean up old export files to manage disk space"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
            
            deleted_count = 0
            for file_path in self.export_dir.glob("dashboard_*.json"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old export files")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old exports: {e}")
    
    async def _perform_export(self) -> bool:
        """Perform a single export cycle"""
        try:
            export_timestamp = datetime.utcnow()
            logger.info("Starting scheduled export to KPMG dashboard")
            
            # Generate comprehensive analytics export
            export_data = analytics_service.generate_dashboard_export()
            
            if not export_data or not export_data.get("time_ranges"):
                logger.warning("No analytics data available for export")
                return False
            
            # Save export file locally
            filename = self._create_export_filename(export_timestamp)
            file_path = await self._save_export_file(export_data, filename)
            
            # Prepare payload for KPMG
            payload = await self._prepare_kpmg_payload(export_data)
            
            # Attempt transmission to KPMG
            transmission_success = await self._transmit_to_kpmg(payload)
            
            if transmission_success:
                logger.info("Export completed successfully")
                # Process any queued exports
                await self._process_offline_queue()
            else:
                logger.warning("Export transmission failed - queuing for later retry")
                await self._queue_for_offline_processing(payload)
            
            # Cleanup old export files
            await self._cleanup_old_exports()
            
            return True
            
        except Exception as e:
            logger.error(f"Export cycle failed: {e}")
            return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Export scheduler started")
        
        while self.is_running:
            try:
                # Perform export
                await self._perform_export()
                
                # Wait for next export interval
                await asyncio.sleep(self.config.export_interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("Export scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                # Wait before retrying to avoid rapid error loops
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the export scheduler"""
        if self.is_running:
            logger.warning("Export scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Export scheduler started successfully")
    
    async def stop(self):
        """Stop the export scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping export scheduler...")
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Export scheduler stopped")
    
    async def force_export(self) -> bool:
        """Force an immediate export (for testing/manual triggers)"""
        logger.info("Forcing immediate export")
        return await self._perform_export()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "running": self.is_running,
            "export_interval_minutes": self.config.export_interval_minutes,
            "offline_queue_size": len(self.offline_queue),
            "export_directory": str(self.export_dir),
            "kpmg_endpoint": self.config.kpmg_endpoint,
            "client_id": self.config.client_id,
            "last_export_files": [
                f.name for f in sorted(
                    self.export_dir.glob("dashboard_*.json"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )[:5]
            ]
        }

# Global export scheduler instance
export_scheduler = ExportScheduler()