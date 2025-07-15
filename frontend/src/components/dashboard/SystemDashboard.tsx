import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { SystemHealth } from '../../types';

interface SystemDashboardProps {
  systemHealth: SystemHealth | null;
  metrics: any;
  onRefresh: () => void;
  isLoading?: boolean;
}

const SystemDashboard: React.FC<SystemDashboardProps> = ({
  systemHealth,
  metrics,
  onRefresh,
  isLoading = false,
}) => {
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#00D4AA';
      case 'degraded':
        return '#FFB800';
      case 'unhealthy':
        return '#FF6B6B';
      case 'critical':
        return '#FF3D71';
      default:
        return '#6B7280';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckIcon sx={{ color: '#00D4AA' }} />;
      case 'degraded':
        return <WarningIcon sx={{ color: '#FFB800' }} />;
      case 'unhealthy':
        return <ErrorIcon sx={{ color: '#FF6B6B' }} />;
      case 'critical':
        return <ErrorIcon sx={{ color: '#FF3D71' }} />;
      default:
        return <InfoIcon sx={{ color: '#6B7280' }} />;
    }
  };

  const recentEvents = [
    { id: 1, type: 'detection', message: 'High-risk content blocked', time: '2 min ago', severity: 'high' },
    { id: 2, type: 'system', message: 'System health check completed', time: '5 min ago', severity: 'info' },
    { id: 3, type: 'detection', message: 'PII detected and masked', time: '8 min ago', severity: 'medium' },
    { id: 4, type: 'system', message: 'Detector configuration updated', time: '12 min ago', severity: 'info' },
    { id: 5, type: 'detection', message: 'Spam message filtered', time: '15 min ago', severity: 'low' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h4" sx={{ color: '#FFFFFF', fontWeight: 600, mb: 1 }}>
              System Dashboard
            </Typography>
            <Typography variant="body1" sx={{ color: '#A8B2D1' }}>
              Real-time monitoring and analytics
            </Typography>
          </Box>
          <Tooltip title="Refresh Data">
            <IconButton
              onClick={onRefresh}
              disabled={isLoading}
              sx={{
                backgroundColor: '#00D4AA20',
                color: '#00D4AA',
                '&:hover': {
                  backgroundColor: '#00D4AA30',
                },
              }}
            >
              {isLoading ? (
                <CircularProgress size={24} sx={{ color: '#00D4AA' }} />
              ) : (
                <RefreshIcon />
              )}
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '2fr 1fr' }, gap: 3, mb: 3 }}>
          {/* System Health Overview */}
          <Paper
            elevation={8}
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
              border: '1px solid #374151',
              borderRadius: '16px',
            }}
          >
            <Typography variant="h6" sx={{ color: '#FFFFFF', mb: 2, fontWeight: 600 }}>
              System Health Overview
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 3fr' }, gap: 2 }}>
              {/* Overall Status */}
              <Card sx={{ backgroundColor: '#0A0E1A', border: '1px solid #374151', textAlign: 'center' }}>
                <CardContent>
                  <Avatar
                    sx={{
                      width: 60,
                      height: 60,
                      margin: '0 auto 16px',
                      backgroundColor: `${getHealthColor(systemHealth?.status || 'unknown')}20`,
                    }}
                  >
                    {getHealthIcon(systemHealth?.status || 'unknown')}
                  </Avatar>
                  <Typography variant="h6" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                    {systemHealth?.status?.toUpperCase() || 'UNKNOWN'}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#A8B2D1' }}>
                    Overall Status
                  </Typography>
                </CardContent>
              </Card>

              {/* Metrics */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' }, gap: 2 }}>
                <Card sx={{ backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <MemoryIcon sx={{ color: '#00D4AA', fontSize: '2rem', mb: 1 }} />
                    <Typography variant="h5" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                      {systemHealth?.detectors_available?.length || 0}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                      Detectors
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <SpeedIcon sx={{ color: '#FFB800', fontSize: '2rem', mb: 1 }} />
                    <Typography variant="h5" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                      {Math.round(Math.random() * 50 + 10)}ms
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                      Avg Response
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <SecurityIcon sx={{ color: '#FF6B6B', fontSize: '2rem', mb: 1 }} />
                    <Typography variant="h5" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                      {Math.round(Math.random() * 100)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                      Blocked Today
                    </Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: '#0A0E1A', border: '1px solid #374151' }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <TrendingUpIcon sx={{ color: '#4ECDC4', fontSize: '2rem', mb: 1 }} />
                    <Typography variant="h5" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                      99.2%
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                      Uptime
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          </Paper>

          {/* Recent Events */}
          <Paper
            elevation={8}
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
              border: '1px solid #374151',
              borderRadius: '16px',
            }}
          >
            <Typography variant="h6" sx={{ color: '#FFFFFF', mb: 2, fontWeight: 600 }}>
              Recent Events
            </Typography>
            
            <List sx={{ maxHeight: 280, overflow: 'auto' }}>
              {recentEvents.map((event, index) => (
                <React.Fragment key={event.id}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          backgroundColor: event.severity === 'high' ? '#FF3D7120' :
                                          event.severity === 'medium' ? '#FFB80020' :
                                          event.severity === 'low' ? '#00D4AA20' : '#6B728020',
                        }}
                      >
                        {event.severity === 'high' ? (
                          <ErrorIcon sx={{ fontSize: '1rem', color: '#FF3D71' }} />
                        ) : event.severity === 'medium' ? (
                          <WarningIcon sx={{ fontSize: '1rem', color: '#FFB800' }} />
                        ) : (
                          <InfoIcon sx={{ fontSize: '1rem', color: '#00D4AA' }} />
                        )}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="body2" sx={{ color: '#FFFFFF' }}>
                          {event.message}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
                          {event.time}
                        </Typography>
                      }
                    />
                  </ListItem>
                  {index < recentEvents.length - 1 && (
                    <Divider sx={{ borderColor: '#374151' }} />
                  )}
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Box>
      </Box>
    </motion.div>
  );
};

export default SystemDashboard;