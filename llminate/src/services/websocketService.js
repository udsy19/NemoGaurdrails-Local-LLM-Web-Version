/**
 * WebSocket Service for LLMinate Dashboard
 * Handles real-time communication with backend dashboard websocket manager
 * Implements message routing and reconnection logic from IMPLEMENTATION_MAP.md
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.messageHandlers = new Map();
    this.isConnected = false;
    this.reconnectInterval = 5000; // 5 seconds
    this.messageQueue = [];
    this.clientId = this.generateClientId();
    this.onConnectionChange = null;
  }

  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect(url = process.env.REACT_APP_WEBSOCKET_URL || 'ws://scanllmai.com/ws/guardrails/') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      console.log(`Connecting to WebSocket: ${url}`);
      this.ws = new WebSocket(url);
      
      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('✅ Connected to Django WebSocket:', url);
        console.log('🔗 Client ID:', this.clientId);
        this.onConnectionChange?.(true);
        
        // Process queued messages
        this.processMessageQueue();
        
        // Send initial connection message
        this.send({
          type: 'client_connect',
          client_id: this.clientId,
          dashboard_type: 'llminate',
          timestamp: new Date().toISOString()
        });
        
        // Send initial ping
        this.sendPing();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('📨 Received WebSocket message:', message.type, message);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Invalid message format:', error, event.data);
        }
      };

      this.ws.onclose = (event) => {
        this.isConnected = false;
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.onConnectionChange?.(false);
        
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * this.reconnectAttempts;
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  handleMessage(message) {
    console.log(`🔄 Handling message type: ${message.type}`);
    const handlers = this.messageHandlers.get(message.type);
    if (handlers && handlers.length > 0) {
      console.log(`🔄 Found ${handlers.length} handlers for ${message.type}`);
      handlers.forEach((handler, index) => {
        try {
          handler(message.data || message, message);
          console.log(`✅ Handler ${index + 1}/${handlers.length} succeeded for ${message.type}`);
        } catch (error) {
          console.error(`❌ Handler ${index + 1}/${handlers.length} failed for ${message.type}:`, error);
        }
      });
    } else {
      console.warn(`⚠️ No handlers for message type: ${message.type}`, message);
      console.log('Available message types:', Array.from(this.messageHandlers.keys()));
    }
  }

  subscribe(messageType, handler) {
    // Allow multiple handlers for the same message type
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    
    const handlers = this.messageHandlers.get(messageType);
    handlers.push(handler);
    console.log(`📝 Subscribed to ${messageType} (${handlers.length} handlers)`);
    
    // Return unsubscribe function
    return () => {
      const currentHandlers = this.messageHandlers.get(messageType);
      if (currentHandlers) {
        const index = currentHandlers.indexOf(handler);
        if (index > -1) {
          currentHandlers.splice(index, 1);
          console.log(`🗑️ Unsubscribed from ${messageType} (${currentHandlers.length} handlers remaining)`);
          
          // Remove the message type if no handlers remain
          if (currentHandlers.length === 0) {
            this.messageHandlers.delete(messageType);
          }
        }
      }
    };
  }

  unsubscribe(messageType) {
    this.messageHandlers.delete(messageType);
  }

  send(message) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        this.queueMessage(message);
        return false;
      }
    } else {
      console.warn('WebSocket not connected, message queued');
      this.queueMessage(message);
      return false;
    }
  }

  queueMessage(message) {
    this.messageQueue.push(message);
    
    // Limit queue size to prevent memory issues
    if (this.messageQueue.length > 100) {
      this.messageQueue.shift(); // Remove oldest message
    }
  }

  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (!this.send(message)) {
        // If send fails, put it back at the front
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  // Dashboard-specific methods

  configureDashboard(dashboard, updateFrequency = 15) {
    this.send({
      type: 'dashboard_config',
      dashboard_type: dashboard,
      update_frequency: updateFrequency,
      client_id: this.clientId
    });
  }

  requestUserDetail(userId) {
    this.send({
      type: 'request_user_detail',
      user_id: userId,
      client_id: this.clientId
    });
  }

  requestRefresh() {
    this.send({
      type: 'refresh_request',
      timestamp: new Date().toISOString(),
      client_id: this.clientId
    });
  }

  sendPing() {
    this.send({
      type: 'ping',
      timestamp: new Date().toISOString(),
      client_id: this.clientId
    });
  }

  // Request analytics data from guardrails
  requestAnalyticsData(timeframe = '24h') {
    this.send({
      type: 'request_analytics',
      timeframe: timeframe,
      client_id: this.clientId
    });
  }

  // Request user data 
  requestUserData(userId = null, timeframe = '24h') {
    this.send({
      type: 'request_user_data',
      user_id: userId,
      timeframe: timeframe,
      client_id: this.clientId
    });
  }

  // Cleanup method
  disconnect() {
    this.isConnected = false;
    this.messageHandlers.clear();
    this.messageQueue = [];
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService;