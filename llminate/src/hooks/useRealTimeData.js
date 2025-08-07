/**
 * Custom hook for real-time dashboard data management
 * Handles data state and WebSocket message subscriptions
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import websocketService from '../services/websocketService';

export const useRealTimeData = (dashboardType = 'main') => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  const { isConnected, subscribe, configureDashboard } = useWebSocket();
  
  console.log(`🔄 useRealTimeData hook initialized for ${dashboardType}`, { isConnected, loading });

  useEffect(() => {
    console.log(`🔄 useRealTimeData useEffect triggered for ${dashboardType}`, { isConnected, loading });
    
    // Set a fallback timeout to stop loading even if not connected
    const fallbackTimeout = setTimeout(() => {
      console.log(`⏰ Fallback timeout for ${dashboardType} - stopping loading state`);
      setLoading(false);
    }, 5000); // 5 second fallback
    
    if (!isConnected) {
      console.log(`⚠️ ${dashboardType} not connected yet, but will timeout eventually`);
      // Don't return early - still set up subscriptions for when connection comes
    }
    
    // Clear fallback if we get connected
    if (isConnected) {
      clearTimeout(fallbackTimeout);
    }

    console.log(`✅ Setting up ${dashboardType} dashboard data subscriptions`);

    // Configure dashboard type  
    configureDashboard(dashboardType, 15); // 15 second updates

    // Subscribe to Django channels message types
    const unsubscribeAnalytics = subscribe('analytics_data', (newData, message) => {
      console.log('📊 useRealTimeData received analytics_data for', dashboardType, ':', message);
      // Handle both direct data and nested data structure
      const actualData = newData?.data || newData;
      console.log('📊 Setting data to:', actualData);
      setData(actualData);
      setLoading(false);
      setError(null);
      setLastUpdated(new Date(message.timestamp || Date.now()));
      console.log('📊 Data state updated successfully for', dashboardType);
    });

    const unsubscribeUserData = subscribe('user_data', (newData, message) => {
      console.log('👥 Received user_data:', message);
      if (dashboardType === 'user') {
        // Handle both direct data and nested data structure
        const actualData = newData?.data || newData;
        setData(actualData);
        setLoading(false);
        setError(null);
        setLastUpdated(new Date(message.timestamp || Date.now()));
      }
    });

    // Subscribe to guardrails updates
    const unsubscribeGuardrails = subscribe('guardrails_update', (newData, message) => {
      console.log('🛡️ Received guardrails_update:', message);
      const actualData = newData?.data || newData;
      setData(actualData);
      setLoading(false);
      setError(null);
      setLastUpdated(new Date(message.timestamp || Date.now()));
    });

    // Subscribe to detection events
    const unsubscribeDetection = subscribe('detection_event', (newData, message) => {
      console.log('🚨 Received detection_event:', message);
      // Update data incrementally for real-time detection events
      const eventData = newData?.data || newData || message;
      setData(prevData => ({
        ...prevData,
        recent_events: [eventData, ...(prevData?.recent_events || []).slice(0, 9)]
      }));
      setLastUpdated(new Date(message.timestamp || Date.now()));
    });

    // Subscribe to connection status updates
    const unsubscribeStatus = subscribe('connection_status', (statusData, message) => {
      console.log('Received connection_status:', message);
    });

    // Subscribe to error messages
    const unsubscribeError = subscribe('error', (errorData, message) => {
      console.error('WebSocket error:', errorData);
      setError(errorData.message || 'WebSocket error occurred');
    });

    // Use the service methods for initial data requests
    setTimeout(() => {
      console.log(`🔄 Requesting initial data for ${dashboardType} dashboard`);
      if (dashboardType === 'main') {
        websocketService.requestAnalyticsData('24h');
        // Set loading to false after timeout if no data comes
        setTimeout(() => {
          console.log(`⏰ Timeout fallback for ${dashboardType} - setting loading to false`);
          setLoading(false);
        }, 3000);
      } else if (dashboardType === 'user') {
        websocketService.requestUserData(null, '24h');
        // Set loading to false after timeout if no data comes
        setTimeout(() => {
          console.log(`⏰ Timeout fallback for ${dashboardType} - setting loading to false`);
          setLoading(false);
        }, 3000);
      }
    }, 1500); // Give connection time to establish

    return () => {
      unsubscribeAnalytics();
      unsubscribeUserData();
      unsubscribeGuardrails();
      unsubscribeDetection();
      unsubscribeStatus();
      unsubscribeError();
    };
  }, [isConnected, dashboardType, subscribe, configureDashboard]);

  const refreshData = useCallback(() => {
    setLoading(true);
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    lastUpdated,
    isConnected,
    refreshData
  };
};

export const useUserDetail = () => {
  const [userDetail, setUserDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const { subscribe, requestUserDetail } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('user_detail_response', (data, message) => {
      setUserDetail(data);
      setLoading(false);
      setError(null);
    });

    return unsubscribe;
  }, [subscribe]);

  const fetchUserDetail = useCallback((userId) => {
    setLoading(true);
    setError(null);
    requestUserDetail(userId);
  }, [requestUserDetail]);

  const clearUserDetail = useCallback(() => {
    setUserDetail(null);
    setLoading(false);
    setError(null);
  }, []);

  return {
    userDetail,
    loading,
    error,
    fetchUserDetail,
    clearUserDetail
  };
};