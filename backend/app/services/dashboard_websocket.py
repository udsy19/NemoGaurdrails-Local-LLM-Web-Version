"""
Enhanced WebSocket service for real-time dashboard data streaming.
Handles connections from LLMinate dashboard frontend with message routing.
Implements the WebSocket message routing system from IMPLEMENTATION_MAP.md.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from pathlib import Path

from ..services.analytics_service import analytics_service
from ..utils.logger import app_logger

class DashboardConnection(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    
    websocket: WebSocket
    client_id: str
    dashboard_type: str  # 'main' or 'user'
    connected_at: datetime
    last_ping: datetime
    refresh_interval: int = 5000  # milliseconds

class DashboardWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, DashboardConnection] = {}
        self.refresh_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
        self.db_path = Path("user_data/ai_safety_analytics.db")
        
        # Message handlers for different inbound message types
        self.message_handlers = {
            'request_user_detail': self._handle_user_detail_request,
            'dashboard_config': self._handle_dashboard_config,
            'refresh_request': self._handle_refresh_request,
            'ping': self._handle_ping
        }

    async def connect(self, websocket: WebSocket, client_id: str, dashboard_type: str = 'main'):
        """Accept a new dashboard connection"""
        await websocket.accept()
        
        connection = DashboardConnection(
            websocket=websocket,
            client_id=client_id,
            dashboard_type=dashboard_type,
            connected_at=datetime.now(),
            last_ping=datetime.now()
        )
        
        self.active_connections[client_id] = connection
        
        # Start periodic data refresh for this connection
        self.refresh_tasks[client_id] = asyncio.create_task(
            self._periodic_refresh(client_id)
        )
        
        app_logger.info(f"Dashboard client {client_id} connected ({dashboard_type})")
        
        # Send initial data
        await self.send_initial_data(client_id)

    async def disconnect(self, client_id: str):
        """Remove a dashboard connection"""
        if client_id in self.active_connections:
            # Cancel refresh task
            if client_id in self.refresh_tasks:
                self.refresh_tasks[client_id].cancel()
                del self.refresh_tasks[client_id]
            
            # Remove connection
            del self.active_connections[client_id]
            app_logger.info(f"Dashboard client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        """Send a message to a specific dashboard client"""
        if client_id not in self.active_connections:
            return False
        
        connection = self.active_connections[client_id]
        try:
            await connection.websocket.send_text(json.dumps(message))
            return True
        except Exception as e:
            app_logger.error(f"Failed to send message to {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast_to_type(self, dashboard_type: str, message: dict):
        """Broadcast a message to all clients of a specific dashboard type"""
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if connection.dashboard_type == dashboard_type:
                success = await self.send_message(client_id, message)
                if not success:
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def send_initial_data(self, client_id: str):
        """Send initial dashboard data to a newly connected client"""
        connection = self.active_connections.get(client_id)
        if not connection:
            return

        try:
            if connection.dashboard_type == 'main':
                # Send CISO dashboard data
                data = await self._get_main_dashboard_data()
                await self.send_message(client_id, {
                    'type': 'analytics_data',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
            
            elif connection.dashboard_type == 'user':
                # Send user analytics data
                data = await self._get_user_dashboard_data()
                await self.send_message(client_id, {
                    'type': 'user_data_update',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })
        
        except Exception as e:
            app_logger.error(f"Failed to send initial data to {client_id}: {e}")

    async def _periodic_refresh(self, client_id: str):
        """Periodically send updated data to a dashboard client"""
        while client_id in self.active_connections:
            try:
                connection = self.active_connections[client_id]
                refresh_interval = connection.refresh_interval / 1000  # Convert to seconds
                
                await asyncio.sleep(refresh_interval)
                
                # Check if connection still exists
                if client_id not in self.active_connections:
                    break
                
                # Send updated data based on dashboard type
                if connection.dashboard_type == 'main':
                    data = await self._get_main_dashboard_data()
                    await self.send_message(client_id, {
                        'type': 'analytics_update',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })
                
                elif connection.dashboard_type == 'user':
                    data = await self._get_user_dashboard_data()
                    await self.send_message(client_id, {
                        'type': 'user_data_update', 
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                app_logger.error(f"Error in periodic refresh for {client_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _get_main_dashboard_data(self) -> dict:
        """Get data for the main CISO dashboard"""
        try:
            # Get analytics data for multiple timeframes
            timeframes = ['1h', '6h', '12h', '24h', '3d', '1w']
            dashboard_data = {}
            
            for timeframe in timeframes:
                try:
                    stats = await analytics_service.get_timeframe_stats(timeframe)
                    guardrail_performance = await analytics_service.get_guardrail_performance_summary(timeframe)
                    user_activity = await analytics_service.get_user_activity_summary(timeframe)
                    provider_performance = await analytics_service.get_provider_performance_summary(timeframe)
                    
                    dashboard_data[timeframe] = {
                        'summary': stats,
                        'guardrail_analysis': guardrail_performance,
                        'user_activity': user_activity,
                        'provider_performance': provider_performance,
                        'alerts': await analytics_service.get_active_alerts(timeframe)
                    }
                except Exception as e:
                    app_logger.error(f"Failed to get data for timeframe {timeframe}: {e}")
                    dashboard_data[timeframe] = {}
            
            return {
                'export_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'export_version': '1.0',
                    'time_ranges': timeframes,
                    'database_path': 'user_data/ai_safety_analytics.db',
                    'system_info': await analytics_service.get_database_stats()
                },
                'time_ranges': dashboard_data
            }
        
        except Exception as e:
            app_logger.error(f"Failed to get main dashboard data: {e}")
            return {}

    async def _get_user_dashboard_data(self) -> dict:
        """Get data for the user analytics dashboard"""
        try:
            # Get user list and activity data
            users_summary = await analytics_service.get_users_summary()
            
            return {
                'users': users_summary.get('users', []),
                'summary': users_summary.get('summary', {}),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            app_logger.error(f"Failed to get user dashboard data: {e}")
            return {'users': [], 'summary': {}}

    async def handle_client_message(self, client_id: str, message: dict):
        """Handle incoming messages from dashboard clients - Enhanced for new message routing"""
        try:
            message_type = message.get('type')
            
            # Use new message handler system
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](client_id, message)
                return
            
            if message_type == 'ping':
                # Update last ping time
                if client_id in self.active_connections:
                    self.active_connections[client_id].last_ping = datetime.now()
                
                await self.send_message(client_id, {
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                })
            
            elif message_type == 'register_dashboard':
                # Update dashboard settings
                dashboard_type = message.get('dashboard_type', 'main')
                refresh_interval = message.get('refresh_interval', 5000)
                
                if client_id in self.active_connections:
                    connection = self.active_connections[client_id]
                    connection.dashboard_type = dashboard_type
                    connection.refresh_interval = refresh_interval
                    
                    # Restart refresh task with new settings
                    if client_id in self.refresh_tasks:
                        self.refresh_tasks[client_id].cancel()
                    
                    self.refresh_tasks[client_id] = asyncio.create_task(
                        self._periodic_refresh(client_id)
                    )
                    
                    await self.send_initial_data(client_id)
            
            elif message_type == 'request_analytics':
                # Send analytics data for specific timeframe
                timeframe = message.get('timeframe', '24h')
                if client_id in self.active_connections:
                    data = await self._get_main_dashboard_data()
                    await self.send_message(client_id, {
                        'type': 'analytics_data',
                        'data': data,
                        'timeframe': timeframe,
                        'timestamp': datetime.now().isoformat()
                    })
            
            elif message_type == 'request_user_data':
                # Send user data
                user_id = message.get('userId')
                timeframe = message.get('timeframe', '24h')
                
                if user_id:
                    # Get specific user data
                    user_data = await analytics_service.get_user_detailed_data(user_id, timeframe)
                    await self.send_message(client_id, {
                        'type': 'user_detail_data',
                        'data': user_data,
                        'user_id': user_id,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    # Get all users data
                    data = await self._get_user_dashboard_data()
                    await self.send_message(client_id, {
                        'type': 'user_data_update',
                        'data': data,
                        'timestamp': datetime.now().isoformat()
                    })
            
            elif message_type == 'refresh_dashboard':
                # Force refresh dashboard data
                await self.send_initial_data(client_id)
        
        except Exception as e:
            app_logger.error(f"Error handling message from {client_id}: {e}")

    async def send_security_alert(self, alert_data: dict):
        """Send security alert to all connected dashboards"""
        alert_message = {
            'type': 'security_alert',
            'data': alert_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all connected clients
        for client_id in list(self.active_connections.keys()):
            await self.send_message(client_id, alert_message)

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        now = datetime.now()
        stats = {
            'total_connections': len(self.active_connections),
            'main_dashboard_connections': 0,
            'user_dashboard_connections': 0,
            'connections_by_type': {},
            'average_uptime_minutes': 0
        }
        
        if not self.active_connections:
            return stats
        
        total_uptime = timedelta()
        
        for connection in self.active_connections.values():
            if connection.dashboard_type == 'main':
                stats['main_dashboard_connections'] += 1
            elif connection.dashboard_type == 'user':
                stats['user_dashboard_connections'] += 1
            
            # Track connections by type
            dashboard_type = connection.dashboard_type
            if dashboard_type not in stats['connections_by_type']:
                stats['connections_by_type'][dashboard_type] = 0
            stats['connections_by_type'][dashboard_type] += 1
            
            # Calculate uptime
            uptime = now - connection.connected_at
            total_uptime += uptime
        
        # Calculate average uptime
        if len(self.active_connections) > 0:
            avg_uptime = total_uptime / len(self.active_connections)
            stats['average_uptime_minutes'] = round(avg_uptime.total_seconds() / 60, 2)
        
        return stats
    
    # New message handler methods for enhanced routing
    
    async def _handle_user_detail_request(self, client_id: str, message: dict):
        """Handle user detail request - sends detailed user data"""
        try:
            user_id = message.get('user_id')
            if not user_id:
                await self.send_message(client_id, {
                    'type': 'error',
                    'message': 'user_id is required for user detail requests'
                })
                return
            
            # Get detailed user data from aggregated tables
            user_detail_data = await self._get_user_detail_data(user_id)
            
            await self.send_message(client_id, {
                'type': 'user_detail_response',
                'user_id': user_id,
                'data': user_detail_data,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            app_logger.error(f"Failed to handle user detail request: {e}")
            await self.send_message(client_id, {
                'type': 'error',
                'message': f'Failed to get user details: {str(e)}'
            })
    
    async def _handle_dashboard_config(self, client_id: str, message: dict):
        """Handle dashboard configuration updates"""
        try:
            dashboard = message.get('dashboard', 'main')
            update_frequency = message.get('update_frequency', 15)  # seconds
            
            if client_id in self.active_connections:
                connection = self.active_connections[client_id]
                connection.dashboard_type = dashboard
                connection.refresh_interval = update_frequency * 1000  # Convert to ms
                
                # Restart periodic refresh with new settings
                if client_id in self.refresh_tasks:
                    self.refresh_tasks[client_id].cancel()
                
                self.refresh_tasks[client_id] = asyncio.create_task(
                    self._periodic_refresh(client_id)
                )
                
                await self.send_message(client_id, {
                    'type': 'config_updated',
                    'dashboard': dashboard,
                    'update_frequency': update_frequency,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Send initial data for new configuration
                await self.send_initial_data(client_id)
                
        except Exception as e:
            app_logger.error(f"Failed to handle dashboard config: {e}")
    
    async def _handle_refresh_request(self, client_id: str, message: dict):
        """Handle manual refresh requests"""
        try:
            await self.send_initial_data(client_id)
        except Exception as e:
            app_logger.error(f"Failed to handle refresh request: {e}")
    
    async def _handle_ping(self, client_id: str, message: dict):
        """Handle ping messages"""
        try:
            if client_id in self.active_connections:
                self.active_connections[client_id].last_ping = datetime.now()
            
            await self.send_message(client_id, {
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            app_logger.error(f"Failed to handle ping: {e}")
    
    async def _get_user_detail_data(self, user_identifier: str) -> dict:
        """Get detailed data for a specific user from aggregated tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user summary data
                cursor = conn.execute("""
                    SELECT * FROM user_summary 
                    WHERE user_identifier = ? OR ip_address = ?
                    LIMIT 1
                """, (user_identifier, user_identifier))
                
                user_summary = cursor.fetchone()
                if not user_summary:
                    return {
                        'profile': {'user_id': user_identifier, 'error': 'User not found'},
                        'activity_timeline': [],
                        'violated_categories': {},
                        'detailed_logs': []
                    }
                
                user_summary_dict = dict(user_summary)
                
                # Get user activity timeline (last 7 days, hourly aggregation)
                cursor = conn.execute("""
                    SELECT 
                        datetime(datetime(timestamp), 'start of hour') as hour,
                        COUNT(*) as request_count,
                        SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_count,
                        AVG(guardrail_confidence_avg) as avg_confidence
                    FROM user_activity_log 
                    WHERE user_identifier = ?
                      AND datetime(timestamp) >= datetime('now', '-7 days')
                    GROUP BY hour
                    ORDER BY hour
                """, (user_identifier,))
                
                activity_timeline = [dict(row) for row in cursor.fetchall()]
                
                # Get detailed activity logs (last 100 entries)
                cursor = conn.execute("""
                    SELECT * FROM user_activity_log 
                    WHERE user_identifier = ?
                      AND datetime(timestamp) >= datetime('now', '-7 days')
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (user_identifier,))
                
                detailed_logs = []
                for row in cursor.fetchall():
                    log_entry = dict(row)
                    # Parse prompt context fingerprint
                    if log_entry['prompt_context_fingerprint']:
                        try:
                            log_entry['prompt_context_fingerprint'] = json.loads(log_entry['prompt_context_fingerprint'])
                        except:
                            pass
                    detailed_logs.append(log_entry)
                
                # Parse violated categories JSON
                violated_categories = {}
                if user_summary_dict['top_violated_categories_json']:
                    try:
                        violated_categories = json.loads(user_summary_dict['top_violated_categories_json'])
                    except:
                        pass
                
                return {
                    'profile': {
                        'user_id': user_summary_dict['user_identifier'],
                        'ip_address': user_summary_dict['ip_address'],
                        'hostname': user_summary_dict['hostname'],
                        'department': user_summary_dict['department'],
                        'risk_score': user_summary_dict['risk_score'],
                        'total_requests': user_summary_dict['total_requests'],
                        'blocked_percentage': user_summary_dict['blocked_percentage'],
                        'last_active': user_summary_dict['last_active_timestamp'],
                        'top_violated_policy': self._get_top_violation_policy(violated_categories)
                    },
                    'activity_timeline': activity_timeline,
                    'violated_categories': violated_categories,
                    'detailed_logs': detailed_logs
                }
                
        except Exception as e:
            app_logger.error(f"Failed to get user detail data for {user_identifier}: {e}")
            return {
                'profile': {'user_id': user_identifier, 'error': str(e)},
                'activity_timeline': [],
                'violated_categories': {},
                'detailed_logs': []
            }
    
    async def _get_optimized_main_dashboard_data(self) -> dict:
        """Get main dashboard data from optimized aggregated tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get latest daily summaries for different time ranges
                timeframes = ['1h', '6h', '12h', '24h', '3d', '1w']
                dashboard_data = {}
                
                for timeframe in timeframes:
                    hours_back = self._timeframe_to_hours(timeframe)
                    
                    # Get aggregated summary for this timeframe
                    cursor = conn.execute("""
                        SELECT 
                            SUM(total_requests) as total_requests,
                            SUM(blocked_requests) as blocked_requests,
                            SUM(allowed_requests) as allowed_requests,
                            SUM(data_exfiltration_attempts) as data_exfiltration_attempts,
                            SUM(prompt_injection_attempts) as prompt_injection_attempts,
                            SUM(toxicity_triggers) as toxicity_triggers,
                            AVG(avg_response_time) as avg_response_time_ms,
                            AVG(risk_score) as avg_risk_score,
                            AVG(guardrail_effectiveness_rate) as effectiveness_rate,
                            SUM(unique_users) as unique_users_total
                        FROM daily_summary 
                        WHERE datetime(date_hour) >= datetime('now', ?)
                    """, (f'-{hours_back} hours',))
                    
                    summary_row = cursor.fetchone()
                    
                    if summary_row and summary_row['total_requests']:
                        summary = dict(summary_row)
                        summary['block_rate'] = summary['blocked_requests'] / summary['total_requests'] if summary['total_requests'] > 0 else 0
                        
                        # Get guardrail analysis
                        guardrail_analysis = await self._get_guardrail_analysis_optimized(hours_back)
                        
                        # Get user activity from user_summary
                        cursor = conn.execute("""
                            SELECT 
                                user_identifier, ip_address, hostname,
                                total_requests, blocked_requests, risk_score,
                                blocked_percentage, last_active_timestamp
                            FROM user_summary 
                            WHERE datetime(last_active_timestamp) >= datetime('now', ?)
                            ORDER BY risk_score DESC, blocked_requests DESC
                            LIMIT 10
                        """, (f'-{hours_back} hours',))
                        
                        user_activity = {}
                        for user_row in cursor.fetchall():
                            user_dict = dict(user_row)
                            user_activity[user_dict['user_identifier']] = user_dict
                        
                        # Get provider performance
                        cursor = conn.execute("""
                            SELECT 
                                provider_name,
                                SUM(total_requests) as total_requests,
                                SUM(blocked_responses) as blocked_responses,
                                AVG(avg_response_time) as avg_response_time_ms,
                                AVG(error_rate) as error_rate,
                                SUM(estimated_cost) as total_cost
                            FROM provider_summary 
                            WHERE datetime(date_hour) >= datetime('now', ?)
                            GROUP BY provider_name
                        """, (f'-{hours_back} hours',))
                        
                        provider_performance = {}
                        for provider_row in cursor.fetchall():
                            provider_dict = dict(provider_row)
                            provider_performance[provider_dict['provider_name']] = provider_dict
                        
                        dashboard_data[timeframe] = {
                            'summary': summary,
                            'guardrail_analysis': guardrail_analysis,
                            'user_activity': user_activity,
                            'provider_performance': provider_performance,
                            'alerts': [],  # Can be enhanced later
                            'data_points': summary['total_requests']
                        }
                    else:
                        dashboard_data[timeframe] = {
                            'summary': {'total_requests': 0, 'blocked_requests': 0, 'allowed_requests': 0},
                            'guardrail_analysis': {},
                            'user_activity': {},
                            'provider_performance': {},
                            'alerts': [],
                            'data_points': 0
                        }
                
                return {
                    'export_metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'export_version': '2.0',
                        'time_ranges': timeframes,
                        'database_path': str(self.db_path),
                        'system_info': await self._get_system_info()
                    },
                    'time_ranges': dashboard_data
                }
                
        except Exception as e:
            app_logger.error(f"Failed to get optimized main dashboard data: {e}")
            # Fall back to original method
            return await self._get_main_dashboard_data()
    
    async def _get_optimized_user_dashboard_data(self) -> dict:
        """Get user dashboard data from optimized aggregated tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get user list from user_summary table
                cursor = conn.execute("""
                    SELECT 
                        user_identifier, ip_address, email, hostname,
                        risk_score, total_requests, blocked_requests, 
                        blocked_percentage, last_active_timestamp,
                        violation_severity_avg, request_frequency_score
                    FROM user_summary 
                    WHERE datetime(last_active_timestamp) >= datetime('now', '-30 days')
                    ORDER BY risk_score DESC, blocked_percentage DESC, total_requests DESC
                    LIMIT 500
                """)
                
                users_list = []
                for row in cursor.fetchall():
                    user_dict = dict(row)
                    users_list.append({
                        'user_id': user_dict['user_identifier'],
                        'ip_address': user_dict['ip_address'],
                        'email': user_dict['email'],
                        'hostname': user_dict['hostname'] or 'Unknown',
                        'risk_score': user_dict['risk_score'],
                        'total_requests': user_dict['total_requests'],
                        'blocked_percentage': user_dict['blocked_percentage'],
                        'last_active': user_dict['last_active_timestamp']
                    })
                
                # Get overview stats
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        SUM(CASE WHEN risk_score >= 70 THEN 1 ELSE 0 END) as high_risk_users,
                        SUM(CASE WHEN risk_score BETWEEN 40 AND 69 THEN 1 ELSE 0 END) as medium_risk_users,
                        AVG(risk_score) as avg_risk_score,
                        SUM(total_requests) as total_requests,
                        SUM(blocked_requests) as total_blocked
                    FROM user_summary
                    WHERE datetime(last_active_timestamp) >= datetime('now', '-30 days')
                """)
                
                stats_row = cursor.fetchone()
                overview_stats = dict(stats_row) if stats_row else {}
                
                return {
                    'users_list': users_list,
                    'overview_stats': overview_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            app_logger.error(f"Failed to get optimized user dashboard data: {e}")
            # Fall back to original method
            return await self._get_user_dashboard_data()
    
    async def _get_guardrail_analysis_optimized(self, hours_back: int) -> dict:
        """Get guardrail analysis from sensitive_data_summary table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get sensitive data detections
                cursor = conn.execute("""
                    SELECT 
                        data_type,
                        SUM(detection_count) as triggers,
                        AVG(confidence_avg) as avg_confidence,
                        MAX(confidence_avg) as max_score,
                        COUNT(*) as total_analyzed,
                        (SUM(detection_count) * 100.0 / COUNT(*)) as effectiveness_percentage
                    FROM sensitive_data_summary 
                    WHERE datetime(date_hour) >= datetime('now', ?)
                    GROUP BY data_type
                """, (f'-{hours_back} hours',))
                
                guardrail_data = {}
                for row in cursor.fetchall():
                    data_type = row['data_type'].lower().replace('_', ' ')
                    # Map data types to guardrail names
                    guardrail_name = self._map_data_type_to_guardrail(row['data_type'])
                    
                    guardrail_data[guardrail_name] = {
                        'triggers': row['triggers'] or 0,
                        'avg_confidence': row['avg_confidence'] or 0.0,
                        'max_score': row['max_score'] or 0.0,
                        'total_analyzed': row['total_analyzed'] or 0,
                        'effectiveness_percentage': row['effectiveness_percentage'] or 0.0
                    }
                
                return guardrail_data
                
        except Exception as e:
            app_logger.error(f"Failed to get guardrail analysis: {e}")
            return {}
    
    def _timeframe_to_hours(self, timeframe: str) -> int:
        """Convert timeframe string to hours"""
        mapping = {
            '1h': 1, '6h': 6, '12h': 12, '24h': 24,
            '3d': 72, '1w': 168, '1M': 720, '3M': 2160, '6M': 4320, '1Y': 8760
        }
        return mapping.get(timeframe, 24)
    
    def _map_data_type_to_guardrail(self, data_type: str) -> str:
        """Map sensitive data type to guardrail name"""
        mapping = {
            'PII_DETECTION': 'pii',
            'CREDIT_CARD': 'pii',
            'EMAIL_ADDRESS': 'pii',
            'API_KEYS': 'privacy',
            'TOXIC_CONTENT': 'toxicity',
            'PROMPT_INJECTION': 'prompt_injection',
            'HATE_SPEECH': 'hate_speech',
            'BIAS_CONTENT': 'bias'
        }
        return mapping.get(data_type, data_type.lower())
    
    def _get_top_violation_policy(self, violated_categories: dict) -> str:
        """Get the top violation policy from violated categories"""
        if not violated_categories:
            return "No violations"
        
        max_category = max(violated_categories.items(), key=lambda x: x[1])
        percentage = (max_category[1] / sum(violated_categories.values())) * 100
        return f"{max_category[0].replace('_', ' ').title()} ({percentage:.1f}%)"
    
    async def _get_system_info(self) -> dict:
        """Get system information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get database stats
                cursor = conn.execute("SELECT COUNT(*) FROM user_analytics")
                total_records = cursor.fetchone()[0]
                
                # Get database file size
                db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
                return {
                    'total_records': total_records,
                    'database_size_mb': round(db_size_mb, 2)
                }
        except Exception:
            return {'total_records': 0, 'database_size_mb': 0}

# Global instance
dashboard_websocket_manager = DashboardWebSocketManager()