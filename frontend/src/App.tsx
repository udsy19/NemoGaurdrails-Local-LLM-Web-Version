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
  Button,
  Divider,
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
import { useOllamaModels } from './hooks/useOllamaModels';
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
import DocsPage from './components/docs/DocsPage';

// Auth components
import { AuthProvider } from './contexts/AuthContext';
import AuthGuard from './components/auth/AuthGuard';

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

const MainApp: React.FC = () => {
  // Core state
  const [message, setMessage] = useState('');
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  // Load active tab from localStorage
  const loadActiveTab = () => {
    try {
      const saved = localStorage.getItem('app_active_tab');
      if (saved && ['chat', 'models', 'terminal', 'guardrails', 'providers', 'analytics', 'testing', 'hardware', 'docs'].includes(saved)) {
        return saved as 'chat' | 'models' | 'terminal' | 'guardrails' | 'providers' | 'analytics' | 'testing' | 'hardware' | 'docs';
      }
    } catch (error) {
      console.error('Failed to load active tab from localStorage:', error);
    }
    return 'chat';
  };
  
  const [activeTab, setActiveTab] = useState<'chat' | 'models' | 'terminal' | 'guardrails' | 'providers' | 'analytics' | 'testing' | 'hardware' | 'docs'>(loadActiveTab);
  const [terminalExpanded, setTerminalExpanded] = useState(false);
  const [modelSearch, setModelSearch] = useState('');
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>([]);
  const [installedModels, setInstalledModels] = useState<OllamaModel[]>([]);
  const [showInstalledOnly, setShowInstalledOnly] = useState(false);
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>([]);
  const [compatibilityFilter, setCompatibilityFilter] = useState<string>('all');
  const [filteredOllamaModels, setFilteredOllamaModels] = useState<import('./services/ollamaModels').OllamaModel[]>([]);
  const [displayedModels, setDisplayedModels] = useState<import('./services/ollamaModels').OllamaModel[]>([]);
  const [modelsPerPage] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [downloadProgress, setDownloadProgress] = useState<Map<string, DownloadProgress>>(new Map());
  const [sessionId] = useState(() => `session_${Date.now()}`);

  // API hooks
  const { isConnected } = useApi();
  const { health } = useSystemHealth();
  const { detectors, selectedDetectors, detectorConfig, toggleDetector } = useDetectors();
  const { messages, isLoading, sendMessage: sendChatMessage, clearHistory } = useChat(sessionId);
  const { providers, enabledProviders, connectedProviders } = useProviders();
  const { 
    models: ollamaModels, 
    topRecommended, 
    isLoading: modelsLoading, 
    error: modelsError,
    refreshModels,
    searchModels: searchOllamaModels 
  } = useOllamaModels();
  
  
  // Load selected provider from localStorage
  const loadSelectedProvider = () => {
    try {
      const saved = localStorage.getItem('selected_provider');
      if (saved) {
        return saved;
      }
    } catch (error) {
      console.error('Failed to load selected provider from localStorage:', error);
    }
    return '';
  };
  
  // Provider selection state
  const [selectedProvider, setSelectedProvider] = useState<string>(loadSelectedProvider);
  
  // Set default provider when providers load and validate current selection
  useEffect(() => {
    if (connectedProviders.length > 0) {
      // Check if current selection is still valid
      const isCurrentProviderValid = selectedProvider && 
        connectedProviders.some(p => p.id === selectedProvider);
      
      if (!isCurrentProviderValid) {
        const newProviderId = connectedProviders[0].id;
        setSelectedProvider(newProviderId);
        // Save to localStorage
        try {
          localStorage.setItem('selected_provider', newProviderId);
        } catch (error) {
          console.error('Failed to save selected provider to localStorage:', error);
        }
        console.log('[DEBUG] Provider selection updated to:', newProviderId);
      }
    } else if (selectedProvider) {
      // Clear selection if no providers available
      setSelectedProvider('');
      // Clear from localStorage
      try {
        localStorage.removeItem('selected_provider');
      } catch (error) {
        console.error('Failed to clear selected provider from localStorage:', error);
      }
      console.log('[DEBUG] No providers available, cleared selection');
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
        
        // Also fetch installed models
        await fetchInstalledModels();
      } catch (error) {
        console.error('Failed to initialize system:', error);
      }
    };

    initializeSystem();
  }, []);

  // Function to fetch installed models
  const fetchInstalledModels = async () => {
    try {
      const installed = await ollamaService.getLocalModels();
      setInstalledModels(installed);
    } catch (error) {
      console.error('Failed to fetch installed models:', error);
    }
  };

  // Handle model deletion
  const handleDeleteModel = async (modelName: string) => {
    try {
      await ollamaService.deleteModel(modelName);
      toast.success(`Model ${modelName} removed successfully`);
      // Refresh the installed models list
      await fetchInstalledModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
      toast.error(`Failed to remove model ${modelName}`);
    }
  };

  // Handle message send
  const handleSendMessage = async () => {
    if (!message.trim() || isLoading) return;
    
    const messageText = message;
    setMessage('');
    
    try {
      // Filter detector config to only include enabled detectors with supported parameters
      const filteredConfig: any = {};
      Object.entries(detectorConfig).forEach(([detectorName, config]: [string, any]) => {
        if (config.enabled) {
          filteredConfig[detectorName] = {
            enabled: config.enabled,
            threshold: config.threshold
          };
          // Add PII-specific parameters if it's PII detector
          if (detectorName === 'PIIDetector' && config.sensitivity) {
            filteredConfig[detectorName].sensitivity = config.sensitivity;
          }
        }
      });
      
      await sendChatMessage(messageText, filteredConfig, selectedProvider);
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
          // Refresh installed models list when download completes
          fetchInstalledModels();
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

  // Filter Ollama models based on search, capabilities, and compatibility
  useEffect(() => {
    console.log(`🔍 Filtering models: ${ollamaModels.length} total, search: "${modelSearch}", capabilities: [${selectedCapabilities.join(',')}], compatibility: ${compatibilityFilter}`);
    
    let filtered = ollamaModels;

    // Apply search filter
    if (modelSearch) {
      filtered = filtered.filter(model =>
        model.name.toLowerCase().includes(modelSearch.toLowerCase()) ||
        model.description.toLowerCase().includes(modelSearch.toLowerCase()) ||
        model.capabilities.some(cap => cap.toLowerCase().includes(modelSearch.toLowerCase()))
      );
      console.log(`🔍 After search filter: ${filtered.length} models`);
    }

    // Apply capability filter
    if (selectedCapabilities.length > 0) {
      filtered = filtered.filter(model =>
        selectedCapabilities.every(cap => model.capabilities.includes(cap))
      );
      console.log(`🔍 After capability filter: ${filtered.length} models`);
    }

    // Apply compatibility filter
    if (compatibilityFilter !== 'all') {
      filtered = filtered.filter(model => model.compatibility_label === compatibilityFilter);
      console.log(`🔍 After compatibility filter: ${filtered.length} models`);
    }

    // Sort by compatibility score and popularity
    filtered.sort((a, b) => {
      // Primary sort: compatibility score
      if (b.compatibility_score !== a.compatibility_score) {
        return b.compatibility_score - a.compatibility_score;
      }
      // Secondary sort: pull count (convert string like "1.5M" to number)
      const aPulls = parseFloat(a.pull_count.replace(/[KM]/g, '')) * (a.pull_count.includes('M') ? 1000000 : a.pull_count.includes('K') ? 1000 : 1);
      const bPulls = parseFloat(b.pull_count.replace(/[KM]/g, '')) * (b.pull_count.includes('M') ? 1000000 : b.pull_count.includes('K') ? 1000 : 1);
      return bPulls - aPulls;
    });

    console.log(`✓ Final filtered models: ${filtered.length}`);
    setFilteredOllamaModels(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  }, [ollamaModels, modelSearch, selectedCapabilities, compatibilityFilter]);

  // Update displayed models based on pagination
  useEffect(() => {
    const startIndex = (currentPage - 1) * modelsPerPage;
    const endIndex = startIndex + modelsPerPage;
    const paginatedModels = filteredOllamaModels.slice(startIndex, endIndex);
    
    console.log(`📄 Page ${currentPage}: showing models ${startIndex + 1}-${Math.min(endIndex, filteredOllamaModels.length)} of ${filteredOllamaModels.length}`);
    setDisplayedModels(paginatedModels);
  }, [filteredOllamaModels, currentPage, modelsPerPage]);

  // Calculate pagination info
  const totalPages = Math.ceil(filteredOllamaModels.length / modelsPerPage);
  const hasNextPage = currentPage < totalPages;
  const hasPrevPage = currentPage > 1;

  // Filter recommendations based on search (legacy support)
  const filteredRecommendations = recommendations.filter(rec =>
    rec.model.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  // Filter installed models based on search  
  const filteredInstalledModels = installedModels.filter(model =>
    model.name.toLowerCase().includes(modelSearch.toLowerCase())
  );

  // Get status color
  const getStatusColor = () => {
    if (!isConnected) return '#ef4444';
    if (health?.status === 'healthy') return '#00D4AA';
    return '#f59e0b';
  };

  return (
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
          {(['chat', 'testing', 'analytics', 'guardrails', 'providers', 'hardware', 'models', 'docs', 'terminal'] as const).map((tab) => (
            <Box
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                // Save to localStorage
                try {
                  localStorage.setItem('app_active_tab', tab);
                } catch (error) {
                  console.error('Failed to save active tab to localStorage:', error);
                }
              }}
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
            maxHeight: '250px',
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
              style={{ minHeight: '500px', maxHeight: '85vh', position: 'relative' }}
            >
              <ModernChatInterface
                messages={messages}
                onSendMessage={(msg, provider, detectorConfig) => {
                  setMessage('');
                  // Only use detectors that are explicitly enabled in detectorConfig
                  // Don't auto-enable all selectedDetectors - this was causing blocking of simple messages
                  const config = detectorConfig || {};
                  
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
                onProviderChange={(providerId) => {
                  setSelectedProvider(providerId);
                  // Save to localStorage
                  try {
                    localStorage.setItem('selected_provider', providerId);
                  } catch (error) {
                    console.error('Failed to save selected provider to localStorage:', error);
                  }
                }}
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
              {/* Header */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                  Model Explorer
                </Typography>
                <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 2 }}>
                  Discover and download AI models with intelligent compatibility scoring for your system
                </Typography>
                
                {modelsError && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    {modelsError} - Showing cached results.
                  </Alert>
                )}

                <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
                  <Chip 
                    label={`${ollamaModels.length} Total Models`} 
                    variant="outlined"
                    sx={{ color: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.2)' }} 
                  />
                  <Chip 
                    label={`${filteredOllamaModels.length} Filtered`} 
                    variant="outlined"
                    sx={{ color: '#f59e0b', borderColor: '#f59e0b' }} 
                  />
                  <Chip 
                    label={`${topRecommended.length} Recommended`} 
                    variant="outlined"
                    sx={{ color: '#00D4AA', borderColor: '#00D4AA' }} 
                  />
                  <Chip 
                    label={`Page ${currentPage} of ${totalPages}`} 
                    variant="outlined"
                    sx={{ color: '#6366f1', borderColor: '#6366f1' }} 
                  />
                </Box>
              </Box>

              {/* Search and Filters */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2, fontWeight: 500 }}>
                    Search & Filters
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                    <Search size={20} color="#6b7280" />
                    <TextField
                      fullWidth
                      value={modelSearch}
                      onChange={(e) => setModelSearch(e.target.value)}
                      placeholder="Search models..."
                      variant="outlined"
                      size="small"
                      sx={{ flex: 1 }}
                    />
                    <Button
                      variant="outlined"
                      onClick={refreshModels}
                      disabled={modelsLoading}
                      size="small"
                      startIcon={<Download size={16} />}
                    >
                      {modelsLoading ? 'Loading...' : 'Refresh'}
                    </Button>
                  </Box>

                  <Divider sx={{ mb: 2 }} />

                  {/* Capability Filters */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 500 }}>
                      Capabilities
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {['tools', 'vision', 'thinking', 'embedding'].map((capability) => (
                        <Chip
                          key={capability}
                          label={capability}
                          size="small"
                          variant={selectedCapabilities.includes(capability) ? 'filled' : 'outlined'}
                          onClick={() => {
                            setSelectedCapabilities(prev =>
                              prev.includes(capability)
                                ? prev.filter(c => c !== capability)
                                : [...prev, capability]
                            );
                          }}
                          sx={{
                            backgroundColor: selectedCapabilities.includes(capability) ? '#00D4AA' : 'transparent',
                            color: selectedCapabilities.includes(capability) ? '#000000' : '#ffffff',
                            borderColor: selectedCapabilities.includes(capability) ? '#00D4AA' : 'rgba(255, 255, 255, 0.2)',
                            '&:hover': {
                              backgroundColor: selectedCapabilities.includes(capability) ? '#00B894' : 'rgba(0, 212, 170, 0.1)',
                            },
                          }}
                        />
                      ))}
                    </Box>
                  </Box>

                  {/* Compatibility Filter */}
                  <Box>
                    <Typography variant="body2" sx={{ color: '#6b7280', mb: 1, fontWeight: 500 }}>
                      Compatibility Level
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {['all', 'Excellent', 'Good', 'Fair', 'Limited'].map((level) => (
                        <Chip
                          key={level}
                          label={level === 'all' ? 'All Levels' : level}
                          size="small"
                          variant={compatibilityFilter === level ? 'filled' : 'outlined'}
                          onClick={() => setCompatibilityFilter(level)}
                          sx={{
                            backgroundColor: compatibilityFilter === level ? 
                              (level === 'Excellent' ? '#00D4AA' :
                               level === 'Good' ? '#f59e0b' :
                               level === 'Fair' ? '#6b7280' :
                               level === 'Limited' ? '#ef4444' : '#00D4AA') : 'transparent',
                            color: compatibilityFilter === level ? '#000000' : '#ffffff',
                            borderColor: compatibilityFilter === level ? 'transparent' : 'rgba(255, 255, 255, 0.2)',
                            '&:hover': {
                              backgroundColor: compatibilityFilter === level ? 
                                (level === 'Excellent' ? '#00B894' :
                                 level === 'Good' ? '#d97706' :
                                 level === 'Fair' ? '#4b5563' :
                                 level === 'Limited' ? '#dc2626' : '#00B894') : 'rgba(255, 255, 255, 0.05)',
                            },
                          }}
                        />
                      ))}
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              {/* Top Recommendations */}
              {!modelSearch && selectedCapabilities.length === 0 && compatibilityFilter === 'all' && topRecommended.length > 0 && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <CheckCircle size={20} color="#00D4AA" />
                      <Typography variant="h6" sx={{ fontWeight: 500 }}>
                        Recommended for Your System
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 3 }}>
                      These models offer the best compatibility with your hardware configuration
                    </Typography>
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 2 }}>
                      {topRecommended.slice(0, 6).map((model) => (
                        <Card key={model.name} sx={{ border: '1px solid rgba(0, 212, 170, 0.3)', backgroundColor: 'rgba(0, 212, 170, 0.02)' }}>
                          <CardContent sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                {model.name}
                              </Typography>
                              <Chip
                                label={`${model.compatibility_score}%`}
                                size="small"
                                sx={{ backgroundColor: '#00D4AA', color: '#000000', fontWeight: 600 }}
                              />
                            </Box>
                            <Typography variant="caption" sx={{ color: '#6b7280', display: 'block', mb: 1 }}>
                              {model.estimated_memory_usage} • {model.performance_tier}
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#a1a1aa', fontSize: '0.85rem' }}>
                              {model.description.substring(0, 100)}...
                            </Typography>
                          </CardContent>
                        </Card>
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Models Grid */}
              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: 2 }}>
                {modelsLoading ? (
                  // Loading skeleton
                  [...Array(6)].map((_, i) => (
                    <Card key={i}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                          <Box sx={{ height: '24px', width: '150px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 1 }} />
                          <Box sx={{ height: '20px', width: '80px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 1 }} />
                        </Box>
                        <Box sx={{ height: '40px', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 1, mb: 2 }} />
                        <Box sx={{ height: '20px', width: '60%', backgroundColor: 'rgba(255, 255, 255, 0.1)', borderRadius: 1 }} />
                      </CardContent>
                    </Card>
                  ))
                ) : filteredOllamaModels.length === 0 ? (
                  <Card sx={{ gridColumn: '1 / -1' }}>
                    <CardContent sx={{ textAlign: 'center', py: 4 }}>
                      <Search size={48} color="#6b7280" />
                      <Typography variant="h6" sx={{ color: '#6b7280', mb: 1, mt: 2 }}>
                        No models found
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                        Try adjusting your search terms or filters
                      </Typography>
                    </CardContent>
                  </Card>
                ) : (
                  displayedModels.map((model) => (
                    <Card key={model.name}>
                      <CardContent>
                        {/* Model Header */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Box sx={{ flex: 1, mr: 2 }}>
                            <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                              {model.name}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <Chip
                                label={`${model.compatibility_score}%`}
                                size="small"
                                sx={{
                                  backgroundColor: model.compatibility_label === 'Excellent' ? '#00D4AA' : 
                                                model.compatibility_label === 'Good' ? '#f59e0b' :
                                                model.compatibility_label === 'Fair' ? '#6b7280' : '#ef4444',
                                  color: '#000000',
                                  fontWeight: 600,
                                  fontSize: '0.75rem',
                                }}
                              />
                              <Typography variant="caption" sx={{ color: '#6b7280' }}>
                                {model.performance_tier}
                              </Typography>
                            </Box>
                          </Box>
                          <Typography variant="caption" sx={{ color: '#00D4AA', fontWeight: 500 }}>
                            {model.pull_count} pulls
                          </Typography>
                        </Box>

                        {/* Description */}
                        <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2, lineHeight: 1.4 }}>
                          {model.description}
                        </Typography>

                        {/* Model Details */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <HardDrive size={14} color="#6b7280" />
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              {model.estimated_memory_usage}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Cpu size={14} color="#6b7280" />
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              {model.sizes.join(', ')}
                            </Typography>
                          </Box>
                          <Typography variant="caption" sx={{ color: '#6b7280' }}>
                            {model.tag_count} variants
                          </Typography>
                        </Box>

                        {/* Capabilities & Recommended Use */}
                        <Box sx={{ mb: 2 }}>
                          {model.capabilities.length > 0 && (
                            <Box sx={{ mb: 1 }}>
                              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                {model.capabilities.map((capability) => (
                                  <Chip
                                    key={capability}
                                    label={capability}
                                    size="small"
                                    variant="outlined"
                                    sx={{
                                      borderColor: 'rgba(255, 255, 255, 0.2)',
                                      color: '#ffffff',
                                      fontSize: '0.7rem',
                                      height: '24px',
                                    }}
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                          <Typography variant="caption" sx={{ color: '#00D4AA' }}>
                            Best for: {model.recommended_for.join(', ')}
                          </Typography>
                        </Box>

                        {/* Download Progress */}
                        {downloadProgress.has(model.name) && (
                          <Box sx={{ mb: 2 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={downloadProgress.get(model.name)?.percentage || 0}
                              sx={{ mb: 1, backgroundColor: 'rgba(255, 255, 255, 0.1)' }}
                            />
                            <Typography variant="caption" sx={{ color: '#6b7280' }}>
                              {downloadProgress.get(model.name)?.status}: {downloadProgress.get(model.name)?.percentage.toFixed(1)}%
                            </Typography>
                          </Box>
                        )}

                        <Divider sx={{ my: 2 }} />

                        {/* Action Buttons */}
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => window.open(`https://ollama.com${model.library_path}`, '_blank')}
                          >
                            Details
                          </Button>
                          {downloadingModels.has(model.name) ? (
                            <Button
                              variant="contained"
                              color="error"
                              size="small"
                              onClick={() => handleCancelDownload(model.name)}
                            >
                              Cancel
                            </Button>
                          ) : (
                            <Button
                              variant="contained"
                              size="small"
                              onClick={() => handleDownloadModel(model.name)}
                              startIcon={<Download size={16} />}
                              disabled={model.compatibility_score < 40}
                              sx={{
                                backgroundColor: model.compatibility_score >= 40 ? '#00D4AA' : 'rgba(255, 255, 255, 0.1)',
                                color: model.compatibility_score >= 40 ? '#000000' : '#6b7280',
                                '&:hover': { 
                                  backgroundColor: model.compatibility_score >= 40 ? '#00B894' : 'rgba(255, 255, 255, 0.1)' 
                                },
                              }}
                            >
                              {model.compatibility_score >= 40 ? 'Download' : 'Incompatible'}
                            </Button>
                          )}
                        </Box>
                      </CardContent>
                    </Card>
                  ))
                )}
              </Box>

              {/* Pagination Controls */}
              {filteredOllamaModels.length > modelsPerPage && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mt: 4, gap: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={!hasPrevPage}
                    sx={{ color: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.2)' }}
                  >
                    Previous
                  </Button>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {[...Array(Math.min(5, totalPages))].map((_, i) => {
                      const pageNum = Math.max(1, currentPage - 2) + i;
                      if (pageNum > totalPages) return null;
                      
                      return (
                        <Button
                          key={pageNum}
                          variant={pageNum === currentPage ? "contained" : "outlined"}
                          onClick={() => setCurrentPage(pageNum)}
                          sx={{
                            minWidth: '40px',
                            color: pageNum === currentPage ? '#000000' : '#ffffff',
                            backgroundColor: pageNum === currentPage ? '#00D4AA' : 'transparent',
                            borderColor: pageNum === currentPage ? '#00D4AA' : 'rgba(255, 255, 255, 0.2)',
                            '&:hover': {
                              backgroundColor: pageNum === currentPage ? '#00B894' : 'rgba(0, 212, 170, 0.1)',
                            },
                          }}
                        >
                          {pageNum}
                        </Button>
                      );
                    })}
                  </Box>
                  
                  <Button
                    variant="outlined"
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={!hasNextPage}
                    sx={{ color: '#ffffff', borderColor: 'rgba(255, 255, 255, 0.2)' }}
                  >
                    Next
                  </Button>
                </Box>
              )}

              {/* Load All Button */}
              {filteredOllamaModels.length > modelsPerPage && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setDisplayedModels(filteredOllamaModels);
                      setCurrentPage(1);
                    }}
                    sx={{ 
                      color: '#00D4AA', 
                      borderColor: '#00D4AA',
                      '&:hover': { 
                        backgroundColor: 'rgba(0, 212, 170, 0.1)',
                        borderColor: '#00B894' 
                      }
                    }}
                  >
                    Show All {filteredOllamaModels.length} Models
                  </Button>
                </Box>
              )}
            </motion.div>
          )}

          {/* Other tabs content */}
          {activeTab === 'testing' && <AdvancedTestingPlayground />}

          {activeTab === 'analytics' && <GuardrailAnalyticsDashboard />}
          {activeTab === 'guardrails' && <GuardrailsConfig />}
          {activeTab === 'providers' && <ProvidersConfig />}
          {activeTab === 'hardware' && <GPUAcceleration />}
          {activeTab === 'docs' && <DocsPage />}
        </AnimatePresence>
      </Box>
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={minimalTheme}>
      <CssBaseline />
      <Toaster position="top-center" />
      <AuthProvider>
        <AuthGuard>
          <MainApp />
        </AuthGuard>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;