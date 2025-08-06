import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  Button,
  Alert,
  LinearProgress,
  Chip,
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
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Memory,
  Speed,
  Settings,
  Refresh,
  PlayArrow,
  Clear,
  ExpandMore,
  Info,
  TrendingUp,
  Computer,
  Storage,
  Timeline
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';

interface GPUDevice {
  device_id: number;
  name: string;
  vendor: string;
  memory_total_mb: number;
  memory_free_mb: number;
  memory_used_mb: number;
  memory_utilization_percent: number;
  gpu_utilization_percent: number;
  temperature?: number;
  power_usage?: number;
  is_active: boolean;
}

interface GPUConfig {
  prefer_gpu: boolean;
  auto_device_selection: boolean;
  mixed_precision: boolean;
  memory_fraction: number;
  batch_size_multiplier: number;
  cache_models: boolean;
  fallback_to_cpu: boolean;
  max_gpu_memory_mb?: number;
}

interface GPUStatus {
  gpu_info: any;
  memory_usage: any;
  active_device: string;
  available_devices_count: number;
  cache_status: {
    cached_models: number;
    cache_enabled: boolean;
  };
}

interface BenchmarkResult {
  device: string;
  benchmark_results: Record<string, number>;
  timestamp: number;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const GPUAcceleration: React.FC = () => {
  const [config, setConfig] = useState<GPUConfig | null>(null);
  const [status, setStatus] = useState<GPUStatus | null>(null);
  const [devices, setDevices] = useState<GPUDevice[]>([]);
  const [memoryInfo, setMemoryInfo] = useState<any>(null);
  const [cacheStatus, setCacheStatus] = useState<any>(null);
  const [performanceStats, setPerformanceStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showBenchmarkDialog, setShowBenchmarkDialog] = useState(false);

  const fetchGPUData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusRes, configRes, devicesRes, memoryRes, cacheRes, perfRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/gpu/status`),
        fetch(`${BACKEND_URL}/api/gpu/config`),
        fetch(`${BACKEND_URL}/api/gpu/devices`),
        fetch(`${BACKEND_URL}/api/gpu/memory`),
        fetch(`${BACKEND_URL}/api/gpu/cache/status`),
        fetch(`${BACKEND_URL}/api/gpu/performance/stats`)
      ]);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        if (statusData.success) setStatus(statusData);
      }

      if (configRes.ok) {
        const configData = await configRes.json();
        if (configData.success) setConfig(configData.config);
      }

      if (devicesRes.ok) {
        const devicesData = await devicesRes.json();
        if (devicesData.success) setDevices(devicesData.devices);
      }

      if (memoryRes.ok) {
        const memoryData = await memoryRes.json();
        if (memoryData.success) setMemoryInfo(memoryData);
      }

      if (cacheRes.ok) {
        const cacheData = await cacheRes.json();
        if (cacheData.success) setCacheStatus(cacheData);
      }

      if (perfRes.ok) {
        const perfData = await perfRes.json();
        if (perfData.success) setPerformanceStats(perfData.performance_stats);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast.error(`Failed to load GPU data: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (updates: Partial<GPUConfig>) => {
    try {
      setUpdating(true);
      
      const response = await fetch(`${BACKEND_URL}/api/gpu/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      const data = await response.json();
      
      if (data.success) {
        setConfig(data.new_config);
        toast.success('GPU configuration updated successfully');
        
        // Refresh status after config change
        setTimeout(fetchGPUData, 1000);
      } else {
        throw new Error(data.message || 'Failed to update configuration');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to update configuration: ${errorMessage}`);
    } finally {
      setUpdating(false);
    }
  }, [fetchGPUData]);

  const runBenchmark = useCallback(async (deviceId?: number) => {
    try {
      setBenchmarking(true);
      
      const payload = deviceId !== undefined ? { device_id: deviceId } : {};
      
      const response = await fetch(`${BACKEND_URL}/api/gpu/benchmark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (data.success) {
        setBenchmarkResults(data);
        setShowBenchmarkDialog(true);
        toast.success('Benchmark completed successfully');
      } else {
        throw new Error(data.message || 'Benchmark failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Benchmark failed: ${errorMessage}`);
    } finally {
      setBenchmarking(false);
    }
  }, []);

