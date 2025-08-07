import React, { useMemo } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  Chip,
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  Shield,
  BugReport,
  Analytics,
} from '@mui/icons-material';

import { useRealTimeData } from '../../hooks/useRealTimeData';
import AnimatedMetricCard from '../shared/AnimatedMetricCard';
import LoadingSkeleton from '../shared/LoadingSkeleton';
import {
  ThreatTimelineChart,
  ThreatDistributionChart,
  RiskGaugeChart,
  RealTimeActivityChart
} from '../shared/ModernCharts';
import { sanitizeData, getEmptyDashboardData } from '../../utils/testDataHandler';

const MainDashboard = () => {
  const { data: rawData, loading, error, isConnected } = useRealTimeData('main');
  
  // Sanitize and validate the data
  const dashboardData = useMemo(() => {
    console.log('📊 MainDashboard rawData update:', { rawData, loading, error, isConnected });
    if (!rawData) {
      console.log('⚠️ MainDashboard using empty data because rawData is:', rawData);
      return getEmptyDashboardData();
    }
    const sanitized = sanitizeData(rawData);
    console.log('✅ MainDashboard sanitized data:', sanitized);
    console.log('📊 Total events in sanitized data:', sanitized?.recent_events?.length);
    return sanitized;
  }, [rawData, loading, error, isConnected]);

  // Calculate risk based on live data structure
  const riskScore = useMemo(() => {
    if (!dashboardData) return 0;
    
    // Calculate risk from live detection events
    const recentEvents = dashboardData.recent_events || [];
    const totalRequests = dashboardData.total_requests || 1;
    const blockedRequests = recentEvents.filter(e => e.status === 'blocked').length;
    const dataExfiltrationAttempts = recentEvents.filter(e => 
      e.detection_type === 'pii' || e.detection_type === 'privacy'
    ).length;
    const promptInjectionAttempts = recentEvents.filter(e => 
      e.detection_type === 'prompt_injection'
    ).length;
    
    // Use risk calculation algorithm (40% data exfiltration, 30% prompt injection, 20% blocked, 10% trend)
    const riskScore = Math.min(100, Math.max(0, 
      (dataExfiltrationAttempts / totalRequests * 500 * 0.4) +
      (promptInjectionAttempts / totalRequests * 400 * 0.3) +
      (blockedRequests / totalRequests * 200 * 0.2) +
      (0 * 0.1) // No trend data yet
    ));
    
    return Math.round(riskScore);
  }, [dashboardData]);

  const riskColor = useMemo(() => {
    if (riskScore >= 70) return 'error';
    if (riskScore >= 40) return 'warning';
    return 'success';
  }, [riskScore]);

  const riskLevel = useMemo(() => {
    if (riskScore >= 70) return 'HIGH';
    if (riskScore >= 40) return 'MEDIUM';
    return 'LOW';
  }, [riskScore]);

  if (loading) {
    return <LoadingSkeleton type="dashboard" />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6">Dashboard Error</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      p: 3, 
      minHeight: '100vh',
      width: '100%',
      maxWidth: '100%',
      overflow: 'auto',
      boxSizing: 'border-box'
    }}>
      {/* Connection Status Alert */}
      {!isConnected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          WebSocket disconnected - Dashboard may show stale data
        </Alert>
      )}

      {/* Executive Risk Summary */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <RiskGaugeChart
            value={riskScore}
            title="Executive Risk Score"
            max={100}
          />
        </Grid>

        <Grid item xs={12} md={9}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Detection Events
              </Typography>
              {dashboardData?.recent_events?.length > 0 ? (
                dashboardData.recent_events
                  .filter(event => event.status === 'blocked')
                  .slice(0, 3)
                  .map((event, index) => (
                    <ThreatItem key={index} threat={{
                      type: event.detection_type || 'Unknown',
                      count: 1,
                      confidence: (event.confidence * 100) || 0,
                      timestamp: event.timestamp
                    }} rank={index + 1} />
                  ))
              ) : (
                <Box display="flex" alignItems="center" py={2}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  <Typography color="text.secondary">
                    No recent threats detected
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Key Metrics Row */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Data Exfiltration Attempts"
            value={dashboardData?.recent_events?.filter(e => 
              e.detection_type === 'pii' || e.detection_type === 'privacy'
            ).length || 0}
            icon={<Security />}
            color="error"
            delay={0.1}
            subtitle="Security breaches detected"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Blocked Requests"
            value={dashboardData?.recent_events?.filter(e => e.status === 'blocked').length || 0}
            icon={<Shield />}
            color="warning"
            delay={0.2}
            subtitle="Threats prevented"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Total Requests"
            value={dashboardData?.recent_events?.length || 0}
            icon={<Analytics />}
            color="primary"
            delay={0.3}
            subtitle="System activity"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Prompt Injections"
            value={dashboardData?.recent_events?.filter(e => 
              e.detection_type === 'prompt_injection'
            ).length || 0}
            icon={<BugReport />}
            color="error"
            delay={0.4}
            subtitle="Malicious attempts"
          />
        </Grid>
      </Grid>

      {/* Advanced Analytics Charts */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} lg={8}>
          <ThreatTimelineChart
            data={generateTimelineData(dashboardData)}
            title="Threat Analysis Timeline"
          />
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <ThreatDistributionChart
            data={generateThreatDistribution(dashboardData)}
            title="Threat Distribution"
          />
        </Grid>
        
        <Grid item xs={12}>
          <RealTimeActivityChart
            data={generateActivityData(dashboardData)}
            title="Real-Time Security Activity"
          />
        </Grid>
      </Grid>
    </Box>
  );
};

// Helper Components
const ThreatItem = ({ threat, rank }) => {
  const formatDetectionType = (type) => {
    const typeMap = {
      'pii': 'PII Detection',
      'prompt_injection': 'Prompt Injection',
      'toxicity': 'Toxic Content',
      'privacy': 'Privacy Violation',
      'hate_speech': 'Hate Speech',
      'bias': 'Bias Detection'
    };
    return typeMap[type] || type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  return (
    <Box display="flex" alignItems="center" py={1}>
      <Chip
        label={`#${rank}`}
        size="small"
        color="primary"
        sx={{ mr: 2, minWidth: 35 }}
      />
      <Box flex={1}>
        <Typography variant="body1" fontWeight="medium">
          {formatDetectionType(threat.type)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {threat.confidence?.toFixed(1) || 0}% confidence
          {threat.timestamp && ` • ${formatTimestamp(threat.timestamp)}`}
        </Typography>
      </Box>
      <Warning color="warning" />
    </Box>
  );
};

// Data transformation functions for charts
const generateTimelineData = (dashboardData) => {
  if (!dashboardData?.recent_events || dashboardData.recent_events.length === 0) {
    // Return empty data with proper structure for charts
    const emptyData = [];
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const timeKey = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      emptyData.push({ time: timeKey, blocked: 0, allowed: 0 });
    }
    return emptyData;
  }
  
  // Group events by hour for timeline
  const hourlyData = {};
  const now = new Date();
  
  // Initialize last 12 hours
  for (let i = 11; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
    const timeKey = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    hourlyData[timeKey] = { time: timeKey, blocked: 0, allowed: 0 };
  }
  
  // Populate with actual data
  dashboardData.recent_events.forEach(event => {
    try {
      const eventTime = new Date(event.timestamp);
      const timeKey = eventTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      if (hourlyData[timeKey]) {
        if (event.status === 'blocked') {
          hourlyData[timeKey].blocked++;
        } else {
          hourlyData[timeKey].allowed++;
        }
      }
    } catch (e) {
      // Skip invalid timestamps
    }
  });
  
  return Object.values(hourlyData);
};

const generateThreatDistribution = (dashboardData) => {
  if (!dashboardData?.recent_events || dashboardData.recent_events.length === 0) {
    return [{ name: 'No Threats Detected', value: 1 }];
  }
  
  const distribution = {};
  dashboardData.recent_events
    .filter(e => e.status === 'blocked')
    .forEach(event => {
      const type = event.detection_type || 'unknown';
      distribution[type] = (distribution[type] || 0) + 1;
    });
  
  return Object.entries(distribution).map(([name, value]) => ({
    name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value
  }));
};

const generateActivityData = (dashboardData) => {
  if (!dashboardData?.recent_events) {
    // Generate empty activity data for last 30 minutes
    const activityData = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 1000);
      const timeKey = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      activityData.push({ time: timeKey, activity: 0 });
    }
    
    return activityData;
  }
  
  // Generate activity data for last 30 minutes
  const activityData = [];
  const now = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 1000);
    const timeKey = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    // Count events in this minute
    const eventsInMinute = dashboardData.recent_events.filter(event => {
      try {
        const eventTime = new Date(event.timestamp);
        return Math.abs(eventTime.getTime() - time.getTime()) < 60000; // Within 1 minute
      } catch {
        return false;
      }
    }).length;
    
    activityData.push({
      time: timeKey,
      activity: eventsInMinute
    });
  }
  
  return activityData;
};

export default MainDashboard;