import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Memory,
  Speed,
  Storage,
  DeveloperBoard as Cpu,
  Refresh,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import { useOllamaModels } from '../../hooks/useOllamaModels';
import { OllamaModel } from '../../services/ollamaModels';

// Interfaces for hardware monitoring data
interface SystemMetrics {
  cpu: {
    usage_percent: number;
    cores: number;
    frequency_mhz: number;
    temperature?: number;
    processes: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    available_gb: number;
    usage_percent: number;
    swap_total_gb: number;
    swap_used_gb: number;
  };
  gpu: {
    devices: Array<{
      device_id: number;
      name: string;
      vendor: string;
      memory_total_gb: number;
      memory_used_gb: number;
      utilization_percent: number;
      temperature?: number;
      power_usage?: number;
      is_active: boolean;
      driver_version: string;
    }>;
    total_memory_gb: number;
    used_memory_gb: number;
    temperature?: number;
    power_usage?: number;
    utilization_percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    available_gb: number;
    usage_percent: number;
    io_read_mb_s: number;
    io_write_mb_s: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
    download_speed_mb_s: number;
    upload_speed_mb_s: number;
  };
  timestamp: number;
}

interface HardwareResponse {
  success: boolean;
  metrics: SystemMetrics;
  message?: string;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const HardwareMonitoringDashboard: React.FC = () => {
  console.log('🖥️ HardwareMonitoringDashboard: Component rendering');
  
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historicalData, setHistoricalData] = useState<Array<{timestamp: string, cpu: number, memory: number}>>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Get Ollama models for the models section
  const { models: ollamaModels, isLoading: modelsLoading, error: modelsError } = useOllamaModels();

