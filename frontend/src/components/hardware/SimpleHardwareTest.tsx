import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, Alert } from '@mui/material';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const SimpleHardwareTest: React.FC = () => {
  console.log('🔍 SimpleHardwareTest: Component rendering');
  
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    console.log('🔍 SimpleHardwareTest: Fetching data from:', `${BACKEND_URL}/api/hardware/metrics`);
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/hardware/metrics`);
      console.log('🔍 SimpleHardwareTest: Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('🔍 SimpleHardwareTest: Response data:', result);
      setData(result);
    } catch (err) {
      console.error('🚨 SimpleHardwareTest: Error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('🔍 SimpleHardwareTest: useEffect triggered');
    fetchData();
  }, []);

  console.log('🔍 SimpleHardwareTest: Render state - loading:', loading, 'error:', error, 'data:', !!data);

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading hardware data...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error: {error}
        </Alert>
        <Button onClick={fetchData} variant="outlined">
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, color: '#ffffff' }}>
        Hardware Test Dashboard
      </Typography>
      
      {data && data.success && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                CPU Info
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Usage: {data.metrics.cpu.usage_percent.toFixed(1)}%
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Cores: {data.metrics.cpu.cores}
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Processes: {data.metrics.cpu.processes}
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                Memory Info
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Usage: {data.metrics.memory.usage_percent.toFixed(1)}%
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Total: {data.metrics.memory.total_gb.toFixed(1)} GB
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Available: {data.metrics.memory.available_gb.toFixed(1)} GB
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                GPU Info
              </Typography>
              {data.metrics.gpu.devices.map((device: any, index: number) => (
                <Box key={index} sx={{ mb: 1 }}>
                  <Typography sx={{ color: '#6b7280' }}>
                    {device.name} ({device.vendor})
                  </Typography>
                  <Typography sx={{ color: '#6b7280' }}>
                    Utilization: {device.utilization_percent.toFixed(1)}%
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
            <CardContent>
              <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
                Disk Info
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Usage: {data.metrics.disk.usage_percent.toFixed(1)}%
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Total: {data.metrics.disk.total_gb.toFixed(1)} GB
              </Typography>
              <Typography sx={{ color: '#6b7280' }}>
                Available: {data.metrics.disk.available_gb.toFixed(1)} GB
              </Typography>
            </CardContent>
          </Card>
        </Box>
      )}

      <Box sx={{ mt: 3 }}>
        <Button onClick={fetchData} variant="outlined" sx={{ color: '#ffffff', borderColor: '#374151' }}>
          Refresh Data
        </Button>
      </Box>

      {/* Raw Data Display for debugging */}
      <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
            Raw API Response (for debugging)
          </Typography>
          <Box 
            component="pre" 
            sx={{ 
              color: '#6b7280', 
              fontSize: '0.75rem', 
              overflow: 'auto',
              maxHeight: '200px',
              backgroundColor: '#0f172a',
              p: 2,
              borderRadius: 1
            }}
          >
            {JSON.stringify(data, null, 2)}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SimpleHardwareTest;