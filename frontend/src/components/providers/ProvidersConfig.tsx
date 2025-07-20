import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Switch,
  Alert,
  Divider,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Cloud,
  Brain,
  Server,
  Wifi,
  WifiOff,
  Settings,
  Key,
  TestTube,
  CheckCircle,
  XCircle,
  RefreshCw,
  Info,
  AlertTriangle,
  Shield,
  Zap,
  Globe,
  Play,
  Square,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { useProviders } from '../../hooks/useProviders';
import PortConflictDialog from './PortConflictDialog';
import LoadingSpinner from '../common/LoadingSpinner';

interface ProvidersConfigProps {
  onProviderChange?: (providers: any[]) => void;
}

const ProvidersConfig: React.FC<ProvidersConfigProps> = ({ onProviderChange }) => {
  const {
    providers,
    stats,
    loading,
    error,
    testConnection,
    updateProviderConfig,
    testAllConnections,
    enableProvider,
    disableProvider,
    enableProviderWithPortSelection,
  } = useProviders();

  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [portConflictDialog, setPortConflictDialog] = useState<{
    open: boolean;
    provider: any;
    conflictData: any;
  }>({
    open: false,
    provider: null,
    conflictData: null,
  });
  const initializedRef = useRef(false);

  // Initialize local state when providers load (only once)
  useEffect(() => {
    if (Object.keys(providers).length > 0 && !initializedRef.current) {
      const keys: Record<string, string> = {};
      const models: Record<string, string> = {};
      
      Object.values(providers).forEach(provider => {
        keys[provider.id] = provider.api_key || '';
        models[provider.id] = provider.selected_model || '';
      });
      
      setApiKeys(keys);
      setSelectedModels(models);
      initializedRef.current = true;
    }
  }, [providers]);

  // Notify parent component of provider changes
  useEffect(() => {
    if (onProviderChange && Object.keys(providers).length > 0) {
      onProviderChange(Object.values(providers));
    }
  }, [providers, onProviderChange]);

  const handleProviderToggle = async (providerId: string, enabled: boolean) => {
    if (enabled) {
      // Enable provider with port conflict detection
      const result = await enableProvider(providerId);
      if (result.conflict) {
        // Show port conflict dialog
        const provider = providers[providerId as keyof typeof providers];
        if (provider) {
          setPortConflictDialog({
            open: true,
            provider,
            conflictData: result.data,
          });
        }
      }
    } else {
      // Disable provider
      await disableProvider(providerId);
    }
  };

  const handleForceEnable = async () => {
    if (portConflictDialog.provider) {
      const result = await enableProvider(portConflictDialog.provider.id, true);
      if (result.success) {
        setPortConflictDialog({ open: false, provider: null, conflictData: null });
      }
    }
  };

  const handleUseNextPort = async () => {
    if (portConflictDialog.provider) {
      const result = await enableProviderWithPortSelection(portConflictDialog.provider.id, true);
      if (result.success) {
        setPortConflictDialog({ open: false, provider: null, conflictData: null });
      }
    }
  };

  const handleClosePortConflictDialog = () => {
    setPortConflictDialog({ open: false, provider: null, conflictData: null });
  };

  const handleApiKeyChange = (providerId: string, apiKey: string) => {
    console.log('API Key change:', providerId, apiKey); // Debug log
    setApiKeys(prev => ({ ...prev, [providerId]: apiKey }));
  };

  const handleApiKeyBlur = async (providerId: string) => {
    const apiKey = apiKeys[providerId];
    await updateProviderConfig(providerId, { api_key: apiKey });
  };

  const handleModelChange = async (providerId: string, modelId: string) => {
    setSelectedModels(prev => ({ ...prev, [providerId]: modelId }));
    await updateProviderConfig(providerId, { selected_model: modelId });
  };

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case 'openai': return <Brain size={20} />;
      case 'anthropic': return <Cloud size={20} />;
      case 'gemini': return <Globe size={20} />;
      case 'ollama': return <Server size={20} />;
      default: return <Settings size={20} />;
    }
  };

  const getProviderColor = (providerId: string) => {
    switch (providerId) {
      case 'openai': return '#00A67E';
      case 'anthropic': return '#D97706';
      case 'gemini': return '#4285F4';
      case 'ollama': return '#8B5CF6';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <LoadingSpinner 
        message="Loading providers..." 
        size="large" 
        variant="linear" 
      />
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load providers: {error}
        </Alert>
      </Box>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle size={16} style={{ color: '#10b981' }} />;
      case 'testing':
        return <RefreshCw size={16} style={{ color: '#f59e0b' }} className="animate-spin" />;
      case 'error':
        return <XCircle size={16} style={{ color: '#ef4444' }} />;
      default:
        return <WifiOff size={16} style={{ color: '#6b7280' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return '#10b981';
      case 'testing': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected': return 'Connected';
      case 'testing': return 'Testing...';
      case 'error': return 'Error';
      default: return 'Disconnected';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Settings size={28} style={{ color: '#00D4AA' }} />
            <Typography variant="h4" sx={{ fontWeight: 600, color: '#ffffff' }}>
              Provider Configuration
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 2 }}>
            Configure and manage AI model providers with port-based traffic routing and guardrail protection.
          </Typography>
          
          <Alert 
            severity="info" 
            icon={<Info size={16} />}
            sx={{ 
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              '& .MuiAlert-icon': { color: '#3b82f6' },
              mb: 2
            }}
          >
            All traffic flows through dedicated ports with guardrail protection. Each provider runs on a separate port for precise traffic management.
          </Alert>

          <Alert 
            severity="warning" 
            icon={<AlertTriangle size={16} />}
            sx={{ 
              backgroundColor: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              '& .MuiAlert-icon': { color: '#f59e0b' }
            }}
          >
            <Typography variant="body2">
              <strong>Ollama Users:</strong> Port 8895 routes through guardrails (RECOMMENDED). 
              Direct Ollama port 11434 BYPASSES all safety checks.
            </Typography>
          </Alert>
        </Box>

        {/* Traffic Flow Diagram */}
        <Card sx={{ mb: 4, backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#ffffff', mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Shield size={20} />
              Traffic Flow Architecture
            </Typography>
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2, 
              flexWrap: 'wrap',
              p: 2,
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              borderRadius: '8px'
            }}>
              <Chip label="User Request" sx={{ backgroundColor: '#3b82f6', color: '#ffffff' }} />
              <Typography sx={{ color: '#6b7280' }}>→</Typography>
              <Chip label="Provider Port" sx={{ backgroundColor: '#10b981', color: '#ffffff' }} />
              <Typography sx={{ color: '#6b7280' }}>→</Typography>
              <Chip label="Guardrails" sx={{ backgroundColor: '#f59e0b', color: '#ffffff' }} />
              <Typography sx={{ color: '#6b7280' }}>→</Typography>
              <Chip label="AI Service" sx={{ backgroundColor: '#8b5cf6', color: '#ffffff' }} />
              <Typography sx={{ color: '#6b7280' }}>→</Typography>
              <Chip label="Safe Response" sx={{ backgroundColor: '#00D4AA', color: '#ffffff' }} />
            </Box>
          </CardContent>
        </Card>

        {/* Provider Configuration */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' },
          gap: 3 
        }}>
          {Object.values(providers).map((provider, index) => {
            const providerColor = getProviderColor(provider.id);
            const providerIcon = getProviderIcon(provider.id);
            
            return (
              <motion.div
                key={provider.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                  <Card 
                    sx={{ 
                      backgroundColor: provider.enabled 
                        ? 'rgba(255, 255, 255, 0.02)' 
                        : 'rgba(255, 255, 255, 0.01)',
                      border: provider.enabled 
                        ? `1px solid ${providerColor}40` 
                        : '1px solid rgba(255, 255, 255, 0.06)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.04)',
                        transform: 'translateY(-2px)',
                      },
                    }}
                  >
                    <CardContent sx={{ p: 3 }}>
                      {/* Provider Header */}
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Box
                            sx={{
                              p: 1.5,
                              borderRadius: '12px',
                              backgroundColor: `${providerColor}20`,
                              color: providerColor,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            {providerIcon}
                          </Box>
                          <Box>
                            <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                              {provider.display_name}
                            </Typography>
                            <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                              Port: {provider.port}
                            </Typography>
                          </Box>
                        </Box>
                        <Switch
                          checked={provider.enabled}
                          onChange={(e) => handleProviderToggle(provider.id, e.target.checked)}
                          sx={{
                            '& .MuiSwitch-switchBase.Mui-checked': {
                              color: providerColor,
                            },
                            '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                              backgroundColor: providerColor,
                            },
                          }}
                        />
                      </Box>

                      <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 3 }}>
                        {provider.description}
                      </Typography>

                      {/* Connection Status */}
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                        {getStatusIcon(provider.status)}
                        <Typography variant="body2" sx={{ color: getStatusColor(provider.status), fontWeight: 500 }}>
                          {getStatusText(provider.status)}
                        </Typography>
                        {provider.last_tested && (
                          <Typography variant="caption" sx={{ color: '#6b7280' }}>
                            • Last tested: {new Date(provider.last_tested).toLocaleTimeString()}
                          </Typography>
                        )}
                      </Box>

                      {provider.error_message && (
                        <Alert severity="error" sx={{ mb: 3, fontSize: '0.8rem' }}>
                          {provider.error_message}
                        </Alert>
                      )}

                      {/* Provider Configuration */}
                      <AnimatePresence>
                        {provider.enabled && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                          >
                            <Divider sx={{ mb: 3, borderColor: 'rgba(255, 255, 255, 0.06)' }} />
                            
                            {/* API Key */}
                            {provider.requires_api_key && (
                              <Box sx={{ mb: 3 }}>
                                <TextField
                                  fullWidth
                                  label="API Key"
                                  type="password"
                                  value={apiKeys[provider.id] ?? ''}
                                  onChange={(e) => {
                                    console.log('TextField onChange triggered:', provider.id, e.target.value);
                                    handleApiKeyChange(provider.id, e.target.value);
                                  }}
                                  onBlur={() => handleApiKeyBlur(provider.id)}
                                  placeholder={`Enter your ${provider.display_name} API key`}
                                  size="small"
                                  autoComplete="new-password"
                                  disabled={false}
                                  InputProps={{
                                    startAdornment: <Key size={16} style={{ marginRight: 8, color: '#6b7280' }} />,
                                    readOnly: false,
                                  }}
                                  sx={{
                                    '& .MuiOutlinedInput-root': {
                                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                      color: '#ffffff',
                                      '& input': {
                                        color: '#ffffff !important',
                                        WebkitTextFillColor: '#ffffff !important',
                                      },
                                      '& fieldset': {
                                        borderColor: 'rgba(255, 255, 255, 0.23)',
                                      },
                                      '&:hover .MuiOutlinedInput-notchedOutline': {
                                        borderColor: providerColor,
                                      },
                                      '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                                        borderColor: providerColor,
                                      },
                                    },
                                    '& .MuiInputLabel-root': {
                                      color: '#a1a1aa',
                                      '&.Mui-focused': {
                                        color: providerColor,
                                      },
                                    },
                                  }}
                                />
                              </Box>
                            )}

                            {/* Model Selection */}
                            <Box sx={{ mb: 3 }}>
                              <FormControl fullWidth size="small">
                                <InputLabel>Model</InputLabel>
                                <Select
                                  value={selectedModels[provider.id] || ''}
                                  label="Model"
                                  onChange={(e) => handleModelChange(provider.id, e.target.value)}
                                  sx={{
                                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                                    '&:hover .MuiOutlinedInput-notchedOutline': {
                                      borderColor: providerColor,
                                    },
                                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                                      borderColor: providerColor,
                                    },
                                  }}
                                >
                                  {provider.models.map((model) => (
                                    <MenuItem key={model.id} value={model.id}>
                                      <Box>
                                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                          {model.name}
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: '#6b7280' }}>
                                          {model.description} • {model.context_length.toLocaleString()} tokens
                                        </Typography>
                                      </Box>
                                    </MenuItem>
                                  ))}
                                </Select>
                              </FormControl>
                            </Box>

                            {/* Test Connection */}
                            <Box sx={{ display: 'flex', gap: 2 }}>
                              <Button
                                onClick={() => testConnection(provider.id)}
                                disabled={provider.status === 'testing' || (provider.requires_api_key && !apiKeys[provider.id])}
                                startIcon={<TestTube size={16} />}
                                variant="outlined"
                                sx={{
                                  borderColor: providerColor,
                                  color: providerColor,
                                  '&:hover': {
                                    backgroundColor: `${providerColor}20`,
                                    borderColor: providerColor,
                                  },
                                }}
                              >
                                Test Connection
                              </Button>
                              {provider.status === 'testing' && (
                                <LinearProgress 
                                  sx={{ 
                                    flexGrow: 1, 
                                    alignSelf: 'center',
                                    '& .MuiLinearProgress-bar': {
                                      backgroundColor: providerColor,
                                    },
                                  }} 
                                />
                              )}
                            </Box>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </CardContent>
                  </Card>
              </motion.div>
            );
          })}
        </Box>

        {/* Active Providers Summary */}
        <Box sx={{ mt: 4 }}>
          <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ color: '#ffffff' }}>
                  Active Providers Summary
                </Typography>
                {stats && (
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip 
                      label={`${stats.connected_providers}/${stats.total_providers} Connected`}
                      size="small"
                      sx={{ backgroundColor: '#10b98120', color: '#10b981' }}
                    />
                    <Button
                      onClick={testAllConnections}
                      size="small"
                      startIcon={<RefreshCw size={16} />}
                      sx={{ color: '#00D4AA' }}
                    >
                      Test All
                    </Button>
                  </Box>
                )}
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.values(providers)
                  .filter(p => p.enabled && p.status === 'connected')
                  .map(provider => {
                    const providerColor = getProviderColor(provider.id);
                    return (
                      <Chip
                        key={provider.id}
                        label={`${provider.display_name}:${provider.port} (${provider.selected_model})`}
                        size="small"
                        sx={{
                          backgroundColor: `${providerColor}20`,
                          color: providerColor,
                          border: `1px solid ${providerColor}40`,
                        }}
                      />
                    );
                  })}
                {Object.values(providers).filter(p => p.enabled && p.status === 'connected').length === 0 && (
                  <Typography variant="body2" sx={{ color: '#a1a1aa', fontStyle: 'italic' }}>
                    No providers connected
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Port Conflict Dialog */}
      <PortConflictDialog
        open={portConflictDialog.open}
        onClose={handleClosePortConflictDialog}
        provider={portConflictDialog.provider}
        conflictData={portConflictDialog.conflictData}
        onForceEnable={handleForceEnable}
        onUseNextPort={handleUseNextPort}
      />
    </motion.div>
  );
};

export default ProvidersConfig;