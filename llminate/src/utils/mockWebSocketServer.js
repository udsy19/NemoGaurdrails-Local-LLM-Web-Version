/**
 * Mock WebSocket Server for Testing Dashboard
 * Simulates Django Channels responses for debugging
 */

class MockWebSocketServer {
  constructor() {
    this.clients = new Set();
    this.isRunning = false;
    this.mockDataInterval = null;
  }

  // Mock Django response data
  getMockAnalyticsData() {
    return {
      type: 'analytics_data',
      timestamp: new Date().toISOString(),
      data: {
        total_requests: Math.floor(Math.random() * 1000) + 500,
        recent_events: [
          {
            id: 1,
            detection_type: 'pii',
            status: 'blocked',
            confidence: 0.95,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            user_id: 'user_123',
            ip_address: '192.168.1.100',
            message: 'PII data detected in request'
          },
          {
            id: 2,
            detection_type: 'prompt_injection',
            status: 'blocked',
            confidence: 0.87,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            user_id: 'user_456',
            ip_address: '192.168.1.101',
            message: 'Malicious prompt injection attempt'
          },
          {
            id: 3,
            detection_type: 'toxicity',
            status: 'allowed',
            confidence: 0.45,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            user_id: 'user_789',
            ip_address: '192.168.1.102',
            message: 'Low toxicity content'
          },
          {
            id: 4,
            detection_type: 'hate_speech',
            status: 'blocked',
            confidence: 0.92,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            user_id: 'user_321',
            ip_address: '192.168.1.103',
            message: 'Hate speech detected'
          },
          {
            id: 5,
            detection_type: 'privacy',
            status: 'blocked',
            confidence: 0.78,
            timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            user_id: 'user_654',
            ip_address: '192.168.1.104',
            message: 'Privacy violation attempt'
          }
        ],
        blocked_requests: Math.floor(Math.random() * 50) + 20,
        allowed_requests: Math.floor(Math.random() * 400) + 300,
        risk_metrics: {
          pii_detection: Math.floor(Math.random() * 20) + 5,
          prompt_injection: Math.floor(Math.random() * 15) + 3,
          toxicity: Math.floor(Math.random() * 30) + 10,
          hate_speech: Math.floor(Math.random() * 10) + 2,
          privacy_violations: Math.floor(Math.random() * 25) + 8
        }
      }
    };
  }

  getMockUserData() {
    return {
      type: 'user_data',
      timestamp: new Date().toISOString(),
      data: {
        overview_stats: {
          total_users: Math.floor(Math.random() * 100) + 50,
          high_risk_users: Math.floor(Math.random() * 10) + 2,
          medium_risk_users: Math.floor(Math.random() * 20) + 8,
          avg_risk_score: Math.random() * 100
        },
        users_list: [
          {
            user_id: 'user_123',
            ip_address: '192.168.1.100',
            risk_score: Math.floor(Math.random() * 100),
            total_requests: Math.floor(Math.random() * 200) + 50,
            blocked_percentage: Math.random() * 30,
            last_active: new Date(Date.now() - Math.random() * 86400000).toISOString()
          },
          {
            user_id: 'user_456',
            ip_address: '192.168.1.101',
            risk_score: Math.floor(Math.random() * 100),
            total_requests: Math.floor(Math.random() * 200) + 50,
            blocked_percentage: Math.random() * 30,
            last_active: new Date(Date.now() - Math.random() * 86400000).toISOString()
          },
          {
            user_id: 'user_789',
            ip_address: '192.168.1.102',
            risk_score: Math.floor(Math.random() * 100),
            total_requests: Math.floor(Math.random() * 200) + 50,
            blocked_percentage: Math.random() * 30,
            last_active: new Date(Date.now() - Math.random() * 86400000).toISOString()
          },
          {
            user_id: 'user_321',
            ip_address: '192.168.1.103',
            risk_score: Math.floor(Math.random() * 100),
            total_requests: Math.floor(Math.random() * 200) + 50,
            blocked_percentage: Math.random() * 30,
            last_active: new Date(Date.now() - Math.random() * 86400000).toISOString()
          },
          {
            user_id: 'user_654',
            ip_address: '192.168.1.104',
            risk_score: Math.floor(Math.random() * 100),
            total_requests: Math.floor(Math.random() * 200) + 50,
            blocked_percentage: Math.random() * 30,
            last_active: new Date(Date.now() - Math.random() * 86400000).toISOString()
          }
        ]
      }
    };
  }

  getMockDetectionEvent() {
    const types = ['pii', 'prompt_injection', 'toxicity', 'hate_speech', 'privacy'];
    const statuses = ['blocked', 'allowed'];
    
    return {
      type: 'detection_event',
      timestamp: new Date().toISOString(),
      data: {
        id: Math.floor(Math.random() * 10000),
        detection_type: types[Math.floor(Math.random() * types.length)],
        status: statuses[Math.floor(Math.random() * statuses.length)],
        confidence: Math.random(),
        user_id: `user_${Math.floor(Math.random() * 1000)}`,
        ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
        message: 'Real-time detection event',
        timestamp: new Date().toISOString()
      }
    };
  }

  // Simulate the Django WebSocket server responses
  simulateResponse(ws, message) {
    console.log('🔄 Mock server received:', message.type);
    
    setTimeout(() => {
      switch (message.type) {
        case 'client_connect':
          ws.send(JSON.stringify({
            type: 'connection_status',
            data: { status: 'connected', client_id: message.client_id },
            timestamp: new Date().toISOString()
          }));
          break;

        case 'request_analytics':
          ws.send(JSON.stringify(this.getMockAnalyticsData()));
          break;

        case 'request_user_data':
          ws.send(JSON.stringify(this.getMockUserData()));
          break;

        case 'dashboard_config':
          ws.send(JSON.stringify({
            type: 'dashboard_configured',
            data: { 
              dashboard_type: message.dashboard_type,
              update_frequency: message.update_frequency 
            },
            timestamp: new Date().toISOString()
          }));
          // Send initial data after configuration
          setTimeout(() => {
            if (message.dashboard_type === 'main') {
              ws.send(JSON.stringify(this.getMockAnalyticsData()));
            } else if (message.dashboard_type === 'user') {
              ws.send(JSON.stringify(this.getMockUserData()));
            }
          }, 500);
          break;

        case 'ping':
          ws.send(JSON.stringify({
            type: 'pong',
            timestamp: new Date().toISOString(),
            client_id: message.client_id
          }));
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    }, Math.random() * 500 + 100); // Random delay 100-600ms
  }

  // Start sending periodic updates
  startPeriodicUpdates(ws) {
    if (this.mockDataInterval) return;
    
    this.mockDataInterval = setInterval(() => {
      // Send random detection events
      if (Math.random() > 0.7) {
        ws.send(JSON.stringify(this.getMockDetectionEvent()));
      }
      
      // Send analytics updates every 15 seconds
      if (Math.random() > 0.8) {
        ws.send(JSON.stringify(this.getMockAnalyticsData()));
      }
      
      // Send user data updates every 30 seconds
      if (Math.random() > 0.9) {
        ws.send(JSON.stringify(this.getMockUserData()));
      }
    }, 5000); // Every 5 seconds
  }

  stopPeriodicUpdates() {
    if (this.mockDataInterval) {
      clearInterval(this.mockDataInterval);
      this.mockDataInterval = null;
    }
  }
}

export default new MockWebSocketServer();