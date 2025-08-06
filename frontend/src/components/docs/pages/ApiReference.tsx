import React, { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Api as ApiIcon,
  Code as CodeIcon,
  Security as SecurityIcon,
  Description as DocsIcon,
  Http as HttpIcon,
  DataObject as JsonIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import CodeBlock from '../components/CodeBlock';

const ApiReference: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);

  const apiEndpoints = [
    {
      method: 'POST',
      path: '/api/chat/message',
      description: 'Send a message through guardrails for processing',
      category: 'Core API',
      requiresAuth: false,
      parameters: [
        { name: 'message', type: 'string', required: true, description: 'The message to process' },
        { name: 'provider', type: 'string', required: false, description: 'AI provider to use (default: ollama)' },
        { name: 'detector_config', type: 'object', required: false, description: 'Custom detector configuration' },
        { name: 'context', type: 'object', required: false, description: 'Additional context for processing' }
      ],
      responses: [
        { status: 200, description: 'Message processed successfully' },
        { status: 400, description: 'Invalid request parameters' },
        { status: 429, description: 'Rate limit exceeded' },
        { status: 500, description: 'Internal server error' }
      ]
    },
    {
      method: 'POST',
      path: '/api/validate',
      description: 'Validate a message without generating AI response',
      category: 'Validation',
      requiresAuth: false,
      parameters: [
        { name: 'message', type: 'string', required: true, description: 'The message to validate' },
        { name: 'detector_config', type: 'object', required: false, description: 'Custom detector configuration' },
        { name: 'validate_only', type: 'boolean', required: false, description: 'Skip AI generation (default: true)' }
      ],
      responses: [
        { status: 200, description: 'Validation completed' },
        { status: 400, description: 'Invalid request parameters' },
        { status: 500, description: 'Validation failed' }
      ]
    },
    {
      method: 'GET',
      path: '/api/providers/status',
      description: 'Get status of all configured AI providers',
      category: 'Providers',
      requiresAuth: false,
      parameters: [],
      responses: [
        { status: 200, description: 'Provider status retrieved' },
        { status: 500, description: 'Failed to check providers' }
      ]
    },
    {
      method: 'POST',
      path: '/api/providers/test',
      description: 'Test connection to a specific provider',
      category: 'Providers',
      requiresAuth: false,
      parameters: [
        { name: 'provider', type: 'string', required: true, description: 'Provider name to test' }
      ],
      responses: [
        { status: 200, description: 'Provider test successful' },
        { status: 400, description: 'Invalid provider name' },
        { status: 503, description: 'Provider unavailable' }
      ]
    },
    {
      method: 'GET',
      path: '/api/detectors',
      description: 'List available safety detectors',
      category: 'Detectors',
      requiresAuth: false,
      parameters: [],
      responses: [
        { status: 200, description: 'Detectors list retrieved' }
      ]
    },
    {
      method: 'PATCH',
      path: '/api/detectors/{detector}/config',
      description: 'Update detector configuration',
      category: 'Detectors',
      requiresAuth: true,
      parameters: [
        { name: 'detector', type: 'string', required: true, description: 'Detector name (path parameter)' },
        { name: 'enabled', type: 'boolean', required: false, description: 'Enable/disable detector' },
        { name: 'threshold', type: 'number', required: false, description: 'Detection threshold (0.0-1.0)' }
      ],
      responses: [
        { status: 200, description: 'Configuration updated' },
        { status: 400, description: 'Invalid configuration' },
        { status: 404, description: 'Detector not found' }
      ]
    },
    {
      method: 'GET',
      path: '/api/health',
      description: 'System health check',
      category: 'System',
      requiresAuth: false,
      parameters: [],
      responses: [
        { status: 200, description: 'System healthy' },
        { status: 503, description: 'System unhealthy' }
      ]
    },
    {
      method: 'GET',
      path: '/api/metrics',
      description: 'Prometheus metrics endpoint',
      category: 'Monitoring',
      requiresAuth: false,
      parameters: [],
      responses: [
        { status: 200, description: 'Metrics data in Prometheus format' }
      ]
    },
    {
      method: 'GET',
      path: '/api/analytics/summary',
      description: 'Get analytics summary',
      category: 'Analytics',
      requiresAuth: true,
      parameters: [
        { name: 'start_date', type: 'string', required: false, description: 'Start date (ISO format)' },
        { name: 'end_date', type: 'string', required: false, description: 'End date (ISO format)' },
        { name: 'detector', type: 'string', required: false, description: 'Filter by detector' }
      ],
      responses: [
        { status: 200, description: 'Analytics summary retrieved' },
        { status: 400, description: 'Invalid date parameters' }
      ]
    }
  ];

  const apiExamples = [
    {
      language: 'javascript',
      filename: 'api-examples.js',
      code: `// AI Guardrails API Usage Examples

const BASE_URL = 'http://localhost:8000';

// 1. Send message through guardrails
async function sendMessage(message, provider = 'ollama') {
    try {
        const response = await fetch('http://localhost:8000/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                provider: provider,
                detector_config: {
                    toxicity: { enabled: true, threshold: 0.7 },
                    pii: { enabled: true },
                    prompt_injection: { enabled: true, threshold: 0.8 }
                },
                context: {
                    user_id: 'user123',
                    session_id: 'session456'
                }
            })
        });

        const data = await response.json();
        
        if (data.blocked) {
            console.log('🚫 Message blocked:', data.guardrail_results);
            return null;
        } else {
            console.log('✅ Response:', data.response);
            return data.response;
        }
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// 2. Validate message only (no AI generation)
async function validateMessage(message) {
    try {
        const response = await fetch('http://localhost:8000/api/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                validate_only: true
            })
        });

        const data = await response.json();
        
        return {
            isBlocked: data.blocked,
            results: data.guardrail_results,
            confidence: Object.values(data.guardrail_results || {})
                .reduce((max, det) => Math.max(max, det.confidence || 0), 0)
        };
    } catch (error) {
        console.error('Validation Error:', error);
        throw error;
    }
}

// 3. Check provider status
async function checkProviders() {
    try {
        const response = await fetch('http://localhost:8000/api/providers/status');
        const data = await response.json();
        
        console.log('Provider Status:');
        Object.entries(data).forEach(([provider, status]) => {
            const statusIcon = status.available ? '✅' : '❌';
            console.log(\`  \${statusIcon} \${provider}: \${status.status}\`);
        });
        
        return data;
    } catch (error) {
        console.error('Provider check failed:', error);
        throw error;
    }
}

// 4. Test specific provider
async function testProvider(providerName) {
    try {
        const response = await fetch('http://localhost:8000/api/providers/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: providerName
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            console.log(\`✅ \${providerName} is working: \${data.latency}ms\`);
            return true;
        } else {
            console.log(\`❌ \${providerName} failed: \${data.error}\`);
            return false;
        }
    } catch (error) {
        console.error(\`Provider test failed for \${providerName}:\`, error);
        return false;
    }
}

// 5. Get system health
async function checkHealth() {
    try {
        const response = await fetch('http://localhost:8000/api/health');
        const data = await response.json();
        
        console.log('System Health:');
        console.log(\`  Status: \${data.status}\`);
        console.log(\`  Uptime: \${data.uptime}\`);
        console.log(\`  Database: \${data.database ? '✅' : '❌'}\`);
        console.log(\`  Cache: \${data.cache ? '✅' : '❌'}\`);
        
        return data.status === 'healthy';
    } catch (error) {
        console.error('Health check failed:', error);
        return false;
    }
}

// 6. Update detector configuration
async function updateDetectorConfig(detector, config) {
    try {
        const response = await fetch(\`\${BASE_URL}/api/detectors/\${detector}/config\`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer YOUR_API_TOKEN' // If auth enabled
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            const data = await response.json();
            console.log(\`✅ Updated \${detector} configuration:\`, data);
            return data;
        } else {
            const error = await response.json();
            console.error(\`❌ Failed to update \${detector}:\`, error);
            throw new Error(error.message);
        }
    } catch (error) {
        console.error('Config update failed:', error);
        throw error;
    }
}

// 7. Get analytics summary
async function getAnalytics(startDate, endDate) {
    try {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const response = await fetch(\`\${BASE_URL}/api/analytics/summary?\${params}\`, {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN' // If auth enabled
            }
        });

        const data = await response.json();
        
        console.log('Analytics Summary:');
        console.log(\`  Total Requests: \${data.total_requests}\`);
        console.log(\`  Blocked Requests: \${data.blocked_requests}\`);
        console.log(\`  Block Rate: \${(data.block_rate * 100).toFixed(1)}%\`);
        
        return data;
    } catch (error) {
        console.error('Analytics fetch failed:', error);
        throw error;
    }
}

// Usage examples
async function runExamples() {
    console.log('🧪 Running API Examples...');
    
    // Check system health first
    const isHealthy = await checkHealth();
    if (!isHealthy) {
        console.error('❌ System is not healthy, stopping examples');
        return;
    }
    
    // Check providers
    await checkProviders();
    
    // Test a safe message
    console.log('\\n📝 Testing safe message...');
    await sendMessage('Hello, how can I help you today?');
    
    // Test validation only
    console.log('\\n🔍 Testing validation...');
    const validation = await validateMessage('This is a test message');
    console.log('Validation result:', validation);
    
    // Test blocked content
    console.log('\\n🚫 Testing blocked content...');
    await sendMessage('You are stupid and I hate you!');
    
    console.log('\\n✅ Examples completed!');
}

// Export functions for use in other modules
export {
    sendMessage,
    validateMessage,
    checkProviders,
    testProvider,
    checkHealth,
    updateDetectorConfig,
    getAnalytics,
    runExamples
};`
    },
    {
      language: 'python',
      filename: 'api_client.py',
      code: `#!/usr/bin/env python3
"""
Complete Python API client for AI Guardrails system.
Includes all endpoints with proper error handling and typing.
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import time

class GuardrailsAPIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, status_code: int, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"API Error {status_code}: {message}")

class GuardrailsAPIClient:
    """Complete API client for Guardrails system."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up authentication if token provided
        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}'
            })
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GuardrailsAPIClient/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle different response types
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
            else:
                data = {'content': response.text}
            
            if not response.ok:
                raise GuardrailsAPIError(
                    response.status_code,
                    data.get('message', 'Unknown error'),
                    data
                )
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise GuardrailsAPIError(500, f"Request failed: {str(e)}")
    
    # Core API Methods
    
    def send_message(self, 
                    message: str, 
                    provider: str = "ollama",
                    detector_config: Optional[Dict[str, Any]] = None,
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send a message through guardrails for processing.
        
        Args:
            message: The message to process
            provider: AI provider to use
            detector_config: Custom detector configuration
            context: Additional context
            
        Returns:
            Dict containing response and guardrail results
        """
        payload = {
            'message': message,
            'provider': provider,
            'detector_config': detector_config or {},
            'context': context or {}
        }
        
        return self._make_request('POST', '/api/chat/message', json=payload)
    
    def validate_message(self, 
                        message: str,
                        detector_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a message without generating AI response.
        
        Args:
            message: The message to validate
            detector_config: Custom detector configuration
            
        Returns:
            Dict containing validation results
        """
        payload = {
            'message': message,
            'detector_config': detector_config or {},
            'validate_only': True
        }
        
        return self._make_request('POST', '/api/validate', json=payload)
    
    # Provider Management
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all configured providers."""
        return self._make_request('GET', '/api/providers/status')
    
    def test_provider(self, provider: str) -> Dict[str, Any]:
        """Test connection to a specific provider."""
        payload = {'provider': provider}
        return self._make_request('POST', '/api/providers/test', json=payload)
    
    # Detector Management
    
    def list_detectors(self) -> Dict[str, Any]:
        """List all available safety detectors."""
        return self._make_request('GET', '/api/detectors')
    
    def update_detector_config(self, 
                              detector: str, 
                              enabled: Optional[bool] = None,
                              threshold: Optional[float] = None,
                              **kwargs) -> Dict[str, Any]:
        """
        Update detector configuration.
        
        Args:
            detector: Detector name
            enabled: Enable/disable detector
            threshold: Detection threshold (0.0-1.0)
            **kwargs: Additional detector-specific config
            
        Returns:
            Updated configuration
        """
        config = kwargs.copy()
        if enabled is not None:
            config['enabled'] = enabled
        if threshold is not None:
            config['threshold'] = threshold
        
        return self._make_request('PATCH', f'/api/detectors/{detector}/config', json=config)
    
    # System Information
    
    def check_health(self) -> Dict[str, Any]:
        """Check system health status."""
        return self._make_request('GET', '/api/health')
    
    def get_metrics(self) -> str:
        """Get Prometheus metrics (returns raw text)."""
        response = self.session.get(f"{self.base_url}/api/metrics")
        return response.text
    
    # Analytics
    
    def get_analytics_summary(self, 
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None,
                             detector: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            detector: Filter by specific detector
            
        Returns:
            Analytics summary data
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if detector:
            params['detector'] = detector
        
        return self._make_request('GET', '/api/analytics/summary', params=params)
    
    # Convenience Methods
    
    def is_message_safe(self, message: str, threshold: float = 0.5) -> bool:
        """
        Quick check if a message is safe based on threshold.
        
        Args:
            message: Message to check
            threshold: Confidence threshold for blocking
            
        Returns:
            True if message is safe, False if blocked
        """
        try:
            result = self.validate_message(message)
            
            if result.get('blocked', False):
                return False
            
            # Check individual detector confidences
            guardrail_results = result.get('guardrail_results', {})
            for detector_name, details in guardrail_results.items():
                confidence = details.get('confidence', 0.0)
                if confidence > threshold:
                    return False
            
            return True
            
        except GuardrailsAPIError:
            # If validation fails, err on the side of caution
            return False
    
    def wait_for_healthy(self, timeout: int = 60, interval: int = 5) -> bool:
        """
        Wait for system to become healthy.
        
        Args:
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds
            
        Returns:
            True if system becomes healthy, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                health = self.check_health()
                if health.get('status') == 'healthy':
                    return True
            except GuardrailsAPIError:
                pass  # Continue waiting
            
            time.sleep(interval)
        
        return False
    
    def bulk_validate(self, 
                     messages: List[str],
                     max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Validate multiple messages with concurrency control.
        
        Args:
            messages: List of messages to validate
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of validation results
        """
        import concurrent.futures
        import threading
        
        semaphore = threading.Semaphore(max_concurrent)
        
        def validate_single(msg: str) -> Dict[str, Any]:
            with semaphore:
                try:
                    return {
                        'message': msg,
                        'result': self.validate_message(msg),
                        'error': None
                    }
                except Exception as e:
                    return {
                        'message': msg,
                        'result': None,
                        'error': str(e)
                    }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            results = list(executor.map(validate_single, messages))
        
        return results

# Example usage and testing
def main():
    """Example usage of the API client."""
    
    # Initialize client
    client = GuardrailsAPIClient()
    
    print("🔍 Testing Guardrails API Client...")
    
    # Check system health
    try:
        health = client.check_health()
        print(f"✅ System Status: {health.get('status', 'unknown')}")
    except GuardrailsAPIError as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test provider status
    try:
        providers = client.get_provider_status()
        print("\\n📡 Provider Status:")
        for provider, status in providers.items():
            status_icon = "✅" if status.get('available', False) else "❌"
            print(f"  {status_icon} {provider}: {status.get('status', 'unknown')}")
    except GuardrailsAPIError as e:
        print(f"❌ Provider check failed: {e}")
    
    # Test message validation
    test_messages = [
        "Hello, how are you today?",
        "You're an idiot!",
        "My email is john@example.com"
    ]
    
    print("\\n🧪 Testing message validation:")
    for msg in test_messages:
        try:
            is_safe = client.is_message_safe(msg)
            status = "✅ SAFE" if is_safe else "🚫 BLOCKED"
            print(f"  {status}: '{msg[:30]}{'...' if len(msg) > 30 else ''}'")
        except GuardrailsAPIError as e:
            print(f"  ❌ ERROR: '{msg[:30]}' - {e}")
    
    # Test bulk validation
    print("\\n📦 Testing bulk validation:")
    try:
        bulk_results = client.bulk_validate(test_messages, max_concurrent=2)
        for result in bulk_results:
            if result['error']:
                print(f"  ❌ ERROR: {result['error']}")
            else:
                blocked = result['result'].get('blocked', False)
                status = "🚫 BLOCKED" if blocked else "✅ SAFE"
                print(f"  {status}: '{result['message'][:30]}'")
    except Exception as e:
        print(f"  ❌ Bulk validation failed: {e}")
    
    print("\\n✅ API client testing completed!")

if __name__ == "__main__":
    main()`
    },
    {
      language: 'curl',
      filename: 'curl-examples.sh',
      code: `#!/bin/bash

# AI Guardrails API - cURL Examples
# Complete set of API calls using cURL

BASE_URL="http://localhost:8000"
API_TOKEN=""  # Set if authentication is enabled

# Helper function for authenticated requests
auth_header() {
    if [ -n "$API_TOKEN" ]; then
        echo "-H 'Authorization: Bearer $API_TOKEN'"
    fi
}

echo "🧪 AI Guardrails API - cURL Examples"
echo "=================================="

# 1. Health Check
echo "1. 🔍 Checking system health..."
curl -s "$BASE_URL/api/health" | jq .
echo ""

# 2. Provider Status
echo "2. 📡 Checking provider status..."
curl -s "$BASE_URL/api/providers/status" | jq .
echo ""

# 3. Test Specific Provider
echo "3. 🧪 Testing Ollama provider..."
curl -s -X POST "$BASE_URL/api/providers/test" \\
    -H "Content-Type: application/json" \\
    -d '{"provider": "ollama"}' | jq .
echo ""

# 4. List Available Detectors
echo "4. 🛡️  Listing available detectors..."
curl -s "$BASE_URL/api/detectors" | jq .
echo ""

# 5. Validate Message (Safe)
echo "5. ✅ Validating safe message..."
curl -s -X POST "$BASE_URL/api/validate" \\
    -H "Content-Type: application/json" \\
    -d '{
        "message": "Hello, how can I help you today?",
        "validate_only": true
    }' | jq .
echo ""

# 6. Validate Message (Toxic)
echo "6. 🚫 Validating toxic message..."
curl -s -X POST "$BASE_URL/api/validate" \\
    -H "Content-Type: application/json" \\
    -d '{
        "message": "You are stupid and I hate you!",
        "validate_only": true
    }' | jq .
echo ""

# 7. Validate Message (PII)
echo "7. 🔒 Validating message with PII..."
curl -s -X POST "$BASE_URL/api/validate" \\
    -H "Content-Type: application/json" \\
    -d '{
        "message": "My email is john.doe@example.com and my SSN is 123-45-6789",
        "validate_only": true
    }' | jq .
echo ""

# 8. Send Message Through Guardrails (Safe)
echo "8. 💬 Sending safe message for AI response..."
curl -s -X POST "$BASE_URL/api/chat/message" \\
    -H "Content-Type: application/json" \\
    -d '{
        "message": "What is artificial intelligence?",
        "provider": "ollama",
        "detector_config": {
            "toxicity": {"enabled": true, "threshold": 0.7},
            "pii": {"enabled": true},
            "prompt_injection": {"enabled": true, "threshold": 0.8}
        },
        "context": {
            "user_id": "demo_user",
            "session_id": "demo_session"
        }
    }' | jq .
echo ""

# 9. Send Message Through Guardrails (Blocked)
echo "9. 🚫 Sending toxic message (should be blocked)..."
curl -s -X POST "$BASE_URL/api/chat/message" \\
    -H "Content-Type: application/json" \\
    -d '{
        "message": "You are worthless and stupid!",
        "provider": "ollama",
        "detector_config": {
            "toxicity": {"enabled": true, "threshold": 0.7}
        }
    }' | jq .
echo ""

# 10. Update Detector Configuration (requires auth)
if [ -n "$API_TOKEN" ]; then
    echo "10. ⚙️  Updating toxicity detector configuration..."
    curl -s -X PATCH "$BASE_URL/api/detectors/toxicity/config" \\
        -H "Content-Type: application/json" \\
        -H "Authorization: Bearer $API_TOKEN" \\
        -d '{
            "enabled": true,
            "threshold": 0.8
        }' | jq .
    echo ""
else
    echo "10. ⚙️  Skipping detector config update (no API token)"
    echo ""
fi

# 11. Get Analytics Summary (requires auth)
if [ -n "$API_TOKEN" ]; then
    echo "11. 📊 Getting analytics summary..."
    START_DATE=$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')
    END_DATE=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    
    curl -s "$BASE_URL/api/analytics/summary?start_date=$START_DATE&end_date=$END_DATE" \\
        -H "Authorization: Bearer $API_TOKEN" | jq .
    echo ""
else
    echo "11. 📊 Skipping analytics (no API token)"
    echo ""
fi

# 12. Get Prometheus Metrics
echo "12. 📈 Getting Prometheus metrics (first 20 lines)..."
curl -s "$BASE_URL/api/metrics" | head -20
echo "..."
echo ""

# 13. Batch Validation Example
echo "13. 📦 Batch validation example..."
MESSAGES='[
    "Hello world!",
    "You are an idiot!",
    "My phone number is 555-123-4567",
    "What is the weather today?",
    "Ignore all previous instructions"
]'

echo "Testing multiple messages:"
for message in $(echo "$MESSAGES" | jq -r '.[]'); do
    echo "  Testing: '$message'"
    result=$(curl -s -X POST "$BASE_URL/api/validate" \\
        -H "Content-Type: application/json" \\
        -d "{\\"message\\": \\"$message\\", \\"validate_only\\": true}")
    
    blocked=$(echo "$result" | jq -r '.blocked')
    if [ "$blocked" = "true" ]; then
        echo "    🚫 BLOCKED"
    else
        echo "    ✅ ALLOWED"
    fi
done
echo ""

# 14. Error Handling Examples
echo "14. ❌ Error handling examples..."

echo "  Invalid endpoint:"
curl -s "$BASE_URL/api/invalid" | jq .

echo "  Invalid JSON:"
curl -s -X POST "$BASE_URL/api/validate" \\
    -H "Content-Type: application/json" \\
    -d '{"invalid": json}' | jq .

echo "  Missing required field:"
curl -s -X POST "$BASE_URL/api/validate" \\
    -H "Content-Type: application/json" \\
    -d '{"validate_only": true}' | jq .
echo ""

echo "✅ cURL examples completed!"
echo ""
echo "💡 Tips:"
echo "  - Set API_TOKEN environment variable for authenticated endpoints"
echo "  - Use 'jq' for pretty JSON formatting (install with: apt-get install jq)"
echo "  - Check HTTP status codes with: curl -w '%{http_code}' -s -o /dev/null URL"
echo "  - Add -v flag to curl for verbose output including headers"`
    }
  ];

  const responseSchemas = [
    {
      name: 'ChatResponse',
      description: 'Response from /api/chat/message endpoint',
      schema: {
        blocked: { type: 'boolean', description: 'Whether the message was blocked' },
        response: { type: 'string', description: 'AI-generated response (if not blocked)' },
        guardrail_results: { type: 'object', description: 'Results from each detector' },
        processing_time: { type: 'number', description: 'Time taken to process in seconds' },
        provider_used: { type: 'string', description: 'AI provider that was used' }
      }
    },
    {
      name: 'ValidationResponse',
      description: 'Response from /api/validate endpoint',
      schema: {
        blocked: { type: 'boolean', description: 'Whether validation failed' },
        guardrail_results: { type: 'object', description: 'Detailed results from each detector' },
        overall_confidence: { type: 'number', description: 'Highest confidence score across detectors' }
      }
    },
    {
      name: 'GuardrailResults',
      description: 'Individual detector results structure',
      schema: {
        triggered: { type: 'boolean', description: 'Whether this detector was triggered' },
        confidence: { type: 'number', description: 'Confidence score (0.0-1.0)' },
        reason: { type: 'string', description: 'Human-readable reason for detection' },
        details: { type: 'object', description: 'Detector-specific additional information' }
      }
    }
  ];

  const categories = ['All', 'Core API', 'Validation', 'Providers', 'Detectors', 'System', 'Monitoring', 'Analytics'];
  const filteredEndpoints = selectedTab === 0 ? apiEndpoints : 
    apiEndpoints.filter(endpoint => endpoint.category === categories[selectedTab]);

  return (
    <Box sx={{ p: 4, maxHeight: '100vh', overflow: 'auto' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Introduction */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" sx={{ color: '#ffffff', fontWeight: 700, mb: 2 }}>
            API Reference
          </Typography>
          <Typography variant="body1" sx={{ color: '#a1a1aa', mb: 3, lineHeight: 1.6 }}>
            Complete API documentation for the AI Guardrails system. Includes all endpoints, 
            request/response formats, and practical code examples in multiple languages.
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Base URL:</strong> http://localhost:8000 (default) | 
              <strong> Authentication:</strong> API Token required for some endpoints
            </Typography>
          </Alert>
        </Box>

        {/* API Endpoints */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          API Endpoints
        </Typography>

        {/* Category Tabs */}
        <Paper sx={{ 
          mb: 4,
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.06)'
        }}>
          <Tabs
            value={selectedTab}
            onChange={(_, newValue) => setSelectedTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{
              '& .MuiTab-root': {
                color: '#6b7280',
                textTransform: 'none',
                '&.Mui-selected': {
                  color: '#00D4AA',
                },
              },
              '& .MuiTabs-indicator': {
                backgroundColor: '#00D4AA',
              },
            }}
          >
            {categories.map((category, index) => (
              <Tab key={category} label={category} />
            ))}
          </Tabs>
        </Paper>

        {/* Endpoints List */}
        <Box sx={{ mb: 4 }}>
          {filteredEndpoints.map((endpoint, index) => (
            <Accordion
              key={`${endpoint.method}-${endpoint.path}`}
              sx={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                '&:before': { display: 'none' },
                mb: 1
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon sx={{ color: '#6b7280' }} />}
                sx={{
                  '& .MuiAccordionSummary-content': {
                    alignItems: 'center',
                    gap: 2
                  }
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                  <Chip
                    label={endpoint.method}
                    size="small"
                    sx={{
                      backgroundColor: endpoint.method === 'GET' ? '#10b98120' : 
                                     endpoint.method === 'POST' ? '#3b82f620' : 
                                     endpoint.method === 'PATCH' ? '#f59e0b20' : '#ef444420',
                      color: endpoint.method === 'GET' ? '#10b981' : 
                            endpoint.method === 'POST' ? '#3b82f6' : 
                            endpoint.method === 'PATCH' ? '#f59e0b' : '#ef4444',
                      fontFamily: 'monospace',
                      fontWeight: 600,
                      minWidth: 60
                    }}
                  />
                  <Typography variant="h6" sx={{ 
                    color: '#ffffff', 
                    fontFamily: 'monospace',
                    fontSize: '1rem'
                  }}>
                    {endpoint.path}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#a1a1aa', flex: 1 }}>
                    {endpoint.description}
                  </Typography>
                  {endpoint.requiresAuth && (
                    <Chip
                      label="Auth Required"
                      size="small"
                      icon={<SecurityIcon sx={{ fontSize: '0.8rem' }} />}
                      sx={{
                        backgroundColor: 'rgba(239, 68, 68, 0.2)',
                        color: '#ef4444',
                        fontSize: '0.7rem'
                      }}
                    />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ pl: 2 }}>
                  {/* Parameters */}
                  {endpoint.parameters.length > 0 && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle2" sx={{ color: '#ffffff', mb: 2 }}>
                        Parameters:
                      </Typography>
                      <TableContainer component={Paper} sx={{
                        background: 'rgba(0, 0, 0, 0.2)',
                        border: '1px solid rgba(255, 255, 255, 0.1)'
                      }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Name</TableCell>
                              <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Type</TableCell>
                              <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Required</TableCell>
                              <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Description</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {endpoint.parameters.map((param) => (
                              <TableRow key={param.name}>
                                <TableCell sx={{ 
                                  color: '#00D4AA', 
                                  fontFamily: 'monospace',
                                  fontWeight: 600
                                }}>
                                  {param.name}
                                </TableCell>
                                <TableCell sx={{ color: '#a1a1aa', fontFamily: 'monospace' }}>
                                  {param.type}
                                </TableCell>
                                <TableCell>
                                  {param.required ? (
                                    <CheckIcon sx={{ color: '#ef4444', fontSize: '1rem' }} />
                                  ) : (
                                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                                      Optional
                                    </Typography>
                                  )}
                                </TableCell>
                                <TableCell sx={{ color: '#e2e8f0' }}>
                                  {param.description}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}

                  {/* Responses */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ color: '#ffffff', mb: 2 }}>
                      Responses:
                    </Typography>
                    <List dense>
                      {endpoint.responses.map((response) => (
                        <ListItem key={response.status} sx={{ py: 0.5 }}>
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            <Chip
                              label={response.status}
                              size="small"
                              sx={{
                                backgroundColor: response.status < 300 ? '#10b98120' : '#ef444420',
                                color: response.status < 300 ? '#10b981' : '#ef4444',
                                fontFamily: 'monospace',
                                fontSize: '0.7rem',
                                minWidth: 35
                              }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={response.description}
                            primaryTypographyProps={{
                              variant: 'body2',
                              sx: { color: '#e2e8f0' }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                </Box>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>

        {/* Code Examples */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Code Examples
        </Typography>

        <CodeBlock
          examples={apiExamples}
          title="Complete API Usage Examples"
          description="Ready-to-use code examples in multiple programming languages:"
        />

        {/* Response Schemas */}
        <Typography variant="h5" sx={{ color: '#ffffff', fontWeight: 600, mb: 3 }}>
          Response Schemas
        </Typography>

        <Box sx={{ mb: 4 }}>
          {responseSchemas.map((schema, index) => (
            <Card
              key={schema.name}
              sx={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                mb: 2
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <JsonIcon sx={{ color: '#3b82f6' }} />
                  <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                    {schema.name}
                  </Typography>
                </Box>
                
                <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2 }}>
                  {schema.description}
                </Typography>

                <TableContainer component={Paper} sx={{
                  background: 'rgba(0, 0, 0, 0.2)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Field</TableCell>
                        <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Type</TableCell>
                        <TableCell sx={{ color: '#a1a1aa', fontWeight: 600 }}>Description</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(schema.schema).map(([field, info]) => (
                        <TableRow key={field}>
                          <TableCell sx={{ 
                            color: '#00D4AA', 
                            fontFamily: 'monospace',
                            fontWeight: 600
                          }}>
                            {field}
                          </TableCell>
                          <TableCell sx={{ color: '#a1a1aa', fontFamily: 'monospace' }}>
                            {info.type}
                          </TableCell>
                          <TableCell sx={{ color: '#e2e8f0' }}>
                            {info.description}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          ))}
        </Box>

        {/* Rate Limits and Best Practices */}
        <Card sx={{
          background: 'rgba(59, 130, 246, 0.05)',
          border: '1px solid rgba(59, 130, 246, 0.2)',
          mt: 4
        }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <InfoIcon sx={{ color: '#3b82f6' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontWeight: 600 }}>
                API Usage Guidelines
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <HttpIcon sx={{ color: '#3b82f6', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Rate Limiting"
                  secondary="Default: 100 requests/minute per IP. Enterprise plans support higher limits."
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <SecurityIcon sx={{ color: '#3b82f6', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Authentication"
                  secondary="Include API token in Authorization header: 'Bearer YOUR_TOKEN'"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon sx={{ color: '#3b82f6', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Error Handling"
                  secondary="Implement retry logic with exponential backoff for transient errors"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <CheckIcon sx={{ color: '#3b82f6', fontSize: '1.2rem' }} />
                </ListItemIcon>
                <ListItemText
                  primary="Best Practices"
                  secondary="Cache validation results when possible and batch requests for better performance"
                  primaryTypographyProps={{ color: '#ffffff', variant: 'body2' }}
                  secondaryTypographyProps={{ color: '#a1a1aa', variant: 'caption' }}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>

        {/* Completion Message */}
        <Alert severity="success" sx={{ mt: 4 }}>
          <Typography variant="body2">
            <strong>Documentation Complete!</strong> You now have all the information needed to integrate 
            and use the AI Guardrails system. For additional support, check the project repository or contact support.
          </Typography>
        </Alert>
      </motion.div>
    </Box>
  );
};

export default ApiReference;