  const clearCache = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/gpu/cache/clear`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        fetchGPUData(); // Refresh data
      } else {
        throw new Error(data.message || 'Failed to clear cache');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to clear cache: ${errorMessage}`);
    }
  }, [fetchGPUData]);

  useEffect(() => {
    fetchGPUData();
  }, [fetchGPUData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchGPUData, 30000);
    return () => clearInterval(interval);
  }, [fetchGPUData]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">GPU Acceleration Error</Typography>
        <Typography>{error}</Typography>
        <Button onClick={fetchGPUData} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const formatBytes = (bytes: number | undefined | null) => {
    if (!bytes || bytes === 0) return '0 MB';
    const mb = bytes;
    return `${mb.toFixed(1)} MB`;
  };

  const getDeviceTypeIcon = (vendor: string) => {
    switch (vendor.toLowerCase()) {
      case 'nvidia': return '🟢';
      case 'apple': return '🍎';
      case 'amd': return '🔴';
      case 'intel': return '🔵';
      default: return '💻';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Computer />
          GPU Acceleration
        </Typography>
        <Box>
          <Button 
            onClick={fetchGPUData} 
            startIcon={<Refresh />} 
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            onClick={() => runBenchmark()} 
            startIcon={<PlayArrow />} 
            disabled={benchmarking}
            variant="outlined"
          >
            {benchmarking ? 'Running...' : 'Benchmark'}
          </Button>
        </Box>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3, mb: 3 }}>
        {/* Status Overview */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Memory />
              System Status
            </Typography>
            
            {status && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Active Device: <Chip label={status.active_device} size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Available Devices: {status.available_devices_count}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Cached Models: {status.cache_status.cached_models}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cache: {status.cache_status.cache_enabled ? 
                    <Chip label="Enabled" color="success" size="small" /> : 
                    <Chip label="Disabled" color="error" size="small" />
                  }
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Performance Stats */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Timeline />
              Performance
            </Typography>
            
            {performanceStats && (
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Avg CPU Inference: {performanceStats.avg_cpu_inference_ms?.toFixed(2) || 0} ms
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Avg GPU Inference: {performanceStats.avg_gpu_inference_ms?.toFixed(2) || 0} ms
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  GPU Speedup: {performanceStats.gpu_speedup_factor?.toFixed(2) || 1}x
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Cache Hit Rate: {cacheStatus?.statistics?.hit_rate_percent ? 
                    `${cacheStatus.statistics.hit_rate_percent.toFixed(1)}%` : 'N/A'
                  }
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Memory Usage */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Storage />
              Memory Usage
            </Typography>
            
            {memoryInfo && (
              <Box>
                {memoryInfo.gpu_memory && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      GPU Memory
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={memoryInfo.gpu_memory.total_mb > 0 ? (memoryInfo.gpu_memory.allocated_mb / memoryInfo.gpu_memory.total_mb) * 100 : 0}
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {formatBytes(memoryInfo.gpu_memory.allocated_mb)} / {formatBytes(memoryInfo.gpu_memory.total_mb)}
                    </Typography>
                  </>
                )}
                
                <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  System Memory
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={memoryInfo.system_memory?.used_percent || 0}
                  sx={{ mb: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {memoryInfo.system_memory?.used_percent?.toFixed(1) || 0}% used
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Configuration Panel */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Settings />
            GPU Configuration
            {updating && <CircularProgress size={20} sx={{ ml: 1 }} />}
          </Typography>

          {config && (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.prefer_gpu}
                      onChange={(e) => updateConfig({ prefer_gpu: e.target.checked })}
                      disabled={updating}
                    />
                  }
                  label="Prefer GPU"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.auto_device_selection}
                      onChange={(e) => updateConfig({ auto_device_selection: e.target.checked })}
                      disabled={updating}
                    />
                  }
                  label="Auto Device Selection"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.mixed_precision}
                      onChange={(e) => updateConfig({ mixed_precision: e.target.checked })}
                      disabled={updating}
                    />
                  }
                  label="Mixed Precision"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.cache_models}
                      onChange={(e) => updateConfig({ cache_models: e.target.checked })}
                      disabled={updating}
                    />
                  }
                  label="Cache Models"
                />
              </Box>
              
              <Box>
                <Box sx={{ mb: 3 }}>
                  <Typography gutterBottom>Memory Fraction</Typography>
                  <Slider
                    value={config.memory_fraction || 0.8}
                    onChange={(_, value) => updateConfig({ memory_fraction: value as number })}
                    min={0.1}
                    max={1.0}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                    disabled={updating}
                  />
                </Box>
                
                <Box sx={{ mb: 3 }}>
                  <Typography gutterBottom>Batch Size Multiplier</Typography>
                  <Slider
                    value={config.batch_size_multiplier || 1.5}
                    onChange={(_, value) => updateConfig({ batch_size_multiplier: value as number })}
                    min={0.5}
                    max={5.0}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                    disabled={updating}
                  />
                </Box>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* GPU Devices */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Computer />
              GPU Devices ({devices.length})
            </Typography>
            {cacheStatus && cacheStatus.cached_models_count > 0 && (
              <Button 
                onClick={clearCache}
                startIcon={<Clear />}
                color="warning"
                variant="outlined"
                size="small"
              >
                Clear Cache ({cacheStatus.cached_models_count})
              </Button>
            )}
          </Box>

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Device</TableCell>
                  <TableCell>Memory</TableCell>
                  <TableCell>Utilization</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {devices.map((device) => (
                  <TableRow key={device.device_id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <span>{getDeviceTypeIcon(device.vendor)}</span>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {device.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {device.vendor.toUpperCase()} #{device.device_id}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box>
                        <LinearProgress
                          variant="determinate"
                          value={device.memory_utilization_percent || 0}
                          sx={{ mb: 0.5 }}
                        />
                        <Typography variant="caption">
                          {formatBytes(device.memory_used_mb)} / {formatBytes(device.memory_total_mb)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {device.gpu_utilization_percent?.toFixed(1) || 0}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {device.is_active ? (
                        <Chip label="Active" color="success" size="small" />
                      ) : (
                        <Chip label="Available" color="default" size="small" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        onClick={() => runBenchmark(device.device_id)}
                        disabled={benchmarking}
                        size="small"
                        startIcon={<Speed />}
                      >
                        Benchmark
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Benchmark Results Dialog */}
      <Dialog 
        open={showBenchmarkDialog} 
        onClose={() => setShowBenchmarkDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip icon={<Speed />} label="Hardware Benchmark Results" size="small" />
          </Box>
        </DialogTitle>
        <DialogContent>
          {benchmarkResults && (
            <Box>
              {/* Device Information */}
              <Card sx={{ mb: 3, bgcolor: 'rgba(0, 212, 170, 0.1)', border: '1px solid rgba(0, 212, 170, 0.2)' }}>
                <CardContent sx={{ pb: 2 }}>
                  <Typography variant="h6" sx={{ mb: 1, color: '#00D4AA' }}>
                    🖥️ Device Information
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Device</Typography>
                      <Typography variant="body1" fontWeight="medium">{benchmarkResults.device}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">Timestamp</Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {new Date(benchmarkResults.timestamp * 1000).toLocaleString()}
                      </Typography>
                    </Box>
                    {benchmarkResults.benchmark_results['Device Info'] && (
                      <>
                        <Box>
                          <Typography variant="body2" color="text.secondary">Type</Typography>
                          <Typography variant="body1" fontWeight="medium">
                            {(benchmarkResults.benchmark_results['Device Info'] as any)?.type?.toUpperCase() || 'CPU'}
                          </Typography>
                        </Box>
                        {(benchmarkResults.benchmark_results['Device Info'] as any)?.memory_gb && (
                          <Box>
                            <Typography variant="body2" color="text.secondary">Memory</Typography>
                            <Typography variant="body1" fontWeight="medium">
                              {(benchmarkResults.benchmark_results['Device Info'] as any)?.memory_gb} GB
                            </Typography>
                          </Box>
                        )}
                      </>
                    )}
                  </Box>
                </CardContent>
              </Card>

              {/* Matrix Multiplication Performance */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, color: '#ffffff' }}>
                    ⚡ Matrix Multiplication Performance
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Matrix Size</strong></TableCell>
                          <TableCell align="right"><strong>Time (ms)</strong></TableCell>
                          <TableCell align="right"><strong>TFLOPS</strong></TableCell>
                          <TableCell align="right"><strong>Operations</strong></TableCell>
                          <TableCell align="right"><strong>Memory (GB)</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(benchmarkResults.benchmark_results)
                          .filter(([key]) => key.startsWith('Matrix'))
                          .map(([test, data]: [string, any]) => (
                          <TableRow key={test}>
                            <TableCell><strong>{test}</strong></TableCell>
                            <TableCell align="right">
                              <Chip 
                                label={`${data.time_ms} ms`} 
                                size="small" 
                                color={data.time_ms < 10 ? 'success' : data.time_ms < 100 ? 'warning' : 'error'}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" fontWeight="medium" color="#00D4AA">
                                {data.tflops} TFLOPS
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" color="text.secondary">
                                {data.operations}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2" color="text.secondary">
                                {data.memory_gb} GB
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>

              {/* Memory Bandwidth */}
              {benchmarkResults.benchmark_results['Memory Bandwidth'] && (
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ mb: 2, color: '#ffffff' }}>
                      💾 Memory Bandwidth Performance
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 2 }}>
                      <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'rgba(0, 212, 170, 0.1)', borderRadius: 2 }}>
                        <Typography variant="h4" sx={{ color: '#00D4AA', fontWeight: 'bold' }}>
                          {(benchmarkResults.benchmark_results['Memory Bandwidth'] as any)?.bandwidth_gb_s || 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">GB/s</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 'bold' }}>
                          {(benchmarkResults.benchmark_results['Memory Bandwidth'] as any)?.test_size_mb || 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">MB Test Size</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 2 }}>
                        <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 'bold' }}>
                          {(benchmarkResults.benchmark_results['Memory Bandwidth'] as any)?.time_ms || 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">ms</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Performance Summary */}
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Performance Tip:</strong> Higher TFLOPS indicates better computational performance. 
                  Memory bandwidth affects how quickly data can be transferred to/from the GPU.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBenchmarkDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GPUAcceleration;