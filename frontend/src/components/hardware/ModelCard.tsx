import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Memory,
  Speed,
  Computer,
  PlayArrow,
  Stop,
  Info,
  TrendingUp,
  CheckCircle,
  Warning
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { OllamaModel } from '../../services/ollamaModels';

interface ModelCardProps {
  model: OllamaModel;
  isLoaded: boolean;
  isLoading?: boolean;
  performanceMetrics?: {
    memory_usage_mb: number;
    inference_time_ms: number;
    tokens_per_second: number;
    gpu_utilization_percent: number;
  };
  onLoad: (modelName: string) => void;
  onUnload: (modelName: string) => void;
  disabled?: boolean;
}

const ModelCard: React.FC<ModelCardProps> = ({
  model,
  isLoaded,
  isLoading = false,
  performanceMetrics,
  onLoad,
  onUnload,
  disabled = false
}) => {
  const getCompatibilityColor = (label: string) => {
    switch (label) {
      case 'Excellent': return '#00D4AA';
      case 'Good': return '#f59e0b';
      case 'Fair': return '#6b7280';
      case 'Limited': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = () => {
    if (isLoading) return <Speed className="animate-spin" />;
    if (isLoaded) return <CheckCircle sx={{ color: '#00D4AA' }} />;
    return <Computer sx={{ color: '#6b7280' }} />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card 
        sx={{ 
          bgcolor: isLoaded ? 'rgba(0, 212, 170, 0.05)' : '#111827',
          border: isLoaded ? '1px solid rgba(0, 212, 170, 0.3)' : '1px solid #374151',
          transition: 'all 0.3s ease',
          height: '280px',
          display: 'flex',
          flexDirection: 'column',
          '&:hover': {
            borderColor: '#00D4AA',
            boxShadow: '0 4px 20px rgba(0, 212, 170, 0.1)'
          }
        }}
      >
        <CardContent sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box flex={1} mr={1}>
              <Typography 
                variant="body1" 
                sx={{ 
                  color: '#ffffff', 
                  fontWeight: 'medium',
                  fontSize: '0.9rem',
                  lineHeight: 1.2,
                  overflow: 'hidden',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  textOverflow: 'ellipsis'
                }}
              >
                {model.name}
              </Typography>
            </Box>
            <Tooltip title={isLoaded ? 'Model Loaded' : isLoading ? 'Loading...' : 'Model Available'}>
              <IconButton size="small">
                {getStatusIcon()}
              </IconButton>
            </Tooltip>
          </Box>

          {/* Capabilities */}
          <Box display="flex" gap={0.5} mb={2} flexWrap="wrap" sx={{ minHeight: '24px' }}>
            {model.capabilities.slice(0, 3).map((cap) => (
              <Chip
                key={cap}
                label={cap}
                size="small"
                variant="outlined"
                sx={{ 
                  fontSize: '0.65rem',
                  height: '20px',
                  borderColor: '#374151',
                  color: '#00D4AA',
                  '& .MuiChip-label': { px: 1 }
                }}
              />
            ))}
          </Box>

          {/* Performance Metrics (if loaded) */}
          {isLoaded && performanceMetrics && (
            <Box sx={{ mb: 2, p: 1, bgcolor: 'rgba(0, 212, 170, 0.1)', borderRadius: 1 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="caption" sx={{ color: '#00D4AA', fontWeight: 'medium' }}>
                  Performance
                </Typography>
                <Chip 
                  label={`${performanceMetrics.tokens_per_second.toFixed(1)} t/s`} 
                  size="small"
                  sx={{ 
                    bgcolor: '#00D4AA', 
                    color: '#000000', 
                    fontSize: '0.65rem',
                    height: '18px'
                  }}
                />
              </Box>
              
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="caption" sx={{ color: '#6b7280' }}>
                  Memory: {(performanceMetrics.memory_usage_mb / 1024).toFixed(1)}GB
                </Typography>
                <Typography variant="caption" sx={{ color: '#6b7280' }}>
                  Inference: {performanceMetrics.inference_time_ms.toFixed(0)}ms
                </Typography>
              </Box>
              
              <LinearProgress 
                variant="determinate" 
                value={Math.min(100, performanceMetrics.gpu_utilization_percent)}
                sx={{ 
                  height: 4,
                  borderRadius: 2,
                  backgroundColor: 'rgba(107, 114, 128, 0.3)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#00D4AA',
                    borderRadius: 2
                  }
                }}
              />
              <Typography variant="caption" sx={{ color: '#6b7280', fontSize: '0.6rem' }}>
                GPU Utilization: {performanceMetrics.gpu_utilization_percent.toFixed(1)}%
              </Typography>
            </Box>
          )}

          {/* Compatibility & Memory */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} sx={{ mt: 'auto' }}>
            <Chip
              label={model.compatibility_label}
              size="small"
              sx={{
                backgroundColor: getCompatibilityColor(model.compatibility_label),
                color: '#000000',
                fontSize: '0.65rem',
                fontWeight: 'bold'
              }}
            />
            <Box display="flex" alignItems="center" gap={0.5}>
              <Memory sx={{ fontSize: 12, color: '#6b7280' }} />
              <Typography variant="caption" sx={{ color: '#6b7280' }}>
                {model.estimated_memory_usage}
              </Typography>
            </Box>
          </Box>

          {/* Action Button */}
          <Button
            onClick={() => isLoaded ? onUnload(model.name) : onLoad(model.name)}
            variant={isLoaded ? "outlined" : "contained"}
            color={isLoaded ? "error" : "primary"}
            size="small"
            fullWidth
            disabled={disabled || isLoading}
            startIcon={isLoaded ? <Stop /> : <PlayArrow />}
            sx={{ 
              mt: 'auto',
              bgcolor: isLoaded ? 'transparent' : '#00D4AA',
              color: isLoaded ? '#ef4444' : '#000000',
              borderColor: isLoaded ? '#ef4444' : '#00D4AA',
              '&:hover': {
                bgcolor: isLoaded ? 'rgba(239, 68, 68, 0.1)' : '#00B894',
                borderColor: isLoaded ? '#dc2626' : '#00B894'
              },
              '&:disabled': {
                bgcolor: '#374151',
                color: '#6b7280',
                borderColor: '#374151'
              }
            }}
          >
            {isLoading ? 'Loading...' : isLoaded ? 'Unload' : 'Load Model'}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ModelCard;