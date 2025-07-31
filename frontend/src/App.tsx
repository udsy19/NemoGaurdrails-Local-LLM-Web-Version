import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  CssBaseline,
  ThemeProvider,
  Typography,
  TextField,
  IconButton,
  Switch,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Tooltip,
  Fade,
  Collapse,
  Alert,
  MenuItem,
} from '@mui/material';
import {
  Send,
  Shield,
  Terminal,
  Download,
  Cpu,
  HardDrive,
  Zap,
  CheckCircle,
  AlertCircle,
  X,
  Search,
  Filter,
  ArrowDown,
  TestTube,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';

// Theme and services
import { darkTheme } from './themes/darkTheme';
import { useApi, useSystemHealth, useDetectors, useChat } from './hooks/useApi';
import { useRealTimeLogs } from './hooks/useRealTime';
import { useProviders } from './hooks/useProviders';
import { ollamaService, SystemInfo, ModelRecommendation, OllamaModel } from './services/ollama';
import { ollamaDownloadService, DownloadProgress } from './services/ollamaDownload';
import GuardrailsConfig from './components/guardrails/GuardrailsConfig';
import ProvidersConfig from './components/providers/ProvidersConfig';
import AnalyticsOverview from './components/analytics/AnalyticsOverview';
import GuardrailAnalyticsDashboard from './components/analytics/GuardrailAnalyticsDashboard';
import AdvancedTestingPlayground from './components/testing/AdvancedTestingPlayground';
import ModernChatInterface from './components/chat/ModernChatInterface';
import GPUAcceleration from './components/gpu/GPUAcceleration';
import DistributedProcessing from './components/distributed/DistributedProcessing';

// Linear-inspired minimal theme
const minimalTheme = {
  ...darkTheme,
  components: {
    ...darkTheme.components,
    MuiCard: {
      styleOverrides: {
        root: {
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            background: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid rgba(0, 212, 170, 0.2)',
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            background: 'rgba(255, 255, 255, 0.02)',
            border: 'none',
            borderRadius: '8px',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.04)',
            },
            '&.Mui-focused': {
              background: 'rgba(255, 255, 255, 0.06)',
              boxShadow: '0 0 0 1px rgba(0, 212, 170, 0.3)',
            },
          },
        },
      },
    },
  },
};

