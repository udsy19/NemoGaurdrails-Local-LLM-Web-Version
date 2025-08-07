import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import websocketService from '../../services/websocketService';
import mockWebSocketServer from '../../utils/mockWebSocketServer';
import DataInjector from './DataInjector';

const WebSocketDebugger = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [useMockServer, setUseMockServer] = useState(true);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  useEffect(() => {
    // Setup connection change listener
    websocketService.onConnectionChange = (connected) => {
      setIsConnected(connected);
      if (connected) {
        addMessage('✅ Connected to WebSocket', 'success');
      } else {
        addMessage('❌ Disconnected from WebSocket', 'error');
      }
    };

    // Subscribe to all message types for debugging
    const messageTypes = [
      'analytics_data',
      'user_data',
      'guardrails_update',
      'detection_event',
      'connection_status',
      'dashboard_configured',
      'pong',
      'error'
    ];

    const unsubscribers = messageTypes.map(type => {
      return websocketService.subscribe(type, (data, message) => {
        addMessage(`📨 Received ${type}`, 'info', message);
      });
    });

    return () => {
      unsubscribers.forEach(unsub => unsub && unsub());
    };
  }, []);

  const addMessage = (content, type = 'info', data = null) => {
    const newMessage = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      content,
      type,
      data: data ? JSON.stringify(data, null, 2) : null
    };
    
    setMessages(prev => [newMessage, ...prev.slice(0, 49)]); // Keep last 50 messages
  };

  const handleConnect = () => {
    setConnectionAttempts(prev => prev + 1);
    addMessage(`🔄 Connection attempt #${connectionAttempts + 1}`, 'info');
    
    if (useMockServer) {
      // Use mock WebSocket for testing
      connectWithMockServer();
    } else {
      // Use real Django server
      websocketService.connect('ws://scanllmai.com/ws/guardrails/');
    }
  };

  const connectWithMockServer = () => {
    // Create mock WebSocket that responds to Django-like messages
    const mockWs = {
      readyState: 1, // OPEN
      send: (data) => {
        const message = JSON.parse(data);
        addMessage(`📤 Sent ${message.type}`, 'info', message);
        mockWebSocketServer.simulateResponse(mockWs, message);
      },
      close: () => {
        addMessage('Mock WebSocket closed', 'warning');
      }
    };

    // Override WebSocket send method
    mockWs.send = (data) => {
      try {
        const message = JSON.parse(data);
        addMessage(`📤 Sent to mock server: ${message.type}`, 'info', message);
        
        // Simulate server response
        setTimeout(() => {
          mockWebSocketServer.simulateResponse({
            send: (responseData) => {
              const response = JSON.parse(responseData);
              addMessage(`📨 Mock response: ${response.type}`, 'success', response);
              
              // Trigger the actual message handler
              websocketService.handleMessage(response);
            }
          }, message);
        }, 200 + Math.random() * 300);
      } catch (error) {
        addMessage(`❌ Error parsing message: ${error.message}`, 'error');
      }
    };

    // Simulate connection success
    setTimeout(() => {
      setIsConnected(true);
      addMessage('✅ Connected to mock WebSocket server', 'success');
      
      // Trigger connection handler
      if (websocketService.onConnectionChange) {
        websocketService.onConnectionChange(true);
      }
      
      // Set mock WebSocket
      websocketService.ws = mockWs;
      websocketService.isConnected = true;
      
      // Start periodic mock updates
      mockWebSocketServer.startPeriodicUpdates({
        send: (data) => {
          const message = JSON.parse(data);
          addMessage(`📨 Periodic update: ${message.type}`, 'info', message);
          websocketService.handleMessage(message);
        }
      });
      
    }, 1000);
  };

  const handleDisconnect = () => {
    websocketService.disconnect();
    mockWebSocketServer.stopPeriodicUpdates();
    setIsConnected(false);
    addMessage('🔌 Disconnected', 'warning');
  };

  const handleSendTestMessage = (type) => {
    switch (type) {
      case 'request_analytics':
        websocketService.requestAnalyticsData();
        break;
      case 'request_user_data':
        websocketService.requestUserData();
        break;
      case 'ping':
        websocketService.sendPing();
        break;
      case 'refresh':
        websocketService.requestRefresh();
        break;
    }
  };

  const clearMessages = () => {
    setMessages([]);
    addMessage('🧹 Messages cleared', 'info');
  };

  const getChipColor = (type) => {
    switch (type) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            🔧 WebSocket Debugger
          </Typography>
          
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Chip 
              label={isConnected ? 'Connected' : 'Disconnected'} 
              color={isConnected ? 'success' : 'error'}
              variant="filled"
            />
            <Typography variant="body2" color="text.secondary">
              Attempts: {connectionAttempts}
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={useMockServer}
                  onChange={(e) => setUseMockServer(e.target.checked)}
                />
              }
              label="Use Mock Server (for testing)"
            />
          </Box>

          <Box display="flex" gap={1} mb={2} flexWrap="wrap">
            <Button 
              variant="contained" 
              onClick={handleConnect}
              disabled={isConnected}
              size="small"
            >
              Connect
            </Button>
            <Button 
              variant="outlined" 
              onClick={handleDisconnect}
              disabled={!isConnected}
              size="small"
            >
              Disconnect
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleSendTestMessage('request_analytics')}
              disabled={!isConnected}
              size="small"
            >
              Request Analytics
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleSendTestMessage('request_user_data')}
              disabled={!isConnected}
              size="small"
            >
              Request Users
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => handleSendTestMessage('ping')}
              disabled={!isConnected}
              size="small"
            >
              Ping
            </Button>
            <Button 
              variant="text" 
              onClick={clearMessages}
              size="small"
            >
              Clear
            </Button>
          </Box>

          {useMockServer && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Mock server is enabled. This will simulate Django WebSocket responses for testing.
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📋 Message Log ({messages.length})
          </Typography>
          
          <List sx={{ maxHeight: 600, overflow: 'auto' }}>
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  <ListItem alignItems="flex-start">
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip 
                            label={message.timestamp} 
                            size="small" 
                            variant="outlined"
                          />
                          <Chip 
                            label={message.type} 
                            size="small" 
                            color={getChipColor(message.type)}
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2">
                            {message.content}
                          </Typography>
                          {message.data && (
                            <Box 
                              component="pre" 
                              sx={{ 
                                mt: 1, 
                                p: 1, 
                                bgcolor: 'grey.100', 
                                borderRadius: 1,
                                fontSize: '0.75rem',
                                overflow: 'auto',
                                maxHeight: 200
                              }}
                            >
                              {message.data}
                            </Box>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < messages.length - 1 && <Divider />}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {messages.length === 0 && (
              <ListItem>
                <ListItemText 
                  primary="No messages yet"
                  secondary="Connect to WebSocket and start testing"
                />
              </ListItem>
            )}
          </List>
        </CardContent>
      </Card>
      
      <DataInjector />
    </Box>
  );
};

export default WebSocketDebugger;