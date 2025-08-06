import React from 'react';
import {
  Box,
  Typography,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Tune as ConfigIcon,
  Cloud as CloudIcon,
  Speed as PerformanceIcon,
  Security as SecurityIcon,
  Storage as DatabaseIcon,
  Monitor as MonitorIcon,
  Settings as AdvancedIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import CodeBlock from '../components/CodeBlock';

const AdvancedConfiguration: React.FC = () => {
  const configurationAreas = [
    {
      name: 'Enterprise Deployment',
      icon: <CloudIcon sx={{ color: '#3b82f6' }} />,
      description: 'Production-ready deployment configurations',
      topics: ['Load balancing', 'High availability', 'Container orchestration', 'SSL/TLS setup']
    },
    {
      name: 'Performance Tuning',
      icon: <PerformanceIcon sx={{ color: '#00D4AA' }} />,
      description: 'Optimize system performance and throughput',
      topics: ['Caching strategies', 'Connection pooling', 'Resource allocation', 'Batch processing']
    },
    {
      name: 'Security Hardening',
      icon: <SecurityIcon sx={{ color: '#ef4444' }} />,
      description: 'Advanced security configurations and best practices',
      topics: ['Authentication methods', 'API security', 'Network security', 'Audit logging']
    },
    {
      name: 'Data Management',
      icon: <DatabaseIcon sx={{ color: '#f59e0b' }} />,
      description: 'Database and storage configuration options',
      topics: ['Database optimization', 'Data retention', 'Backup strategies', 'Migration tools']
    },
    {
      name: 'Monitoring & Observability',
      icon: <MonitorIcon sx={{ color: '#8b5cf6' }} />,
      description: 'Comprehensive monitoring and alerting setup',
      topics: ['Metrics collection', 'Log aggregation', 'Alert configuration', 'Dashboard setup']
    }
  ];

  const advancedExamples = [
    {
      language: 'yaml',
      filename: 'docker-compose.production.yml',
      code: `version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - guardrails-api-1
      - guardrails-api-2
    restart: unless-stopped

  # Guardrails API Instances (Load Balanced)
  guardrails-api-1: &guardrails-api
    build: 
      context: ./backend
      dockerfile: Dockerfile.production
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/guardrails
      - REDIS_URL=redis://redis:6379/0
      - MODEL_CACHE_SIZE=1000
      - MAX_WORKERS=4
      - LOG_LEVEL=INFO
      - ENABLE_METRICS=true
      - PROMETHEUS_PORT=9090
    depends_on:
      - postgres
      - redis
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  guardrails-api-2:
    <<: *guardrails-api

  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=guardrails
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass redis_password
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

  # Log Management
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    deploy:
      resources:
        limits:
          memory: 2G
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  default:
    driver: bridge`
    },
    {
      language: 'python',
      filename: 'advanced_config.py',
      code: `import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class DeploymentMode(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    database: str = "guardrails"
    username: str = "user"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    ssl_mode: str = "prefer"
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class CacheConfig:
    """Cache configuration settings."""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_ttl: int = 3600  # 1 hour
    max_connections: int = 50
    retry_on_timeout: bool = True
    
    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

@dataclass  
class SecurityConfig:
    """Security configuration settings."""
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    jwt_secret: Optional[str] = None
    jwt_expiry: int = 3600  # 1 hour
    cors_origins: list = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    allowed_content_types: list = field(default_factory=lambda: ["application/json", "text/plain"])
    
@dataclass
class ModelConfig:
    """Model configuration settings."""
    cache_size: int = 1000
    max_batch_size: int = 32
    timeout_seconds: int = 30
    enable_gpu: bool = False
    gpu_memory_fraction: float = 0.5
    model_download_timeout: int = 300  # 5 minutes
    enable_model_versioning: bool = True
    auto_update_models: bool = False
    
@dataclass
class MonitoringConfig:
    """Monitoring and observability settings."""
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    jaeger_endpoint: Optional[str] = None
    log_sampling_rate: float = 1.0
    health_check_interval: int = 30  # seconds
    alert_webhook_url: Optional[str] = None
    
@dataclass
class PerformanceConfig:
    """Performance tuning settings."""
    max_workers: int = 4
    worker_timeout: int = 120
    max_requests_per_worker: int = 1000
    enable_async: bool = True
    request_queue_size: int = 1000
    connection_timeout: int = 30
    read_timeout: int = 60
    write_timeout: int = 60

class AdvancedGuardrailsConfig:
    """Advanced configuration management for Guardrails system."""
    
    def __init__(self, deployment_mode: DeploymentMode = DeploymentMode.DEVELOPMENT):
        self.deployment_mode = deployment_mode
        self.database = DatabaseConfig()
        self.cache = CacheConfig() 
        self.security = SecurityConfig()
        self.models = ModelConfig()
        self.monitoring = MonitoringConfig()
        self.performance = PerformanceConfig()
        
        # Load configuration from environment
        self._load_from_environment()
        
        # Apply deployment-specific settings
        self._apply_deployment_settings()
        
        # Validate configuration
        self._validate_config()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Database settings
        self.database.host = os.getenv("DB_HOST", self.database.host)
        self.database.port = int(os.getenv("DB_PORT", str(self.database.port)))
        self.database.database = os.getenv("DB_NAME", self.database.database)
        self.database.username = os.getenv("DB_USER", self.database.username)
        self.database.password = os.getenv("DB_PASSWORD", self.database.password)
        
        # Cache settings
        self.cache.redis_host = os.getenv("REDIS_HOST", self.cache.redis_host)
        self.cache.redis_port = int(os.getenv("REDIS_PORT", str(self.cache.redis_port)))
        self.cache.redis_password = os.getenv("REDIS_PASSWORD", self.cache.redis_password)
        
        # Security settings
        self.security.jwt_secret = os.getenv("JWT_SECRET", self.security.jwt_secret)
        cors_origins = os.getenv("CORS_ORIGINS")
        if cors_origins:
            self.security.cors_origins = cors_origins.split(",")
        
        # Performance settings
        self.performance.max_workers = int(os.getenv("MAX_WORKERS", str(self.performance.max_workers)))
        
        # Model settings
        self.models.enable_gpu = os.getenv("ENABLE_GPU", "false").lower() == "true"
        self.models.cache_size = int(os.getenv("MODEL_CACHE_SIZE", str(self.models.cache_size)))
        
        # Monitoring settings
        self.monitoring.enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.monitoring.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
        self.monitoring.alert_webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    
    def _apply_deployment_settings(self):
        """Apply deployment-specific configuration overrides."""
        if self.deployment_mode == DeploymentMode.PRODUCTION:
            # Production optimizations
            self.database.pool_size = 20
            self.database.max_overflow = 40
            self.performance.max_workers = 8
            self.security.cors_origins = []  # Restrict in production
            self.models.auto_update_models = False
            self.monitoring.log_sampling_rate = 0.1  # Sample 10% of logs
            
        elif self.deployment_mode == DeploymentMode.STAGING:
            # Staging optimizations
            self.database.pool_size = 10
            self.performance.max_workers = 4
            self.monitoring.log_sampling_rate = 0.5  # Sample 50% of logs
            
        elif self.deployment_mode == DeploymentMode.DEVELOPMENT:
            # Development settings
            self.database.pool_size = 5
            self.performance.max_workers = 2
            self.models.auto_update_models = True
            self.monitoring.log_sampling_rate = 1.0  # Log everything
    
    def _validate_config(self):
        """Validate configuration settings."""
        errors = []
        
        # Database validation
        if not self.database.password and self.deployment_mode == DeploymentMode.PRODUCTION:
            errors.append("Database password is required in production")
        
        # Security validation  
        if not self.security.jwt_secret and self.deployment_mode != DeploymentMode.DEVELOPMENT:
            errors.append("JWT secret is required in staging/production")
        
        if self.security.cors_origins == ["*"] and self.deployment_mode == DeploymentMode.PRODUCTION:
            errors.append("CORS origins should be restricted in production")
        
        # Performance validation
        if self.performance.max_workers < 1:
            errors.append("Max workers must be at least 1")
        
        if self.models.cache_size < 100:
            errors.append("Model cache size should be at least 100")
        
        if errors:
            raise ValueError("Configuration validation failed:\\n" + "\\n".join(f"  - {error}" for error in errors))
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        level = LogLevel.INFO if self.deployment_mode == DeploymentMode.PRODUCTION else LogLevel.DEBUG
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": level.value,
                    "formatter": "detailed" if self.deployment_mode != DeploymentMode.PRODUCTION else "simple",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": level.value,
                    "formatter": "detailed",
                    "filename": f"logs/guardrails_{self.deployment_mode.value}.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {
                    "level": level.value,
                    "handlers": ["console", "file"]
                }
            }
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "deployment_mode": self.deployment_mode.value,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow
            },
            "cache": {
                "host": self.cache.redis_host,
                "port": self.cache.redis_port,
                "default_ttl": self.cache.default_ttl
            },
            "security": {
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window": self.security.rate_limit_window,
                "max_request_size": self.security.max_request_size
            },
            "models": {
                "cache_size": self.models.cache_size,
                "enable_gpu": self.models.enable_gpu,
                "timeout_seconds": self.models.timeout_seconds
            },
            "performance": {
                "max_workers": self.performance.max_workers,
                "worker_timeout": self.performance.worker_timeout
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "enable_tracing": self.monitoring.enable_tracing
            }
        }

# Usage example
if __name__ == "__main__":
    # Production configuration
    config = AdvancedGuardrailsConfig(DeploymentMode.PRODUCTION)
    
    print("Production Configuration:")
    print("=" * 40)
    
    # Export and display configuration
    config_dict = config.export_config()
    for section, settings in config_dict.items():
        print(f"\\n[{section.upper()}]")
        for key, value in settings.items():
            print(f"  {key}: {value}")
    
    # Setup logging
    import logging.config
    logging.config.dictConfig(config.get_logging_config())
    
    logger = logging.getLogger(__name__)
    logger.info("Advanced configuration initialized successfully")
    logger.info(f"Deployment mode: {config.deployment_mode.value}")
    logger.info(f"Database URL: {config.database.url}")
    logger.info(f"Redis URL: {config.cache.redis_url}")`
    },
    {
      language: 'bash',
      filename: 'monitoring-setup.sh',
      code: `#!/bin/bash

# Guardrails System Monitoring Setup Script
# This script sets up comprehensive monitoring for the Guardrails system

set -e

echo "🔧 Setting up Guardrails System Monitoring..."

# Configuration
GRAFANA_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD:-"admin123"}
PROMETHEUS_RETENTION=\${PROMETHEUS_RETENTION:-"30d"}
ELASTICSEARCH_MEMORY=\${ELASTICSEARCH_MEMORY:-"2g"}

# Create monitoring directories
mkdir -p monitoring/{prometheus,grafana,elasticsearch,kibana}
mkdir -p monitoring/grafana/{dashboards,datasources}
mkdir -p logs

echo "📊 Configuring Prometheus..."

# Prometheus configuration
cat > monitoring/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'guardrails-monitor'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'guardrails-api'
    static_configs:
      - targets: ['guardrails-api-1:9090', 'guardrails-api-2:9090']
    metrics_path: '/metrics'
    scrape_interval: 10s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis' 
    static_configs:
      - targets: ['redis-exporter:9121']
      
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
      
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

# Prometheus alert rules
cat > monitoring/prometheus/alert_rules.yml << EOF
groups:
  - name: guardrails.rules
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ \\$value }} errors per second"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "95th percentile latency is {{ \\$value }}s"
          
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database has {{ \\$value }} active connections"
          
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is {{ \\$value | humanizePercentage }}"
          
      - alert: GuardrailsServiceDown
        expr: up{job="guardrails-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Guardrails service is down"
          description: "Guardrails API instance {{ \\$labels.instance }} is down"
EOF

echo "📈 Configuring Grafana..."

# Grafana datasource
cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

# Grafana dashboard for Guardrails
cat > monitoring/grafana/dashboards/guardrails-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Guardrails System Monitoring",
    "tags": ["guardrails", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Safety Detections",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(guardrails_detections_total[5m])",
            "legendFormat": "{{detector}}"
          }
        ],
        "yAxes": [
          {
            "label": "Detections/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 24,
          "x": 0,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

echo "🔍 Setting up log aggregation..."

# Elasticsearch configuration
cat > monitoring/elasticsearch/elasticsearch.yml << EOF
cluster.name: "guardrails-logs"
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
xpack.monitoring.collection.enabled: true

# Performance settings
indices.memory.index_buffer_size: 30%
bootstrap.memory_lock: true

# Index management
index.number_of_shards: 1
index.number_of_replicas: 0
EOF

# Kibana configuration
cat > monitoring/kibana/kibana.yml << EOF
server.name: kibana
server.host: 0.0.0.0
elasticsearch.hosts: ["http://elasticsearch:9200"]

# Monitoring
monitoring.ui.container.elasticsearch.enabled: true
monitoring.ui.container.kibana.enabled: true

# Security
xpack.security.enabled: false
xpack.encryptedSavedObjects.encryptionKey: "a7a6311933d3503b89bc2dbc36572c33a7a6311933d3503b89bc2dbc36572c33"
EOF

echo "🚨 Setting up alerting..."

# Alertmanager configuration
mkdir -p monitoring/alertmanager
cat > monitoring/alertmanager/alertmanager.yml << EOF
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@guardrails.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'webhook'

receivers:
  - name: 'webhook'
    webhook_configs:
      - url: 'http://alertmanager-webhook:5000/alerts'
        send_resolved: true
        
  - name: 'email'
    email_configs:
      - to: 'admin@company.com'
        subject: 'Guardrails Alert: {{ .GroupLabels.alertname }}'
        body: |
          Alert: {{ .GroupLabels.alertname }}
          Summary: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}
          Description: {{ range .Alerts }}{{ .Annotations.description }}{{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

echo "🐳 Creating monitoring Docker Compose override..."

cat > docker-compose.monitoring.yml << EOF
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=\${PROMETHEUS_RETENTION}'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_ADMIN_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)(\\$|/)'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

echo "✅ Monitoring setup complete!"
echo ""
echo "🚀 To start monitoring:"
echo "  docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d"
echo ""
echo "📊 Access monitoring services:"
echo "  Grafana:      http://localhost:3001 (admin/\${GRAFANA_ADMIN_PASSWORD})"
echo "  Prometheus:   http://localhost:9090"
echo "  Alertmanager: http://localhost:9093"
echo "  Kibana:       http://localhost:5601"
echo ""
echo "📝 Next steps:"
echo "  1. Import Grafana dashboards"
echo "  2. Configure alert notifications"
echo "  3. Set up log shipping to Elasticsearch"
echo "  4. Test alert rules"

chmod +x monitoring-setup.sh`
    }
  ];

  const configurationTable = [
    { parameter: 'MAX_WORKERS', type: 'Integer', default: '4', description: 'Number of worker processes', production: '8-16' },
    { parameter: 'DB_POOL_SIZE', type: 'Integer', default: '10', description: 'Database connection pool size', production: '20-50' },
    { parameter: 'CACHE_TTL', type: 'Integer', default: '3600', description: 'Cache time-to-live in seconds', production: '7200' },
    { parameter: 'MODEL_CACHE_SIZE', type: 'Integer', default: '1000', description: 'Number of cached model results', production: '5000' },
    { parameter: 'REQUEST_TIMEOUT', type: 'Integer', default: '30', description: 'Request timeout in seconds', production: '60' },
    { parameter: 'ENABLE_GPU', type: 'Boolean', default: 'false', description: 'Enable GPU acceleration', production: 'true' },
    { parameter: 'LOG_LEVEL', type: 'String', default: 'INFO', description: 'Logging level', production: 'WARNING' },
    { parameter: 'RATE_LIMIT', type: 'Integer', default: '100', description: 'Requests per minute per IP', production: '1000' }
  ];

  return (
    <Box sx={{ p: 4, maxHeight: '100vh', overflow: 'auto' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Introduction */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700, mb: 2 }}>
            Advanced Configuration
          </Typography>
          <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 3, lineHeight: 1.6 }}>
            Configure the AI Guardrails system for enterprise deployment with advanced settings, 
            monitoring, security, and performance optimization options.
          </Typography>

          <Alert severity="warning" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Enterprise Notice:</strong> These configurations are designed for production environments. 
              Test thoroughly in staging before applying to production systems.
            </Typography>
          </Alert>
        </Box>

        {/* Configuration Areas */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Configuration Areas
        </Typography>

        <Box sx={{ display: 'grid', gap: 3, mb: 4 }}>
          {configurationAreas.map((area, index) => (
            <motion.div
              key={area.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Card sx={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(0, 212, 170, 0.3)'
                },
                transition: 'all 0.2s ease-in-out'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    {area.icon}
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                        {area.name}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        {area.description}
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {area.topics.map((topic) => (
                      <Chip
                        key={topic}
                        label={topic}
                        size="small"
                        variant="outlined"
                        sx={{
                          borderColor: 'rgba(255, 255, 255, 0.2)',
                          color: '#e2e8f0',
                          fontSize: '0.7rem'
                        }}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </Box>

        {/* Configuration Examples */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Enterprise Configuration Examples
        </Typography>

        <CodeBlock
          examples={advancedExamples}
          title="Production-Ready Configuration Files"
          description="Complete configuration examples for enterprise deployment:"
        />

        {/* Configuration Parameters */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Key Configuration Parameters
        </Typography>

        <TableContainer component={Paper} sx={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          mb: 4
        }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#ffffff', fontWeight: 600 }}>Parameter</TableCell>
                <TableCell sx={{ color: '#ffffff', fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ color: '#ffffff', fontWeight: 600 }}>Default</TableCell>
                <TableCell sx={{ color: '#ffffff', fontWeight: 600 }}>Description</TableCell>
                <TableCell sx={{ color: '#ffffff', fontWeight: 600 }}>Production Rec.</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {configurationTable.map((row) => (
                <TableRow key={row.parameter}>
                  <TableCell sx={{ 
                    color: '#00D4AA', 
                    fontFamily: 'monospace',
                    fontWeight: 600
                  }}>
                    {row.parameter}
                  </TableCell>
                  <TableCell sx={{ color: '#a1a1aa' }}>{row.type}</TableCell>
                  <TableCell sx={{ color: '#a1a1aa', fontFamily: 'monospace' }}>
                    {row.default}
                  </TableCell>
                  <TableCell sx={{ color: '#e2e8f0' }}>{row.description}</TableCell>
                  <TableCell sx={{ color: '#f59e0b', fontFamily: 'monospace' }}>
                    {row.production}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Best Practices */}
        <Card sx={{
          background: 'rgba(16, 185, 129, 0.05)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          mt: 4
        }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <AdvancedIcon sx={{ color: '#10b981' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                Production Deployment Best Practices
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Use environment-specific configurations"
                  secondary="Separate config files for development, staging, and production"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <SecurityIcon sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Implement comprehensive monitoring"
                  secondary="Set up metrics, logging, and alerting for all components"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <PerformanceIcon sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Load test before production"
                  secondary="Validate performance under expected production load"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <DatabaseIcon sx={{ color: '#10b981', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Plan for data persistence and backup"
                  secondary="Implement automated backups and disaster recovery procedures"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Alert severity="info" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>Next:</strong> Review the "API Reference" section for detailed API documentation 
            and integration examples, or return to earlier sections to complete your setup.
          </Typography>
        </Alert>
      </motion.div>
    </Box>
  );
};

export default AdvancedConfiguration;