import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface DetectorStat {
  name: string;
  display_name: string;
  total_detections: number;
  blocked_count: number;
  allowed_count: number;
  block_rate: number;
  avg_confidence: number;
  last_triggered?: string;
  effectiveness: string;
}

interface UserActivity {
  ip_address: string;
  total_requests: number;
  blocked_requests: number;
  allowed_requests: number;
  block_rate: number;
  first_seen?: string;
  last_seen?: string;
  user_agent: string;
}

interface TimelineEntry {
  hour: string;
  timestamp: string;
  total_requests: number;
  blocked_requests: number;
  allowed_requests: number;
  error_requests: number;
  unique_ips: number;
}

interface GeographicData {
  location: string;
  country_code: string;
  request_count: number;
  percentage: number;
}

interface BlockingReason {
  reason: string;
  count: number;
}

interface AnalyticsSummary {
  timeframe_hours: number;
  total_requests: number;
  blocked_requests: number;
  allowed_requests: number;
  unique_users: number;
  unique_ips: number;
  top_blocking_reasons: BlockingReason[];
  detector_stats: DetectorStat[];
  request_timeline: TimelineEntry[];
  user_activity: UserActivity[];
  geographic_data: GeographicData[];
  error_rate: number;
  avg_response_time: number;
}

interface RealtimeStats {
  total_requests: number;
  blocked_requests: number;
  allowed_requests: number;
  error_requests: number;
  recent_requests_5min: number;
  unique_users_total: number;
  avg_response_time: number;
  block_rate: number;
  requests_per_minute: number;
  timestamp: string;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const useAnalytics = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyticsSummary = useCallback(async (hours: number = 24) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/api/analytics/summary?hours=${hours}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setSummary(data.summary);
      } else {
        throw new Error('Failed to fetch analytics summary');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      console.error('Failed to fetch analytics summary:', errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchRealtimeStats = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/realtime`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setRealtimeStats(data.stats);
      } else {
        throw new Error('Failed to fetch realtime stats');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch realtime stats:', errorMessage);
    }
  }, []);

  const fetchDetectorAnalytics = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/detectors`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.detectors;
      } else {
        throw new Error('Failed to fetch detector analytics');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch detector analytics:', errorMessage);
      return [];
    }
  }, []);

  const fetchUserAnalytics = useCallback(async (limit: number = 50) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/users?limit=${limit}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.users;
      } else {
        throw new Error('Failed to fetch user analytics');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch user analytics:', errorMessage);
      return [];
    }
  }, []);

  const fetchTimeline = useCallback(async (hours: number = 24) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/timeline?hours=${hours}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.timeline;
      } else {
        throw new Error('Failed to fetch timeline');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to fetch timeline:', errorMessage);
      return [];
    }
  }, []);

  const trackRequest = useCallback(async (
    message: string,
    status: 'allowed' | 'blocked' | 'error',
    blockingReasons?: string[],
    detectionResults?: Record<string, any>,
    responseTimeMs?: number,
    provider?: string,
    model?: string,
    sessionId?: string
  ) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          status,
          blocking_reasons: blockingReasons,
          detection_results: detectionResults,
          response_time_ms: responseTimeMs,
          provider,
          model,
          session_id: sessionId,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh realtime stats after tracking
        fetchRealtimeStats();
        return data.event_id;
      } else {
        throw new Error('Failed to track request');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Failed to track request:', errorMessage);
      return null;
    }
  }, [fetchRealtimeStats]);

  const exportAnalyticsData = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/export`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Create download link
        const blob = new Blob([JSON.stringify(data.export_data, null, 2)], {
          type: 'application/json',
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `analytics-export-${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        toast.success('Analytics data exported successfully');
        return true;
      } else {
        throw new Error('Failed to export analytics data');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Export failed: ${errorMessage}`);
      return false;
    }
  }, []);

  const cleanupOldData = useCallback(async (hours: number = 168) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics/cleanup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ hours }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        toast.success('Old analytics data cleaned up successfully');
        // Refresh summary after cleanup
        fetchAnalyticsSummary();
        fetchRealtimeStats();
        return true;
      } else {
        throw new Error('Failed to cleanup old data');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Cleanup failed: ${errorMessage}`);
      return false;
    }
  }, [fetchAnalyticsSummary, fetchRealtimeStats]);

  // Auto-refresh realtime stats every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchRealtimeStats, 30000);
    return () => clearInterval(interval);
  }, [fetchRealtimeStats]);

  // Load initial data
  useEffect(() => {
    fetchAnalyticsSummary();
    fetchRealtimeStats();
  }, [fetchAnalyticsSummary, fetchRealtimeStats]);

  return {
    summary,
    realtimeStats,
    loading,
    error,
    
    // Actions
    fetchAnalyticsSummary,
    fetchRealtimeStats,
    fetchDetectorAnalytics,
    fetchUserAnalytics,
    fetchTimeline,
    trackRequest,
    exportAnalyticsData,
    cleanupOldData,
    
    // Computed values
    isLoaded: !loading && !error,
    hasData: summary && summary.total_requests > 0,
    blockRate: summary ? (summary.blocked_requests / summary.total_requests * 100) : 0,
    safetyEffectiveness: summary ? 
      (summary.blocked_requests > 0 ? 'Active' : 'Monitoring') : 'Unknown',
  };
};