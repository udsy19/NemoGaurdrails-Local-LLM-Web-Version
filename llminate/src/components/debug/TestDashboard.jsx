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
  Shield,
  BugReport,
  Analytics,
  CheckCircle,
} from '@mui/icons-material';

import AnimatedMetricCard from '../shared/AnimatedMetricCard';
import {
  ThreatTimelineChart,
  ThreatDistributionChart,
  RiskGaugeChart,
  RealTimeActivityChart
} from '../shared/ModernCharts';
import { generateSampleData } from '../../utils/testDataHandler';

const TestDashboard = () => {
  // Use enhanced test data with more realistic enterprise metrics
  const dashboardData = useMemo(() => {
    const baseData = generateSampleData();
    return {
      ...baseData,
      total_requests: 15420,
      blocked_requests: 892,
      allowed_requests: 14528,
      // Add enterprise metrics
      compliance_score: 94.2,
      threat_intelligence: {
        new_threats_today: 23,
        threat_actors_identified: 7,
        malware_families: 12,
        geographical_threats: {
          'North Korea': 8,
          'Russia': 15,
          'China': 12,
          'Iran': 6
        }
      },
      performance_metrics: {
        avg_response_time: 245, // ms
        false_positive_rate: 2.1, // %
        detection_accuracy: 97.8, // %
        system_uptime: 99.9 // %
      },
      user_behavior: {
        high_risk_users: 23,
        suspicious_patterns: 156,
        after_hours_activity: 89,
        data_access_violations: 12
      }
    };
  }, []);
  
  console.log('🧪 TestDashboard using enhanced enterprise data:', dashboardData);

  // Calculate risk based on test data
  const riskScore = useMemo(() => {
    if (!dashboardData) return 0;
    
    const recentEvents = dashboardData.recent_events || [];
    const totalRequests = dashboardData.total_requests || 1;
    const blockedRequests = recentEvents.filter(e => e.status === 'blocked').length;
    const dataExfiltrationAttempts = recentEvents.filter(e => 
      e.detection_type === 'pii' || e.detection_type === 'privacy'
    ).length;
    const promptInjectionAttempts = recentEvents.filter(e => 
      e.detection_type === 'prompt_injection'
    ).length;
    
    const riskScore = Math.min(100, Math.max(0, 
      (dataExfiltrationAttempts / totalRequests * 500 * 0.4) +
      (promptInjectionAttempts / totalRequests * 400 * 0.3) +
      (blockedRequests / totalRequests * 200 * 0.2) +
      (0 * 0.1)
    ));
    
    return Math.round(riskScore);
  }, [dashboardData]);

  // Data transformation functions for charts
  const generateTimelineData = (dashboardData) => {
    if (!dashboardData?.recent_events || dashboardData.recent_events.length === 0) {
      const emptyData = [];
      const now = new Date();
      for (let i = 11; i >= 0; i--) {
        const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
        const timeKey = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        emptyData.push({ time: timeKey, blocked: Math.floor(Math.random() * 5), allowed: Math.floor(Math.random() * 20) });
      }
      return emptyData;
    }
    
    // Generate realistic timeline data
    const hourlyData = {};
    const now = new Date();
    
    for (let i = 11; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const timeKey = hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      hourlyData[timeKey] = { time: timeKey, blocked: Math.floor(Math.random() * 8), allowed: Math.floor(Math.random() * 25) };
    }
    
    return Object.values(hourlyData);
  };

  const generateThreatDistribution = (dashboardData) => {
    if (!dashboardData?.recent_events || dashboardData.recent_events.length === 0) {
      return [
        { name: 'PII Detection', value: 8 },
        { name: 'Prompt Injection', value: 5 },
        { name: 'Toxicity', value: 12 },
        { name: 'Hate Speech', value: 3 },
        { name: 'Privacy Violation', value: 6 }
      ];
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
    const activityData = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 1000);
      const timeKey = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      
      activityData.push({
        time: timeKey,
        activity: Math.floor(Math.random() * 15)
      });
    }
    
    return activityData;
  };

  return (
    <Box sx={{ 
      p: 3, 
      minHeight: '100vh',
      width: '100%',
      maxWidth: '100%',
      overflow: 'auto',
      boxSizing: 'border-box'
    }}>
      <Alert severity="info" sx={{ mb: 2 }}>
        🧪 This is a test dashboard using hardcoded data to verify component rendering.
      </Alert>

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

      {/* Primary Security Metrics */}
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

      {/* Secondary Metrics Row */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Compliance Score"
            value={`${dashboardData.compliance_score}%`}
            icon={<CheckCircle />}
            color="success"
            delay={0.5}
            subtitle="Regulatory compliance"
            progress={dashboardData.compliance_score}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Detection Accuracy"
            value={`${dashboardData.performance_metrics?.detection_accuracy}%`}
            icon={<Analytics />}
            color="primary"
            delay={0.6}
            subtitle="ML model precision"
            progress={dashboardData.performance_metrics?.detection_accuracy}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="System Uptime"
            value={`${dashboardData.performance_metrics?.system_uptime}%`}
            icon={<CheckCircle />}
            color="success"
            delay={0.7}
            subtitle="Service availability"
            progress={dashboardData.performance_metrics?.system_uptime}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="False Positive Rate"
            value={`${dashboardData.performance_metrics?.false_positive_rate}%`}
            icon={<Warning />}
            color="warning"
            delay={0.8}
            subtitle="Model optimization needed"
          />
        </Grid>
      </Grid>

      {/* Threat Intelligence Row */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="New Threats Today"
            value={dashboardData.threat_intelligence?.new_threats_today || 0}
            icon={<Warning />}
            color="error"
            delay={0.9}
            subtitle="Requires immediate attention"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Threat Actors"
            value={dashboardData.threat_intelligence?.threat_actors_identified || 0}
            icon={<Security />}
            color="error"
            delay={1.0}
            subtitle="Active threat groups"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="High Risk Users"
            value={dashboardData.user_behavior?.high_risk_users || 0}
            icon={<BugReport />}
            color="warning"
            delay={1.1}
            subtitle="Behavioral anomalies"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Response Time"
            value={`${dashboardData.performance_metrics?.avg_response_time}ms`}
            icon={<Analytics />}
            color="primary"
            delay={1.2}
            subtitle="Average detection latency"
          />
        </Grid>
      </Grid>

      {/* Advanced Analytics Charts */}
      <Grid container spacing={3} sx={{ mt: 1, width: '100%', mx: 0 }}>
        <Grid item xs={12} lg={8} sx={{ paddingLeft: '0 !important' }}>
          <Box sx={{ width: '100%', pr: { lg: 1.5 } }}>
            <ThreatTimelineChart
              data={generateTimelineData(dashboardData)}
              title="Threat Analysis Timeline"
            />
          </Box>
        </Grid>
        
        <Grid item xs={12} lg={4} sx={{ paddingLeft: '0 !important' }}>
          <Box sx={{ width: '100%', pl: { lg: 1.5 } }}>
            <ThreatDistributionChart
              data={generateThreatDistribution(dashboardData)}
              title="Threat Distribution"
            />
          </Box>
        </Grid>
        
        <Grid item xs={12} sx={{ paddingLeft: '0 !important' }}>
          <Box sx={{ width: '100%' }}>
            <RealTimeActivityChart
              data={generateActivityData(dashboardData)}
              title="Real-Time Security Activity"
            />
          </Box>
        </Grid>
      </Grid>

      {/* Executive Summary & Additional Insights */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="error">
                🚨 Critical Security Alerts
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Alert severity="error" sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>High Priority:</strong> 7 threat actors identified with sophisticated attack patterns
                  </Typography>
                </Alert>
                <Alert severity="warning" sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Medium Priority:</strong> {dashboardData.user_behavior?.after_hours_activity} unusual after-hours activities detected
                  </Typography>
                </Alert>
                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Info:</strong> System performance optimal - 97.8% detection accuracy maintained
                  </Typography>
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🌍 Geographic Threat Analysis
              </Typography>
              <Box>
                {Object.entries(dashboardData.threat_intelligence?.geographical_threats || {}).map(([country, count]) => (
                  <Box key={country} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="body2">{country}</Typography>
                    <Box display="flex" alignItems="center">
                      <Box 
                        sx={{ 
                          width: `${(count / 15) * 100}px`,
                          height: 8,
                          bgcolor: count > 10 ? 'error.main' : count > 5 ? 'warning.main' : 'success.main',
                          borderRadius: 1,
                          mr: 1
                        }} 
                      />
                      <Chip label={count} size="small" />
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics Summary */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Executive Security Posture Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={3}>
                  <Box textAlign="center" p={2}>
                    <Typography variant="h3" color="success.main" fontWeight="bold">
                      {((dashboardData.allowed_requests / dashboardData.total_requests) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Clean Traffic
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Box textAlign="center" p={2}>
                    <Typography variant="h3" color="error.main" fontWeight="bold">
                      {((dashboardData.blocked_requests / dashboardData.total_requests) * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Threats Blocked
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Box textAlign="center" p={2}>
                    <Typography variant="h3" color="primary.main" fontWeight="bold">
                      {Math.floor(dashboardData.total_requests / 24)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg Requests/Hour
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Box textAlign="center" p={2}>
                    <Typography variant="h3" color="warning.main" fontWeight="bold">
                      {dashboardData.user_behavior?.suspicious_patterns}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Suspicious Patterns
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
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

export default TestDashboard;