const App: React.FC = () => {
  // Core state
  const [message, setMessage] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'models' | 'terminal' | 'guardrails' | 'providers' | 'analytics' | 'testing' | 'hardware'>('chat');
  const [terminalExpanded, setTerminalExpanded] = useState(false);
  const [modelSearch, setModelSearch] = useState('');
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>([]);
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, DownloadProgress>>(new Map());
  const [sessionId] = useState(() => `session_${Date.now()}`);

  // API hooks
  const { isConnected } = useApi();
  const { health } = useSystemHealth();
  const { detectors, selectedDetectors, detectorConfig, toggleDetector } = useDetectors();
  const { messages, isLoading, sendMessage: sendChatMessage, clearHistory } = useChat(sessionId);
  const { providers, enabledProviders, connectedProviders } = useProviders();
  
  
  // Provider selection state
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  
  // Set default provider when providers load
  useEffect(() => {
    if (connectedProviders.length > 0 && !selectedProvider) {
      setSelectedProvider(connectedProviders[0].id);
    }
  }, [connectedProviders, selectedProvider]);

  // Auto-scroll when new messages are added
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => scrollToBottom(true), 100);
    }
  }, [messages]);

  // Handle scroll detection for scroll button
  const handleScroll = () => {
    if (chatContainerRef.current) {
      const container = chatContainerRef.current;
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 20;
      setShowScrollButton(!isAtBottom && messages.length > 2);
    }
  };

  // Auto-scroll function with multiple fallback strategies
  const scrollToBottom = (force = false) => {
    const scroll = () => {
      if (chatContainerRef.current) {
        const container = chatContainerRef.current;
        const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 50;
        
        // Always scroll if forced, or if already near bottom
        if (force || isAtBottom || messages.length <= 1) {
          // Force scroll to bottom with multiple methods
          const scrollHeight = container.scrollHeight;
          
          // Method 1: Direct scrollTop
          container.scrollTop = scrollHeight;
          
          // Method 2: ScrollTo with behavior
          container.scrollTo({
            top: scrollHeight,
            behavior: force ? 'auto' : 'smooth'
          });
          
          // Method 3: ScrollIntoView on last message
          const lastMessage = container.lastElementChild;
          if (lastMessage) {
            lastMessage.scrollIntoView({ behavior: force ? 'auto' : 'smooth', block: 'end' });
          }
        }
        
        // Update scroll button visibility
        handleScroll();
      }
    };

    // Multiple attempts with different timings to ensure scroll works
    requestAnimationFrame(scroll);
    setTimeout(scroll, 10);
    setTimeout(scroll, 50);
    setTimeout(scroll, 100);
    setTimeout(scroll, 200);
  };

  // Auto-scroll when messages change or loading state changes
  useEffect(() => {
    scrollToBottom(true);
  }, [messages.length]);

  useEffect(() => {
    if (!isLoading) {
      // Scroll after loading is complete
      setTimeout(() => scrollToBottom(true), 100);
    }
  }, [isLoading]);

  // Scroll to bottom on initial render
  useEffect(() => {
    const timer = setTimeout(() => scrollToBottom(true), 500);
    return () => clearTimeout(timer);
  }, []);
  const { logs } = useRealTimeLogs();

  // Initialize system info and recommendations
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        const sysInfo = await ollamaService.getSystemInfo();
        setSystemInfo(sysInfo);
        
        const recs = await ollamaService.getRecommendations(sysInfo);
        setRecommendations(recs);
      } catch (error) {
        console.error('Failed to initialize system:', error);
      }
    };

    initializeSystem();
  }, []);

  // Handle message send
  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return;
    
    const messageText = message;
    setMessage('');
    
    try {
      await sendChatMessage(messageText, detectorConfig, selectedProvider);
      // Force scroll to bottom after sending message with multiple attempts
      setTimeout(() => scrollToBottom(true), 100);
      setTimeout(() => scrollToBottom(true), 500);
      setTimeout(() => scrollToBottom(true), 1000);
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  // Handle model download
  const handleDownloadModel = async (modelName: string) => {
    setDownloadingModels(prev => {
      const newSet = new Set(prev);
      newSet.add(modelName);
      return newSet;
    });
    
    try {
      await ollamaDownloadService.downloadModel(modelName, (progress) => {
        setDownloadProgress(prev => {
          const newMap = new Map(prev);
          newMap.set(modelName, progress);
          return newMap;
        });
        
        // Show toast notifications for key progress events
        if (progress.status === 'completed') {
          toast.success(`${modelName} downloaded successfully`);
        } else if (progress.status === 'error') {
          toast.error(progress.error || `Failed to download ${modelName}`);
        } else if (progress.status === 'cancelled') {
          toast.success(`Download cancelled for ${modelName}`);
        }
      });
    } catch (error) {
      toast.error(`Failed to download ${modelName}`);
    } finally {
      setDownloadingModels(prev => {
        const newSet = new Set(prev);
        newSet.delete(modelName);
        return newSet;
      });
      
      // Clean up progress tracking
      setDownloadProgress(prev => {
        const newMap = new Map(prev);
        newMap.delete(modelName);
        return newMap;
      });
    }
  };

  // Handle model download cancellation
  const handleCancelDownload = (modelName: string) => {
    ollamaDownloadService.cancelDownload(modelName);
    setDownloadingModels(prev => {
      const newSet = new Set(prev);
      newSet.delete(modelName);
      return newSet;
    });
    
    setDownloadProgress(prev => {
      const newMap = new Map(prev);
      newMap.delete(modelName);
      return newMap;
    });
  };

  // Filter recommendations based on search
  const filteredRecommendations = recommendations.filter(rec =>
    rec.model.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  // Get status color
  const getStatusColor = () => {
    if (!isConnected) return '#ef4444';
    if (health?.status === 'healthy') return '#00D4AA';
    return '#f59e0b';
  };

  return (
    <ThemeProvider theme={minimalTheme}>
      <CssBaseline />
      <Toaster position="top-center" />
      
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
          color: '#ffffff',
          fontFamily: '"Inter", system-ui, sans-serif',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 3,
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            backdropFilter: 'blur(20px)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Shield size={24} color="#00D4AA" />
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  background: 'linear-gradient(135deg, #ffffff 0%, #a1a1aa 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                AI Safety System
              </Typography>
            </Box>

            {/* Status indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  px: 2,
                  py: 0.5,
                  borderRadius: '20px',
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: `1px solid ${getStatusColor()}30`,
                }}
              >
                <Box
                  sx={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: getStatusColor(),
                    animation: isConnected ? 'pulse 2s infinite' : 'none',
                  }}
                />
                <Typography variant="caption" sx={{ color: getStatusColor() }}>
                  {isConnected ? 'Online' : 'Offline'}
                </Typography>
              </Box>

              {/* Terminal toggle */}
              <Tooltip title="Toggle Terminal">
                <IconButton
                  onClick={() => setTerminalExpanded(!terminalExpanded)}
                  sx={{
                    color: terminalExpanded ? '#00D4AA' : '#6b7280',
                    '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' },
                  }}
                >
                  <Terminal size={18} />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Tab Navigation */}
          <Box sx={{ display: 'flex', gap: 1, mt: 3 }}>
            {(['chat', 'testing', 'analytics', 'guardrails', 'providers', 'hardware', 'models', 'terminal'] as const).map((tab) => (
              <Box
                key={tab}
                onClick={() => setActiveTab(tab)}
                sx={{
                  px: 3,
                  py: 1.5,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  backgroundColor: activeTab === tab ? 'rgba(0, 212, 170, 0.1)' : 'transparent',
                  color: activeTab === tab ? '#00D4AA' : '#6b7280',
                  border: activeTab === tab ? '1px solid rgba(0, 212, 170, 0.2)' : '1px solid transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  },
                }}
              >
                <Typography variant="body2" sx={{ fontWeight: 500, textTransform: 'capitalize' }}>
                  {tab}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>

        {/* Terminal Overlay */}
        <Collapse in={terminalExpanded}>
          <Box
            sx={{
              p: 3,
              background: 'rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(20px)',
              borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
              maxHeight: '300px',
              overflow: 'auto',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6" sx={{ color: '#00D4AA', fontWeight: 500 }}>
                Live System Logs
              </Typography>
              <IconButton
                onClick={() => setTerminalExpanded(false)}
                sx={{ color: '#6b7280', '&:hover': { color: '#ffffff' } }}
              >
                <X size={18} />
              </IconButton>
            </Box>
            
            <Box
              sx={{
                fontFamily: 'JetBrains Mono, Monaco, monospace',
                fontSize: '0.8rem',
                lineHeight: 1.5,
              }}
            >
              <AnimatePresence>
                {logs.slice(-10).map((log, index) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 4,
                      padding: 4,
                      borderRadius: 4,
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#6b7280',
                        minWidth: '60px',
                        fontSize: '0.7rem',
                      }}
                    >
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        color:
                          log.level === 'error' ? '#ef4444' :
                          log.level === 'warn' ? '#f59e0b' :
                          log.level === 'success' ? '#00D4AA' : '#ffffff',
                        fontSize: '0.8rem',
                      }}
                    >
                      [{log.source}] {log.message}
                    </Typography>
                  </motion.div>
                ))}
              </AnimatePresence>
            </Box>
          </Box>
        </Collapse>

        {/* Main Content */}
        <Box sx={{ p: 3 }}>
          <AnimatePresence mode="wait">
            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                style={{ height: '100vh', position: 'relative' }}
              >
                <ModernChatInterface
                  messages={messages}
                  onSendMessage={(msg, provider, detectorConfig) => {
                    setMessage('');
                    // Use the detector config or create one from selectedDetectors
                    const config = detectorConfig || selectedDetectors.reduce((acc, detector) => {
                      acc[detector] = { enabled: true };
                      return acc;
                    }, {} as any);
                    
                    sendChatMessage(msg, config, provider);
                  }}
                  isLoading={isLoading}
                  disabled={!isConnected}
                  detectorConfig={detectorConfig}
                  onDetectorConfigChange={(config) => {
                    // Update detector config using the proper hook
                    Object.keys(config).forEach(detector => {
                      const isEnabled = config[detector]?.enabled || false;
                      const wasEnabled = detectorConfig[detector]?.enabled || false;
                      if (isEnabled !== wasEnabled) {
                        toggleDetector(detector, isEnabled);
                      }
                    });
                  }}
                  onClearHistory={() => {
                    clearHistory();
                    toast.success('Chat history cleared');
                  }}
                  availableProviders={connectedProviders}
                  selectedProvider={selectedProvider}
                  onProviderChange={setSelectedProvider}
                  onNavigateToProviders={() => setActiveTab('providers')}
                  onNavigateToGuardrails={() => setActiveTab('guardrails')}
                />
              </motion.div>
            )}

            {activeTab === 'models' && (
              <motion.div
                key="models"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {/* System Info */}
                {systemInfo && (
                  <Card sx={{ mb: 3 }}>
                    <CardContent>
                      <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>
                        System Information
                      </Typography>
                      
                      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Cpu size={20} color="#00D4AA" />
                          <Box>
                            <Typography variant="body2" sx={{ color: '#6b7280' }}>CPU Cores</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>{systemInfo.cpu.cores}</Typography>
                          </Box>
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <HardDrive size={20} color="#f59e0b" />
                          <Box>
                            <Typography variant="body2" sx={{ color: '#6b7280' }}>Memory</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>
                              {(systemInfo.memory.total / 1024).toFixed(1)} GB
                            </Typography>
                          </Box>
                        </Box>
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Zap size={20} color="#8b5cf6" />
                          <Box>
                            <Typography variant="body2" sx={{ color: '#6b7280' }}>Platform</Typography>
                            <Typography variant="body1" sx={{ fontWeight: 500 }}>{systemInfo.platform}</Typography>
                          </Box>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                )}

                {/* Model Search */}
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Search size={20} color="#6b7280" />
                      <TextField
                        fullWidth
                        value={modelSearch}
                        onChange={(e) => setModelSearch(e.target.value)}
                        placeholder="Search models..."
                        variant="outlined"
                        size="small"
                      />
                      <Filter size={20} color="#6b7280" />
                    </Box>
                  </CardContent>
                </Card>

                {/* Model Recommendations */}
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: 2 }}>
                  {filteredRecommendations.map((rec) => (
                    <Card key={rec.model.name}>
                      <CardContent>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {rec.model.name}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              size="small"
                              label={rec.compatibility}
                              sx={{
                                backgroundColor:
                                  rec.compatibility === 'perfect' ? '#00D4AA20' :
                                  rec.compatibility === 'good' ? '#f59e0b20' :
                                  rec.compatibility === 'partial' ? '#f59e0b20' : '#ef444420',
                                color:
                                  rec.compatibility === 'perfect' ? '#00D4AA' :
                                  rec.compatibility === 'good' ? '#f59e0b' :
                                  rec.compatibility === 'partial' ? '#f59e0b' : '#ef4444',
                                fontSize: '0.7rem',
                              }}
                            />
                            
                            {downloadingModels.has(rec.model.name) ? (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Box sx={{ width: 60 }}>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={downloadProgress.get(rec.model.name)?.percentage || 0}
                                    sx={{ 
                                      '& .MuiLinearProgress-bar': { 
                                        backgroundColor: '#00D4AA' 
                                      } 
                                    }}
                                  />
                                </Box>
                                <IconButton
                                  onClick={() => handleCancelDownload(rec.model.name)}
                                  size="small"
                                  sx={{
                                    color: '#ef4444',
                                    '&:hover': { backgroundColor: 'rgba(239, 68, 68, 0.1)' },
                                  }}
                                >
                                  <X size={14} />
                                </IconButton>
                              </Box>
                            ) : (
                              <IconButton
                                onClick={() => handleDownloadModel(rec.model.name)}
                                disabled={rec.compatibility === 'incompatible'}
                                sx={{
                                  color: rec.compatibility === 'incompatible' ? '#6b7280' : '#00D4AA',
                                  '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.05)' },
                                }}
                              >
                                <Download size={16} />
                              </IconButton>
                            )}
                          </Box>
                        </Box>

                        <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2 }}>
                          {rec.model.description || 'No description available'}
                        </Typography>

                        <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                          {rec.reason}
                        </Typography>

                        {/* Download Progress Details */}
                        {downloadingModels.has(rec.model.name) && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" sx={{ color: '#00D4AA', mb: 1 }}>
                              {downloadProgress.get(rec.model.name)?.message || 'Downloading...'}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              {downloadProgress.get(rec.model.name)?.percentage || 0}% complete
                            </Typography>
                          </Box>
                        )}

                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          {(rec.model.tags || []).slice(0, 3).map((tag) => (
                            <Chip
                              key={tag}
                              label={tag}
                              size="small"
                              sx={{
                                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                color: '#a1a1aa',
                                fontSize: '0.7rem',
                              }}
                            />
                          ))}
                        </Box>

                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="caption" sx={{ color: '#6b7280' }}>
                            {((rec.model.size || 0) / (1024 * 1024 * 1024)).toFixed(1)} GB
                          </Typography>
                          <Typography variant="caption" sx={{ color: '#6b7280' }}>
                            {(rec.model.pulls || 0).toLocaleString()} pulls
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </motion.div>
            )}

            {activeTab === 'guardrails' && (
              <motion.div
                key="guardrails"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <GuardrailsConfig 
                  onConfigChange={(config) => {
                    // Handle real-time configuration changes
                    console.log('Guardrails config updated:', config);
                    // TODO: Implement real-time config update to detector system
                  }}
                />
              </motion.div>
            )}

            {activeTab === 'providers' && (
              <motion.div
                key="providers"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ProvidersConfig 
                  onProviderChange={(providers) => {
                    // Handle provider configuration changes
                    console.log('Providers config updated:', providers);
                    // TODO: Implement real-time provider updates
                  }}
                />
              </motion.div>
            )}

            {activeTab === 'analytics' && (
              <motion.div
                key="analytics"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <GuardrailAnalyticsDashboard />
              </motion.div>
            )}

            {activeTab === 'testing' && (
              <motion.div
                key="testing"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <AdvancedTestingPlayground />
              </motion.div>
            )}

            {activeTab === 'hardware' && (
              <motion.div
                key="hardware"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <Typography variant="h4" component="h1">
                    Hardware & Distributed Computing
                  </Typography>
                  
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
                    {/* GPU Acceleration Section */}
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          GPU Acceleration
                        </Typography>
                        <GPUAcceleration />
                      </CardContent>
                    </Card>

                    {/* Distributed Processing Section */}
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Distributed Computing
                        </Typography>
                        <DistributedProcessing />
                      </CardContent>
                    </Card>
                  </Box>
                </Box>
              </motion.div>
            )}

            {activeTab === 'terminal' && (
              <motion.div
                key="terminal"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {/* Header */}
                  <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <Terminal size={24} style={{ color: '#00D4AA' }} />
                        <Typography variant="h5" sx={{ fontWeight: 600, color: '#ffffff' }}>
                          🖥️ System Activity Monitor
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2 }}>
                        Real-time system logs and activity tracking. Monitor requests, responses, and system events.
                      </Typography>
                      
                      {/* Stats */}
                      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                        <Chip
                          label={`📊 ${logs.length} Total Events`}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            color: '#3b82f6',
                            border: '1px solid rgba(59, 130, 246, 0.2)',
                          }}
                        />
                        <Chip
                          label={`✅ ${logs.filter(l => l.level === 'success').length} Success`}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            color: '#00D4AA',
                            border: '1px solid rgba(0, 212, 170, 0.2)',
                          }}
                        />
                        <Chip
                          label={`⚠️ ${logs.filter(l => l.level === 'warn').length} Warnings`}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            color: '#f59e0b',
                            border: '1px solid rgba(245, 158, 11, 0.2)',
                          }}
                        />
                        <Chip
                          label={`❌ ${logs.filter(l => l.level === 'error').length} Errors`}
                          size="small"
                          sx={{
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            border: '1px solid rgba(239, 68, 68, 0.2)',
                          }}
                        />
                      </Box>
                    </CardContent>
                  </Card>

                  {/* Logs Container */}
                  <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                    <CardContent sx={{ p: 0 }}>
                      <Box
                        sx={{
                          height: '600px',
                          overflow: 'auto',
                          fontFamily: 'JetBrains Mono, Monaco, "Fira Code", monospace',
                          fontSize: '0.9rem',
                          backgroundColor: 'rgba(0, 0, 0, 0.3)',
                          position: 'relative',
                          '&::-webkit-scrollbar': {
                            width: '8px',
                          },
                          '&::-webkit-scrollbar-track': {
                            background: 'rgba(255, 255, 255, 0.05)',
                          },
                          '&::-webkit-scrollbar-thumb': {
                            background: 'rgba(255, 255, 255, 0.2)',
                            borderRadius: '4px',
                            '&:hover': {
                              background: 'rgba(255, 255, 255, 0.3)',
                            },
                          },
                        }}
                      >
                        {logs.length === 0 ? (
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center', 
                            height: '100%',
                            flexDirection: 'column',
                            gap: 2
                          }}>
                            <Typography variant="h6" sx={{ color: '#6b7280' }}>
                              🌟 System Ready
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#a1a1aa', textAlign: 'center' }}>
                              No recent activity. System logs will appear here as requests are processed.
                            </Typography>
                          </Box>
                        ) : (
                          <AnimatePresence>
                            {logs.map((log, index) => {
                              const getLogIcon = (level: string, source: string) => {
                                if (level === 'error') return '💥';
                                if (level === 'warn') return '⚠️';
                                if (level === 'success') return '✅';
                                if (source === 'Chat Service') return '💬';
                                if (source === 'Detection Service') return '🛡️';
                                if (source === 'Provider Service') return '🔌';
                                if (source === 'Analytics Service') return '📊';
                                return '📝';
                              };

                              const getLogColor = (level: string) => {
                                switch (level) {
                                  case 'error': return '#ef4444';
                                  case 'warn': return '#f59e0b';
                                  case 'success': return '#00D4AA';
                                  default: return '#ffffff';
                                }
                              };

                              const getSourceColor = (source: string) => {
                                const colors: { [key: string]: string } = {
                                  'Chat Service': '#3b82f6',
                                  'Detection Service': '#8b5cf6',
                                  'Provider Service': '#10b981',
                                  'Analytics Service': '#f59e0b',
                                  'System': '#6b7280',
                                };
                                return colors[source] || '#00D4AA';
                              };

                              return (
                                <motion.div
                                  key={log.id}
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  exit={{ opacity: 0, x: 20 }}
                                  transition={{ duration: 0.3, delay: index * 0.02 }}
                                >
                                  <Box
                                    sx={{
                                      display: 'flex',
                                      alignItems: 'flex-start',
                                      gap: 1.5,
                                      mb: 0.25,
                                      p: 1.5,
                                      borderRadius: 1,
                                      backgroundColor: log.level === 'error' ? 'rgba(239, 68, 68, 0.05)' : 
                                                     log.level === 'warn' ? 'rgba(245, 158, 11, 0.05)' : 
                                                     log.level === 'success' ? 'rgba(0, 212, 170, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                                      border: `1px solid ${
                                        log.level === 'error' ? 'rgba(239, 68, 68, 0.2)' : 
                                        log.level === 'warn' ? 'rgba(245, 158, 11, 0.2)' : 
                                        log.level === 'success' ? 'rgba(0, 212, 170, 0.2)' : 'rgba(255, 255, 255, 0.06)'
                                      }`,
                                      position: 'relative',
                                      '&:hover': {
                                        backgroundColor: log.level === 'error' ? 'rgba(239, 68, 68, 0.1)' : 
                                                       log.level === 'warn' ? 'rgba(245, 158, 11, 0.1)' : 
                                                       log.level === 'success' ? 'rgba(0, 212, 170, 0.1)' : 'rgba(255, 255, 255, 0.04)',
                                      },
                                    }}
                                  >
                                  {/* Time & Icon */}
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: '100px' }}>
                                    <Typography
                                      variant="caption"
                                      sx={{
                                        color: '#6b7280',
                                        fontSize: '0.75rem',
                                        fontWeight: 500,
                                      }}
                                    >
                                      {new Date(log.timestamp || Date.now()).toLocaleTimeString('en-US', { 
                                        hour12: false, 
                                        hour: '2-digit', 
                                        minute: '2-digit', 
                                        second: '2-digit' 
                                      })}
                                    </Typography>
                                    <span style={{ fontSize: '16px' }}>
                                      {getLogIcon(log.level, log.source)}
                                    </span>
                                  </Box>

                                  {/* Source Badge */}
                                  <Box sx={{ minWidth: '120px' }}>
                                    <Chip
                                      label={log.source}
                                      size="small"
                                      sx={{
                                        backgroundColor: `${getSourceColor(log.source)}20`,
                                        color: getSourceColor(log.source),
                                        border: `1px solid ${getSourceColor(log.source)}40`,
                                        fontSize: '0.7rem',
                                        fontWeight: 500,
                                      }}
                                    />
                                  </Box>

                                    {/* Message */}
                                    <Typography
                                      variant="body2"
                                      sx={{
                                        color: getLogColor(log.level),
                                        fontSize: '0.9rem',
                                        lineHeight: 1.4,
                                        flex: 1,
                                        fontWeight: log.level === 'error' ? 600 : 400,
                                      }}
                                    >
                                      {log.message}
                                    </Typography>

                                    {/* Level Badge */}
                                    <Box sx={{ minWidth: '80px', display: 'flex', justifyContent: 'flex-end' }}>
                                      <Chip
                                        label={log.level.toUpperCase()}
                                        size="small"
                                        variant="outlined"
                                        sx={{
                                          color: getLogColor(log.level),
                                          borderColor: getLogColor(log.level),
                                          fontSize: '0.7rem',
                                          fontWeight: 600,
                                          backgroundColor: `${getLogColor(log.level)}10`,
                                        }}
                                      />
                                    </Box>
                                  </Box>
                                </motion.div>
                              );
                            })}
                          </AnimatePresence>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </Box>

        {/* Global styles for animations */}
        <style>
          {`
            @keyframes pulse {
              0%, 100% { opacity: 1; }
              50% { opacity: 0.5; }
            }
          `}
        </style>
      </Box>
    </ThemeProvider>
  );
};

export default App;