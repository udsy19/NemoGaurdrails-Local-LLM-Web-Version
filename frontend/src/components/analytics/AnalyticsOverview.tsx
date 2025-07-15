import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  BarChart3 as Analytics,
  Shield,
  Users,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Globe,
  Server,
  Eye,
  Filter,
  BarChart3,
  PieChart as PieChartIcon,
  Calendar,
  ChevronDown as ExpandMore,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { useAnalytics } from '../../hooks/useAnalytics';

interface AnalyticsOverviewProps {
  onRefresh?: () => void;
}

const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({ onRefresh }) => {
  const {
    summary,
    realtimeStats,
    loading,
    error,
    fetchAnalyticsSummary,
    fetchRealtimeStats,
    exportAnalyticsData,
    isLoaded,
    hasData,
    blockRate,
    safetyEffectiveness,
  } = useAnalytics();

  const [timeframe, setTimeframe] = useState(24);
  const [refreshing, setRefreshing] = useState(false);
  const [expanded, setExpanded] = useState<string | false>('overview');

  const handleTimeframeChange = async (newTimeframe: number) => {
    setTimeframe(newTimeframe);
    await fetchAnalyticsSummary(newTimeframe);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        fetchAnalyticsSummary(timeframe),
        fetchRealtimeStats(),
      ]);
      toast.success('Analytics data refreshed');
      onRefresh?.();
    } catch (err) {
      toast.error('Failed to refresh analytics data');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpanded(isExpanded ? panel : false);
  };

  // Chart colors
  const colors = {
    primary: '#00D4AA',
    secondary: '#3b82f6',
    danger: '#ef4444',
    warning: '#f59e0b',
    success: '#10b981',
    info: '#6b7280',
  };

  const pieColors = [colors.primary, colors.danger, colors.warning, colors.info];

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <LinearProgress sx={{ flexGrow: 1 }} />
          <Typography sx={{ color: '#ffffff' }}>Loading analytics...</Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load analytics: {error}
        </Alert>
        <Button onClick={handleRefresh} startIcon={<RefreshCw size={16} />}>
          Retry
        </Button>
      </Box>
    );
  }

  if (!hasData) {
    return (
      <Box sx={{ p: 3 }}>
        <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <CardContent sx={{ textAlign: 'center', py: 6 }}>
            <Analytics size={64} style={{ color: '#6b7280', marginBottom: 16 }} />
            <Typography variant="h5" sx={{ color: '#ffffff', mb: 2 }}>
              No Analytics Data Available
            </Typography>
            <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 3 }}>
              Start using the AI Safety System to generate analytics data.
            </Typography>
            <Button
              onClick={handleRefresh}
              startIcon={<RefreshCw size={16} />}
              variant="outlined"
              sx={{ color: colors.primary, borderColor: colors.primary }}
            >
              Check for Data
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Analytics size={28} style={{ color: colors.primary }} />
              <Typography variant="h4" sx={{ fontWeight: 600, color: '#ffffff' }}>
                Analytics Overview
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel sx={{ color: '#a1a1aa' }}>Timeframe</InputLabel>
                <Select
                  value={timeframe}
                  label="Timeframe"
                  onChange={(e) => handleTimeframeChange(e.target.value as number)}
                  sx={{
                    color: '#ffffff',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.2)',
                    },
                  }}
                >
                  <MenuItem value={1}>Last Hour</MenuItem>
                  <MenuItem value={6}>Last 6 Hours</MenuItem>
                  <MenuItem value={24}>Last 24 Hours</MenuItem>
                  <MenuItem value={72}>Last 3 Days</MenuItem>
                  <MenuItem value={168}>Last Week</MenuItem>
                </Select>
              </FormControl>
              
              <Tooltip title="Export Data">
                <IconButton
                  onClick={exportAnalyticsData}
                  sx={{ color: '#a1a1aa', '&:hover': { color: '#ffffff' } }}
                >
                  <Download size={20} />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Refresh">
                <IconButton
                  onClick={handleRefresh}
                  disabled={refreshing}
                  sx={{ color: colors.primary, '&:hover': { color: '#ffffff' } }}
                >
                  <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          <Typography variant="body1" sx={{ color: '#a1a1aa' }}>
            Comprehensive analytics and monitoring for AI safety system performance.
          </Typography>
        </Box>

        {/* Real-time Stats Cards */}
        {realtimeStats && (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h4" sx={{ color: colors.primary, fontWeight: 600 }}>
                        {realtimeStats.total_requests.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        Total Requests
                      </Typography>
                    </Box>
                    <Server size={24} style={{ color: colors.primary }} />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <TrendingUp size={14} style={{ color: colors.success }} />
                    <Typography variant="caption" sx={{ color: colors.success }}>
                      {realtimeStats.recent_requests_5min} in last 5 min
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h4" sx={{ color: colors.danger, fontWeight: 600 }}>
                        {realtimeStats.blocked_requests.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        Blocked Requests
                      </Typography>
                    </Box>
                    <Shield size={24} style={{ color: colors.danger }} />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Typography variant="caption" sx={{ color: colors.danger }}>
                      {realtimeStats.block_rate.toFixed(1)}% block rate
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.2 }}
            >
              <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h4" sx={{ color: colors.secondary, fontWeight: 600 }}>
                        {realtimeStats.unique_users_total.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        Unique Users
                      </Typography>
                    </Box>
                    <Users size={24} style={{ color: colors.secondary }} />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Typography variant="caption" sx={{ color: '#a1a1aa' }}>
                      {realtimeStats.requests_per_minute.toFixed(1)} req/min
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: 0.3 }}
            >
              <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h4" sx={{ color: colors.warning, fontWeight: 600 }}>
                        {realtimeStats.avg_response_time.toFixed(0)}ms
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        Avg Response Time
                      </Typography>
                    </Box>
                    <Clock size={24} style={{ color: colors.warning }} />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                    <Typography variant="caption" sx={{ color: colors.success }}>
                      {safetyEffectiveness} mode
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Box>
        )}

        {/* Main Analytics Sections */}
        <Box sx={{ mb: 3 }}>
          {/* Overview Section */}
          <Accordion
            expanded={expanded === 'overview'}
            onChange={handleAccordionChange('overview')}
            sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)', mb: 2 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMore style={{ color: '#ffffff' }} />}
              sx={{ '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 2 } }}
            >
              <BarChart3 size={20} style={{ color: colors.primary }} />
              <Typography variant="h6" sx={{ color: '#ffffff' }}>
                Request Overview
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {summary && (
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                  {/* Request Timeline Chart */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Request Timeline
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={summary.request_timeline}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                          <XAxis
                            dataKey="hour"
                            tick={{ fill: '#a1a1aa', fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString()}
                          />
                          <YAxis tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              borderRadius: '8px',
                              color: '#ffffff',
                            }}
                          />
                          <Legend />
                          <Line type="monotone" dataKey="total_requests" stroke={colors.primary} name="Total" />
                          <Line type="monotone" dataKey="blocked_requests" stroke={colors.danger} name="Blocked" />
                          <Line type="monotone" dataKey="allowed_requests" stroke={colors.success} name="Allowed" />
                        </LineChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Request Distribution Pie Chart */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Request Distribution
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Allowed', value: summary.allowed_requests, color: colors.success },
                              { name: 'Blocked', value: summary.blocked_requests, color: colors.danger },
                            ]}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(1) : '0'}%`}
                          >
                            {[
                              { name: 'Allowed', value: summary.allowed_requests, color: colors.success },
                              { name: 'Blocked', value: summary.blocked_requests, color: colors.danger },
                            ].map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              borderRadius: '8px',
                              color: '#ffffff',
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Detector Analytics Section */}
          <Accordion
            expanded={expanded === 'detectors'}
            onChange={handleAccordionChange('detectors')}
            sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)', mb: 2 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMore style={{ color: '#ffffff' }} />}
              sx={{ '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 2 } }}
            >
              <Filter size={20} style={{ color: colors.secondary }} />
              <Typography variant="h6" sx={{ color: '#ffffff' }}>
                Detector Performance
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {summary && summary.detector_stats.length > 0 && (
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                  {/* Detector Stats Table */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Detection Statistics
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell sx={{ color: '#a1a1aa' }}>Detector</TableCell>
                              <TableCell sx={{ color: '#a1a1aa' }} align="right">Detections</TableCell>
                              <TableCell sx={{ color: '#a1a1aa' }} align="right">Block Rate</TableCell>
                              <TableCell sx={{ color: '#a1a1aa' }} align="right">Confidence</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {summary.detector_stats.map((detector) => (
                              <TableRow key={detector.name}>
                                <TableCell sx={{ color: '#ffffff' }}>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    {detector.name.replace('_', ' ').split(' ').map(word => 
                                      word.charAt(0).toUpperCase() + word.slice(1)
                                    ).join(' ')}
                                    {detector.last_triggered && (
                                      <Chip
                                        size="small"
                                        label="Active"
                                        sx={{
                                          backgroundColor: colors.success + '20',
                                          color: colors.success,
                                          fontSize: '0.7rem',
                                        }}
                                      />
                                    )}
                                  </Box>
                                </TableCell>
                                <TableCell sx={{ color: '#ffffff' }} align="right">
                                  {detector.total_detections}
                                </TableCell>
                                <TableCell sx={{ color: '#ffffff' }} align="right">
                                  <Typography
                                    variant="body2"
                                    sx={{
                                      color: detector.block_rate > 50 ? colors.danger : 
                                             detector.block_rate > 25 ? colors.warning : colors.success
                                    }}
                                  >
                                    {detector.block_rate.toFixed(1)}%
                                  </Typography>
                                </TableCell>
                                <TableCell sx={{ color: '#ffffff' }} align="right">
                                  {(detector.avg_confidence * 100).toFixed(1)}%
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>

                  {/* Detector Performance Chart */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Block Rate by Detector
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={summary.detector_stats}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                          <XAxis
                            dataKey="name"
                            tick={{ fill: '#a1a1aa', fontSize: 10 }}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                          />
                          <YAxis tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              borderRadius: '8px',
                              color: '#ffffff',
                            }}
                          />
                          <Bar dataKey="block_rate" fill={colors.danger} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>

          {/* User Analytics Section */}
          <Accordion
            expanded={expanded === 'users'}
            onChange={handleAccordionChange('users')}
            sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)', mb: 2 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMore style={{ color: '#ffffff' }} />}
              sx={{ '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 2 } }}
            >
              <Users size={20} style={{ color: colors.info }} />
              <Typography variant="h6" sx={{ color: '#ffffff' }}>
                User Activity
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {summary && summary.user_activity.length > 0 && (
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                  <CardContent>
                    <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                      Top Users by Activity
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell sx={{ color: '#a1a1aa' }}>IP Address</TableCell>
                            <TableCell sx={{ color: '#a1a1aa' }} align="right">Requests</TableCell>
                            <TableCell sx={{ color: '#a1a1aa' }} align="right">Blocked</TableCell>
                            <TableCell sx={{ color: '#a1a1aa' }} align="right">Block Rate</TableCell>
                            <TableCell sx={{ color: '#a1a1aa' }}>Last Seen</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {summary.user_activity.slice(0, 10).map((user, index) => (
                            <TableRow key={`${user.ip_address}-${index}`}>
                              <TableCell sx={{ color: '#ffffff' }}>
                                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                  {user.ip_address}
                                </Typography>
                              </TableCell>
                              <TableCell sx={{ color: '#ffffff' }} align="right">
                                {user.total_requests}
                              </TableCell>
                              <TableCell sx={{ color: '#ffffff' }} align="right">
                                {user.blocked_requests}
                              </TableCell>
                              <TableCell sx={{ color: '#ffffff' }} align="right">
                                <Typography
                                  variant="body2"
                                  sx={{
                                    color: user.block_rate > 50 ? colors.danger : 
                                           user.block_rate > 25 ? colors.warning : colors.success
                                  }}
                                >
                                  {user.block_rate.toFixed(1)}%
                                </Typography>
                              </TableCell>
                              <TableCell sx={{ color: '#a1a1aa' }}>
                                {user.last_seen ? 
                                  new Date(user.last_seen).toLocaleString() : 
                                  'Unknown'
                                }
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Blocking Reasons Section */}
          {summary && summary.top_blocking_reasons.length > 0 && (
            <Accordion
              expanded={expanded === 'blocking'}
              onChange={handleAccordionChange('blocking')}
              sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}
            >
              <AccordionSummary
                expandIcon={<ExpandMore style={{ color: '#ffffff' }} />}
                sx={{ '& .MuiAccordionSummary-content': { alignItems: 'center', gap: 2 } }}
              >
                <AlertTriangle size={20} style={{ color: colors.danger }} />
                <Typography variant="h6" sx={{ color: '#ffffff' }}>
                  Top Blocking Reasons
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                  {/* Blocking Reasons Chart */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Blocking Frequency
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={summary.top_blocking_reasons.slice(0, 5)}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                          <XAxis
                            dataKey="reason"
                            tick={{ fill: '#a1a1aa', fontSize: 10 }}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                          />
                          <YAxis tick={{ fill: '#a1a1aa', fontSize: 12 }} />
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: 'rgba(0, 0, 0, 0.8)',
                              border: '1px solid rgba(255, 255, 255, 0.2)',
                              borderRadius: '8px',
                              color: '#ffffff',
                            }}
                          />
                          <Bar dataKey="count" fill={colors.danger} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Blocking Reasons List */}
                  <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                        Detailed Breakdown
                      </Typography>
                      <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                        {summary.top_blocking_reasons.map((reason, index) => (
                          <Box
                            key={index}
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              p: 2,
                              mb: 1,
                              backgroundColor: 'rgba(255, 255, 255, 0.02)',
                              borderRadius: '8px',
                              border: '1px solid rgba(255, 255, 255, 0.06)',
                            }}
                          >
                            <Typography variant="body2" sx={{ color: '#ffffff', flexGrow: 1 }}>
                              {reason.reason}
                            </Typography>
                            <Chip
                              label={reason.count}
                              size="small"
                              sx={{
                                backgroundColor: colors.danger + '20',
                                color: colors.danger,
                              }}
                            />
                          </Box>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
        </Box>

        {/* System Health Summary */}
        <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
              System Health Summary
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <CheckCircle size={32} style={{ color: colors.success, marginBottom: 8 }} />
                <Typography variant="h6" sx={{ color: colors.success }}>
                  {safetyEffectiveness}
                </Typography>
                <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                  Safety Status
                </Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center' }}>
                <Activity size={32} style={{ color: colors.primary, marginBottom: 8 }} />
                <Typography variant="h6" sx={{ color: colors.primary }}>
                  {summary ? `${summary.error_rate.toFixed(1)}%` : '0%'}
                </Typography>
                <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                  Error Rate
                </Typography>
              </Box>
              
              <Box sx={{ textAlign: 'center' }}>
                <Clock size={32} style={{ color: colors.warning, marginBottom: 8 }} />
                <Typography variant="h6" sx={{ color: colors.warning }}>
                  {summary ? `${summary.avg_response_time.toFixed(0)}ms` : '0ms'}
                </Typography>
                <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                  Avg Response Time
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </motion.div>
  );
};

export default AnalyticsOverview;