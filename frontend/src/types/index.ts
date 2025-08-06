// API Types
export interface DetectorConfig {
  [key: string]: {
    enabled: boolean;
    threshold?: number;
    config?: any;
    customKeywords?: string[];
    blockedWords?: string[];
    customResponse?: string;
    actionType?: 'block' | 'warn' | 'log';
    severity?: 'low' | 'medium' | 'high';
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  session_id: string;
  blocked?: boolean;
  blocking_reasons?: string[];
  input_analysis?: DetectionResult;
  output_analysis?: DetectionResult;
}

export interface DetectionResult {
  [detector: string]: {
    blocked: boolean;
    confidence: number;
    reason: string;
    details?: any;
  };
}

export interface ChatResponse {
  response: string;
  blocked: boolean;
  blocking_reasons: string[];
  warnings: string[];
  session_id: string;
  message_id: string;
  timestamp: string;
  input_analysis?: DetectionResult;
  output_analysis?: DetectionResult;
}

export interface DetectorInfo {
  name: string;
  loaded: boolean;
  active: boolean;
  description: string;
  status: 'loaded' | 'loading' | 'error';
  config?: any;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'critical';
  models_loaded: boolean;
  detectors_available: string[];
  ollama_connected: boolean;
  nemo_guardrails: boolean;
  system_health?: {
    overall_status: string;
    components: SystemComponent[];
    system_metrics: any;
    timestamp: string;
  };
}

export interface SystemComponent {
  name: string;
  status: string;
  response_time: number;
  error?: string;
}

// Terminal/Log Types
export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug' | 'success';
  source: string;
  message: string;
  details?: any;
}

export interface TerminalOutput {
  type: 'input' | 'output' | 'error' | 'system';
  content: string;
  timestamp: string;
  source?: string;
}

// UI State Types
export interface AppState {
  isConnected: boolean;
  systemHealth: SystemHealth | null;
  detectors: DetectorInfo[];
  selectedDetectors: string[];
  currentSession: string;
  messages: ChatMessage[];
  logs: LogEntry[];
  terminalOutput: TerminalOutput[];
  isLoading: boolean;
  error: string | null;
}

// Animation Types
export interface AnimationConfig {
  duration: number;
  delay?: number;
  easing?: string;
}

// Component Props Types
export interface ChatInterfaceProps {
  onSendMessage: (message: string) => void;
  messages: ChatMessage[];
  isLoading: boolean;
  disabled?: boolean;
}

export interface GuardrailPanelProps {
  detectors: DetectorInfo[];
  selectedDetectors: string[];
  onDetectorToggle: (detectorName: string, enabled: boolean) => void;
  onConfigChange: (config: DetectorConfig) => void;
}

export interface TerminalProps {
  logs: LogEntry[];
  output: TerminalOutput[];
  maxLines?: number;
  autoScroll?: boolean;
}

export interface DashboardProps {
  systemHealth: SystemHealth;
  metrics: any;
  onRefresh: () => void;
}

// WebSocket Types
export interface WSMessage {
  type: 'chat' | 'log' | 'system' | 'health' | 'detector_status';
  data: any;
  timestamp: string;
}

// API Service Types
export interface ApiClient {
  sendMessage: (message: string, detectorConfig?: DetectorConfig) => Promise<ChatResponse>;
  getDetectors: () => Promise<DetectorInfo[]>;
  getHealth: () => Promise<SystemHealth>;
  getChatHistory: (sessionId: string) => Promise<ChatMessage[]>;
  clearHistory: (sessionId: string) => Promise<void>;
  updateDetectorConfig: (sessionId: string, config: DetectorConfig) => Promise<void>;
}

// Error Types
export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

export interface ValidationError {
  field: string;
  message: string;
}

// Performance Metrics
export interface PerformanceMetrics {
  responseTime: number;
  memoryUsage: number;
  cpuUsage: number;
  activeConnections: number;
  errorRate: number;
  throughput: number;
}