  const fetchHardwareMetrics = useCallback(async () => {
    console.log('🔄 Fetching hardware metrics...');
    try {
      const response = await fetch(`${BACKEND_URL}/api/hardware/metrics`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: HardwareResponse = await response.json();
      console.log('✅ Hardware metrics fetched successfully:', data);

      if (data.success && data.metrics) {
        setMetrics(data.metrics);
        setLastUpdate(new Date());
        
        // Add to historical data for charts
        const now = new Date().toLocaleTimeString();
        setHistoricalData(prev => [
          ...prev.slice(-19), // Keep last 20 data points
          {
            timestamp: now,
            cpu: data.metrics.cpu.usage_percent,
            memory: data.metrics.memory.usage_percent,
          }
        ]);
        
        setError(null);
      } else {
        throw new Error(data.message || 'Invalid response format');
      }
    } catch (err) {
      console.error('❌ Error fetching hardware metrics:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast.error(`Hardware monitoring error: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and auto-refresh setup
  useEffect(() => {
    fetchHardwareMetrics();
    
    let interval: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchHardwareMetrics, 3000); // Refresh every 3 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchHardwareMetrics, autoRefresh]);

  const getStatusColor = (percentage: number) => {
    if (percentage >= 90) return '#ef4444'; // Red for critical
    if (percentage >= 70) return '#f59e0b'; // Orange for warning
    return '#00D4AA'; // Green for normal
  };

  const getStatusIcon = (percentage: number) => {
    if (percentage >= 90) return <ErrorIcon />;
    if (percentage >= 70) return <Warning />;
    return <CheckCircle />;
  };

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        flexDirection: 'column',
        gap: 2
      }}>
        <CircularProgress size={60} sx={{ color: '#00D4AA' }} />
        <Typography sx={{ color: '#6b7280' }}>Loading hardware metrics...</Typography>
      </Box>
    );
  }

  if (error && !metrics) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load hardware metrics: {error}
        </Alert>
        <Button onClick={fetchHardwareMetrics} variant="outlined" startIcon={<Refresh />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 3 
        }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, color: '#ffffff' }}>
              Hardware Analytics Dashboard
            </Typography>
            <Typography variant="body2" sx={{ color: '#6b7280' }}>
              Real-time system monitoring and performance analytics
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              color={autoRefresh ? 'success' : 'default'}
              size="small"
              onClick={() => setAutoRefresh(!autoRefresh)}
              sx={{ cursor: 'pointer' }}
            />
            <Tooltip title="Refresh Now">
              <IconButton onClick={fetchHardwareMetrics} sx={{ color: '#00D4AA' }}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {error && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            Warning: {error} (Showing cached data)
          </Alert>
        )}

        {metrics && (
          <>
            {/* System Overview Cards */}
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: '1fr 1fr 1fr 1fr' }, 
              gap: 3, 
              mb: 4 
            }}>
              {/* CPU Card */}
              <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Cpu sx={{ color: '#00D4AA', mr: 1 }} />
                    <Typography variant="h6" sx={{ color: '#ffffff' }}>CPU</Typography>
                    {getStatusIcon(metrics.cpu.usage_percent)}
                  </Box>
                  <Typography variant="h3" sx={{ 
                    color: getStatusColor(metrics.cpu.usage_percent), 
                    fontWeight: 'bold',
                    mb: 1
                  }}>
                    {metrics.cpu.usage_percent.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={metrics.cpu.usage_percent}
                    sx={{ 
                      mb: 2,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getStatusColor(metrics.cpu.usage_percent)
                      }
                    }}
                  />
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    {metrics.cpu.cores} cores • {metrics.cpu.processes} processes
                  </Typography>
                </CardContent>
              </Card>

              {/* Memory Card */}
              <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Memory sx={{ color: '#00D4AA', mr: 1 }} />
                    <Typography variant="h6" sx={{ color: '#ffffff' }}>Memory</Typography>
                    {getStatusIcon(metrics.memory.usage_percent)}
                  </Box>
                  <Typography variant="h3" sx={{ 
                    color: getStatusColor(metrics.memory.usage_percent), 
                    fontWeight: 'bold',
                    mb: 1
                  }}>
                    {metrics.memory.usage_percent.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={metrics.memory.usage_percent}
                    sx={{ 
                      mb: 2,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getStatusColor(metrics.memory.usage_percent)
                      }
                    }}
                  />
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    {metrics.memory.used_gb.toFixed(1)}GB / {metrics.memory.total_gb.toFixed(1)}GB
                  </Typography>
                </CardContent>
              </Card>

              {/* Storage Card */}
              <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Storage sx={{ color: '#00D4AA', mr: 1 }} />
                    <Typography variant="h6" sx={{ color: '#ffffff' }}>Storage</Typography>
                    {getStatusIcon(metrics.disk.usage_percent)}
                  </Box>
                  <Typography variant="h3" sx={{ 
                    color: getStatusColor(metrics.disk.usage_percent), 
                    fontWeight: 'bold',
                    mb: 1
                  }}>
                    {metrics.disk.usage_percent.toFixed(1)}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={metrics.disk.usage_percent}
                    sx={{ 
                      mb: 2,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getStatusColor(metrics.disk.usage_percent)
                      }
                    }}
                  />
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    {(metrics.disk.total_gb - metrics.disk.available_gb).toFixed(1)}GB / {metrics.disk.total_gb.toFixed(1)}GB
                  </Typography>
                </CardContent>
              </Card>

              {/* GPU Card */}
              <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Speed sx={{ color: '#00D4AA', mr: 1 }} />
                    <Typography variant="h6" sx={{ color: '#ffffff' }}>GPU</Typography>
                  </Box>
                  {metrics.gpu.devices.length > 0 ? (
                    <>
                      <Typography variant="h3" sx={{ 
                        color: getStatusColor(metrics.gpu.devices[0].utilization_percent), 
                        fontWeight: 'bold',
                        mb: 1
                      }}>
                        {metrics.gpu.devices[0].utilization_percent.toFixed(1)}%
                      </Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={metrics.gpu.devices[0].utilization_percent}
                        sx={{ 
                          mb: 2,
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getStatusColor(metrics.gpu.devices[0].utilization_percent)
                          }
                        }}
                      />
                      <Typography variant="body2" sx={{ color: '#6b7280' }}>
                        {metrics.gpu.devices[0].name}
                      </Typography>
                    </>
                  ) : (
                    <Typography sx={{ color: '#6b7280' }}>No GPU detected</Typography>
                  )}
                </CardContent>
              </Card>
            </Box>

            {/* Historical Performance Chart */}
            {historicalData.length > 0 && (
              <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', mb: 4 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ color: '#ffffff', mb: 3 }}>
                    Performance History
                  </Typography>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="timestamp" stroke="#6b7280" />
                        <YAxis stroke="#6b7280" />
                        <RechartsTooltip 
                          contentStyle={{ 
                            backgroundColor: '#1f2937', 
                            border: '1px solid #374151',
                            borderRadius: '8px'
                          }} 
                        />
                        <Area
                          type="monotone"
                          dataKey="cpu"
                          stackId="1"
                          stroke="#00D4AA"
                          fill="#00D4AA"
                          fillOpacity={0.3}
                          name="CPU Usage (%)"
                        />
                        <Area
                          type="monotone"
                          dataKey="memory"
                          stackId="2"
                          stroke="#3b82f6"
                          fill="#3b82f6"
                          fillOpacity={0.3}
                          name="Memory Usage (%)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Ollama Models Section */}
            <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" sx={{ color: '#ffffff', flexGrow: 1 }}>
                    Available Ollama Models
                  </Typography>
                  <Chip 
                    label={`${ollamaModels.length} models`} 
                    sx={{ bgcolor: '#00D4AA', color: '#000000', fontWeight: 'bold' }}
                  />
                </Box>

                {modelsLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress size={40} sx={{ color: '#00D4AA' }} />
                  </Box>
                ) : modelsError ? (
                  <Alert severity="error">Error loading models: {modelsError}</Alert>
                ) : (
                  <Box sx={{ 
                    display: 'grid', 
                    gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, 
                    gap: 2,
                    maxHeight: 400,
                    overflowY: 'auto'
                  }}>
                    {ollamaModels.slice(0, 12).map((model: OllamaModel, index: number) => (
                      <Card key={index} sx={{ bgcolor: '#1f2937', border: '1px solid #374151' }}>
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="body1" sx={{ 
                            color: '#ffffff', 
                            fontWeight: 'bold', 
                            mb: 1,
                            fontSize: '0.9rem'
                          }}>
                            {model.name}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, mb: 1, flexWrap: 'wrap' }}>
                            <Chip
                              label={model.compatibility_label}
                              size="small"
                              sx={{ 
                                bgcolor: model.compatibility_score >= 80 ? '#00D4AA' : 
                                        model.compatibility_score >= 60 ? '#f59e0b' : '#ef4444',
                                color: '#000000',
                                fontSize: '0.6rem',
                                height: '18px'
                              }}
                            />
                            {model.sizes.length > 0 && (
                              <Chip
                                label={model.sizes[0]}
                                size="small"
                                sx={{ 
                                  bgcolor: '#374151',
                                  color: '#ffffff',
                                  fontSize: '0.6rem',
                                  height: '18px'
                                }}
                              />
                            )}
                          </Box>
                          <Typography variant="caption" sx={{ 
                            color: '#6b7280', 
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {model.description}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}
                
                {ollamaModels.length > 12 && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                      Showing 12 of {ollamaModels.length} models
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Footer with last update info */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="caption" sx={{ color: '#6b7280' }}>
                Last updated: {lastUpdate.toLocaleTimeString()}
              </Typography>
            </Box>
          </>
        )}
      </Box>
    </motion.div>
  );
};

export default HardwareMonitoringDashboard;