import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Card,
  CardContent,
  Alert,
  Button,
} from '@mui/material';
import {
  Send,
  Bot,
  User,
  ChevronDown,
  Copy,
  Shield,
  AlertTriangle,
  CheckCircle,
  Zap,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  blocked?: boolean;
  blocking_reasons?: string[];
  input_analysis?: any;
  output_analysis?: any;
}

interface DetectorConfig {
  [key: string]: {
    enabled: boolean;
    threshold?: number;
    sensitivity?: string;
  };
}

interface ChatGPTInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, provider: string, detectorConfig: DetectorConfig) => void;
  isLoading: boolean;
  selectedProvider: string;
  connectedProviders: Array<{ id: string; display_name: string; status: string }>;
  onProviderChange: (providerId: string) => void;
  detectorConfig?: DetectorConfig;
}

// Provider icon mapping
const getProviderIcon = (providerId: string) => {
  switch (providerId.toLowerCase()) {
    case 'openai':
      return '🤖';
    case 'claude':
      return '🧠';
    case 'gemini':
      return '💎';
    case 'ollama':
      return '🦙';
    default:
      return '⚡';
  }
};

// Typing indicator component with improved animation
const TypingIndicator = memo(() => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.3 }}
    style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12,
      marginBottom: 16,
      padding: '0 16px',
    }}
  >
    <Avatar
      sx={{
        width: 32,
        height: 32,
        bgcolor: '#374151',
        fontSize: '14px',
      }}
    >
      <Bot size={16} />
    </Avatar>
    
    <Card
      sx={{
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px 16px 16px 4px',
        backdropFilter: 'blur(10px)',
        padding: '12px 16px',
      }}
    >
      <Box sx={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: '#00D4AA',
            }}
          />
        ))}
      </Box>
    </Card>
  </motion.div>
));

// Message bubble component with modern styling
const MessageBubble = memo(({ message, isUser }: { message: ChatMessage; isUser: boolean }) => {
  const [showCopy, setShowCopy] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
        padding: '0 16px',
      }}
      onMouseEnter={() => setShowCopy(true)}
      onMouseLeave={() => setShowCopy(false)}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12,
          maxWidth: '75%',
          flexDirection: isUser ? 'row-reverse' : 'row',
          position: 'relative',
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: isUser ? '#00D4AA' : '#374151',
            fontSize: '14px',
            flexShrink: 0,
          }}
        >
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </Avatar>
        
        <Card
          sx={{
            backgroundColor: isUser 
              ? 'rgba(0, 212, 170, 0.15)' 
              : 'rgba(255, 255, 255, 0.05)',
            border: `1px solid ${isUser 
              ? 'rgba(0, 212, 170, 0.3)' 
              : 'rgba(255, 255, 255, 0.1)'}`,
            borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            backdropFilter: 'blur(10px)',
            position: 'relative',
            transition: 'all 0.2s ease-out',
            '&:hover': {
              backgroundColor: isUser 
                ? 'rgba(0, 212, 170, 0.2)' 
                : 'rgba(255, 255, 255, 0.08)',
              transform: 'translateY(-1px)',
              boxShadow: isUser
                ? '0 4px 12px rgba(0, 212, 170, 0.2)'
                : '0 4px 12px rgba(0, 0, 0, 0.1)',
            },
          }}
        >
          <CardContent sx={{ p: '12px 16px', '&:last-child': { pb: '12px' } }}>
            <Typography
              variant="body1"
              sx={{
                color: '#ffffff',
                whiteSpace: 'pre-wrap',
                fontSize: '14px',
                fontWeight: 400,
                lineHeight: 1.6,
                wordBreak: 'break-word',
              }}
            >
              {message.content}
            </Typography>
            
            {/* Message timestamp */}
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: '11px',
                mt: 0.5,
                display: 'block',
              }}
            >
              {new Date(message.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </Typography>
            
            {/* Detection results */}
            {(message.blocked || message.blocking_reasons?.length) && (
              <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Chip
                  icon={<Shield size={12} />}
                  label={message.blocked ? "Content Blocked" : "Flagged Content"}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#ef4444',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    fontSize: '10px',
                    height: '20px',
                  }}
                />
                {message.blocking_reasons?.length && (
                  <Typography variant="caption" sx={{ color: '#9ca3af', fontSize: '10px', display: 'block', mt: 0.5 }}>
                    {message.blocking_reasons.join(', ')}
                  </Typography>
                )}
              </Box>
            )}
            
            {message.output_analysis?.summary && (
              <Box sx={{ mt: 1, pt: 1, borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <Typography variant="caption" sx={{ color: '#9ca3af', fontSize: '10px' }}>
                  {message.output_analysis.summary}
                </Typography>
              </Box>
            )}
          </CardContent>
          
          {/* Copy button */}
          <AnimatePresence>
            {showCopy && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ duration: 0.15 }}
                style={{
                  position: 'absolute',
                  top: -8,
                  right: isUser ? 'auto' : -8,
                  left: isUser ? -8 : 'auto',
                }}
              >
                <IconButton
                  onClick={handleCopy}
                  sx={{
                    width: 24,
                    height: 24,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: '#ffffff',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 0, 0.9)',
                      transform: 'scale(1.1)',
                    },
                  }}
                >
                  <Copy size={12} />
                </IconButton>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </Box>
    </motion.div>
  );
});

