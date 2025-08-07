import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  ChatResponse,
  DetectorInfo,
  SystemHealth,
  ChatMessage,
  DetectorConfig,
  ApiError,
  LogEntry,
} from '../types';

// Authentication token management
class TokenManager {
  private static TOKEN_KEY = 'auth_token';
  private static REFRESH_TOKEN_KEY = 'refresh_token';
  
  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }
  
  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }
  
  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }
  
  static setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }
  
  static clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
  }
  
  static hasValidToken(): boolean {
    const token = this.getToken();
    if (!token) return false;
    
    try {
      // Basic JWT validation - check if it's not expired
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp > now;
    } catch {
      return false;
    }
  }
}

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for authentication and logging
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token if available
        const token = TokenManager.getToken();
        if (token && TokenManager.hasValidToken()) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('❌ API Response Error:', error);
        
        // Handle authentication errors
        if (error.response?.status === 401) {
          // Clear invalid tokens
          TokenManager.clearTokens();
          // Redirect to login page or emit event
          window.dispatchEvent(new CustomEvent('auth:logout'));
        }
        
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private handleError(error: any): ApiError {
    if (error.response) {
      return {
        message: error.response.data?.message || error.response.statusText,
        status: error.response.status,
        details: error.response.data,
      };
    } else if (error.request) {
      return {
        message: 'Network error - please check your connection',
        status: 0,
        details: error.request,
      };
    } else {
      return {
        message: error.message || 'An unknown error occurred',
        status: -1,
        details: error,
      };
    }
  }

  // Health and System Status
  async getHealth(): Promise<SystemHealth> {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getDetailedHealth(): Promise<any> {
    const response = await this.client.get('/health/detailed');
    return response.data;
  }

  // Detector Management
  async getDetectors(): Promise<DetectorInfo[]> {
    const response = await this.client.get('/api/detectors');
    const data = response.data;
    
    // Handle both formats: direct array or wrapped in detectors property
    const detectorsArray = Array.isArray(data) ? data : (data.detectors || []);
    
    return detectorsArray.map((detector: any) => ({
      name: detector.name,
      loaded: detector.loaded || detector.status === 'loaded',
      active: detector.active !== false,
      description: detector.description || 'No description available',
      status: detector.status || (detector.loaded ? 'loaded' : 'loading'),
      config: detector.config,
    }));
  }

  async getDetectorStatus(detectorName: string): Promise<any> {
    const response = await this.client.get(`/api/detectors/${detectorName}/status`);
    return response.data;
  }

  async updateDetectorConfig(detectorName: string, config: any): Promise<void> {
    await this.client.put(`/api/config/detectors`, {
      detector_name: detectorName,
      config: config
    });
  }

  // Configuration Management
  async getDetectorConfigs(): Promise<any> {
    const response = await this.client.get('/api/config/detectors');
    return response.data;
  }

  async getDetectorConfig(detectorName: string): Promise<any> {
    const response = await this.client.get(`/api/config/detectors/${detectorName}`);
    return response.data;
  }

  async updateAllDetectorConfigs(configs: Record<string, any>): Promise<void> {
    // Update each detector individually with better error handling
    const updatePromises = Object.entries(configs).map(async ([detectorName, config]) => {
      try {
        await this.updateDetectorConfig(detectorName, config);
        console.log(`✅ Successfully updated detector config for: ${detectorName}`);
      } catch (error) {
        console.error(`❌ Failed to update detector config for ${detectorName}:`, error);
        throw new Error(`Failed to update ${detectorName}: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    });
    await Promise.all(updatePromises);
  }

  // Chat Operations
  async sendMessage(
    message: string,
    detectorConfig?: DetectorConfig,
    sessionId?: string,
    providerId?: string
  ): Promise<ChatResponse> {
    const payload = {
      message,
      detector_config: detectorConfig,
      session_id: sessionId,
      provider_id: providerId,
    };

    // Use longer timeout for chat messages since they may involve AI processing
    const response = await this.client.post('/api/chat/message', payload, {
      timeout: 60000 // 60 seconds instead of 30
    });
    return response.data;
  }

  async getChatHistory(sessionId: string, limit: number = 50): Promise<ChatMessage[]> {
    const response = await this.client.get(`/api/chat/history/${sessionId}`, {
      params: { limit },
    });
    return Array.isArray(response.data) ? response.data : (response.data.messages || []);
  }

  async clearChatHistory(sessionId: string): Promise<void> {
    await this.client.delete(`/api/chat/history/${sessionId}`);
  }

  async updateSessionDetectorConfig(sessionId: string, config: DetectorConfig): Promise<void> {
    await this.client.post('/api/chat/config', {
      session_id: sessionId,
      detector_config: config,
    });
  }

  async getSessionConfig(sessionId: string): Promise<DetectorConfig> {
    const response = await this.client.get(`/api/chat/config/${sessionId}`);
    return response.data.config || {};
  }

  async getActiveSessions(): Promise<string[]> {
    const response = await this.client.get('/api/chat/sessions');
    return response.data.active_sessions || [];
  }

  async getSessionStats(sessionId: string): Promise<any> {
    const response = await this.client.get(`/api/chat/stats/${sessionId}`);
    return response.data;
  }

  // Batch Operations
  async processBatchMessages(
    messages: string[],
    detectorConfig?: DetectorConfig
  ): Promise<any> {
    const response = await this.client.post('/api/chat/batch', {
      messages,
      detector_config: detectorConfig,
    });
    return response.data;
  }

  // Test Operations
  async testDetector(detectorName: string, testMessage: string): Promise<any> {
    const response = await this.client.post(`/api/detectors/${detectorName}/test`, {
      text: testMessage,
    });
    return response.data;
  }

  async testChatPipeline(message: string, detectorConfig?: DetectorConfig): Promise<ChatResponse> {
    const response = await this.client.post('/api/chat/test', {
      message,
      detector_config: detectorConfig,
    });
    return response.data;
  }

  // Monitoring and Diagnostics
  async getAlerts(): Promise<any> {
    const response = await this.client.get('/alerts');
    return response.data;
  }

  async getPerformanceMetrics(): Promise<any> {
    const response = await this.client.get('/performance');
    return response.data;
  }

  async runDiagnostics(level: string = 'detailed'): Promise<any> {
    const response = await this.client.post('/diagnostics/run', { level });
    return response.data;
  }

  async executeRecovery(): Promise<any> {
    const response = await this.client.post('/recovery/execute');
    return response.data;
  }

  async getSelfHealingStatus(): Promise<any> {
    const response = await this.client.get('/self-healing');
    return response.data;
  }

  async getMonitoringOverview(): Promise<any> {
    const response = await this.client.get('/monitoring/overview');
    return response.data;
  }

  // Configuration Management
  async getConfig(): Promise<any> {
    const response = await this.client.get('/api/config/');
    return response.data;
  }

  async updateConfig(config: any): Promise<void> {
    await this.client.post('/api/config/', config);
  }

  async exportConfig(): Promise<any> {
    const response = await this.client.get('/api/config/export');
    return response.data;
  }

  async importConfig(config: any): Promise<void> {
    await this.client.post('/api/config/import', config);
  }

  // Utility Methods
  async ping(): Promise<boolean> {
    try {
      const response = await this.client.get('/');
      return response.status === 200;
    } catch {
      return false;
    }
  }

  getBaseURL(): string {
    return this.baseURL;
  }

  // Log streaming simulation (since we don't have WebSocket logs from backend)
  async simulateLogStream(): Promise<LogEntry[]> {
    // This would be replaced with actual WebSocket connection in real implementation
    const mockLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'info',
        source: 'api',
        message: 'API service initialized',
      },
      {
        id: '2',
        timestamp: new Date().toISOString(),
        level: 'success',
        source: 'health',
        message: 'System health check passed',
      },
    ];
    return mockLogs;
  }

  // Authentication methods
  async login(email: string, password: string, useBypass: boolean = false) {
    const response = await this.client.post('/api/auth/login', {
      email,
      password,
      use_bypass: useBypass,
    });

    const data = response.data;
    if (data.success && data.session?.access_token) {
      TokenManager.setToken(data.session.access_token);
      if (data.session.refresh_token) {
        TokenManager.setRefreshToken(data.session.refresh_token);
      }
    }

    return data;
  }

  async verifyLicense(licenseUuid: string, useBypass: boolean = false) {
    return await this.client.post('/api/auth/verify-license', {
      license_uuid: licenseUuid,
      use_bypass: useBypass,
    });
  }

  async logout() {
    try {
      await this.client.post('/api/auth/logout');
    } finally {
      TokenManager.clearTokens();
    }
  }

  async getSession() {
    return await this.client.get('/api/auth/session');
  }

  async getSystemInfo() {
    return await this.client.get('/api/auth/system-info');
  }

  async checkAuthHealth() {
    return await this.client.get('/api/auth/health');
  }

  // Token management utilities
  static clearAuthTokens() {
    TokenManager.clearTokens();
  }

  static hasValidAuthToken(): boolean {
    return TokenManager.hasValidToken();
  }

  static getAuthToken(): string | null {
    return TokenManager.getToken();
  }
}

// Create and export a singleton instance
export const apiService = new ApiService();
export default apiService;