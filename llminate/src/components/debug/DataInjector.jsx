import React from 'react';
import { Button, Card, CardContent, Typography, Box } from '@mui/material';
import { generateSampleData } from '../../utils/testDataHandler';
import websocketService from '../../services/websocketService';

const DataInjector = () => {
  const injectAnalyticsData = () => {
    const sampleData = generateSampleData();
    const mockMessage = {
      type: 'analytics_data',
      timestamp: new Date().toISOString(),
      data: sampleData
    };
    
    console.log('🚀 Manually injecting analytics data:', mockMessage);
    websocketService.handleMessage(mockMessage);
  };

  const injectUserData = () => {
    const mockUserData = {
      overview_stats: {
        total_users: 150,
        high_risk_users: 12,
        medium_risk_users: 28,
        avg_risk_score: 45.5
      },
      users_list: [
        {
          user_id: 'test_user_1',
          ip_address: '10.0.0.1',
          risk_score: 75,
          total_requests: 120,
          blocked_percentage: 15.5,
          last_active: new Date().toISOString()
        },
        {
          user_id: 'test_user_2',
          ip_address: '10.0.0.2',
          risk_score: 25,
          total_requests: 80,
          blocked_percentage: 8.2,
          last_active: new Date().toISOString()
        }
      ]
    };

    const mockMessage = {
      type: 'user_data',
      timestamp: new Date().toISOString(),
      data: mockUserData
    };

    console.log('🚀 Manually injecting user data:', mockMessage);
    websocketService.handleMessage(mockMessage);
  };

  const injectDetectionEvent = () => {
    const mockEvent = {
      type: 'detection_event',
      timestamp: new Date().toISOString(),
      data: {
        id: Math.floor(Math.random() * 10000),
        detection_type: 'pii',
        status: 'blocked',
        confidence: 0.95,
        user_id: 'emergency_test_user',
        ip_address: '192.168.1.999',
        message: 'MANUAL TEST EVENT - PII Detection',
        timestamp: new Date().toISOString()
      }
    };

    console.log('🚀 Manually injecting detection event:', mockEvent);
    websocketService.handleMessage(mockEvent);
  };

  return (
    <Card sx={{ mt: 2 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🎯 Manual Data Injection (for testing dashboard rendering)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Use these buttons to manually inject data directly into the dashboard to test rendering.
        </Typography>
        
        <Box display="flex" gap={1} flexWrap="wrap">
          <Button 
            variant="contained" 
            color="primary"
            onClick={injectAnalyticsData}
            size="small"
          >
            Inject Analytics Data
          </Button>
          
          <Button 
            variant="contained" 
            color="secondary"
            onClick={injectUserData}
            size="small"
          >
            Inject User Data
          </Button>
          
          <Button 
            variant="outlined" 
            color="warning"
            onClick={injectDetectionEvent}
            size="small"
          >
            Inject Detection Event
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default DataInjector;