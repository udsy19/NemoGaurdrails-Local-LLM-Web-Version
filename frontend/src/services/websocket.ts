import { io, Socket } from 'socket.io-client';
import { LogEntry, TerminalOutput, WSMessage } from '../types';

export class WebSocketService {
  private socket: Socket | null = null;
  private baseURL: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  // Event callbacks
  private onLogCallback?: (log: LogEntry) => void;
  private onTerminalCallback?: (output: TerminalOutput) => void;
  private onHealthCallback?: (health: any) => void;
  private onDetectorStatusCallback?: (status: any) => void;
  private onConnectionChangeCallback?: (connected: boolean) => void;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    console.log('🔌 Attempting to connect to WebSocket...');

    this.socket = io(this.baseURL, {
      transports: ['websocket', 'polling'],
      timeout: 10000,
      forceNew: true,
    });

    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.socket) {
      console.log('🔌 Disconnecting from WebSocket...');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.onConnectionChangeCallback?.(true);
      this.addSystemLog('WebSocket connected', 'success');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      this.onConnectionChangeCallback?.(false);
      this.addSystemLog(`WebSocket disconnected: ${reason}`, 'warn');
      
      if (reason === 'io server disconnect') {
        // Server disconnected, don't reconnect automatically
        return;
      }
      
      this.handleReconnection();
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      this.addSystemLog(`Connection error: ${error.message}`, 'error');
      this.handleReconnection();
    });

    // Custom message handlers
    this.socket.on('log', (data: LogEntry) => {
      this.onLogCallback?.(data);
    });

    this.socket.on('terminal_output', (data: TerminalOutput) => {
      this.onTerminalCallback?.(data);
    });

    this.socket.on('health_update', (data: any) => {
      this.onHealthCallback?.(data);
    });

    this.socket.on('detector_status', (data: any) => {
      this.onDetectorStatusCallback?.(data);
    });

    // Chat WebSocket (if backend supports it)
    this.socket.on('chat_response', (data: any) => {
      this.addSystemLog(`Chat response received: ${data.message_id}`, 'info');
    });
  }

  private handleReconnection(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      this.addSystemLog('Max reconnection attempts reached', 'error');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private addSystemLog(message: string, level: LogEntry['level']): void {
    const log: LogEntry = {
      id: `system_${Date.now()}`,
      timestamp: new Date().toISOString(),
      level,
      source: 'websocket',
      message,
    };
    this.onLogCallback?.(log);
  }

  // Simulated real-time updates for demonstration
  startSimulation(): void {
    if (!this.socket?.connected) {
      // Simulate connection for demo purposes
      setTimeout(() => {
        this.onConnectionChangeCallback?.(true);
        this.simulateRealTimeUpdates();
      }, 1000);
    }
  }

  private simulateRealTimeUpdates(): void {
    // Simulate periodic health updates
    setInterval(() => {
      if (Math.random() > 0.7) {
        const healthUpdate = {
          timestamp: new Date().toISOString(),
          status: Math.random() > 0.8 ? 'degraded' : 'healthy',
          components: ['ollama_client', 'model_manager', 'detection_service'],
        };
        this.onHealthCallback?.(healthUpdate);
      }
    }, 5000);

    // Simulate detector status updates
    setInterval(() => {
      if (Math.random() > 0.8) {
        const detectorUpdate = {
          detector: ['toxicity', 'pii', 'prompt_injection'][Math.floor(Math.random() * 3)],
          status: Math.random() > 0.9 ? 'error' : 'loaded',
          timestamp: new Date().toISOString(),
        };
        this.onDetectorStatusCallback?.(detectorUpdate);
      }
    }, 3000);

    // Simulate random log entries
    const logSources = ['api', 'detector', 'guardrails', 'ollama', 'system'];
    const logLevels: LogEntry['level'][] = ['info', 'warn', 'error', 'debug', 'success'];
    const logMessages = [
      'Processing chat message',
      'Running toxicity detection',
      'Guardrail check passed',
      'Model inference completed',
      'Cache miss for detector',
      'Health check executed',
      'Session created',
      'Detector configuration updated',
      'API request processed',
      'System metrics collected',
    ];

    setInterval(() => {
      if (Math.random() > 0.6) {
        const log: LogEntry = {
          id: `sim_${Date.now()}_${Math.random()}`,
          timestamp: new Date().toISOString(),
          level: logLevels[Math.floor(Math.random() * logLevels.length)],
          source: logSources[Math.floor(Math.random() * logSources.length)],
          message: logMessages[Math.floor(Math.random() * logMessages.length)],
        };
        this.onLogCallback?.(log);

        // Also add as terminal output
        const terminalOutput: TerminalOutput = {
          type: log.level === 'error' ? 'error' : 'output',
          content: `[${log.source.toUpperCase()}] ${log.message}`,
          timestamp: log.timestamp,
          source: log.source,
        };
        this.onTerminalCallback?.(terminalOutput);
      }
    }, 2000);
  }

  // Event subscription methods
  onLog(callback: (log: LogEntry) => void): void {
    this.onLogCallback = callback;
  }

  onTerminalOutput(callback: (output: TerminalOutput) => void): void {
    this.onTerminalCallback = callback;
  }

  onHealthUpdate(callback: (health: any) => void): void {
    this.onHealthCallback = callback;
  }

  onDetectorStatus(callback: (status: any) => void): void {
    this.onDetectorStatusCallback = callback;
  }

  onConnectionChange(callback: (connected: boolean) => void): void {
    this.onConnectionChangeCallback = callback;
  }

  // Send methods
  sendChatMessage(message: string, detectorConfig?: any): void {
    if (this.socket?.connected) {
      this.socket.emit('chat_message', {
        type: 'chat_message',
        message,
        detector_config: detectorConfig,
        timestamp: new Date().toISOString(),
      });
    }
  }

  sendCommand(command: string): void {
    if (this.socket?.connected) {
      this.socket.emit('command', {
        type: 'command',
        command,
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Utility methods
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionState(): string {
    if (!this.socket) return 'disconnected';
    return this.socket.connected ? 'connected' : 'disconnected';
  }
}

// Create and export singleton instance
export const wsService = new WebSocketService();
export default wsService;