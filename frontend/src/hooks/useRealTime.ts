import { useState, useEffect, useCallback, useRef } from 'react';
import { wsService } from '../services/websocket';
import { LogEntry, TerminalOutput } from '../types';

export const useRealTimeLogs = (maxLogs: number = 1000) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const addLog = useCallback((newLog: LogEntry) => {
    setLogs(prevLogs => {
      const updatedLogs = [...prevLogs, newLog];
      // Keep only the last maxLogs entries
      return updatedLogs.slice(-maxLogs);
    });
  }, [maxLogs]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  useEffect(() => {
    // Fetch real logs from backend
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/logs?limit=50`);
        if (response.ok) {
          const backendLogs = await response.json();
          // Convert backend log format to LogEntry format
          const convertedLogs = backendLogs.map((log: any) => ({
            id: log.id || `log_${Date.now()}_${Math.random()}`,
            timestamp: log.timestamp || new Date().toISOString(),
            level: log.level || 'info',
            source: log.source || 'system',
            message: log.message || 'Unknown log entry'
          }));
          setLogs(convertedLogs);
          setIsConnected(true);
        } else {
          throw new Error('API request failed');
        }
      } catch (error) {
        console.error('Failed to fetch logs:', error);
        setIsConnected(false);
        // Fallback to some basic logs if first time connecting
        if (logs.length === 0) {
          addLog({
            id: `error_${Date.now()}`,
            timestamp: new Date().toISOString(),
            level: 'error',
            source: 'system',
            message: 'Failed to connect to backend logs - check if backend is running'
          });
        }
      }
    };

    fetchLogs();
    
    // Poll for new logs every 3 seconds
    const interval = setInterval(fetchLogs, 3000);

    return () => {
      clearInterval(interval);
    };
  }, [addLog, logs.length]);

  return {
    logs,
    isConnected,
    clearLogs,
    addLog,
  };
};

export const useTerminal = (maxLines: number = 500) => {
  const [output, setOutput] = useState<TerminalOutput[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);

  const addOutput = useCallback((newOutput: TerminalOutput) => {
    setOutput(prevOutput => {
      const updatedOutput = [...prevOutput, newOutput];
      return updatedOutput.slice(-maxLines);
    });
  }, [maxLines]);

  const addCommand = useCallback((command: string) => {
    const commandOutput: TerminalOutput = {
      type: 'input',
      content: `$ ${command}`,
      timestamp: new Date().toISOString(),
      source: 'user',
    };
    addOutput(commandOutput);
  }, [addOutput]);

  const addSystemMessage = useCallback((message: string, type: TerminalOutput['type'] = 'system') => {
    const systemOutput: TerminalOutput = {
      type,
      content: message,
      timestamp: new Date().toISOString(),
      source: 'system',
    };
    addOutput(systemOutput);
  }, [addOutput]);

  const clearTerminal = useCallback(() => {
    setOutput([]);
    addSystemMessage('Terminal cleared');
  }, [addSystemMessage]);

  const scrollToBottom = useCallback(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    // Initialize terminal with welcome message
    addSystemMessage('🛡️ AI Safety System Terminal v1.0', 'system');
    addSystemMessage('Type "help" for available commands', 'system');
    
    // Fetch real logs from backend API
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/logs?limit=20`);
        if (response.ok) {
          const logs = await response.json();
          logs.forEach((log: any) => {
            const terminalOutput: TerminalOutput = {
              type: log.level === 'error' ? 'error' : log.level === 'warn' ? 'error' : 'output',
              content: `[${log.source?.toUpperCase() || 'SYSTEM'}] ${log.message}`,
              timestamp: log.timestamp || new Date().toISOString(),
              source: log.source || 'system',
            };
            addOutput(terminalOutput);
          });
          setIsConnected(true);
          addSystemMessage('🟢 Connected to AI Safety System', 'system');
        } else {
          throw new Error('Failed to fetch logs');
        }
      } catch (error) {
        console.error('Failed to connect to backend:', error);
        setIsConnected(false);
        addSystemMessage('🔴 Failed to connect to backend - using mock mode', 'error');
      }
    };

    fetchLogs();

    // Poll for new logs every 3 seconds
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/logs?limit=10`);
        if (response.ok) {
          const logs = await response.json();
          // Only add new logs that aren't already in output
          logs.slice(-3).forEach((log: any) => { // Only take last 3 to avoid spam
            const terminalOutput: TerminalOutput = {
              type: log.level === 'error' ? 'error' : log.level === 'warn' ? 'error' : 'output',
              content: `[${log.source?.toUpperCase() || 'SYSTEM'}] ${log.message}`,
              timestamp: log.timestamp || new Date().toISOString(),
              source: log.source || 'system',
            };
            addOutput(terminalOutput);
          });
          if (!isConnected) {
            setIsConnected(true);
            addSystemMessage('🟢 Reconnected to AI Safety System', 'system');
          }
        }
      } catch (error) {
        if (isConnected) {
          setIsConnected(false);
          addSystemMessage('🔴 Connection to backend lost', 'error');
        }
      }
    }, 3000);

    // Auto-scroll to bottom when new output is added
    scrollToBottom();

    return () => clearInterval(interval);
  }, [addOutput, addSystemMessage, scrollToBottom, isConnected]);

  // Auto-scroll effect
  useEffect(() => {
    scrollToBottom();
  }, [output, scrollToBottom]);

  return {
    output,
    isConnected,
    terminalRef,
    addOutput,
    addCommand,
    addSystemMessage,
    clearTerminal,
    scrollToBottom,
  };
};

export const useRealTimeUpdates = () => {
  const [healthUpdates, setHealthUpdates] = useState<any[]>([]);
  const [detectorUpdates, setDetectorUpdates] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const addHealthUpdate = useCallback((update: any) => {
    setHealthUpdates(prev => [...prev.slice(-10), update]); // Keep last 10 updates
  }, []);

  const addDetectorUpdate = useCallback((update: any) => {
    setDetectorUpdates(prev => [...prev.slice(-10), update]); // Keep last 10 updates
  }, []);

  useEffect(() => {
    // Disable WebSocket for testing
    setIsConnected(true);
    
    // Disable real WebSocket connection
    // wsService.onHealthUpdate(addHealthUpdate);
    // wsService.onDetectorStatus(addDetectorUpdate);
    // wsService.onConnectionChange(setIsConnected);

    return () => {
      // Cleanup is handled by the service
    };
  }, [addHealthUpdate, addDetectorUpdate]);

  return {
    healthUpdates,
    detectorUpdates,
    isConnected,
  };
};

// Custom hook for managing chat message streaming
export const useChatStreaming = () => {
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);

  const startStreaming = useCallback(() => {
    setIsStreaming(true);
    setStreamingMessage('');
  }, []);

  const addToStream = useCallback((chunk: string) => {
    setStreamingMessage(prev => prev + chunk);
  }, []);

  const stopStreaming = useCallback(() => {
    setIsStreaming(false);
  }, []);

  const resetStream = useCallback(() => {
    setStreamingMessage('');
    setIsStreaming(false);
  }, []);

  return {
    streamingMessage,
    isStreaming,
    startStreaming,
    addToStream,
    stopStreaming,
    resetStream,
  };
};

// Hook for simulating AI processing stages
export const useProcessingStages = () => {
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [stages, setStages] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const processingStages = [
    '🔍 Analyzing input message...',
    '🛡️ Running safety detectors...',
    '🔬 Toxicity detection in progress...',
    '🔒 PII detection scanning...',
    '🚨 Prompt injection analysis...',
    '🤖 Generating AI response...',
    '✅ Final safety check...',
    '📤 Preparing response...',
  ];

  const startProcessing = useCallback(async (message: string) => {
    setIsProcessing(true);
    setStages([]);
    setCurrentStage('🚀 Processing started...');

    // Simulate processing stages
    for (let i = 0; i < processingStages.length; i++) {
      const stage = processingStages[i];
      setCurrentStage(stage);
      setStages(prev => [...prev, stage]);
      
      // Random delay between 300-800ms for realistic feel
      const delay = Math.random() * 500 + 300;
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    setCurrentStage('✅ Processing complete!');
    setStages(prev => [...prev, '✅ Processing complete!']);
    
    setTimeout(() => {
      setIsProcessing(false);
      setCurrentStage(null);
    }, 1000);
  }, [processingStages]);

  const resetProcessing = useCallback(() => {
    setIsProcessing(false);
    setCurrentStage(null);
    setStages([]);
  }, []);

  return {
    currentStage,
    stages,
    isProcessing,
    startProcessing,
    resetProcessing,
  };
};