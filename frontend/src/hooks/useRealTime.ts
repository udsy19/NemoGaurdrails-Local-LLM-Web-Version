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
        const response = await fetch('http://localhost:8000/api/logs');
        if (response.ok) {
          const backendLogs = await response.json();
          setLogs(backendLogs);
        }
      } catch (error) {
        console.error('Failed to fetch logs:', error);
        // Fallback to some basic logs
        addLog({
          id: `error_${Date.now()}`,
          timestamp: new Date().toISOString(),
          level: 'error',
          source: 'system',
          message: 'Failed to connect to backend logs'
        });
      }
    };

    fetchLogs();
    setIsConnected(true);
    
    // Poll for new logs every 2 seconds
    const interval = setInterval(fetchLogs, 2000);

    return () => {
      clearInterval(interval);
    };
  }, [addLog]);

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
    // Disable WebSocket for testing - use mock terminal
    setIsConnected(true);
    addSystemMessage('🛡️ AI Safety System Terminal v1.0', 'system');
    addSystemMessage('Type "help" for available commands', 'system');
    addSystemMessage('🟢 Connected to AI Safety System', 'system');

    // Disable real WebSocket connection
    // wsService.onTerminalOutput(addOutput);
    // wsService.onConnectionChange((connected) => {
    //   setIsConnected(connected);
    //   if (connected) {
    //     addSystemMessage('🟢 Connected to AI Safety System', 'system');
    //   } else {
    //     addSystemMessage('🔴 Disconnected from AI Safety System', 'error');
    //   }
    // });

    // Auto-scroll to bottom when new output is added
    scrollToBottom();
  }, [addOutput, addSystemMessage, scrollToBottom]);

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