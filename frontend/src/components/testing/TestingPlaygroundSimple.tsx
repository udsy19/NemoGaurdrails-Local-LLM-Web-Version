import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  LinearProgress,
} from '@mui/material';
import { Play, TestTube } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface TestResult {
  id: string;
  timestamp: string;
  message: string;
  response: string;
  blocked: boolean;
  blockingReasons: string[];
  responseTime: number;
}

const TestingPlaygroundSimple: React.FC = () => {
  const [testMessage, setTestMessage] = useState('Hello, how are you?');
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);

  const runTest = async () => {
    if (!testMessage.trim()) {
      toast.error('Please enter a test message');
      return;
    }

    setIsLoading(true);
    setApiError(null);
    const startTime = performance.now();
    
    try {
      console.log('Sending test request:', { message: testMessage });

      const response = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: testMessage,
          session_id: `test_${Date.now()}`,
        }),
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        setApiError(`HTTP ${response.status}: ${errorText}`);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      console.log('Response data:', result);
      
      const responseTime = performance.now() - startTime;
      
      const testResult: TestResult = {
        id: `test_${Date.now()}`,
        timestamp: new Date().toISOString(),
        message: testMessage,
        response: result.response || 'No response received',
        blocked: result.blocked || false,
        blockingReasons: result.blocking_reasons || [],
        responseTime: responseTime,
      };

      setTestResults(prev => [testResult, ...prev]);
      toast.success('Test completed successfully!');
      setApiError(null);
    } catch (error) {
      console.error('Test error:', error);
      setApiError((error as Error).message);
      toast.error('Test failed: ' + (error as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const testApiConnection = async () => {
    try {
      console.log('Testing API connection...');
      setApiError(null);
      
      const response = await fetch('http://localhost:8000/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'Test connection',
          session_id: 'test_connection',
        }),
      });
      
      console.log('API test response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('API test result:', result);
        toast.success('API connection successful!');
        setApiError(null);
      } else {
        const errorText = await response.text();
        console.error('API test error:', errorText);
        setApiError(`API test failed: ${response.status}`);
        toast.error(`API test failed: ${response.status}`);
      }
    } catch (error) {
      console.error('API test error:', error);
      setApiError(`API connection failed: ${(error as Error).message}`);
      toast.error('API connection failed');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <TestTube size={28} style={{ color: '#00D4AA' }} />
          <Typography variant="h4" sx={{ fontWeight: 600, color: '#ffffff' }}>
            Testing Playground (Simple)
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ color: '#a1a1aa' }}>
          Simple test interface for debugging API connection issues.
        </Typography>
        
        {/* API Connection Test */}
        <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={testApiConnection}
            sx={{ borderColor: '#00D4AA', color: '#00D4AA' }}
          >
            Test API Connection
          </Button>
          {apiError && (
            <Alert severity="error" sx={{ flex: 1 }}>
              {apiError}
            </Alert>
          )}
        </Box>
      </Box>

      {/* Test Configuration */}
      <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)', mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
            Test Configuration
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Test Message"
              multiline
              rows={4}
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              fullWidth
              sx={{ '& .MuiInputLabel-root': { color: '#a1a1aa' } }}
            />

            <Button
              variant="contained"
              onClick={runTest}
              disabled={isLoading || !testMessage}
              startIcon={<Play />}
              sx={{ backgroundColor: '#00D4AA', '&:hover': { backgroundColor: '#00b894' } }}
            >
              {isLoading ? 'Testing...' : 'Run Test'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Results */}
      <Card sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
            Test Results ({testResults.length})
          </Typography>

          {testResults.length === 0 ? (
            <Typography variant="body1" sx={{ color: '#a1a1aa', textAlign: 'center', py: 4 }}>
              No test results yet. Run a test to see results here.
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {testResults.map((result) => (
                <Card key={result.id} sx={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Typography variant="caption" sx={{ color: '#a1a1aa' }}>
                        {new Date(result.timestamp).toLocaleString()}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#00D4AA' }}>
                        {result.responseTime.toFixed(0)}ms
                      </Typography>
                      {result.blocked && (
                        <Alert severity="warning" sx={{ py: 0 }}>
                          Blocked: {result.blockingReasons.join(', ')}
                        </Alert>
                      )}
                    </Box>

                    <Typography variant="body2" sx={{ color: '#ffffff', mb: 1 }}>
                      <strong>Message:</strong> {result.message}
                    </Typography>

                    <Typography variant="body2" sx={{ color: '#a1a1aa' }}>
                      <strong>Response:</strong> {result.response}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Loading Overlay */}
      {isLoading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <Card sx={{ p: 3, backgroundColor: 'rgba(255, 255, 255, 0.02)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <LinearProgress sx={{ width: 200 }} />
              <Typography sx={{ color: '#ffffff' }}>Running test...</Typography>
            </Box>
          </Card>
        </Box>
      )}
    </Box>
  );
};

export default TestingPlaygroundSimple;