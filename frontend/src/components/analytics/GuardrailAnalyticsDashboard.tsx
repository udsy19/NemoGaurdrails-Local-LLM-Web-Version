import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Tooltip,
  IconButton,
  Divider
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Security,
  Speed,
  Memory,
  Warning,
  CheckCircle,
  Timeline,
  Assessment,
  Refresh,
  Download,
  FilterList,
  Visibility,
  Computer,
  CloudQueue,
  Psychology,
  TextFields,
  Block,
  Person,
  Language,
  Category
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart as RechartsBarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import LoadingSpinner from '../common/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

interface GuardrailMetrics {
  total_requests: number;
  blocked_requests: number;
  allowed_requests: number;
  block_rate: number;
  top_blocked_categories: { [key: string]: number };
  detector_performance: { [key: string]: any };
  hourly_stats: any[];
  user_analytics: {
    unique_users: number;
    repeat_violators: number;
    new_users_today: number;
  };
  content_analysis: {
    common_words: { [key: string]: number };
    language_distribution: { [key: string]: number };
    content_categories: { [key: string]: number };
  };
}

interface HardwareMetrics {
  cpu_usage: number;
  memory_usage: number;
  gpu_usage?: number;
  disk_usage: number;
  network_io: { sent: number; received: number };
  temperature: number;
  model_load_times: { [key: string]: number };
}

