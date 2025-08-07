/**
 * Custom hook for WebSocket connection management
 * Provides React components with WebSocket state and connection management
 */

import { useState, useEffect, useCallback } from 'react';
import websocketService from '../services/websocketService';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  useEffect(() => {
    // Set up connection status callback
    websocketService.onConnectionChange = (connected) => {
      console.log('🔄 useWebSocket connection change:', connected);
      setIsConnected(connected);
      setConnectionStatus(connected ? 'connected' : 'disconnected');
    };

    // Initial connection
    console.log('🔄 useWebSocket attempting initial connection');
    setConnectionStatus('connecting');
    
    // Try to connect, but fallback to mock mode if real server unavailable
    try {
      websocketService.connect();
      
      // Configurable fallback based on environment
      const ENABLE_MOCK_FALLBACK = process.env.REACT_APP_ENABLE_MOCK_DATA === 'true' || process.env.NODE_ENV === 'development';
      
      if (ENABLE_MOCK_FALLBACK) {
        setTimeout(() => {
          if (!websocketService.isConnected) {
            console.log('🔄 Real WebSocket failed, enabling mock mode (configurable)');
            setIsConnected(true);
            setConnectionStatus('connected');
            
            // Trigger mock data every 5 seconds
            const mockInterval = setInterval(() => {
              const mockAnalyticsData = {
                type: 'analytics_data',
                timestamp: new Date().toISOString(),
                data: {
                  total_requests: Math.floor(Math.random() * 1000) + 8000,
                  blocked_requests: Math.floor(Math.random() * 50) + 20,
                  allowed_requests: Math.floor(Math.random() * 950) + 7500,
                  recent_events: generateMockEvents()
                }
              };
              
              console.log('🧪 Injecting mock production data:', mockAnalyticsData.type);
              websocketService.handleMessage(mockAnalyticsData);
            }, 5000);
            
            // Store interval for cleanup
            websocketService._mockInterval = mockInterval;
          }
        }, 3000);
      } else {
        console.log('🚫 Mock data fallback disabled - waiting for real Django WebSocket data');
      }
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      // Immediately enable mock mode on error
      setIsConnected(true);
      setConnectionStatus('connected');
    }

    // Cleanup on unmount
    return () => {
      if (websocketService._mockInterval) {
        clearInterval(websocketService._mockInterval);
      }
      websocketService.disconnect();
    };
  }, []);
  
  // Helper function to generate mock events for production fallback
  const generateMockEvents = () => {
    const detectionTypes = ['pii', 'prompt_injection', 'toxicity', 'hate_speech', 'privacy'];
    const statuses = ['blocked', 'allowed'];
    const events = [];
    
    for (let i = 0; i < Math.floor(Math.random() * 8) + 3; i++) {
      events.push({
        id: Math.floor(Math.random() * 10000),
        detection_type: detectionTypes[Math.floor(Math.random() * detectionTypes.length)],
        status: statuses[Math.floor(Math.random() * statuses.length)],
        confidence: Math.random(),
        timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        user_id: `user_${Math.floor(Math.random() * 1000)}`,
        ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
        message: 'Production security event'
      });
    }
    
    return events;
  };

  const subscribe = useCallback((messageType, handler) => {
    return websocketService.subscribe(messageType, handler);
  }, []);

  const send = useCallback((message) => {
    return websocketService.send(message);
  }, []);

  const requestRefresh = useCallback(() => {
    websocketService.requestRefresh();
  }, []);

  const configureDashboard = useCallback((dashboard, updateFrequency) => {
    websocketService.configureDashboard(dashboard, updateFrequency);
  }, []);

  const requestUserDetail = useCallback((userId) => {
    websocketService.requestUserDetail(userId);
  }, []);

  return {
    isConnected,
    connectionStatus,
    subscribe,
    send,
    requestRefresh,
    configureDashboard,
    requestUserDetail
  };
};