const ChatGPTInterface: React.FC<ChatGPTInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  selectedProvider,
  connectedProviders,
  onProviderChange,
  detectorConfig = {},
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize input
  useEffect(() => {
    const textarea = inputRef.current?.querySelector('textarea');
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 120);
      textarea.style.height = `${newHeight}px`;
    }
  }, [inputMessage]);

  // Handle message send
  const handleSendMessage = useCallback(() => {
    if (inputMessage.trim() && !isLoading && selectedProvider) {
      onSendMessage(inputMessage.trim(), selectedProvider, detectorConfig);
      setInputMessage('');
    }
  }, [inputMessage, isLoading, selectedProvider, detectorConfig, onSendMessage]);

  // Handle key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage, isLoading]);

  const hasConnectedProviders = connectedProviders.some(p => p.status === 'connected');
  const canSendMessage = inputMessage.trim() && !isLoading && selectedProvider && hasConnectedProviders;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with Provider Selection */}
      <Card
        sx={{
          mb: 2,
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar
                sx={{
                  background: 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)',
                  width: 40,
                  height: 40,
                  boxShadow: '0 4px 12px rgba(0, 212, 170, 0.3)',
                }}
              >
                <Zap size={20} />
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: '#ffffff', fontSize: '16px' }}>
                  AI Chat Assistant
                </Typography>
                <Typography variant="caption" sx={{ color: '#6b7280' }}>
                  {hasConnectedProviders 
                    ? `${connectedProviders.filter(p => p.status === 'connected').length} provider${connectedProviders.filter(p => p.status === 'connected').length !== 1 ? 's' : ''} connected`
                    : 'No providers connected'
                  }
                </Typography>
              </Box>
            </Box>

            {/* Provider Selection */}
            {hasConnectedProviders ? (
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>Provider</InputLabel>
                <Select
                  value={selectedProvider}
                  onChange={(e) => onProviderChange(e.target.value)}
                  label="Provider"
                  sx={{
                    color: '#ffffff',
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(0, 212, 170, 0.3)',
                    },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#00D4AA',
                    },
                    '& .MuiSelect-icon': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                  }}
                >
                  {connectedProviders
                    .filter(provider => provider.status === 'connected')
                    .map((provider) => (
                      <MenuItem key={provider.id} value={provider.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <span>{getProviderIcon(provider.id)}</span>
                          {provider.display_name}
                        </Box>
                      </MenuItem>
                    ))
                  }
                </Select>
              </FormControl>
            ) : (
              <Alert 
                severity="warning" 
                sx={{ 
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  '& .MuiAlert-message': { color: '#ffffff' },
                }}
              >
                No AI providers connected. Please configure a provider first.
              </Alert>
            )}
          </Box>

          {/* Guardrails Status (read-only) */}
          {Object.keys(detectorConfig).length > 0 && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', mb: 1, display: 'block' }}>
                Active Safety Guardrails:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.entries(detectorConfig)
                  .filter(([_, config]) => config.enabled)
                  .map(([detectorName]) => (
                    <Chip
                      key={detectorName}
                      icon={<CheckCircle size={12} />}
                      label={detectorName.replace('_', ' ')}
                      size="small"
                      sx={{
                        backgroundColor: 'rgba(34, 197, 94, 0.2)',
                        color: '#22c55e',
                        border: '1px solid rgba(34, 197, 94, 0.3)',
                        fontSize: '10px',
                        height: '20px',
                      }}
                    />
                  ))
                }
                {Object.values(detectorConfig).every(config => !config.enabled) && (
                  <Chip
                    icon={<AlertTriangle size={12} />}
                    label="No guardrails active"
                    size="small"
                    sx={{
                      backgroundColor: 'rgba(234, 179, 8, 0.2)',
                      color: '#eab308',
                      border: '1px solid rgba(234, 179, 8, 0.3)',
                      fontSize: '10px',
                      height: '20px',
                    }}
                  />
                )}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Messages Container */}
      <Card
        sx={{
          flex: 1,
          background: 'rgba(255, 255, 255, 0.01)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          mb: 2,
        }}
      >
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            py: 2,
            '&::-webkit-scrollbar': {
              width: '6px',
            },
            '&::-webkit-scrollbar-track': {
              background: 'transparent',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '3px',
              '&:hover': {
                background: 'rgba(255, 255, 255, 0.3)',
              },
            },
          }}
        >
          {messages.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                gap: 2,
                p: 4,
              }}
            >
              <motion.div
                animate={{
                  scale: [1, 1.1, 1],
                  rotate: [0, 5, -5, 0],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <Zap size={48} color="rgba(255, 255, 255, 0.3)" />
              </motion.div>
              <Typography 
                variant="h6" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.6)',
                  textAlign: 'center',
                }}
              >
                Start a conversation...
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.4)',
                  textAlign: 'center',
                  maxWidth: 400,
                }}
              >
                Your messages are protected by advanced AI safety guardrails.
              </Typography>
            </Box>
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isUser={message.role === 'user'}
                />
              ))}
              
              {/* Typing indicator */}
              <AnimatePresence>
                {isLoading && <TypingIndicator />}
              </AnimatePresence>
              
              <div ref={messagesEndRef} />
            </>
          )}
        </Box>
      </Card>

      {/* Input Area */}
      <Card
        sx={{
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
        }}
      >
        <CardContent sx={{ p: 2 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: 2,
              position: 'relative',
            }}
          >
            <TextField
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={hasConnectedProviders ? "Type your message..." : "Connect a provider to start chatting..."}
              multiline
              maxRows={4}
              disabled={isLoading || !hasConnectedProviders}
              sx={{
                flex: 1,
                '& .MuiOutlinedInput-root': {
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: 'none',
                  borderRadius: '20px',
                  color: '#ffffff',
                  fontSize: '14px',
                  fontWeight: 400,
                  pr: '60px', // Space for send button
                  transition: 'all 0.3s ease-out',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                  },
                  '&.Mui-focused': {
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 0 0 2px rgba(0, 212, 170, 0.3)',
                  },
                  '&.Mui-disabled': {
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    color: 'rgba(255, 255, 255, 0.3)',
                  },
                },
                '& .MuiOutlinedInput-notchedOutline': {
                  display: 'none',
                },
                '& .MuiInputBase-input': {
                  padding: '12px 16px',
                  '&::placeholder': {
                    color: 'rgba(255, 255, 255, 0.5)',
                    opacity: 1,
                  },
                },
              }}
            />
            
            {/* Send Button */}
            <motion.div
              whileHover={canSendMessage ? { scale: 1.05 } : {}}
              whileTap={canSendMessage ? { scale: 0.95 } : {}}
              style={{
                position: 'absolute',
                right: 8,
                bottom: 8,
              }}
            >
              <IconButton
                onClick={handleSendMessage}
                disabled={!canSendMessage}
                sx={{
                  width: 40,
                  height: 40,
                  backgroundColor: canSendMessage
                    ? '#00D4AA'
                    : 'rgba(255, 255, 255, 0.1)',
                  color: canSendMessage
                    ? '#000000'
                    : 'rgba(255, 255, 255, 0.3)',
                  transition: 'all 0.3s ease-out',
                  '&:hover': {
                    backgroundColor: canSendMessage
                      ? '#00B894'
                      : 'rgba(255, 255, 255, 0.15)',
                    boxShadow: canSendMessage
                      ? '0 4px 12px rgba(0, 212, 170, 0.4)'
                      : 'none',
                  },
                  '&:active': {
                    transform: canSendMessage ? 'scale(0.95)' : 'none',
                  },
                }}
              >
                <Send size={16} />
              </IconButton>
            </motion.div>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ChatGPTInterface;