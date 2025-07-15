import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import {
  SystemHealth,
  DetectorInfo,
  ChatMessage,
  ChatResponse,
  DetectorConfig,
  ApiError,
} from '../types';

export const useApi = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check connection status
  const checkConnection = useCallback(async () => {
    try {
      const connected = await apiService.ping();
      setIsConnected(connected);
      if (connected) {
        setError(null);
      }
      return connected;
    } catch (err) {
      setIsConnected(false);
      setError('Failed to connect to backend');
      return false;
    }
  }, []);

  // Initialize connection check
  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [checkConnection]);

  return {
    isConnected,
    isLoading,
    error,
    checkConnection,
    apiService,
  };
};

export const useSystemHealth = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const healthData = await apiService.getHealth();
      setHealth(healthData);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return {
    health,
    isLoading,
    error,
    refetch: fetchHealth,
  };
};

export const useDetectors = () => {
  const [detectors, setDetectors] = useState<DetectorInfo[]>([]);
  const [selectedDetectors, setSelectedDetectors] = useState<string[]>([]);
  const [detectorConfig, setDetectorConfig] = useState<DetectorConfig>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetectors = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const detectorsData = await apiService.getDetectors();
      setDetectors(detectorsData);
      
      // Initialize selected detectors with loaded ones
      const loadedDetectors = detectorsData
        .filter(d => d.loaded && d.active)
        .map(d => d.name);
      setSelectedDetectors(loadedDetectors);
      
      // Initialize detector config
      const config: DetectorConfig = {};
      loadedDetectors.forEach(name => {
        config[name] = { enabled: true };
      });
      setDetectorConfig(config);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleDetector = useCallback((detectorName: string, enabled: boolean) => {
    setSelectedDetectors(prev => 
      enabled 
        ? [...prev.filter(d => d !== detectorName), detectorName]
        : prev.filter(d => d !== detectorName)
    );
    
    setDetectorConfig(prev => ({
      ...prev,
      [detectorName]: { ...prev[detectorName], enabled }
    }));
  }, []);

  const updateDetectorConfig = useCallback((name: string, config: any) => {
    setDetectorConfig(prev => ({
      ...prev,
      [name]: { ...prev[name], ...config }
    }));
  }, []);

  useEffect(() => {
    fetchDetectors();
  }, [fetchDetectors]);

  return {
    detectors,
    selectedDetectors,
    detectorConfig,
    isLoading,
    error,
    toggleDetector,
    updateDetectorConfig,
    refetch: fetchDetectors,
  };
};

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (
    content: string,
    detectorConfig?: DetectorConfig,
    providerId?: string
  ): Promise<ChatResponse | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.sendMessage(content, detectorConfig, sessionId, providerId);
      
      // Add user message
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
        session_id: sessionId,
      };
      
      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
        session_id: response.session_id,
        blocked: response.blocked,
        blocking_reasons: response.blocking_reasons,
        input_analysis: response.input_analysis,
        output_analysis: response.output_analysis,
      };
      
      setMessages(prev => [...prev, userMessage, assistantMessage]);
      return response;
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearHistory = useCallback(async () => {
    try {
      await apiService.clearChatHistory(sessionId);
      setMessages([]);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    }
  }, [sessionId]);

  const loadHistory = useCallback(async () => {
    try {
      const history = await apiService.getChatHistory(sessionId);
      setMessages(history);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    }
  }, [sessionId]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory,
    refetch: loadHistory,
  };
};

export const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const metricsData = await apiService.getPerformanceMetrics();
      setMetrics(metricsData);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return {
    metrics,
    isLoading,
    error,
    refetch: fetchMetrics,
  };
};