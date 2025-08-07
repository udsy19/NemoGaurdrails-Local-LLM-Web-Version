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
  Switch,
  FormControlLabel,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Memory,
  Speed,
  Computer,
  Timeline,
  Storage,
  DeveloperBoard as Cpu,
  Thermostat,
  Power,
  Refresh,
  Settings,
  PlayArrow,
  Stop,
  Clear,
  Download,
  Upload,
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  Info,
  ExpandMore,
  Close,
  Fullscreen,
  FullscreenExit,
  Visibility,
  VisibilityOff,
  Analytics,
  Tune,
  Build
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
  RadialBarChart,
  RadialBar
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
    swap_total_gb?: number;
    swap_used_gb?: number;
  };
  gpu: {
    devices: GPUDevice[];
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

interface GPUDevice {
  device_id: number;
  name: string;
  vendor: string;
  memory_total_gb: number;
  memory_used_gb: number;
  utilization_percent: number;
  temperature?: number;
  power_usage?: number;
  is_active: boolean;
  driver_version?: string;
}

interface ModelPerformanceMetrics {
  model_name: string;
  memory_usage_mb: number;
  inference_time_ms: number;
  tokens_per_second: number;
  gpu_utilization_percent: number;
  cpu_utilization_percent: number;
  memory_utilization_percent: number;
  status: 'loaded' | 'loading' | 'unloaded' | 'error';
  last_used: number;
}

interface HardwarePressure {
  overall_pressure: number;
  cpu_pressure: number;
  memory_pressure: number;
  gpu_pressure: number;
  disk_pressure: number;
  network_pressure: number;
  recommendations: string[];
  critical_issues: string[];
}

interface ModelManagementSettings {
  auto_unload_inactive: boolean;
  max_concurrent_models: number;
  memory_threshold_percent: number;
  gpu_memory_threshold_percent: number;
  performance_optimization: 'balanced' | 'performance' | 'efficiency';
  cache_strategy: 'aggressive' | 'conservative' | 'adaptive';
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const HardwareMonitoringDashboard: React.FC = () => {
  // Core state
  const [metrics, setMetrics] = useState<SystemMetrics[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(null);
  const [modelMetrics, setModelMetrics] = useState<ModelPerformanceMetrics[]>([]);
  const [pressure, setPressure] = useState<HardwarePressure | null>(null);
  const [settings, setSettings] = useState<ModelManagementSettings>({
    auto_unload_inactive: true,
    max_concurrent_models: 3,
    memory_threshold_percent: 80,
    gpu_memory_threshold_percent: 85,
    performance_optimization: 'balanced',
    cache_strategy: 'adaptive'
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [showModelDialog, setShowModelDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [fullscreenChart, setFullscreenChart] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('1h');
  const [refreshInterval, setRefreshInterval] = useState<number>(5000); // 5 seconds
  const [visibleCharts, setVisibleCharts] = useState({
    cpu: true,
    memory: true,
    gpu: true,
    disk: true,
    network: true,
    models: true
  });

  // Get all Ollama models
  const { models: allModels, isLoading: modelsLoading } = useOllamaModels();
  const [localModels, setLocalModels] = useState<OllamaModel[]>([]);
  const [loadedModels, setLoadedModels] = useState<string[]>([]);

  // Initialize local models (make all 177 models available locally)
  useEffect(() => {
    if (allModels.length > 0) {
      setLocalModels(allModels);
      console.log(`🚀 Hardware Dashboard: ${allModels.length} models available locally`);
    }
  }, [allModels]);

  // Fetch hardware metrics
  const fetchMetrics = useCallback(async () => {
    if (!isMonitoring) return;

    try {
      const [systemRes, modelsRes, pressureRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/hardware/metrics`),
        fetch(`${BACKEND_URL}/api/hardware/models/performance`),
        fetch(`${BACKEND_URL}/api/hardware/pressure`)
      ]);

      if (systemRes.ok) {
        const systemData = await systemRes.json();
        if (systemData.success) {
          const newMetric = systemData.metrics;
          setCurrentMetrics(newMetric);
          setMetrics(prev => {
            const updated = [...prev, newMetric];
            // Keep only last hour of data for performance
            const cutoff = Date.now() - (60 * 60 * 1000);
            return updated.filter(m => m.timestamp > cutoff);
          });
        }
      }

      if (modelsRes.ok) {
        const modelsData = await modelsRes.json();
        if (modelsData.success) {
          setModelMetrics(modelsData.model_metrics);
          setLoadedModels(modelsData.model_metrics.map((m: ModelPerformanceMetrics) => m.model_name));
        }
      }

      if (pressureRes.ok) {
        const pressureData = await pressureRes.json();
        if (pressureData.success) {
          setPressure(pressureData.pressure);
        }
      }

    } catch (err) {
      if (!error) { // Only set error once to avoid spam
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('Hardware monitoring error:', err);
      }
    } finally {
      setLoading(false);
    }
  }, [isMonitoring, error]);

  // Model management functions
  const loadModel = async (modelName: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/hardware/models/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName })
      });

      const data = await response.json();
      if (data.success) {
        toast.success(`Model ${modelName} loaded successfully`);
        fetchMetrics(); // Refresh metrics
      } else {
        toast.error(data.message || 'Failed to load model');
      }
    } catch (err) {
      toast.error(`Failed to load model: ${err}`);
    }
  };

  const unloadModel = async (modelName: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/hardware/models/unload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName })
      });

      const data = await response.json();
      if (data.success) {
        toast.success(`Model ${modelName} unloaded successfully`);
        fetchMetrics(); // Refresh metrics
      } else {
        toast.error(data.message || 'Failed to unload model');
      }
    } catch (err) {
      toast.error(`Failed to unload model: ${err}`);
    }
  };

  const updateSettings = async (newSettings: Partial<ModelManagementSettings>) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/hardware/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });

      const data = await response.json();
      if (data.success) {
        setSettings(prev => ({ ...prev, ...newSettings }));
        toast.success('Settings updated successfully');
      } else {
        toast.error(data.message || 'Failed to update settings');
      }
    } catch (err) {
      toast.error(`Failed to update settings: ${err}`);
    }
  };

  // Setup monitoring interval
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  // Chart data preparation
  const prepareChartData = (dataPoints: SystemMetrics[], key: string) => {
    return dataPoints.slice(-50).map((metric, index) => ({
      time: new Date(metric.timestamp).toLocaleTimeString(),
      value: getNestedValue(metric, key),
      timestamp: metric.timestamp
    }));
  };

  const getNestedValue = (obj: any, path: string) => {
    return path.split('.').reduce((o, p) => o && o[p], obj);
  };

  // Color schemes
  const getStatusColor = (percentage: number) => {
    if (percentage < 50) return '#00D4AA'; // Green
    if (percentage < 75) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const getPressureColor = (pressure: number) => {
    if (pressure < 30) return '#00D4AA';
    if (pressure < 70) return '#f59e0b';
    return '#ef4444';
  };

  // Chart colors
  const chartColors = {
    cpu: '#00D4AA',
    memory: '#3b82f6',
    gpu: '#8b5cf6',
    disk: '#f59e0b',
    network: '#ef4444',
    models: '#06b6d4'
  };

  if (loading && metrics.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading Hardware Monitor...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, bgcolor: '#0a0a0a', minHeight: '100vh' }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#ffffff' }}>
            <Computer sx={{ color: '#00D4AA' }} />
            Hardware Analytics Dashboard
          </Typography>
          <Typography variant="body1" sx={{ color: '#6b7280', mt: 1 }}>
            Real-time monitoring of {localModels.length} local models and system performance
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel sx={{ color: '#6b7280' }}>Refresh Rate</InputLabel>
            <Select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(e.target.value as number)}
              sx={{ color: '#ffffff', borderColor: '#374151' }}
            >
              <MenuItem value={1000}>1s</MenuItem>
              <MenuItem value={5000}>5s</MenuItem>
              <MenuItem value={10000}>10s</MenuItem>
              <MenuItem value={30000}>30s</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            onClick={() => setIsMonitoring(!isMonitoring)}
            startIcon={isMonitoring ? <Stop /> : <PlayArrow />}
            variant={isMonitoring ? "outlined" : "contained"}
            color={isMonitoring ? "error" : "success"}
          >
            {isMonitoring ? 'Stop' : 'Start'} Monitor
          </Button>
          
          <Button
            onClick={() => setShowSettingsDialog(true)}
            startIcon={<Settings />}
            variant="outlined"
            sx={{ borderColor: '#374151', color: '#ffffff' }}
          >
            Settings
          </Button>
          
          <Button
            onClick={fetchMetrics}
            startIcon={<Refresh />}
            variant="outlined"
            sx={{ borderColor: '#374151', color: '#ffffff' }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* System Pressure Alert */}
      {pressure && pressure.overall_pressure > 70 && (
        <Alert 
          severity="warning" 
          sx={{ mb: 3, bgcolor: 'rgba(245, 158, 11, 0.1)', borderColor: '#f59e0b' }}
          action={
            <IconButton size="small" onClick={() => setPressure(null)}>
              <Close />
            </IconButton>
          }
        >
          <Typography variant="body2" sx={{ color: '#f59e0b' }}>
            <strong>High System Pressure ({pressure.overall_pressure.toFixed(1)}%)</strong>
            <br />
            {pressure.recommendations.slice(0, 2).join(' • ')}
          </Typography>
        </Alert>
      )}

      {/* Critical Issues */}
      {pressure?.critical_issues && pressure.critical_issues.length > 0 && (
        <Alert severity="error" sx={{ mb: 3, bgcolor: 'rgba(239, 68, 68, 0.1)', borderColor: '#ef4444' }}>
          <Typography variant="body2" sx={{ color: '#ef4444' }}>
            <strong>Critical Issues Detected:</strong>
            <br />
            {pressure.critical_issues.join(' • ')}
          </Typography>
        </Alert>
      )}

      {/* Quick Stats Cards */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, 
        gap: 3, 
        mb: 4 
      }}>
        <Box>
          <Card sx={{ bgcolor: 'rgba(0, 212, 170, 0.1)', border: '1px solid rgba(0, 212, 170, 0.3)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ color: '#00D4AA', fontWeight: 'bold' }}>
                    {currentMetrics?.cpu.usage_percent.toFixed(1) || 0}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    CPU Usage
                  </Typography>
                </Box>
                <Cpu sx={{ fontSize: 40, color: '#00D4AA', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ bgcolor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ color: '#3b82f6', fontWeight: 'bold' }}>
                    {currentMetrics?.memory.usage_percent.toFixed(1) || 0}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    Memory Usage
                  </Typography>
                </Box>
                <Memory sx={{ fontSize: 40, color: '#3b82f6', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ bgcolor: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ color: '#8b5cf6', fontWeight: 'bold' }}>
                    {currentMetrics?.gpu.utilization_percent.toFixed(1) || 0}%
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    GPU Usage
                  </Typography>
                </Box>
                <Speed sx={{ fontSize: 40, color: '#8b5cf6', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card sx={{ bgcolor: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.3)' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="h4" sx={{ color: '#06b6d4', fontWeight: 'bold' }}>
                    {loadedModels.length}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    Active Models
                  </Typography>
                </Box>
                <Badge badgeContent={localModels.length} color="primary">
                  <Computer sx={{ fontSize: 40, color: '#06b6d4', opacity: 0.7 }} />
                </Badge>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Real-time Charts Grid */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
        gap: 3, 
        mb: 4 
      }}>
        {/* CPU Usage Chart */}
        {visibleCharts.cpu && (
          <Box>
            <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', height: '300px' }}>
              <CardContent sx={{ height: '100%', p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" sx={{ color: '#ffffff' }}>CPU Performance</Typography>
                  <IconButton onClick={() => setFullscreenChart('cpu')} size="small">
                    <Fullscreen sx={{ color: '#6b7280' }} />
                  </IconButton>
                </Box>
                <ResponsiveContainer width="100%" height="85%">
                  <AreaChart data={prepareChartData(metrics, 'cpu.usage_percent')}>
                    <defs>
                      <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={chartColors.cpu} stopOpacity={0.8}/>
                        <stop offset="95%" stopColor={chartColors.cpu} stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                      domain={[0, 100]}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '6px',
                        color: '#ffffff'
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU Usage']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke={chartColors.cpu} 
                      fillOpacity={1} 
                      fill="url(#cpuGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Memory Usage Chart */}
        {visibleCharts.memory && (
          <Box>
            <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', height: '300px' }}>
              <CardContent sx={{ height: '100%', p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" sx={{ color: '#ffffff' }}>Memory Usage</Typography>
                  <IconButton onClick={() => setFullscreenChart('memory')} size="small">
                    <Fullscreen sx={{ color: '#6b7280' }} />
                  </IconButton>
                </Box>
                <ResponsiveContainer width="100%" height="85%">
                  <AreaChart data={prepareChartData(metrics, 'memory.usage_percent')}>
                    <defs>
                      <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={chartColors.memory} stopOpacity={0.8}/>
                        <stop offset="95%" stopColor={chartColors.memory} stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                      domain={[0, 100]}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '6px',
                        color: '#ffffff'
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Memory Usage']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke={chartColors.memory} 
                      fillOpacity={1} 
                      fill="url(#memoryGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* GPU Usage Chart */}
        {visibleCharts.gpu && (
          <Box>
            <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', height: '300px' }}>
              <CardContent sx={{ height: '100%', p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" sx={{ color: '#ffffff' }}>GPU Performance</Typography>
                  <IconButton onClick={() => setFullscreenChart('gpu')} size="small">
                    <Fullscreen sx={{ color: '#6b7280' }} />
                  </IconButton>
                </Box>
                <ResponsiveContainer width="100%" height="85%">
                  <AreaChart data={prepareChartData(metrics, 'gpu.utilization_percent')}>
                    <defs>
                      <linearGradient id="gpuGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={chartColors.gpu} stopOpacity={0.8}/>
                        <stop offset="95%" stopColor={chartColors.gpu} stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                      domain={[0, 100]}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '6px',
                        color: '#ffffff'
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'GPU Usage']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke={chartColors.gpu} 
                      fillOpacity={1} 
                      fill="url(#gpuGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Network I/O Chart */}
        {visibleCharts.network && (
          <Box>
            <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', height: '300px' }}>
              <CardContent sx={{ height: '100%', p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" sx={{ color: '#ffffff' }}>Network I/O</Typography>
                  <IconButton onClick={() => setFullscreenChart('network')} size="small">
                    <Fullscreen sx={{ color: '#6b7280' }} />
                  </IconButton>
                </Box>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={metrics.slice(-50).map((metric, index) => ({
                    time: new Date(metric.timestamp).toLocaleTimeString(),
                    download: metric.network?.download_speed_mb_s || 0,
                    upload: metric.network?.upload_speed_mb_s || 0
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="time" 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      stroke="#6b7280" 
                      tick={{ fontSize: 10 }}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '6px',
                        color: '#ffffff'
                      }}
                      formatter={(value: number, name: string) => [
                        `${value.toFixed(2)} MB/s`, 
                        name === 'download' ? 'Download' : 'Upload'
                      ]}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="download" 
                      stroke="#00D4AA" 
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="upload" 
                      stroke="#ef4444" 
                      strokeWidth={2}
                      dot={false}
                    />
                    <Legend />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>

      {/* Model Management Section */}
      <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', mb: 4 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6" sx={{ color: '#ffffff', display: 'flex', alignItems: 'center', gap: 1 }}>
              <Build sx={{ color: '#00D4AA' }} />
              Local Model Management ({localModels.length} models available)
            </Typography>
            <Box display="flex" gap={2}>
              <Button
                onClick={() => setShowModelDialog(true)}
                startIcon={<Analytics />}
                variant="outlined"
                sx={{ borderColor: '#374151', color: '#ffffff' }}
              >
                Model Analytics
              </Button>
              <Button
                onClick={() => {
                  // Unload all models
                  loadedModels.forEach(model => unloadModel(model));
                }}
                startIcon={<Clear />}
                variant="outlined"
                color="error"
                disabled={loadedModels.length === 0}
              >
                Unload All
              </Button>
            </Box>
          </Box>

          {/* Loaded Models Status */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" sx={{ color: '#ffffff', mb: 2 }}>
              Currently Loaded Models ({loadedModels.length}/{settings.max_concurrent_models})
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
              {modelMetrics.map((model) => (
                <Box key={model.model_name}>
                  <Card sx={{ bgcolor: '#1f2937', border: '1px solid #374151' }}>
                    <CardContent sx={{ p: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="body1" sx={{ color: '#ffffff', fontWeight: 'medium' }}>
                          {model.model_name}
                        </Typography>
                        <Chip 
                          label={model.status} 
                          size="small"
                          color={
                            model.status === 'loaded' ? 'success' :
                            model.status === 'loading' ? 'warning' :
                            model.status === 'error' ? 'error' : 'default'
                          }
                        />
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="caption" sx={{ color: '#6b7280' }}>
                          Memory Usage: {(model.memory_usage_mb / 1024).toFixed(2)} GB
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={(model.memory_usage_mb / (currentMetrics?.memory.total_gb || 16 * 1024)) * 100}
                          sx={{ 
                            mt: 0.5,
                            '& .MuiLinearProgress-bar': {
                              backgroundColor: getStatusColor((model.memory_usage_mb / (currentMetrics?.memory.total_gb || 16 * 1024)) * 100)
                            }
                          }}
                        />
                      </Box>

                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="caption" sx={{ color: '#6b7280' }}>
                          Inference: {model.inference_time_ms.toFixed(1)}ms
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#6b7280' }}>
                          {model.tokens_per_second.toFixed(1)} t/s
                        </Typography>
                      </Box>

                      <Button
                        onClick={() => unloadModel(model.model_name)}
                        size="small"
                        variant="outlined"
                        color="error"
                        fullWidth
                      >
                        Unload Model
                      </Button>
                    </CardContent>
                  </Card>
                </Box>
              ))}
            </Box>
          </Box>

          {/* Available Models Grid */}
          <Accordion sx={{ bgcolor: '#1f2937', border: '1px solid #374151' }}>
            <AccordionSummary 
              expandIcon={<ExpandMore sx={{ color: '#ffffff' }} />}
              sx={{ borderBottom: '1px solid #374151' }}
            >
              <Typography variant="subtitle1" sx={{ color: '#ffffff' }}>
                Available Models ({localModels.length - loadedModels.length} unloaded)
              </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ maxHeight: '400px', overflow: 'auto' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                {localModels
                  .filter(model => !loadedModels.includes(model.name))
                  .map((model) => (
                    <Box key={model.name}>
                      <Card sx={{ 
                        bgcolor: '#111827', 
                        border: '1px solid #374151',
                        transition: 'all 0.2s',
                        '&:hover': {
                          bgcolor: '#1f2937',
                          borderColor: '#00D4AA',
                          transform: 'translateY(-2px)'
                        }
                      }}>
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="body2" sx={{ 
                            color: '#ffffff', 
                            fontWeight: 'medium',
                            mb: 1,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {model.name}
                          </Typography>
                          
                          <Box display="flex" gap={0.5} mb={1} flexWrap="wrap">
                            {model.capabilities.slice(0, 3).map((cap) => (
                              <Chip
                                key={cap}
                                label={cap}
                                size="small"
                                variant="outlined"
                                sx={{ 
                                  fontSize: '0.65rem',
                                  height: '20px',
                                  borderColor: '#374151',
                                  color: '#6b7280'
                                }}
                              />
                            ))}
                          </Box>

                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                            <Chip
                              label={model.compatibility_label}
                              size="small"
                              sx={{
                                backgroundColor: 
                                  model.compatibility_label === 'Excellent' ? '#00D4AA' :
                                  model.compatibility_label === 'Good' ? '#f59e0b' :
                                  model.compatibility_label === 'Fair' ? '#6b7280' : '#ef4444',
                                color: '#000000',
                                fontSize: '0.65rem'
                              }}
                            />
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              {model.estimated_memory_usage}
                            </Typography>
                          </Box>

                          <Button
                            onClick={() => loadModel(model.name)}
                            size="small"
                            variant="contained"
                            fullWidth
                            sx={{ 
                              bgcolor: '#00D4AA',
                              color: '#000000',
                              '&:hover': {
                                bgcolor: '#00B894'
                              }
                            }}
                            disabled={loadedModels.length >= settings.max_concurrent_models}
                          >
                            Load Model
                          </Button>
                        </CardContent>
                      </Card>
                    </Box>
                  ))
                }
              </Box>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>

      {/* System Pressure Analysis */}
      {pressure && (
        <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', mb: 4 }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#ffffff', mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Analytics sx={{ color: '#00D4AA' }} />
              System Pressure Analysis
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ color: '#ffffff', mb: 2 }}>
                    Pressure Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={250}>
                    <RadialBarChart 
                      cx="50%" 
                      cy="50%" 
                      innerRadius="20%" 
                      outerRadius="90%" 
                      data={[
                        { name: 'CPU', value: pressure.cpu_pressure, fill: chartColors.cpu },
                        { name: 'Memory', value: pressure.memory_pressure, fill: chartColors.memory },
                        { name: 'GPU', value: pressure.gpu_pressure, fill: chartColors.gpu },
                        { name: 'Disk', value: pressure.disk_pressure, fill: chartColors.disk },
                        { name: 'Network', value: pressure.network_pressure, fill: chartColors.network }
                      ]}
                    >
                      <RadialBar dataKey="value" cornerRadius={10} fill="#8884d8" />
                      <RechartsTooltip 
                        contentStyle={{ 
                          backgroundColor: '#1f2937', 
                          border: '1px solid #374151',
                          borderRadius: '6px',
                          color: '#ffffff'
                        }}
                        formatter={(value: number) => [`${value.toFixed(1)}%`, 'Pressure']}
                      />
                    </RadialBarChart>
                  </ResponsiveContainer>
                </Box>
              </Box>
              
              <Box>
                <Box>
                  <Typography variant="subtitle1" sx={{ color: '#ffffff', mb: 2 }}>
                    Recommendations
                  </Typography>
                  <List>
                    {pressure.recommendations.map((recommendation, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <ListItemIcon>
                          <Info sx={{ color: '#00D4AA', fontSize: 16 }} />
                        </ListItemIcon>
                        <ListItemText 
                          primary={
                            <Typography variant="body2" sx={{ color: '#ffffff' }}>
                              {recommendation}
                            </Typography>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Settings Dialog */}
      <Dialog 
        open={showSettingsDialog} 
        onClose={() => setShowSettingsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#111827', color: '#ffffff', borderBottom: '1px solid #374151' }}>
          Hardware Management Settings
        </DialogTitle>
        <DialogContent sx={{ bgcolor: '#111827', color: '#ffffff' }}>
          <Box sx={{ pt: 2 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.auto_unload_inactive}
                      onChange={(e) => updateSettings({ auto_unload_inactive: e.target.checked })}
                    />
                  }
                  label="Auto-unload inactive models"
                />
              </Box>
              
              <Box>
                <Typography gutterBottom sx={{ color: '#ffffff' }}>
                  Max Concurrent Models: {settings.max_concurrent_models}
                </Typography>
                <Slider
                  value={settings.max_concurrent_models}
                  onChange={(_, value) => updateSettings({ max_concurrent_models: value as number })}
                  min={1}
                  max={10}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box>
                <Typography gutterBottom sx={{ color: '#ffffff' }}>
                  Memory Threshold: {settings.memory_threshold_percent}%
                </Typography>
                <Slider
                  value={settings.memory_threshold_percent}
                  onChange={(_, value) => updateSettings({ memory_threshold_percent: value as number })}
                  min={50}
                  max={95}
                  step={5}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: '#6b7280' }}>Performance Optimization</InputLabel>
                  <Select
                    value={settings.performance_optimization}
                    onChange={(e) => updateSettings({ performance_optimization: e.target.value as any })}
                    sx={{ color: '#ffffff' }}
                  >
                    <MenuItem value="efficiency">Efficiency</MenuItem>
                    <MenuItem value="balanced">Balanced</MenuItem>
                    <MenuItem value="performance">Performance</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              
              <Box>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: '#6b7280' }}>Cache Strategy</InputLabel>
                  <Select
                    value={settings.cache_strategy}
                    onChange={(e) => updateSettings({ cache_strategy: e.target.value as any })}
                    sx={{ color: '#ffffff' }}
                  >
                    <MenuItem value="conservative">Conservative</MenuItem>
                    <MenuItem value="adaptive">Adaptive</MenuItem>
                    <MenuItem value="aggressive">Aggressive</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ bgcolor: '#111827', borderTop: '1px solid #374151' }}>
          <Button onClick={() => setShowSettingsDialog(false)} sx={{ color: '#6b7280' }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Model Analytics Dialog */}
      <Dialog 
        open={showModelDialog} 
        onClose={() => setShowModelDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#111827', color: '#ffffff', borderBottom: '1px solid #374151' }}>
          Model Performance Analytics
        </DialogTitle>
        <DialogContent sx={{ bgcolor: '#111827', color: '#ffffff' }}>
          <Box sx={{ pt: 2, minHeight: '400px' }}>
            {modelMetrics.length > 0 ? (
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
                <Box>
                  <Card sx={{ bgcolor: '#1f2937', border: '1px solid #374151' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Model Performance Comparison
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={modelMetrics}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                          <XAxis 
                            dataKey="model_name" 
                            stroke="#6b7280"
                            tick={{ fontSize: 10 }}
                          />
                          <YAxis stroke="#6b7280" />
                          <RechartsTooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              border: '1px solid #374151',
                              borderRadius: '6px',
                              color: '#ffffff'
                            }}
                          />
                          <Bar dataKey="tokens_per_second" fill="#00D4AA" name="Tokens/Second" />
                          <Bar dataKey="inference_time_ms" fill="#3b82f6" name="Inference Time (ms)" />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </Box>
              </Box>
            ) : (
              <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                <Typography variant="body1" sx={{ color: '#6b7280' }}>
                  No models currently loaded for analysis
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ bgcolor: '#111827', borderTop: '1px solid #374151' }}>
          <Button onClick={() => setShowModelDialog(false)} sx={{ color: '#6b7280' }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Fullscreen Chart Dialog */}
      <Dialog 
        open={fullscreenChart !== null} 
        onClose={() => setFullscreenChart(null)}
        maxWidth="xl"
        fullWidth
        fullScreen
      >
        <DialogTitle sx={{ bgcolor: '#111827', color: '#ffffff', borderBottom: '1px solid #374151' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {fullscreenChart?.toUpperCase()} Performance Chart
            </Typography>
            <IconButton onClick={() => setFullscreenChart(null)} sx={{ color: '#ffffff' }}>
              <FullscreenExit />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ bgcolor: '#111827', p: 0 }}>
          <Box sx={{ height: 'calc(100vh - 120px)', p: 3 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={fullscreenChart ? prepareChartData(metrics, `${fullscreenChart}.usage_percent`) : []}>
                <defs>
                  <linearGradient id="fullscreenGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColors[fullscreenChart as keyof typeof chartColors] || '#00D4AA'} stopOpacity={0.8}/>
                    <stop offset="95%" stopColor={chartColors[fullscreenChart as keyof typeof chartColors] || '#00D4AA'} stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#6b7280" />
                <YAxis stroke="#6b7280" domain={[0, 100]} />
                <RechartsTooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: '1px solid #374151',
                    borderRadius: '6px',
                    color: '#ffffff'
                  }}
                  formatter={(value: number) => [`${value.toFixed(1)}%`, `${fullscreenChart?.toUpperCase()} Usage`]}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={chartColors[fullscreenChart as keyof typeof chartColors] || '#00D4AA'}
                  fillOpacity={1} 
                  fill="url(#fullscreenGradient)" 
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default HardwareMonitoringDashboard;