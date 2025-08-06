import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Fab,
  Collapse,
  Alert,
  Tooltip,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  ButtonGroup,
  Button,
  Stack,
  Zoom,
} from '@mui/material';
import LoadingSpinner from '../common/LoadingSpinner';
import {
  Send as SendIcon,
  Security as SecurityIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  Warning as WarningIcon,
  Block as BlockIcon,
  CheckCircle as CheckIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Clear as ClearIcon,
  KeyboardArrowDown as ScrollDownIcon,
  Settings as SettingsIcon,
  Shield as ShieldIcon,
  Memory as MemoryIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage, DetectorConfig } from '../../types';
import { useProcessingStages } from '../../hooks/useRealTime';

interface ModernChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, selectedProvider?: string, detectorConfig?: DetectorConfig) => void;
  isLoading: boolean;
  disabled?: boolean;
  detectorConfig: DetectorConfig;
  onDetectorConfigChange: (config: DetectorConfig) => void;
  onClearHistory: () => void;
  availableProviders?: Array<{id: string, display_name: string, enabled: boolean, status: string}>;
  selectedProvider?: string;
  onProviderChange?: (providerId: string) => void;
  onNavigateToProviders?: () => void;
  onNavigateToGuardrails?: () => void;
}

const ModernChatInterface: React.FC<ModernChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  disabled,
  detectorConfig,
  onDetectorConfigChange,
  onClearHistory,
  availableProviders = [],
  selectedProvider,
  onProviderChange,
  onNavigateToProviders,
  onNavigateToGuardrails,
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [expandedMessage, setExpandedMessage] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { currentStage } = useProcessingStages();

  const connectedProviders = availableProviders; // Already filtered to connected providers
  const hasConnectedProviders = connectedProviders.length > 0;
  

  // Handle scroll detection
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setShowScrollButton(!isAtBottom);
      setAutoScroll(isAtBottom);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);

  const handleSendMessage = () => {
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage.trim(), selectedProvider, detectorConfig);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleDetector = (detector: string) => {
    const newConfig = { ...detectorConfig };
    if (newConfig[detector]) {
      newConfig[detector] = { ...newConfig[detector], enabled: !newConfig[detector].enabled };
    } else {
      newConfig[detector] = { enabled: true };
    }
    onDetectorConfigChange(newConfig);
  };

  const getDetectorIcon = (detector: string) => {
    const icons: { [key: string]: React.ReactElement } = {
      toxicity: <WarningIcon />,
      pii: <ShieldIcon />,
      prompt_injection: <SecurityIcon />,
      hate_speech: <BlockIcon />,
      bias: <PsychologyIcon />,
      privacy: <MemoryIcon />,
    };
    return icons[detector] || <SecurityIcon />;
  };

  const getProviderIcon = (providerId: string) => {
    const icons: { [key: string]: string } = {
      openai: '🤖',
      anthropic: '🧠',
      gemini: '✨',
      ollama: '🦙',
    };
    return icons[providerId] || '🤖';
  };

  const formatDetectionResult = (result: any) => {
    if (!result) return null;
    
    return Object.entries(result).map(([detector, data]: [string, any]) => (
      <Box key={detector} sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
          {getDetectorIcon(detector)}
          <Typography variant="body2" sx={{ ml: 1, fontWeight: 'medium', color: '#ffffff' }}>
            {detector.replace('_', ' ').toUpperCase()}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Chip
            size="small"
            label={data.blocked ? 'BLOCKED' : 'ALLOWED'}
            sx={{
              backgroundColor: data.blocked ? '#ef444420' : '#00D4AA20',
              color: data.blocked ? '#ef4444' : '#00D4AA',
              border: `1px solid ${data.blocked ? '#ef4444' : '#00D4AA'}`,
              fontSize: '0.7rem',
            }}
          />
          <Typography variant="caption" sx={{ color: '#6b7280' }}>
            Confidence: {((data.confidence || 0) * 100).toFixed(1)}%
          </Typography>
        </Box>
        {data.reason && (
          <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: '#a1a1aa' }}>
            {data.reason}
          </Typography>
        )}
      </Box>
    ));
  };

  return (
    <Box sx={{ 
      minHeight: '400px',
      maxHeight: '85vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: 'transparent',
    }}>
      {/* Header */}
      <Card sx={{ 
        mb: 2,
        background: 'rgba(255, 255, 255, 0.02)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '12px',
      }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ 
                background: 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)',
                width: 48,
                height: 48,
              }}>
                <BotIcon />
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: '#ffffff' }}>
                  AI Safety System
                </Typography>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  {hasConnectedProviders ? 
                    `${connectedProviders.length} provider${connectedProviders.length > 1 ? 's' : ''} connected` : 
                    'No providers connected'
                  }
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {/* Provider Selection in Main Header */}
              <Box sx={{ minWidth: 180 }}>
                <FormControl fullWidth size="small">
                  <InputLabel sx={{ color: '#6b7280', fontSize: '0.875rem' }}>AI Provider</InputLabel>
                  <Select
                    value={selectedProvider || ''}
                    onChange={(e) => onProviderChange?.(e.target.value)}
                    label="AI Provider"
                    disabled={!hasConnectedProviders}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        background: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: '8px',
                        '&:hover .MuiOutlinedInput-notchedOutline': {
                          borderColor: '#00D4AA',
                        },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                          borderColor: '#00D4AA',
                        },
                      },
                      '& .MuiSelect-select': {
                        color: '#ffffff',
                        fontSize: '0.875rem',
                      },
                      '& .MuiSvgIcon-root': {
                        color: '#6b7280',
                      },
                    }}
                  >
                    {connectedProviders.map((provider) => (
                      <MenuItem key={provider.id} value={provider.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <span>{getProviderIcon(provider.id)}</span>
                          <span>{provider.display_name}</span>
                          <Chip
                            size="small"
                            label="connected"
                            sx={{
                              ml: 'auto',
                              backgroundColor: '#00D4AA20',
                              color: '#00D4AA',
                              border: '1px solid #00D4AA',
                              fontSize: '0.6rem',
                            }}
                          />
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              <Tooltip title="Configure Providers">
                <IconButton 
                  onClick={onNavigateToProviders}
                  sx={{ 
                    color: '#6b7280',
                    '&:hover': { color: '#00D4AA' },
                  }}
                >
                  <MemoryIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Configure Guardrails">
                <IconButton 
                  onClick={onNavigateToGuardrails}
                  sx={{ 
                    color: '#6b7280',
                    '&:hover': { color: '#00D4AA' },
                  }}
                >
                  <ShieldIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Settings">
                <IconButton 
                  onClick={() => setShowSettings(!showSettings)}
                  sx={{ 
                    color: showSettings ? '#00D4AA' : '#6b7280',
                    '&:hover': { color: '#00D4AA' },
                  }}
                >
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Clear History">
                <IconButton 
                  onClick={onClearHistory} 
                  sx={{ 
                    color: '#6b7280',
                    '&:hover': { color: '#ef4444' },
                  }}
                >
                  <ClearIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Settings Panel */}
      <Collapse in={showSettings}>
        <Card sx={{ 
          mb: 2,
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
        }}>
          <CardContent>
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 2, color: '#ffffff' }}>
                Safety Guardrails Configuration
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {['toxicity', 'pii', 'prompt_injection', 'hate_speech', 'bias', 'privacy'].map((detector) => (
                  <motion.div
                    key={detector}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Chip
                      icon={getDetectorIcon(detector)}
                      label={detector.replace('_', ' ')}
                      onClick={() => toggleDetector(detector)}
                      sx={{
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        backgroundColor: detectorConfig[detector]?.enabled 
                          ? '#00D4AA20' 
                          : 'rgba(255, 255, 255, 0.02)',
                        color: detectorConfig[detector]?.enabled 
                          ? '#00D4AA' 
                          : '#6b7280',
                        border: `1px solid ${detectorConfig[detector]?.enabled 
                          ? '#00D4AA' 
                          : 'rgba(255, 255, 255, 0.06)'}`,
                        '&:hover': {
                          transform: 'translateY(-1px)',
                          backgroundColor: detectorConfig[detector]?.enabled 
                            ? '#00D4AA30' 
                            : 'rgba(255, 255, 255, 0.04)',
                        }
                      }}
                    />
                  </motion.div>
                ))}
              </Stack>
            </Box>
          </CardContent>
        </Card>
      </Collapse>

      {/* Messages Container */}
      <Card sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(255, 255, 255, 0.02)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '12px',
        mb: 2,
      }}>
        <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
          <Box
            ref={messagesContainerRef}
            sx={{
              flex: 1,
              overflow: 'auto',
              p: 2,
              scrollbarWidth: 'thin',
              scrollbarColor: 'rgba(255, 255, 255, 0.2) rgba(255, 255, 255, 0.05)',
              '&::-webkit-scrollbar': {
                width: '8px',
              },
              '&::-webkit-scrollbar-track': {
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '4px',
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
            {messages.length === 0 && (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%',
                textAlign: 'center',
              }}>
                <Box>
                  <Typography variant="h6" sx={{ mb: 1, color: '#00D4AA' }}>
                    🛡️ AI Safety System Ready
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280' }}>
                    I'm your local AI assistant with built-in safety guardrails.<br/>
                    Ask me anything and I'll help while keeping our conversation safe and secure.
                  </Typography>
                </Box>
              </Box>
            )}
            
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                      mb: 2,
                    }}
                  >
                    <Box
                      sx={{
                        maxWidth: '80%',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 1,
                        flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                      }}
                    >
                      <Avatar
                        sx={{
                          width: 32,
                          height: 32,
                          background: message.role === 'user' 
                            ? 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)'
                            : message.blocked 
                              ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                              : 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
                        }}
                      >
                        {message.role === 'user' ? <PersonIcon /> : <BotIcon />}
                      </Avatar>
                      
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          maxWidth: '100%',
                          borderRadius: 2,
                          background: message.role === 'user' 
                            ? 'rgba(0, 212, 170, 0.1)'
                            : message.blocked 
                              ? 'rgba(239, 68, 68, 0.1)'
                              : 'rgba(255, 255, 255, 0.05)',
                          border: `1px solid ${message.role === 'user' 
                            ? 'rgba(0, 212, 170, 0.2)'
                            : message.blocked 
                              ? 'rgba(239, 68, 68, 0.2)'
                              : 'rgba(255, 255, 255, 0.06)'}`,
                          backdropFilter: 'blur(10px)',
                        }}
                      >
                        <Typography variant="body1" sx={{ 
                          whiteSpace: 'pre-wrap', 
                          color: '#ffffff',
                          mb: 1,
                        }}>
                          {message.content}
                        </Typography>
                        
                        {message.blocked && (
                          <Box sx={{ mt: 1 }}>
                            <Chip
                              icon={<BlockIcon />}
                              label="BLOCKED"
                              size="small"
                              sx={{ 
                                backgroundColor: '#ef444420',
                                color: '#ef4444',
                                border: '1px solid #ef4444',
                                fontSize: '0.7rem',
                              }}
                            />
                            {message.blocking_reasons && (
                              <Typography variant="caption" sx={{ 
                                display: 'block', 
                                mt: 0.5, 
                                color: '#ef4444',
                              }}>
                                {message.blocking_reasons.join(', ')}
                              </Typography>
                            )}
                          </Box>
                        )}
                        
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1 }}>
                          <Typography variant="caption" sx={{ color: '#6b7280' }}>
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </Typography>
                          
                          {/* Detection Results */}
                          {(message.input_analysis || message.output_analysis) && (
                            <Button
                              size="small"
                              onClick={() => setExpandedMessage(expandedMessage === message.id ? null : message.id)}
                              sx={{ 
                                color: '#6b7280', 
                                minWidth: 'auto', 
                                p: 0.5,
                                '&:hover': { color: '#00D4AA' },
                              }}
                            >
                              {expandedMessage === message.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                              Analysis
                            </Button>
                          )}
                        </Box>
                        
                        <Collapse in={expandedMessage === message.id}>
                          <Box sx={{ 
                            mt: 1, 
                            p: 1, 
                            background: 'rgba(255, 255, 255, 0.02)',
                            borderRadius: 1,
                            border: '1px solid rgba(255, 255, 255, 0.06)',
                          }}>
                            {message.input_analysis && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="caption" sx={{ 
                                  fontWeight: 'bold', 
                                  display: 'block',
                                  color: '#00D4AA',
                                  mb: 1,
                                }}>
                                  Input Analysis:
                                </Typography>
                                {formatDetectionResult(message.input_analysis)}
                              </Box>
                            )}
                            {message.output_analysis && (
                              <Box>
                                <Typography variant="caption" sx={{ 
                                  fontWeight: 'bold', 
                                  display: 'block',
                                  color: '#00D4AA',
                                  mb: 1,
                                }}>
                                  Output Analysis:
                                </Typography>
                                {formatDetectionResult(message.output_analysis)}
                              </Box>
                            )}
                          </Box>
                        </Collapse>
                      </Paper>
                    </Box>
                  </Box>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Loading indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <Avatar sx={{ 
                      width: 32, 
                      height: 32,
                      background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
                    }}>
                      <BotIcon />
                    </Avatar>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        background: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.06)',
                        backdropFilter: 'blur(10px)',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </Box>
                      {currentStage && (
                        <Box sx={{ mt: 1 }}>
                          <LoadingSpinner 
                            message={currentStage || 'Processing...'}
                            size="small" 
                            variant="linear" 
                          />
                        </Box>
                      )}
                    </Paper>
                  </Box>
                </Box>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </Box>
        </CardContent>
      </Card>

      {/* Scroll to bottom button */}
      <AnimatePresence>
        {showScrollButton && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            style={{
              position: 'absolute',
              bottom: 100,
              right: 20,
              zIndex: 1000,
            }}
          >
            <Fab
              size="small"
              onClick={scrollToBottom}
              sx={{
                background: 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)',
                color: '#ffffff',
                '&:hover': {
                  background: 'linear-gradient(135deg, #00A085 0%, #00896B 100%)',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <ScrollDownIcon />
            </Fab>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <Card sx={{
        background: 'rgba(255, 255, 255, 0.02)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.06)',
        borderRadius: '12px',
      }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={4}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                hasConnectedProviders
                  ? 'Type your message...'
                  : 'Connect a provider to start chatting'
              }
              disabled={disabled || !hasConnectedProviders}
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  transition: 'all 0.2s',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(0, 212, 170, 0.2)',
                  },
                  '&.Mui-focused': {
                    background: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid #00D4AA',
                    boxShadow: '0 0 0 2px rgba(0, 212, 170, 0.1)',
                  },
                  '& fieldset': { border: 'none' },
                },
                '& .MuiInputBase-input': {
                  color: '#ffffff',
                  '&::placeholder': {
                    color: '#6b7280',
                  },
                },
              }}
            />
            
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Fab
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading || !hasConnectedProviders}
                sx={{
                  background: (!inputMessage.trim() || isLoading || !hasConnectedProviders) 
                    ? 'rgba(107, 114, 128, 0.3)' 
                    : 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)',
                  color: '#ffffff',
                  '&:hover': {
                    background: (!inputMessage.trim() || isLoading || !hasConnectedProviders) 
                      ? 'rgba(107, 114, 128, 0.4)' 
                      : 'linear-gradient(135deg, #00A085 0%, #00896B 100%)',
                  },
                  '&.Mui-disabled': {
                    color: '#6b7280',
                  },
                }}
              >
                <SendIcon />
              </Fab>
            </motion.div>
          </Box>
          
          {!hasConnectedProviders && (
            <Alert
              severity="info"
              sx={{ 
                mt: 2, 
                borderRadius: 2,
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.2)',
                '& .MuiAlert-icon': { color: '#3b82f6' },
                '& .MuiAlert-message': { color: '#ffffff' },
              }}
              icon={<SecurityIcon />}
            >
              Configure and connect AI providers in the Providers tab to start chatting
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* CSS for typing indicator */}
      <style>{`
        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 2px;
        }
        .typing-indicator span {
          width: 6px;
          height: 6px;
          background: #00D4AA;
          border-radius: 50%;
          animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
          animation-delay: 0.4s;
        }
        @keyframes typing {
          0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.7;
          }
          30% {
            transform: translateY(-10px);
            opacity: 1;
          }
        }
      `}</style>
    </Box>
  );
};

export default ModernChatInterface;