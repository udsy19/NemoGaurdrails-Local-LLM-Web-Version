import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Warning,
  Visibility,
  Group,
  PersonOutline,
  Assessment,
} from '@mui/icons-material';

import { useRealTimeData, useUserDetail } from '../../hooks/useRealTimeData';
import AnimatedMetricCard from '../shared/AnimatedMetricCard';
import LoadingSkeleton from '../shared/LoadingSkeleton';
import { PerformanceBarChart, ThreatDistributionChart } from '../shared/ModernCharts';
import { motion } from 'framer-motion';

const UserDashboard = () => {
  const { data: userData, loading, error, isConnected } = useRealTimeData('user');
  const { userDetail, loading: userDetailLoading, fetchUserDetail } = useUserDetail();
  const [selectedUserId, setSelectedUserId] = useState(null);

  const handleViewUser = (userId) => {
    setSelectedUserId(userId);
    fetchUserDetail(userId);
  };

  if (loading) {
    return <LoadingSkeleton type="dashboard" />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6">User Dashboard Error</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Box>
    );
  }

  const users = userData?.users_list || [];
  const overviewStats = userData?.overview_stats || {};

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
          WebSocket disconnected - User data may be stale
        </Alert>
      )}

      {/* Overview Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Total Users"
            value={overviewStats.total_users || 0}
            icon={<Group />}
            color="primary"
            delay={0.1}
            subtitle="Active users tracked"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="High Risk Users"
            value={overviewStats.high_risk_users || 0}
            icon={<Warning />}
            color="error"
            delay={0.2}
            subtitle="Require immediate attention"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Medium Risk Users"
            value={overviewStats.medium_risk_users || 0}
            icon={<PersonOutline />}
            color="warning"
            delay={0.3}
            subtitle="Monitor closely"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <AnimatedMetricCard
            title="Average Risk Score"
            value={overviewStats.avg_risk_score?.toFixed(1) || '0.0'}
            icon={<Assessment />}
            color="success"
            delay={0.4}
            subtitle="Overall security health"
          />
        </Grid>
      </Grid>

      {/* User Activity Analytics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} lg={6}>
          <PerformanceBarChart
            data={generateUserActivityData(users)}
            title="User Activity Distribution"
          />
        </Grid>
        
        <Grid item xs={12} lg={6}>
          <ThreatDistributionChart
            data={generateUserRiskDistribution(users)}
            title="User Risk Distribution"
          />
        </Grid>
      </Grid>

      {/* User List Table */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.6 }}
      >
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            User Activity Overview
          </Typography>
          
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User ID</TableCell>
                  <TableCell>IP Address</TableCell>
                  <TableCell>Risk Score</TableCell>
                  <TableCell>Total Requests</TableCell>
                  <TableCell>Blocked %</TableCell>
                  <TableCell>Last Active</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length > 0 ? (
                  users.slice(0, 50).map((user, index) => (
                    <UserTableRow
                      key={`${user.user_id}-${index}`}
                      user={user}
                      onViewUser={handleViewUser}
                    />
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography color="text.secondary" py={4}>
                        No user data available
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
      </motion.div>
      
      {/* User Detail Preview (placeholder) */}
      {selectedUserId && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              User Detail: {selectedUserId}
            </Typography>
            {userDetailLoading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            ) : userDetail ? (
              <Typography color="text.secondary">
                User detail implementation in progress...
              </Typography>
            ) : (
              <Typography color="text.secondary">
                Loading user details...
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

// Helper Component
const UserTableRow = ({ user, onViewUser }) => {
  const getRiskColor = (riskScore) => {
    if (riskScore >= 70) return 'error';
    if (riskScore >= 40) return 'warning';
    return 'success';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <TableRow hover>
      <TableCell>
        <Typography variant="body2" noWrap>
          {user.user_id || 'Unknown'}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" fontFamily="monospace">
          {user.ip_address || 'Unknown'}
        </Typography>
      </TableCell>
      <TableCell>
        <Chip
          label={user.risk_score || 0}
          color={getRiskColor(user.risk_score)}
          size="small"
        />
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {user.total_requests || 0}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {user.blocked_percentage?.toFixed(1) || '0.0'}%
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {formatDate(user.last_active)}
        </Typography>
      </TableCell>
      <TableCell>
        <Tooltip title="View user details">
          <IconButton
            size="small"
            onClick={() => onViewUser(user.user_id)}
            color="primary"
          >
            <Visibility />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
};

// Data transformation functions for charts
const generateUserActivityData = (users) => {
  if (!users.length) return [];
  
  const activityRanges = {
    'Low (0-10)': 0,
    'Medium (11-50)': 0,
    'High (51-100)': 0,
    'Very High (100+)': 0
  };
  
  users.forEach(user => {
    const requests = user.total_requests || 0;
    if (requests <= 10) activityRanges['Low (0-10)']++;
    else if (requests <= 50) activityRanges['Medium (11-50)']++;
    else if (requests <= 100) activityRanges['High (51-100)']++;
    else activityRanges['Very High (100+)']++;
  });
  
  return Object.entries(activityRanges).map(([name, requests]) => ({
    name,
    requests,
    blocked: Math.floor(requests * 0.1) // Approximate blocked requests
  }));
};

const generateUserRiskDistribution = (users) => {
  if (!users.length) return [];
  
  const riskDistribution = {
    'Low Risk (0-39)': 0,
    'Medium Risk (40-69)': 0,
    'High Risk (70-100)': 0
  };
  
  users.forEach(user => {
    const riskScore = user.risk_score || 0;
    if (riskScore < 40) riskDistribution['Low Risk (0-39)']++;
    else if (riskScore < 70) riskDistribution['Medium Risk (40-69)']++;
    else riskDistribution['High Risk (70-100)']++;
  });
  
  return Object.entries(riskDistribution).map(([name, value]) => ({ name, value }));
};

export default UserDashboard;