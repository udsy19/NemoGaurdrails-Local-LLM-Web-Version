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
  Tabs,
  Tab,
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
  TextFields
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
  ResponsiveContainer,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

interface AdvancedMetrics {
  requests_per_hour: number;
  block_rate_percentage: number;
  safety_effectiveness: number;
  user_engagement: {
    avg_requests_per_user: number;
    active_user_rate: number;
  };
  detector_efficiency: Record<string, {
    accuracy: number;
    volume: number;
  }>;
}

interface SystemPerformance {
  distributed_processing: {
    status: string;
    active_workers: number;
    queue_size: number;
    throughput: number;
    avg_processing_time: number;
  };
  gpu_acceleration: {
    active_device: string;
    available_devices: number;
    cache_hits: number;
    cache_hit_rate: number;
    memory_usage: any;
  };
  detection_performance: any;
}

interface ThreatIntelligence {
  overall_threat_level: string;
  threat_distribution: Record<string, number>;
  top_categories: Array<[string, number]>;
  threat_velocity: number;
  indicators: string[];
}

interface DashboardData {
  basic_metrics: {
    total_requests: number;
    blocked_requests: number;
    allowed_requests: number;
    block_rate: number;
    unique_users: number;
    unique_ips: number;
  };
  advanced_metrics: AdvancedMetrics;
  system_performance: SystemPerformance;
  threat_intelligence: ThreatIntelligence;
  ml_insights: any;
  predictions: any;
}

const AdvancedAnalyticsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [threatAnalysis, setThreatAnalysis] = useState<any>(null);
  const [mlInsights, setMlInsights] = useState<any>(null);
  const [predictions, setPredictions] = useState<any>(null);
  const [executiveSummary, setExecutiveSummary] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState(24);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showPredictions, setShowPredictions] = useState(false);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewRes, performanceRes, threatRes, mlRes, predRes, execRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/analytics/advanced/dashboard/overview?hours=${timeRange}&include_ml_insights=true&include_predictions=${showPredictions}`),
        fetch(`${BACKEND_URL}/api/analytics/advanced/performance/detailed?hours=${timeRange}`),
        fetch(`${BACKEND_URL}/api/analytics/advanced/security/threat-analysis?hours=${timeRange}`),
        fetch(`${BACKEND_URL}/api/analytics/advanced/ml/insights?hours=${timeRange}`),
        fetch(`${BACKEND_URL}/api/analytics/advanced/predictions/forecast?forecast_hours=24`),
        fetch(`${BACKEND_URL}/api/analytics/advanced/reports/executive-summary?period=daily`)
      ]);

      if (overviewRes.ok) {
        const data = await overviewRes.json();
        if (data.success) setDashboardData(data.overview);
      }

      if (performanceRes.ok) {
        const data = await performanceRes.json();
        if (data.success) setPerformanceData(data.performance_metrics);
      }

      if (threatRes.ok) {
        const data = await threatRes.json();
        if (data.success) setThreatAnalysis(data.threat_analysis);
      }

      if (mlRes.ok) {
        const data = await mlRes.json();
        if (data.success) setMlInsights(data.ml_insights);
      }

      if (predRes.ok) {
        const data = await predRes.json();
        if (data.success) setPredictions(data.predictions);
      }

      if (execRes.ok) {
        const data = await execRes.json();
        if (data.success) setExecutiveSummary(data.executive_summary);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast.error(`Failed to load advanced analytics: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [timeRange, showPredictions]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, 30000);
      return () => clearInterval(interval);
    }
  }, [fetchDashboardData, autoRefresh]);

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
        <Typography variant="h6">Advanced Analytics Error</Typography>
        <Typography>{error}</Typography>
        <Button onClick={fetchDashboardData} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'good':
      case 'running':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'error':
      case 'critical':
      case 'stopped':
        return 'error';
      default:
        return 'default';
    }
  };

  const getThreatLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'high': return '#f44336';
      case 'critical': return '#d32f2f';
      default: return '#9e9e9e';
    }
  };

  const formatNumber = (num: number, decimals: number = 1) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(decimals)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Assessment />
          Advanced Analytics Dashboard
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value as number)}
            >
              <MenuItem value={1}>1 Hour</MenuItem>
              <MenuItem value={6}>6 Hours</MenuItem>
              <MenuItem value={24}>24 Hours</MenuItem>
              <MenuItem value={168}>7 Days</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                size="small"
              />
            }
            label="Auto Refresh"
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={showPredictions}
                onChange={(e) => setShowPredictions(e.target.checked)}
                size="small"
              />
            }
            label="Predictions"
          />
          
          <Button 
            onClick={fetchDashboardData} 
            startIcon={<Refresh />} 
            disabled={loading}
            variant="outlined"
            size="small"
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Executive Summary Cards */}
      {dashboardData && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="h4" color="primary">
                      {formatNumber(dashboardData.basic_metrics.total_requests, 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Requests
                    </Typography>
                    <Typography variant="caption" color="success.main">
                      {dashboardData.advanced_metrics.requests_per_hour.toFixed(1)}/hr
                    </Typography>
                  </Box>
                  <TrendingUp color="primary" />
                </Box>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="h4" color="error">
                      {dashboardData.basic_metrics.blocked_requests}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Threats Blocked
                    </Typography>
                    <Typography variant="caption" color="error.main">
                      {dashboardData.basic_metrics.block_rate.toFixed(1)}% rate
                    </Typography>
                  </Box>
                  <Security color="error" />
                </Box>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="h4" color="success.main">
                      {dashboardData.advanced_metrics.safety_effectiveness.toFixed(0)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Safety Effectiveness
                    </Typography>
                    <Typography variant="caption" color="success.main">
                      Excellent
                    </Typography>
                  </Box>
                  <CheckCircle color="success" />
                </Box>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Box>
                    <Typography variant="h4" color="info.main">
                      {dashboardData.system_performance.distributed_processing.active_workers}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Workers
                    </Typography>
                    <Typography variant="caption" 
                      color={getStatusColor(dashboardData.system_performance.distributed_processing.status)}
                    >
                      {dashboardData.system_performance.distributed_processing.status}
                    </Typography>
                  </Box>
                  <Computer color="info" />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Box>
      )}

      {/* Tabbed Interface */}
      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="Guardrail Analytics" icon={<Security />} />
            <Tab label="Content Analysis" icon={<TextFields />} />
            <Tab label="User Patterns" icon={<Psychology />} />
            <Tab label="Hardware Status" icon={<Computer />} />
            <Tab label="Executive Summary" icon={<Assessment />} />
          </Tabs>

          {/* Guardrail Analytics Tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                System Performance Metrics
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3, mb: 3 }}>
                {/* Response Times */}
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Response Time Distribution</Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Box textAlign="center">
                        <Typography variant="h6" color="success.main">{performanceData.response_times.distribution.fast}%</Typography>
                        <Typography variant="caption">Fast (&lt;100ms)</Typography>
                      </Box>
                      <Box textAlign="center">
                        <Typography variant="h6" color="warning.main">{performanceData.response_times.distribution.medium}%</Typography>
                        <Typography variant="caption">Medium (100-300ms)</Typography>
                      </Box>
                      <Box textAlign="center">
                        <Typography variant="h6" color="error.main">{performanceData.response_times.distribution.slow}%</Typography>
                        <Typography variant="caption">Slow (&gt;300ms)</Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      P95: {performanceData.response_times.p95_ms}ms | P99: {performanceData.response_times.p99_ms}ms
                    </Typography>
                  </CardContent>
                </Card>

                {/* Resource Utilization */}
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Resource Utilization</Typography>
                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">CPU</Typography>
                        <Typography variant="body2">{performanceData.resource_utilization.cpu_utilization.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={performanceData.resource_utilization.cpu_utilization} 
                        color={performanceData.resource_utilization.cpu_utilization > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                    <Box sx={{ mb: 2 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">Memory</Typography>
                        <Typography variant="body2">{performanceData.resource_utilization.memory_utilization.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={performanceData.resource_utilization.memory_utilization} 
                        color={performanceData.resource_utilization.memory_utilization > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                    <Box>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="body2">Queue</Typography>
                        <Typography variant="body2">{performanceData.resource_utilization.queue_utilization.toFixed(1)}%</Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate" 
                        value={performanceData.resource_utilization.queue_utilization} 
                        color={performanceData.resource_utilization.queue_utilization > 80 ? 'error' : 'primary'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Box>

              {/* Detector Performance */}
              <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>Detector Performance</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Detector</TableCell>
                          <TableCell align="right">Accuracy</TableCell>
                          <TableCell align="right">Precision</TableCell>
                          <TableCell align="right">Recall</TableCell>
                          <TableCell align="right">F1 Score</TableCell>
                          <TableCell align="right">Avg Time (ms)</TableCell>
                          <TableCell align="right">Volume</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {performanceData.detector_performance.map((detector: any) => (
                          <TableRow key={detector.name}>
                            <TableCell>{detector.name}</TableCell>
                            <TableCell align="right">{detector.accuracy.toFixed(1)}%</TableCell>
                            <TableCell align="right">{detector.precision.toFixed(1)}%</TableCell>
                            <TableCell align="right">{detector.recall.toFixed(1)}%</TableCell>
                            <TableCell align="right">{detector.f1_score.toFixed(1)}%</TableCell>
                            <TableCell align="right">{detector.processing_time_ms}</TableCell>
                            <TableCell align="right">{detector.volume}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Threat Intelligence Tab */}
          {activeTab === 1 && threatAnalysis && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Threat Intelligence Analysis
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Threat Landscape</Typography>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      <Typography variant="h4" 
                        style={{ color: getThreatLevelColor(threatAnalysis.threat_overview.threat_level) }}
                      >
                        {threatAnalysis.threat_overview.threat_level.toUpperCase()}
                      </Typography>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Overall Threat Level
                        </Typography>
                        <Typography variant="caption">
                          {threatAnalysis.threat_overview.active_campaigns} active campaigns
                        </Typography>
                      </Box>
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>Security Recommendations</Typography>
                    {threatAnalysis.recommendations.map((rec: string, index: number) => (
                      <Typography key={index} variant="body2" color="text.secondary" gutterBottom>
                        • {rec}
                      </Typography>
                    ))}
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Threat Severity Distribution</Typography>
                    <ResponsiveContainer width="100%" height={200}>
                      <RechartsPieChart>
                        <Pie
                          data={Object.entries(threatAnalysis.severity_distribution).map(([key, value]) => ({
                            name: key,
                            value,
                            color: getThreatLevelColor(key)
                          }))}
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          dataKey="value"
                          label={({ name, percent }) => `${name} ${(percent ? (percent * 100).toFixed(0) : 0)}%`}
                        >
                          {Object.entries(threatAnalysis.severity_distribution).map(([key], index) => (
                            <Cell key={`cell-${index}`} fill={getThreatLevelColor(key)} />
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

          {/* ML Insights Tab */}
          {activeTab === 2 && mlInsights && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Machine Learning Insights
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Anomaly Detection</Typography>
                    {mlInsights.anomaly_detection && (
                      <Box>
                        <Typography variant="h4" color={mlInsights.anomaly_detection.anomalies_detected > 0 ? 'warning.main' : 'success.main'}>
                          {mlInsights.anomaly_detection.anomalies_detected}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Anomalies Detected
                        </Typography>
                        <Chip 
                          label={mlInsights.anomaly_detection.severity} 
                          color={mlInsights.anomaly_detection.severity === 'low' ? 'success' : 'warning'}
                          size="small"
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Pattern Recognition</Typography>
                    {mlInsights.pattern_recognition && (
                      <Box>
                        {mlInsights.pattern_recognition.patterns.map((pattern: string, index: number) => (
                          <Chip 
                            key={index}
                            label={pattern.replace('_', ' ')}
                            variant="outlined"
                            size="small"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>User Behavior</Typography>
                    {mlInsights.behavioral_analysis && (
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Normal Users: {mlInsights.behavioral_analysis.normal_users}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={mlInsights.behavioral_analysis.normal_users} 
                          color="success"
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="body2" gutterBottom>
                          Suspicious Users: {mlInsights.behavioral_analysis.suspicious_users}%
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={mlInsights.behavioral_analysis.suspicious_users} 
                          color="warning"
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
            </Box>
          )}

          {/* Predictions Tab */}
          {activeTab === 3 && predictions && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Predictive Analytics
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Traffic Forecast</Typography>
                    <Typography variant="h4" color="primary">
                      {formatNumber(predictions.traffic_forecast.predicted_requests, 0)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Predicted Requests (Next 24h)
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      95% Confidence Interval
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Threat Forecast</Typography>
                    <Typography variant="h4" color="error">
                      {predictions.threat_forecast.predicted_threats}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Predicted Threats (Next 24h)
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Based on historical patterns
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Resource Forecast</Typography>
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        Predicted CPU: {predictions.resource_forecast.cpu}%
                      </Typography>
                      <LinearProgress variant="determinate" value={predictions.resource_forecast.cpu} sx={{ mb: 1 }} />
                      <Typography variant="body2" gutterBottom>
                        Predicted Memory: {predictions.resource_forecast.memory}%
                      </Typography>
                      <LinearProgress variant="determinate" value={predictions.resource_forecast.memory} sx={{ mb: 1 }} />
                      <Typography variant="body2" gutterBottom>
                        Predicted Queue: {predictions.resource_forecast.queue}%
                      </Typography>
                      <LinearProgress variant="determinate" value={predictions.resource_forecast.queue} />
                    </Box>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance Forecast</Typography>
                    <Typography variant="body2" gutterBottom>
                      Response Time: {predictions.performance_forecast.response_time}ms
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      Throughput: {predictions.performance_forecast.throughput.toFixed(1)} req/hr
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Forecasting methodology: Time series analysis
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          )}

          {/* Executive Summary Tab */}
          {activeTab === 4 && executiveSummary && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Executive Summary
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr' }, gap: 3 }}>
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Key Performance Indicators</Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="primary">
                          {formatNumber(executiveSummary.key_metrics.total_interactions, 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Total Interactions</Typography>
                      </Box>
                      <Box textAlign="center">
                        <Typography variant="h4" color="error">
                          {executiveSummary.key_metrics.threats_blocked}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Threats Blocked</Typography>
                      </Box>
                      <Box textAlign="center">
                        <Typography variant="h4" color="success.main">
                          {executiveSummary.key_metrics.success_rate.toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Success Rate</Typography>
                      </Box>
                      <Box textAlign="center">
                        <Typography variant="h4" color="info.main">
                          {executiveSummary.key_metrics.unique_users}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">Unique Users</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Security Posture</Typography>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      <Typography variant="h3" color="success.main">
                        {executiveSummary.security_posture.score}
                      </Typography>
                      <Box>
                        <Typography variant="h6" color="success.main">
                          {executiveSummary.security_posture.posture.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Security Score
                        </Typography>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Your security posture is strong with effective threat detection and minimal false positives.
                    </Typography>
                  </CardContent>
                </Card>

                {executiveSummary.recommendations && (
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>Strategic Recommendations</Typography>
                      {executiveSummary.recommendations.map((rec: string, index: number) => (
                        <Typography key={index} variant="body2" color="text.secondary" gutterBottom>
                          • {rec}
                        </Typography>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AdvancedAnalyticsDashboard;