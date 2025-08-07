import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Chip,
  LinearProgress,
} from '@mui/material';
import { motion } from 'framer-motion';
import CountUp from 'react-countup';
import { 
  TrendingUp, 
  TrendingDown, 
  TrendingFlat,
  ArrowUpward,
  ArrowDownward
} from '@mui/icons-material';

const AnimatedMetricCard = ({ 
  title, 
  value, 
  previousValue, 
  icon, 
  color = 'primary',
  subtitle,
  trend,
  progress,
  delay = 0 
}) => {
  const calculateTrend = () => {
    if (!previousValue || previousValue === 0) return { direction: 'stable', percentage: 0 };
    const change = ((value - previousValue) / previousValue) * 100;
    return {
      direction: change > 5 ? 'up' : change < -5 ? 'down' : 'stable',
      percentage: Math.abs(change)
    };
  };

  const trendData = trend || calculateTrend();
  
  const getTrendIcon = () => {
    switch (trendData.direction) {
      case 'up': return <TrendingUp fontSize="small" />;
      case 'down': return <TrendingDown fontSize="small" />;
      default: return <TrendingFlat fontSize="small" />;
    }
  };

  const getTrendColor = () => {
    switch (trendData.direction) {
      case 'up': return color === 'error' ? 'error' : 'success';
      case 'down': return color === 'error' ? 'success' : 'error';
      default: return 'info';
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30, scale: 0.9 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { 
        delay: delay,
        duration: 0.6,
        ease: "easeOut"
      }
    },
    hover: { 
      y: -8,
      scale: 1.02,
      transition: { duration: 0.2 }
    }
  };

  const iconVariants = {
    hidden: { rotate: 0 },
    visible: { 
      rotate: 360,
      transition: { delay: delay + 0.3, duration: 0.8 }
    },
    hover: {
      scale: 1.1,
      rotate: 370,
      transition: { duration: 0.3 }
    }
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
    >
      <Card 
        sx={{ 
          height: '100%',
          background: `linear-gradient(135deg, ${color === 'primary' ? 'rgba(0, 212, 170, 0.1)' : 
            color === 'error' ? 'rgba(255, 61, 113, 0.1)' :
            color === 'warning' ? 'rgba(255, 184, 0, 0.1)' :
            color === 'success' ? 'rgba(0, 212, 170, 0.1)' :
            'rgba(59, 130, 246, 0.1)'} 0%, rgba(255,255,255,0.05) 100%)`,
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          cursor: 'pointer',
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            background: `linear-gradient(90deg, ${color === 'primary' ? '#00D4AA' : 
              color === 'error' ? '#FF3D71' :
              color === 'warning' ? '#FFB800' :
              color === 'success' ? '#00D4AA' :
              '#3B82F6'} 0%, transparent 100%)`,
          }
        }}
      >
        <CardContent>
          {/* Header with Icon and Trend */}
          <Box display="flex" alignItems="flex-start" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center">
              <motion.div variants={iconVariants}>
                <Box 
                  sx={{ 
                    color: `${color}.main`,
                    mr: 1,
                    p: 1,
                    borderRadius: '50%',
                    background: `${color === 'primary' ? 'rgba(0, 212, 170, 0.1)' : 
                      color === 'error' ? 'rgba(255, 61, 113, 0.1)' :
                      color === 'warning' ? 'rgba(255, 184, 0, 0.1)' :
                      color === 'success' ? 'rgba(0, 212, 170, 0.1)' :
                      'rgba(59, 130, 246, 0.1)'}`,
                  }}
                >
                  {icon}
                </Box>
              </motion.div>
            </Box>
            
            {trendData.percentage > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: delay + 0.5, duration: 0.4 }}
              >
                <Chip
                  icon={getTrendIcon()}
                  label={`${trendData.percentage.toFixed(1)}%`}
                  size="small"
                  color={getTrendColor()}
                  sx={{ 
                    height: 24,
                    '& .MuiChip-icon': { fontSize: 14 }
                  }}
                />
              </motion.div>
            )}
          </Box>

          {/* Title */}
          <Typography 
            variant="body2" 
            color="text.secondary" 
            sx={{ 
              fontSize: '0.75rem',
              fontWeight: 500,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              mb: 1
            }}
          >
            {title}
          </Typography>

          {/* Main Value */}
          <Box display="flex" alignItems="baseline" mb={1}>
            <Typography 
              variant="h3" 
              fontWeight="bold" 
              color={`${color}.main`}
              sx={{ 
                fontFamily: '"JetBrains Mono", "SF Mono", Monaco, monospace',
                fontSize: { xs: '1.8rem', sm: '2.2rem' },
                lineHeight: 1
              }}
            >
              <CountUp
                end={typeof value === 'number' ? value : parseFloat(value) || 0}
                duration={1.5}
                delay={delay}
                separator=","
                suffix={typeof value === 'string' && value.includes('%') ? '%' : ''}
              />
            </Typography>
          </Box>

          {/* Subtitle */}
          {subtitle && (
            <Typography variant="caption" color="text.secondary">
              {subtitle}
            </Typography>
          )}

          {/* Progress Bar */}
          {progress !== undefined && (
            <Box mt={2}>
              <motion.div
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ delay: delay + 0.7, duration: 0.8 }}
                style={{ transformOrigin: 'left' }}
              >
                <LinearProgress 
                  variant="determinate" 
                  value={progress} 
                  color={color}
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    '& .MuiLinearProgress-bar': {
                      borderRadius: 3,
                      background: `linear-gradient(90deg, ${color === 'primary' ? '#00D4AA' : 
                        color === 'error' ? '#FF3D71' :
                        color === 'warning' ? '#FFB800' :
                        color === 'success' ? '#00D4AA' :
                        '#3B82F6'}, ${color === 'primary' ? '#4DFFCC' : 
                        color === 'error' ? '#FF7AA3' :
                        color === 'warning' ? '#FFCC4D' :
                        color === 'success' ? '#4DFFCC' :
                        '#60A5FA'})`
                    }
                  }} 
                />
              </motion.div>
              <Box display="flex" justifyContent="space-between" mt={0.5}>
                <Typography variant="caption" color="text.secondary">0</Typography>
                <Typography variant="caption" color="text.secondary">100</Typography>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default AnimatedMetricCard;