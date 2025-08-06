import React from 'react';
import { Box, LinearProgress, Typography, CircularProgress } from '@mui/material';
import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
  variant?: 'linear' | 'circular';
  color?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  size = 'medium',
  variant = 'linear',
  color = '#00D4AA'
}) => {
  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          container: { minHeight: '100px', p: 2 },
          progressWidth: '200px',
          fontSize: '0.875rem',
          circularSize: 30
        };
      case 'medium':
        return {
          container: { minHeight: '200px', p: 3 },
          progressWidth: '300px',
          fontSize: '1rem',
          circularSize: 40
        };
      case 'large':
        return {
          container: { minHeight: '300px', p: 4 },
          progressWidth: '400px',
          fontSize: '1.125rem',
          circularSize: 50
        };
      case 'fullscreen':
        return {
          container: { 
            minHeight: '100vh', 
            position: 'fixed' as const,
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 9999,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(5px)'
          },
          progressWidth: '400px',
          fontSize: '1.25rem',
          circularSize: 60
        };
      default:
        return {
          container: { minHeight: '200px', p: 3 },
          progressWidth: '300px',
          fontSize: '1rem',
          circularSize: 40
        };
    }
  };

  const styles = getSizeStyles();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Box 
        sx={{
          ...styles.container,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 2
        }}
      >
        {variant === 'linear' ? (
          <>
            <LinearProgress 
              sx={{ 
                width: styles.progressWidth,
                height: 6,
                borderRadius: 3,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: color,
                  borderRadius: 3,
                }
              }} 
            />
            <Typography 
              sx={{ 
                color: '#ffffff', 
                fontSize: styles.fontSize,
                fontWeight: 500,
                textAlign: 'center'
              }}
            >
              {message}
            </Typography>
          </>
        ) : (
          <>
            <CircularProgress 
              size={styles.circularSize}
              thickness={4}
              sx={{
                color: color,
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                }
              }}
            />
            <Typography 
              sx={{ 
                color: '#ffffff', 
                fontSize: styles.fontSize,
                fontWeight: 500,
                textAlign: 'center'
              }}
            >
              {message}
            </Typography>
          </>
        )}
      </Box>
    </motion.div>
  );
};

export default LoadingSpinner;