const GuardrailAnalyticsDashboard: React.FC = () => {
  const [guardrailData, setGuardrailData] = useState<GuardrailMetrics | null>(null);
  const [hardwareData, setHardwareData] = useState<HardwareMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(24);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedDetector, setSelectedDetector] = useState('all');

  const fetchGuardrailData = useCallback(async () => {
    try {
      setError(null);
      
      // Use fast endpoint for immediate basic data
      try {
        const fastResponse = await fetch(`${BACKEND_URL}/api/analytics/guardrails/fast?hours=${Math.min(timeRange, 24)}`);
        if (fastResponse.ok) {
          const fastData = await fastResponse.json();
          // Set basic data immediately for fast loading
          setGuardrailData({
            ...fastData,
            detector_performance: {},
            hourly_stats: [],
            user_analytics: { unique_users: fastData.unique_users, repeat_violators: 0, new_users_today: 0 },
            content_analysis: { common_words: {}, language_distribution: {}, content_categories: {} },
            top_blocked_categories: {}
          });
        }
      } catch (fastError) {
        console.warn('Fast endpoint failed, continuing with full fetch:', fastError);
      }

      // Then fetch full data
      const response = await fetch(`${BACKEND_URL}/api/analytics/guardrails?hours=${timeRange}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setGuardrailData(data);
    } catch (error) {
      console.error('Error fetching guardrail data:', error);
      setError('Failed to fetch guardrail analytics data');
      toast.error('Failed to load guardrail analytics');
    }
  }, [timeRange]);

  const fetchHardwareData = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/system/hardware`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setHardwareData(data);
    } catch (error) {
      console.error('Error fetching hardware data:', error);
      // Hardware data is optional, don't show error
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchGuardrailData(), fetchHardwareData()]);
    setLoading(false);
  }, [fetchGuardrailData, fetchHardwareData]);

  useEffect(() => {
    fetchAllData();
  }, [fetchAllData]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchAllData]);

  const getBlockRateColor = (rate: number) => {
    if (rate < 5) return 'success.main';
    if (rate < 15) return 'warning.main';
    return 'error.main';
  };

  const getDetectorStatusColor = (accuracy: number) => {
    if (accuracy >= 90) return 'success.main';
    if (accuracy >= 75) return 'warning.main';
    return 'error.main';
  };

  const downloadSummaryJson = () => {
    if (!guardrailData) return;
    
    const summaryData = {
      timestamp: new Date().toISOString(),
      timeRange: `${timeRange} hours`,
      summary: {
        total_requests: guardrailData.total_requests,
        blocked_requests: guardrailData.blocked_requests,
        allowed_requests: guardrailData.allowed_requests,
        block_rate: guardrailData.block_rate,
        unique_users: guardrailData.user_analytics?.unique_users || 0
      },
      top_blocked_categories: guardrailData.top_blocked_categories,
      detector_status: Object.keys(guardrailData.detector_performance || {}).map(detector => ({
        name: detector,
        enabled: guardrailData.detector_performance[detector]?.enabled || false,
        accuracy: guardrailData.detector_performance[detector]?.accuracy || 0
      }))
    };
    
    const blob = new Blob([JSON.stringify(summaryData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guardrail-summary-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Summary JSON downloaded successfully');
  };

  const downloadDetailedJson = () => {
    if (!guardrailData) return;
    
    const detailedData = {
      timestamp: new Date().toISOString(),
      timeRange: `${timeRange} hours`,
      guardrail_metrics: guardrailData,
      hardware_metrics: hardwareData,
      export_metadata: {
        exported_by: 'Guardrail Analytics Dashboard',
        version: '1.0.0',
        format: 'detailed'
      }
    };
    
    const blob = new Blob([JSON.stringify(detailedData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guardrail-detailed-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Detailed JSON downloaded successfully');
  };

  const downloadFormattedExcel = () => {
    if (!guardrailData) return;
    
    // Create CSV data that can be opened in Excel
    const csvData = [
      ['Guardrail Analytics Report'],
      ['Generated:', new Date().toISOString()],
      ['Time Range:', `${timeRange} hours`],
      [''],
      ['SUMMARY METRICS'],
      ['Metric', 'Value'],
      ['Total Requests', guardrailData.total_requests],
      ['Blocked Requests', guardrailData.blocked_requests],
      ['Allowed Requests', guardrailData.allowed_requests],
      ['Block Rate (%)', guardrailData.block_rate.toFixed(2)],
      [''],
      ['DETECTOR PERFORMANCE'],
      ['Detector', 'Enabled', 'Accuracy (%)', 'Precision (%)', 'Recall (%)', 'F1 Score (%)', 'Avg Time (ms)', 'Request Count'],
      ...Object.entries(guardrailData.detector_performance || {}).map(([detector, perf]: [string, any]) => [
        detector,
        perf.enabled ? 'Yes' : 'No',
        (perf.accuracy * 100).toFixed(1),
        (perf.precision * 100).toFixed(1),
        (perf.recall * 100).toFixed(1),
        (perf.f1_score * 100).toFixed(1),
        perf.avg_response_time,
        perf.request_count
      ]),
      [''],
      ['TOP BLOCKED CATEGORIES'],
      ['Category', 'Count'],
      ...Object.entries(guardrailData.top_blocked_categories || {}).map(([category, count]) => [category, count]),
      [''],
      ['USER ANALYTICS'],
      ['Metric', 'Value'],
      ['Unique Users', guardrailData.user_analytics?.unique_users || 0],
      ['Repeat Violators', guardrailData.user_analytics?.repeat_violators || 0],
      ['New Users Today', guardrailData.user_analytics?.new_users_today || 0]
    ];

    if (hardwareData) {
      csvData.push(
        [''],
        ['HARDWARE METRICS'],
        ['Metric', 'Value'],
        ['CPU Usage (%)', hardwareData.cpu_usage.toFixed(1)],
        ['Memory Usage (%)', hardwareData.memory_usage.toFixed(1)],
        ['Disk Usage (%)', hardwareData.disk_usage.toFixed(1)],
        ['System Temperature (°C)', hardwareData.temperature.toString()]
      );
    }
    
    const csvContent = csvData.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guardrail-report-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Excel-formatted CSV downloaded successfully');
  };

  if (loading && !guardrailData) {
    return (
      <LoadingSpinner 
        message="Loading Analytics..." 
        size="large" 
        variant="circular" 
      />
    );
  }

  if (error && !guardrailData) {
    return (
      <Alert severity="error" sx={{ margin: 2 }}>
        {error}
        <Button onClick={fetchAllData} sx={{ ml: 2 }}>Retry</Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Guardrail Analytics Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small">
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(Number(e.target.value))}
            >
              <MenuItem value={1}>Last Hour</MenuItem>
              <MenuItem value={6}>Last 6 Hours</MenuItem>
              <MenuItem value={24}>Last 24 Hours</MenuItem>
              <MenuItem value={168}>Last Week</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchAllData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Single Page Analytics - All Content */}
      {guardrailData && (
        <Box>
          {/* Section 1: Key Metrics Overview */}
          <Typography variant="h5" gutterBottom sx={{ mb: 3, color: '#ffffff', fontWeight: 600 }}>
            📊 System Overview
          </Typography>

          {/* Key Metrics */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, gap: 3, mb: 3 }}>
            <Box>
              <Card sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <CheckCircle color="success" fontSize="large" />
                    <Box>
                      <Typography variant="h4" color="success.main">
                        {guardrailData.allowed_requests.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Allowed Requests
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>

            <Box>
              <Card sx={{ backgroundColor: 'rgba(244, 67, 54, 0.1)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Block color="error" fontSize="large" />
                    <Box>
                      <Typography variant="h4" color="error.main">
                        {guardrailData.blocked_requests.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Blocked Requests
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>

            <Box>
              <Card sx={{ backgroundColor: 'rgba(33, 150, 243, 0.1)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Timeline color="primary" fontSize="large" />
                    <Box>
                      <Typography variant="h4" color="primary.main">
                        {guardrailData.total_requests.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Requests
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>

            <Box>
              <Card sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Security color="warning" fontSize="large" />
                    <Box>
                      <Typography variant="h4" sx={{ color: getBlockRateColor(guardrailData.block_rate) }}>
                        {guardrailData.block_rate.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Block Rate
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Box>

          {/* Detector Performance Table */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Detector Performance</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Detector</TableCell>
                      <TableCell align="right">Accuracy</TableCell>
                      <TableCell align="right">Precision</TableCell>
                      <TableCell align="right">Recall</TableCell>
                      <TableCell align="right">F1 Score</TableCell>
                      <TableCell align="right">Avg Time (ms)</TableCell>
                      <TableCell align="right">Volume</TableCell>
                      <TableCell align="center">Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(guardrailData.detector_performance || {}).map(([detector, perf]: [string, any]) => (
                      <TableRow key={detector}>
                        <TableCell component="th" scope="row">
                          <Chip 
                            label={detector} 
                            size="small" 
                            color={perf.enabled ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography sx={{ color: getDetectorStatusColor(perf.accuracy * 100) }}>
                            {(perf.accuracy * 100).toFixed(1)}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">{(perf.precision * 100).toFixed(1)}%</TableCell>
                        <TableCell align="right">{(perf.recall * 100).toFixed(1)}%</TableCell>
                        <TableCell align="right">{(perf.f1_score * 100).toFixed(1)}%</TableCell>
                        <TableCell align="right">{perf.avg_response_time}</TableCell>
                        <TableCell align="right">{perf.request_count}</TableCell>
                        <TableCell align="center">
                          {perf.enabled ? (
                            <CheckCircle color="success" fontSize="small" />
                          ) : (
                            <Warning color="error" fontSize="small" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Detection Categories Chart */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Top Blocked Categories</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <RechartsPieChart>
                      <Pie
                        data={Object.entries(guardrailData.top_blocked_categories || {}).map(([name, value]) => ({ name, value }))}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent ? (percent * 100).toFixed(0) : 0)}%`}
                      >
                        {Object.entries(guardrailData.top_blocked_categories || {}).map(([key], index) => (
                          <Cell key={`cell-${index}`} fill={['#f44336', '#ff9800', '#ffeb3b', '#4caf50', '#2196f3'][index % 5]} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Box>

            <Box>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Detection Timeline (24h)</Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={guardrailData.hourly_stats || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="hour" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Area type="monotone" dataKey="blocked" stackId="1" stroke="#f44336" fill="#f44336" name="Blocked" />
                      <Area type="monotone" dataKey="allowed" stackId="1" stroke="#4caf50" fill="#4caf50" name="Allowed" />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Box>
          </Box>
          
          {/* Section 2: Content Analysis (removing language distribution) */}
          <Typography variant="h5" gutterBottom sx={{ mt: 6, mb: 3, color: '#ffffff', fontWeight: 600 }}>
            🔍 Content Analysis
          </Typography>
          
          {guardrailData?.content_analysis && (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 6 }}>
              <Box>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Most Flagged Words</Typography>
                    <Box>
                      {Object.entries(guardrailData.content_analysis.common_words || {})
                        .slice(0, 10)
                        .map(([word, count]) => (
                          <Box key={word} display="flex" justifyContent="space-between" mb={1}>
                            <Typography variant="body2">{word}</Typography>
                            <Chip label={count} size="small" color="error" />
                          </Box>
                        ))}
                    </Box>
                  </CardContent>
                </Card>
              </Box>

              <Box>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Content Categories</Typography>
                    <ResponsiveContainer width="100%" height={200}>
                      <RechartsPieChart>
                        <Pie
                          data={Object.entries(guardrailData.content_analysis.content_categories || {}).map(([name, value]) => ({ name, value }))}
                          cx="50%"
                          cy="50%"
                          outerRadius={60}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent ? (percent * 100).toFixed(0) : 0)}%`}
                        >
                          {Object.entries(guardrailData.content_analysis.content_categories || {}).map(([key], index) => (
                            <Cell key={`cell-${index}`} fill={['#f44336', '#ff9800', '#ffeb3b', '#4caf50', '#2196f3'][index % 5]} />
                          ))}
                        </Pie>
                        <RechartsTooltip />
                      </RechartsPieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          )}

          {/* Section 3: User Analytics */}
          <Typography variant="h5" gutterBottom sx={{ mb: 3, color: '#ffffff', fontWeight: 600 }}>
            👥 User Analytics
          </Typography>

          {guardrailData?.user_analytics && (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' }, gap: 3, mb: 6 }}>
              <Box>
                <Card sx={{ backgroundColor: 'rgba(33, 150, 243, 0.1)' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Person color="primary" fontSize="large" />
                      <Box>
                        <Typography variant="h4" color="primary.main">
                          {guardrailData.user_analytics.unique_users}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Unique Users
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>

              <Box>
                <Card sx={{ backgroundColor: 'rgba(244, 67, 54, 0.1)' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2}>
                      <Warning color="error" fontSize="large" />
                      <Box>
                        <Typography variant="h4" color="error.main">
                          {guardrailData.user_analytics.repeat_violators}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Repeat Violators
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>

              <Box>
                <Card sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2}>
                      <TrendingUp color="success" fontSize="large" />
                      <Box>
                        <Typography variant="h4" color="success.main">
                          {guardrailData.user_analytics.new_users_today}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          New Users Today
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          )}

          {/* Section 4: Hardware Status */}
          <Typography variant="h5" gutterBottom sx={{ mt: 6, mb: 3, color: '#ffffff', fontWeight: 600 }}>
            💻 System Hardware
          </Typography>

          {hardwareData ? (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 6 }}>
              <Box>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>System Resources</Typography>
                    
                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">CPU Usage</Typography>
                        <Typography variant="body2">{hardwareData.cpu_usage.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={hardwareData.cpu_usage} 
                        color={hardwareData.cpu_usage > 80 ? 'error' : 'primary'}
                      />
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">Memory Usage</Typography>
                        <Typography variant="body2">{hardwareData.memory_usage.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={hardwareData.memory_usage} 
                        color={hardwareData.memory_usage > 80 ? 'error' : 'primary'}
                      />
                    </Box>

                    {hardwareData.gpu_usage && (
                      <Box sx={{ mb: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="body2">GPU Usage</Typography>
                          <Typography variant="body2">{hardwareData.gpu_usage.toFixed(1)}%</Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={hardwareData.gpu_usage} 
                          color={hardwareData.gpu_usage > 80 ? 'error' : 'success'}
                        />
                      </Box>
                    )}

                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">Disk Usage</Typography>
                        <Typography variant="body2">{hardwareData.disk_usage.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={hardwareData.disk_usage} 
                        color={hardwareData.disk_usage > 90 ? 'error' : 'primary'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Box>

              <Box>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Model Performance</Typography>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Model Load Times (ms)
                    </Typography>
                    
                    {Object.entries(hardwareData.model_load_times || {}).map(([model, time]) => (
                      <Box key={model} display="flex" justifyContent="space-between" mb={1}>
                        <Typography variant="body2">{model}</Typography>
                        <Chip 
                          label={`${time}ms`} 
                          size="small" 
                          color={time > 1000 ? 'error' : time > 500 ? 'warning' : 'success'}
                        />
                      </Box>
                    ))}

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Network I/O
                    </Typography>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">Sent: {(hardwareData.network_io.sent / 1024 / 1024).toFixed(2)} MB</Typography>
                      <Typography variant="body2">Received: {(hardwareData.network_io.received / 1024 / 1024).toFixed(2)} MB</Typography>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2">System Temperature</Typography>
                      <Chip 
                        label={`${hardwareData.temperature}°C`} 
                        size="small" 
                        color={hardwareData.temperature > 70 ? 'error' : 'success'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          ) : (
            <Alert severity="info" sx={{ mb: 6 }}>
              Hardware monitoring not available. Enable system monitoring for detailed hardware metrics.
            </Alert>
          )}

          {/* Section 5: Guardrail Visualization */}
          <Typography variant="h5" gutterBottom sx={{ mt: 6, mb: 3, color: '#ffffff', fontWeight: 600 }}>
            🛡️ Guardrail Protection Layers
          </Typography>

          <Card sx={{ mb: 6 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Detection Layer Architecture</Typography>
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                gap: 2,
                p: 3,
                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                borderRadius: '8px'
              }}>
                {/* Request Flow */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                  <Chip label="User Input" sx={{ backgroundColor: '#3b82f6', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="Toxicity Check" sx={{ backgroundColor: '#ef4444', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="PII Detection" sx={{ backgroundColor: '#f59e0b', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="Prompt Injection" sx={{ backgroundColor: '#dc2626', color: '#ffffff', minWidth: '120px' }} />
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', ml: 4 }}>
                  <Typography sx={{ color: '#6b7280' }}>↓</Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                  <Chip label="Topic Filter" sx={{ backgroundColor: '#8b5cf6', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="Spam Detection" sx={{ backgroundColor: '#06b6d4', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="Fact Check" sx={{ backgroundColor: '#10b981', color: '#ffffff', minWidth: '120px' }} />
                  <Typography sx={{ color: '#6b7280' }}>→</Typography>
                  <Chip label="Safe Output" sx={{ backgroundColor: '#00D4AA', color: '#ffffff', minWidth: '120px' }} />
                </Box>
              </Box>

              {/* Active Detectors Status */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="body1" sx={{ mb: 2, fontWeight: 500 }}>Active Protection Status:</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {Object.entries(guardrailData.detector_performance || {}).map(([detector, perf]: [string, any]) => (
                    <Chip
                      key={detector}
                      label={`${detector}: ${perf.enabled ? 'ACTIVE' : 'INACTIVE'}`}
                      size="small"
                      sx={{
                        backgroundColor: perf.enabled ? 'rgba(76, 175, 80, 0.2)' : 'rgba(244, 67, 54, 0.2)',
                        color: perf.enabled ? '#4caf50' : '#f44336',
                        border: `1px solid ${perf.enabled ? '#4caf50' : '#f44336'}40`,
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Section 6: Download Options */}
          <Typography variant="h5" gutterBottom sx={{ mt: 6, mb: 3, color: '#ffffff', fontWeight: 600 }}>
            📥 Export Analytics
          </Typography>

          <Card sx={{ mb: 6 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Download Analytics Data</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Export your analytics data in various formats for reporting and analysis.
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => downloadSummaryJson()}
                  sx={{
                    borderColor: '#00D4AA',
                    color: '#00D4AA',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 212, 170, 0.1)',
                      borderColor: '#00D4AA',
                    },
                  }}
                >
                  Summary JSON
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => downloadDetailedJson()}
                  sx={{
                    borderColor: '#3b82f6',
                    color: '#3b82f6',
                    '&:hover': {
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      borderColor: '#3b82f6',
                    },
                  }}
                >
                  Detailed JSON
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={() => downloadFormattedExcel()}
                  sx={{
                    borderColor: '#10b981',
                    color: '#10b981',
                    '&:hover': {
                      backgroundColor: 'rgba(16, 185, 129, 0.1)',
                      borderColor: '#10b981',
                    },
                  }}
                >
                  Formatted Excel
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default GuardrailAnalyticsDashboard;