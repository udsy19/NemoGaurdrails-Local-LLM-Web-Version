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
  LinearProgress,
  Tooltip,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
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
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { ChatMessage, DetectorConfig } from '../../types';
import { useProcessingStages } from '../../hooks/useRealTime';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, selectedProvider?: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  detectorConfig: DetectorConfig;
  onClearHistory: () => void;
  availableProviders?: Array<{id: string, display_name: string, enabled: boolean}>;
  selectedProvider?: string;
  onProviderChange?: (providerId: string) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  disabled,
  detectorConfig,
  onClearHistory,
  availableProviders = [],
  selectedProvider = 'ollama',
  onProviderChange,
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const [expandedDetails, setExpandedDetails] = useState<{ [key: string]: boolean }>({});
  const [showScrollButton, setShowScrollButton] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const {
    currentStage,
    stages,
    isProcessing,
    startProcessing,
  } = useProcessingStages();

  const scrollToBottom = (smooth = true) => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      const scrollHeight = container.scrollHeight;
      const clientHeight = container.clientHeight;
      
      if (smooth) {
        container.scrollTo({
          top: scrollHeight,
          behavior: 'smooth'
        });
      } else {
        container.scrollTop = scrollHeight;
      }
    }
  };

  // Scroll when messages array changes
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM is updated
    requestAnimationFrame(() => {
      setTimeout(() => scrollToBottom(false), 50);
    });
  }, [messages]);

  // Scroll when processing state changes
  useEffect(() => {
    if (isProcessing) {
      requestAnimationFrame(() => {
        setTimeout(() => scrollToBottom(false), 50);
      });
    }
  }, [isProcessing]);

  // Initial scroll on mount
  useEffect(() => {
    const timer = setTimeout(() => scrollToBottom(false), 100);
    return () => clearTimeout(timer);
  }, []);

  // Handle scroll detection for scroll button
  const handleScroll = () => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
      setShowScrollButton(!isAtBottom && messages.length > 3);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || disabled || isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');

    // Start processing animation
    await startProcessing(message);
    
    // Send the actual message with selected provider
    onSendMessage(message, selectedProvider);
    
    // Force scroll after message is sent with multiple attempts
    setTimeout(() => scrollToBottom(false), 100);
    setTimeout(() => scrollToBottom(false), 500);
    setTimeout(() => scrollToBottom(false), 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleDetails = (messageId: string) => {
    setExpandedDetails(prev => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const getDetectorStatusIcon = (result: any) => {
    if (result.blocked) {
      return <BlockIcon sx={{ color: '#FF3D71', fontSize: '1rem' }} />;
    } else {
      return <CheckIcon sx={{ color: '#00D4AA', fontSize: '1rem' }} />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return '#FF3D71';
    if (confidence > 0.5) return '#FFB800';
    return '#00D4AA';
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Chat Messages */}
      <Box
        ref={messagesContainerRef}
        onScroll={handleScroll}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          overflowX: 'hidden',
          p: 2,
          background: 'linear-gradient(135deg, #0A0E1A 0%, #1A1F2E 100%)',
          position: 'relative',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#1A1F2E',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#374151',
            borderRadius: '4px',
            '&:hover': {
              background: '#4B5563',
            },
          },
        }}
      >
        <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  mb: 3,
                }}
              >
                <Box
                  sx={{
                    maxWidth: '70%',
                    display: 'flex',
                    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                    alignItems: 'flex-start',
                    gap: 1,
                  }}
                >
                  {/* Avatar */}
                  <Avatar
                    sx={{
                      bgcolor: message.role === 'user' ? '#00D4AA' : '#FF6B6B',
                      width: 40,
                      height: 40,
                    }}
                  >
                    {message.role === 'user' ? (
                      <PersonIcon sx={{ fontSize: '1.25rem' }} />
                    ) : (
                      <BotIcon sx={{ fontSize: '1.25rem' }} />
                    )}
                  </Avatar>

                  {/* Message Content */}
                  <Paper
                    elevation={8}
                    sx={{
                      p: 2,
                      background: message.role === 'user' 
                        ? 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)'
                        : 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
                      border: `1px solid ${message.role === 'user' ? '#00D4AA' : '#374151'}`,
                      borderRadius: message.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
                      backdropFilter: 'blur(10px)',
                    }}
                  >
                    {/* Blocked Message Alert */}
                    {message.blocked && (
                      <Alert
                        severity="error"
                        icon={<SecurityIcon />}
                        sx={{
                          mb: 1,
                          backgroundColor: '#FF3D7120',
                          border: '1px solid #FF3D71',
                          '& .MuiAlert-icon': {
                            color: '#FF3D71',
                          },
                        }}
                      >
                        <Typography variant="body2" fontWeight={600}>
                          Message Blocked by AI Safety System
                        </Typography>
                      </Alert>
                    )}

                    {/* Message Text */}
                    <Typography
                      variant="body1"
                      sx={{
                        color: message.role === 'user' ? '#000000' : '#FFFFFF',
                        lineHeight: 1.6,
                        wordBreak: 'break-word',
                      }}
                    >
                      {message.content}
                    </Typography>

                    {/* Timestamp */}
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'block',
                        mt: 1,
                        color: message.role === 'user' ? '#00000070' : '#A8B2D1',
                        textAlign: message.role === 'user' ? 'right' : 'left',
                      }}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>

                    {/* Blocking Reasons */}
                    {message.blocked && message.blocking_reasons && (
                      <Box sx={{ mt: 1 }}>
                        {message.blocking_reasons.map((reason, idx) => (
                          <Chip
                            key={idx}
                            label={reason}
                            size="small"
                            icon={<WarningIcon />}
                            sx={{
                              backgroundColor: '#FF3D7120',
                              color: '#FF3D71',
                              border: '1px solid #FF3D71',
                              mr: 0.5,
                              mb: 0.5,
                            }}
                          />
                        ))}
                      </Box>
                    )}

                    {/* Detection Results */}
                    {(message.input_analysis || message.output_analysis) && (
                      <Box sx={{ mt: 2 }}>
                        <Fab
                          size="small"
                          onClick={() => toggleDetails(message.id)}
                          sx={{
                            background: 'linear-gradient(135deg, #374151 0%, #4B5563 100%)',
                            color: '#FFFFFF',
                            width: 32,
                            height: 32,
                            minHeight: 32,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #4B5563 0%, #6B7280 100%)',
                            },
                          }}
                        >
                          {expandedDetails[message.id] ? (
                            <ExpandLessIcon sx={{ fontSize: '1rem' }} />
                          ) : (
                            <ExpandMoreIcon sx={{ fontSize: '1rem' }} />
                          )}
                        </Fab>

                        <Collapse in={expandedDetails[message.id]}>
                          <Box sx={{ mt: 2 }}>
                            {/* Input Analysis */}
                            {message.input_analysis && (
                              <Card sx={{ mb: 1, backgroundColor: '#1A1F2E', border: '1px solid #374151' }}>
                                <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                                  <Typography variant="subtitle2" sx={{ color: '#FFB800', mb: 1, fontWeight: 600 }}>
                                    🔍 Input Analysis
                                  </Typography>
                                  {Object.entries(message.input_analysis).map(([detector, result]) => (
                                    <Box key={detector} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                      {getDetectorStatusIcon(result)}
                                      <Typography variant="body2" sx={{ ml: 1, mr: 2, color: '#FFFFFF', fontWeight: 500 }}>
                                        {detector.charAt(0).toUpperCase() + detector.slice(1)}
                                      </Typography>
                                      <Typography
                                        variant="caption"
                                        sx={{
                                          color: getConfidenceColor(result.confidence),
                                          fontWeight: 600,
                                        }}
                                      >
                                        {(result.confidence * 100).toFixed(0)}%
                                      </Typography>
                                    </Box>
                                  ))}
                                </CardContent>
                              </Card>
                            )}

                            {/* Output Analysis */}
                            {message.output_analysis && (
                              <Card sx={{ backgroundColor: '#1A1F2E', border: '1px solid #374151' }}>
                                <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                                  <Typography variant="subtitle2" sx={{ color: '#00D4AA', mb: 1, fontWeight: 600 }}>
                                    📤 Output Analysis
                                  </Typography>
                                  {Object.entries(message.output_analysis).map(([detector, result]) => (
                                    <Box key={detector} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                                      {getDetectorStatusIcon(result)}
                                      <Typography variant="body2" sx={{ ml: 1, mr: 2, color: '#FFFFFF', fontWeight: 500 }}>
                                        {detector.charAt(0).toUpperCase() + detector.slice(1)}
                                      </Typography>
                                      <Typography
                                        variant="caption"
                                        sx={{
                                          color: getConfidenceColor(result.confidence),
                                          fontWeight: 600,
                                        }}
                                      >
                                        {(result.confidence * 100).toFixed(0)}%
                                      </Typography>
                                    </Box>
                                  ))}
                                </CardContent>
                              </Card>
                            )}
                          </Box>
                        </Collapse>
                      </Box>
                    )}
                  </Paper>
                </Box>
              </Box>
              </motion.div>
            ))}
          </AnimatePresence>

        {/* Processing Stages */}
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 3 }}>
              <Box sx={{ maxWidth: '70%', display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <Avatar sx={{ bgcolor: '#FF6B6B', width: 40, height: 40 }}>
                  <BotIcon sx={{ fontSize: '1.25rem' }} />
                </Avatar>
                
                <Paper
                  elevation={8}
                  sx={{
                    p: 2,
                    background: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
                    border: '1px solid #374151',
                    borderRadius: '20px 20px 20px 4px',
                    backdropFilter: 'blur(10px)',
                    minWidth: 200,
                  }}
                >
                  <Typography variant="body2" sx={{ color: '#A8B2D1', mb: 1 }}>
                    {currentStage}
                  </Typography>
                  <LinearProgress
                    sx={{
                      backgroundColor: '#374151',
                      '& .MuiLinearProgress-bar': {
                        background: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
                      },
                    }}
                  />
                  <Box sx={{ mt: 1 }}>
                    {stages.map((stage, index) => (
                      <Typography
                        key={index}
                        variant="caption"
                        sx={{
                          display: 'block',
                          color: '#6B7280',
                          fontSize: '0.75rem',
                        }}
                      >
                        ✓ {stage}
                      </Typography>
                    ))}
                  </Box>
                </Paper>
              </Box>
            </Box>
          </motion.div>
        )}


        {/* Scroll to bottom button */}
        <AnimatePresence>
          {showScrollButton && (
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              style={{
                position: 'absolute',
                bottom: 16,
                right: 16,
                zIndex: 1000,
              }}
            >
              <Fab
                size="small"
                onClick={() => scrollToBottom(true)}
                sx={{
                  background: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
                  color: '#FFFFFF',
                  boxShadow: '0 4px 20px rgba(0, 212, 170, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #007A6B 0%, #005A4B 100%)',
                    boxShadow: '0 6px 25px rgba(0, 212, 170, 0.4)',
                  },
                }}
              >
                <ScrollDownIcon />
              </Fab>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {/* Input Area */}
      <Paper
        elevation={8}
        sx={{
          p: 2,
          background: 'linear-gradient(135deg, #1A1F2E 0%, #242938 100%)',
          border: '1px solid #374151',
          borderRadius: 0,
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Provider Selection */}
        {availableProviders.length > 1 && (
          <Box sx={{ mb: 2 }}>
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel sx={{ color: '#A8B2D1' }}>AI Provider</InputLabel>
              <Select
                value={selectedProvider}
                onChange={(e) => onProviderChange?.(e.target.value)}
                label="AI Provider"
                sx={{
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#00D4AA',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#00D4AA',
                  },
                  '& .MuiSelect-select': {
                    color: '#FFFFFF',
                  },
                  '& .MuiSvgIcon-root': {
                    color: '#A8B2D1',
                  },
                }}
              >
                {availableProviders
                  .filter(provider => provider.enabled)
                  .map((provider) => (
                    <MenuItem key={provider.id} value={provider.id}>
                      {provider.display_name}
                    </MenuItem>
                  ))
                }
              </Select>
            </FormControl>
          </Box>
        )}

        <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <TextField
              ref={inputRef}
              fullWidth
              multiline
              maxRows={4}
              placeholder="Type your message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={disabled || isLoading || isProcessing}
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#0A0E1A',
                  borderRadius: '12px',
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#00D4AA',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#00D4AA',
                    borderWidth: '2px',
                  },
                },
                '& .MuiOutlinedInput-input': {
                  color: '#FFFFFF',
                },
              }}
            />
          </Box>

          <Tooltip title="Clear History">
            <IconButton
              onClick={onClearHistory}
              disabled={messages.length === 0}
              sx={{
                color: '#A8B2D1',
                '&:hover': {
                  backgroundColor: '#374151',
                  color: '#FFFFFF',
                },
              }}
            >
              <ClearIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Send Message">
            <span>
              <IconButton
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || disabled || isLoading || isProcessing}
                sx={{
                  background: inputMessage.trim() && !disabled && !isLoading && !isProcessing
                    ? 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)'
                    : '#374151',
                  color: '#FFFFFF',
                  '&:hover': {
                    background: inputMessage.trim() && !disabled && !isLoading && !isProcessing
                      ? 'linear-gradient(135deg, #007A6B 0%, #005A4B 100%)'
                      : '#4B5563',
                  },
                  '&:disabled': {
                    background: '#374151',
                    color: '#6B7280',
                  },
                }}
              >
                <SendIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>

        {/* Active Detectors Info */}
        {Object.keys(detectorConfig).length > 0 && (
          <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <SecurityIcon sx={{ color: '#00D4AA', fontSize: '1rem' }} />
            <Typography variant="caption" sx={{ color: '#A8B2D1' }}>
              Active Guardrails:
            </Typography>
            {Object.entries(detectorConfig)
              .filter(([_, config]) => config.enabled)
              .map(([name, _]) => (
                <Chip
                  key={name}
                  label={name}
                  size="small"
                  sx={{
                    backgroundColor: '#00D4AA20',
                    color: '#00D4AA',
                    border: '1px solid #00D4AA',
                    fontSize: '0.75rem',
                  }}
                />
              ))
            }
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default ChatInterface;