import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Toolbar,
  Chip,
  Tooltip,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Terminal as TerminalIcon,
  Clear as ClearIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useTerminal } from '../../hooks/useRealTime';
import { TerminalOutput } from '../../types';

interface TerminalProps {
  height?: number | string;
  maxLines?: number;
  autoScroll?: boolean;
  showToolbar?: boolean;
}

const Terminal: React.FC<TerminalProps> = ({
  height = 400,
  maxLines = 500,
  autoScroll = true,
  showToolbar = true,
}) => {
  const {
    output,
    isConnected,
    terminalRef,
    addCommand,
    addSystemMessage,
    clearTerminal,
  } = useTerminal(maxLines);

  const [command, setCommand] = useState('');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isRunning, setIsRunning] = useState(true);
  const [filter, setFilter] = useState<string>('');

  // Filter output based on filter text
  const filteredOutput = filter
    ? output.filter(line => 
        line.content.toLowerCase().includes(filter.toLowerCase()) ||
        line.source?.toLowerCase().includes(filter.toLowerCase())
      )
    : output;

  const handleCommandSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;

    addCommand(command);
    
    // Simulate command processing
    setTimeout(() => {
      switch (command.toLowerCase().trim()) {
        case 'help':
          addSystemMessage('Available commands: help, clear, status, health, detectors, logs, test', 'output');
          break;
        case 'clear':
          clearTerminal();
          break;
        case 'status':
          addSystemMessage(`System Status: ${isConnected ? '🟢 Online' : '🔴 Offline'}`, 'output');
          break;
        case 'health':
          addSystemMessage('Running health check...', 'output');
          setTimeout(() => addSystemMessage('Health: ✅ All systems operational', 'output'), 1000);
          break;
        case 'detectors':
          addSystemMessage('Active detectors: toxicity, pii, prompt_injection, spam', 'output');
          break;
        case 'logs':
          addSystemMessage('Displaying real-time logs...', 'output');
          break;
        case 'test':
          addSystemMessage('Running system test...', 'output');
          setTimeout(() => addSystemMessage('Test completed: ✅ PASS', 'output'), 2000);
          break;
        default:
          addSystemMessage(`Command not found: ${command}`, 'error');
          addSystemMessage('Type "help" for available commands', 'output');
      }
    }, 100);

    setCommand('');
  }, [command, addCommand, addSystemMessage, clearTerminal, isConnected]);

  const getOutputColor = (type: TerminalOutput['type']) => {
    switch (type) {
      case 'input':
        return '#00D4AA';
      case 'output':
        return '#C9D1D9';
      case 'error':
        return '#FF3D71';
      case 'system':
        return '#FFB800';
      default:
        return '#C9D1D9';
    }
  };

  const getSourceIcon = (source?: string) => {
    switch (source) {
      case 'api':
        return '🌐';
      case 'detector':
        return '🛡️';
      case 'guardrails':
        return '🚧';
      case 'ollama':
        return '🤖';
      case 'system':
        return '⚙️';
      case 'websocket':
        return '🔌';
      default:
        return '📝';
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const toggleRunning = () => {
    setIsRunning(!isRunning);
    if (isRunning) {
      addSystemMessage('Terminal paused', 'system');
    } else {
      addSystemMessage('Terminal resumed', 'system');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? 9999 : 'auto',
        height: isFullscreen ? '100vh' : height,
      }}
    >
      <Paper
        elevation={8}
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#0D1117',
          border: '1px solid #30363D',
          borderRadius: isFullscreen ? 0 : 2,
          overflow: 'hidden',
        }}
      >
        {showToolbar && (
          <Toolbar
            variant="dense"
            sx={{
              backgroundColor: '#161B22',
              borderBottom: '1px solid #30363D',
              minHeight: 48,
              px: 2,
            }}
          >
            <TerminalIcon sx={{ color: '#00D4AA', mr: 1 }} />
            <Typography variant="h6" sx={{ flexGrow: 1, color: '#C9D1D9', fontSize: '1rem' }}>
              AI Safety System Terminal
            </Typography>
            
            <Chip
              icon={<div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: isConnected ? '#00D4AA' : '#FF3D71' }} />}
              label={isConnected ? 'Connected' : 'Disconnected'}
              size="small"
              sx={{
                backgroundColor: isConnected ? '#00D4AA20' : '#FF3D7120',
                color: isConnected ? '#00D4AA' : '#FF3D71',
                mr: 1,
              }}
            />

            <Tooltip title={isRunning ? 'Pause' : 'Resume'}>
              <IconButton size="small" onClick={toggleRunning} sx={{ color: '#C9D1D9' }}>
                {isRunning ? <StopIcon /> : <PlayIcon />}
              </IconButton>
            </Tooltip>

            <Tooltip title="Clear Terminal">
              <IconButton size="small" onClick={clearTerminal} sx={{ color: '#C9D1D9' }}>
                <ClearIcon />
              </IconButton>
            </Tooltip>

            <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
              <IconButton size="small" onClick={toggleFullscreen} sx={{ color: '#C9D1D9' }}>
                {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
          </Toolbar>
        )}

        {/* Filter bar */}
        <Box sx={{ p: 1, backgroundColor: '#161B22', borderBottom: '1px solid #30363D' }}>
          <TextField
            size="small"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: '#0D1117',
                fontSize: '0.875rem',
                '& fieldset': {
                  borderColor: '#30363D',
                },
                '&:hover fieldset': {
                  borderColor: '#00D4AA',
                },
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Typography sx={{ color: '#6E7681', fontSize: '0.875rem' }}>🔍</Typography>
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {/* Terminal output */}
        <Box
          ref={terminalRef}
          sx={{
            flexGrow: 1,
            overflow: 'auto',
            backgroundColor: '#0D1117',
            fontFamily: '"JetBrains Mono", monospace',
            fontSize: '0.875rem',
            lineHeight: 1.4,
            p: 1,
            '&::-webkit-scrollbar': {
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              background: '#161B22',
            },
            '&::-webkit-scrollbar-thumb': {
              background: '#30363D',
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb:hover': {
              background: '#484F58',
            },
          }}
        >
          <AnimatePresence>
            {filteredOutput.map((line, index) => (
              <motion.div
                key={`${line.timestamp}_${index}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  marginBottom: '2px',
                  padding: '2px 0',
                }}
              >
                <Typography
                  component="span"
                  sx={{
                    color: '#6E7681',
                    fontSize: '0.75rem',
                    minWidth: '80px',
                    mr: 1,
                    fontFamily: 'monospace',
                  }}
                >
                  {new Date(line.timestamp).toLocaleTimeString()}
                </Typography>
                
                <Typography
                  component="span"
                  sx={{
                    fontSize: '0.875rem',
                    mr: 1,
                  }}
                >
                  {getSourceIcon(line.source)}
                </Typography>

                <Typography
                  component="pre"
                  sx={{
                    color: getOutputColor(line.type),
                    fontSize: '0.875rem',
                    fontFamily: '"JetBrains Mono", monospace',
                    margin: 0,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    flexGrow: 1,
                  }}
                >
                  {line.content}
                </Typography>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Blinking cursor */}
          <motion.div
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
            style={{
              color: '#00D4AA',
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: '0.875rem',
            }}
          >
            █
          </motion.div>
        </Box>

        {/* Command input */}
        <Box
          component="form"
          onSubmit={handleCommandSubmit}
          sx={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#161B22',
            borderTop: '1px solid #30363D',
            p: 1,
          }}
        >
          <Typography
            sx={{
              color: '#00D4AA',
              fontSize: '0.875rem',
              fontFamily: '"JetBrains Mono", monospace',
              mr: 1,
            }}
          >
            $
          </Typography>
          <TextField
            fullWidth
            size="small"
            variant="standard"
            placeholder="Enter command..."
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            disabled={!isRunning}
            sx={{
              '& .MuiInput-root': {
                color: '#C9D1D9',
                fontSize: '0.875rem',
                fontFamily: '"JetBrains Mono", monospace',
                '&:before': {
                  borderBottomColor: 'transparent',
                },
                '&:after': {
                  borderBottomColor: '#00D4AA',
                },
                '&:hover:not(.Mui-disabled):before': {
                  borderBottomColor: '#00D4AA50',
                },
              },
              '& .MuiInput-input': {
                padding: '4px 0',
                backgroundColor: 'transparent',
              },
            }}
          />
        </Box>
      </Paper>
    </motion.div>
  );
};

export default Terminal;