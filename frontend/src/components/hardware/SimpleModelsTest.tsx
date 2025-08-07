import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, Alert, Chip } from '@mui/material';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const SimpleModelsTest: React.FC = () => {
  console.log('🔍 SimpleModelsTest: Component rendering');
  
  const [modelsData, setModelsData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchModels = async () => {
    console.log('🔍 SimpleModelsTest: Fetching models from:', `${BACKEND_URL}/api/models/search`);
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/models/search`, {
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      console.log('🔍 SimpleModelsTest: Response status:', response.status);
      console.log('🔍 SimpleModelsTest: Response headers:', Object.fromEntries(response.headers));
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('🔍 SimpleModelsTest: Response data:', {
        type: typeof result,
        hasModels: !!result.models,
        modelsLength: result.models ? result.models.length : 'N/A',
        keys: Object.keys(result)
      });
      
      if (result.models) {
        console.log('🔍 SimpleModelsTest: First 3 models:', result.models.slice(0, 3).map((m: any) => m.name));
      }
      
      setModelsData(result);
    } catch (err) {
      console.error('🚨 SimpleModelsTest: Error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('🔍 SimpleModelsTest: useEffect triggered');
    fetchModels();
  }, []);

  console.log('🔍 SimpleModelsTest: Render state - loading:', loading, 'error:', error, 'modelsCount:', modelsData?.models?.length || 0);

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography sx={{ color: '#ffffff' }}>Loading models data...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error: {error}
        </Alert>
        <Button onClick={fetchModels} variant="outlined">
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, color: '#ffffff' }}>
        Models API Test
      </Typography>
      
      {modelsData && (
        <>
          <Box sx={{ mb: 3 }}>
            <Chip 
              label={`Total Models: ${modelsData.models ? modelsData.models.length : 0}`}
              sx={{ 
                bgcolor: modelsData.models && modelsData.models.length > 100 ? '#00D4AA' : '#ef4444',
                color: '#000000',
                fontWeight: 'bold',
                mr: 2
              }}
            />
            <Chip 
              label={`API Success: ${!!modelsData.models ? 'YES' : 'NO'}`}
              sx={{ 
                bgcolor: modelsData.models ? '#00D4AA' : '#ef4444',
                color: '#000000',
                fontWeight: 'bold'
              }}
            />
          </Box>

          {modelsData.models && modelsData.models.length > 0 && (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2, mb: 3 }}>
              {modelsData.models.slice(0, 6).map((model: any, index: number) => (
                <Card key={index} sx={{ bgcolor: '#111827', border: '1px solid #374151' }}>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="body2" sx={{ color: '#ffffff', fontWeight: 'bold', mb: 1 }}>
                      {model.name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#6b7280', mb: 1, display: 'block' }}>
                      {model.description}
                    </Typography>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {model.capabilities && model.capabilities.map((cap: string, i: number) => (
                        <Chip
                          key={i}
                          label={cap}
                          size="small"
                          sx={{ 
                            fontSize: '0.6rem',
                            height: '18px',
                            bgcolor: '#00D4AA',
                            color: '#000000'
                          }}
                        />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </>
      )}

      <Box sx={{ mt: 3 }}>
        <Button onClick={fetchModels} variant="outlined" sx={{ color: '#ffffff', borderColor: '#374151', mr: 2 }}>
          Refresh Models
        </Button>
      </Box>

      {/* Raw API Response for debugging */}
      <Card sx={{ bgcolor: '#111827', border: '1px solid #374151', mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ color: '#ffffff', mb: 2 }}>
            Raw Models API Response (for debugging)
          </Typography>
          <Box 
            component="pre" 
            sx={{ 
              color: '#6b7280', 
              fontSize: '0.7rem', 
              overflow: 'auto',
              maxHeight: '300px',
              backgroundColor: '#0f172a',
              p: 2,
              borderRadius: 1
            }}
          >
            {JSON.stringify(modelsData, null, 2)}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SimpleModelsTest;