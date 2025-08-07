import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  IconButton,
  Chip
} from '@mui/material';
import {
  Fullscreen,
  TrendingUp,
  TrendingDown,
  Remove
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line
} from 'recharts';

interface MetricDataPoint {
  time: string;
  value: number;
  timestamp: number;
}

interface SystemMetricsChartProps {
  title: string;
  data: MetricDataPoint[];
  color: string;
  icon: React.ReactNode;
  unit: string;
  currentValue: number;
  maxValue?: number;
  onFullscreen?: () => void;
  height?: number;
  chartType?: 'area' | 'line';
  showGradient?: boolean;
}

const SystemMetricsChart: React.FC<SystemMetricsChartProps> = ({
  title,
  data,
  color,
  icon,
  unit,
  currentValue,
  maxValue = 100,
  onFullscreen,
  height = 300,
  chartType = 'area',
  showGradient = true
}) => {
  // Calculate trend
  const getTrend = () => {
    if (data.length < 2) return 'stable';
    const recent = data.slice(-5);
    const older = data.slice(-10, -5);
    
    if (recent.length === 0 || older.length === 0) return 'stable';
    
    const recentAvg = recent.reduce((sum, point) => sum + point.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, point) => sum + point.value, 0) / older.length;
    
    const difference = recentAvg - olderAvg;
    if (Math.abs(difference) < 2) return 'stable';
    return difference > 0 ? 'up' : 'down';
  };

  const trend = getTrend();

  const getTrendIcon = () => {
    switch (trend) {
      case 'up': return <TrendingUp sx={{ color: '#ef4444', fontSize: 16 }} />;
      case 'down': return <TrendingDown sx={{ color: '#00D4AA', fontSize: 16 }} />;
      default: return <Remove sx={{ color: '#6b7280', fontSize: 16 }} />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up': return '#ef4444';
      case 'down': return '#00D4AA'; 
      default: return '#6b7280';
    }
  };

  const getStatusColor = (value: number) => {
    const percentage = (value / maxValue) * 100;
    if (percentage < 50) return '#00D4AA';
    if (percentage < 75) return '#f59e0b';
    return '#ef4444';
  };

  const gradientId = `gradient-${title.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <Card 
      sx={{ 
        bgcolor: '#111827', 
        border: '1px solid #374151',
        height: height + 100,
        transition: 'all 0.2s ease',
        '&:hover': {
          borderColor: color,
          boxShadow: `0 4px 20px ${color}20`
        }
      }}
    >
      <CardContent sx={{ height: '100%', p: 2, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {icon}
            <Typography variant="h6" sx={{ color: '#ffffff', fontSize: '1rem' }}>
              {title}
            </Typography>
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            {/* Current Value */}
            <Chip
              label={`${currentValue.toFixed(1)}${unit}`}
              size="small"
              sx={{
                backgroundColor: getStatusColor(currentValue),
                color: '#000000',
                fontWeight: 'bold',
                fontSize: '0.75rem'
              }}
            />
            
            {/* Trend Indicator */}
            <Box 
              display="flex" 
              alignItems="center" 
              sx={{ 
                bgcolor: `${getTrendColor()}20`,
                px: 1,
                py: 0.5,
                borderRadius: 1,
                border: `1px solid ${getTrendColor()}40`
              }}
            >
              {getTrendIcon()}
            </Box>

            {/* Fullscreen Button */}
            {onFullscreen && (
              <IconButton 
                onClick={onFullscreen} 
                size="small"
                sx={{ 
                  color: '#6b7280',
                  '&:hover': { color: color }
                }}
              >
                <Fullscreen />
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Chart */}
        <Box sx={{ flex: 1, minHeight: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'area' ? (
              <AreaChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  {showGradient && (
                    <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={color} stopOpacity={0.1}/>
                    </linearGradient>
                  )}
                </defs>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="#374151" 
                  strokeOpacity={0.3}
                />
                <XAxis 
                  dataKey="time" 
                  stroke="#6b7280" 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  tickLine={{ stroke: '#6b7280' }}
                  axisLine={{ stroke: '#6b7280' }}
                />
                <YAxis 
                  stroke="#6b7280" 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  tickLine={{ stroke: '#6b7280' }}
                  axisLine={{ stroke: '#6b7280' }}
                  domain={[0, maxValue]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: `1px solid ${color}`,
                    borderRadius: '6px',
                    color: '#ffffff',
                    fontSize: '12px'
                  }}
                  formatter={(value: number) => [`${value.toFixed(1)}${unit}`, title]}
                  labelStyle={{ color: '#6b7280' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={color} 
                  fillOpacity={1} 
                  fill={showGradient ? `url(#${gradientId})` : color} 
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: color,
                    stroke: '#ffffff',
                    strokeWidth: 2
                  }}
                />
              </AreaChart>
            ) : (
              <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="#374151" 
                  strokeOpacity={0.3}
                />
                <XAxis 
                  dataKey="time" 
                  stroke="#6b7280" 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                />
                <YAxis 
                  stroke="#6b7280" 
                  tick={{ fontSize: 10, fill: '#6b7280' }}
                  domain={[0, maxValue]}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: `1px solid ${color}`,
                    borderRadius: '6px',
                    color: '#ffffff',
                    fontSize: '12px'
                  }}
                  formatter={(value: number) => [`${value.toFixed(1)}${unit}`, title]}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke={color} 
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ 
                    r: 4, 
                    fill: color,
                    stroke: '#ffffff',
                    strokeWidth: 2
                  }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </Box>

        {/* Footer Stats */}
        <Box 
          display="flex" 
          justifyContent="space-between" 
          alignItems="center" 
          mt={1}
          pt={1}
          borderTop="1px solid #374151"
        >
          <Typography variant="caption" sx={{ color: '#6b7280' }}>
            {data.length > 0 && (
              <>Min: {Math.min(...data.map(d => d.value)).toFixed(1)}{unit}</>
            )}
          </Typography>
          <Typography variant="caption" sx={{ color: '#6b7280' }}>
            {data.length > 0 && (
              <>Max: {Math.max(...data.map(d => d.value)).toFixed(1)}{unit}</>
            )}
          </Typography>
          <Typography variant="caption" sx={{ color: '#6b7280' }}>
            {data.length > 0 && (
              <>Avg: {(data.reduce((sum, d) => sum + d.value, 0) / data.length).toFixed(1)}{unit}</>
            )}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SystemMetricsChart;