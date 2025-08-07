import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadialBarChart,
  RadialBar,
} from 'recharts';
import { Card, CardContent, Typography, Box, useTheme } from '@mui/material';
import { motion } from 'framer-motion';

const chartVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: 0.8, ease: "easeOut" }
  }
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <Box
        sx={{
          backgroundColor: 'rgba(26, 31, 46, 0.95)',
          border: '1px solid rgba(0, 212, 170, 0.3)',
          borderRadius: 2,
          padding: 2,
          backdropFilter: 'blur(10px)',
        }}
      >
        <Typography variant="body2" sx={{ color: '#A8B2D1', mb: 1 }}>
          {label}
        </Typography>
        {payload.map((pld, index) => (
          <Typography key={index} variant="body2" sx={{ color: pld.color }}>
            {`${pld.dataKey}: ${pld.value}`}
          </Typography>
        ))}
      </Box>
    );
  }
  return null;
};

export const ThreatTimelineChart = ({ data, title }) => {
  const theme = useTheme();
  
  return (
    <Card sx={{ height: '100%', width: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <motion.div variants={chartVariants} initial="hidden" animate="visible">
          <Box sx={{ width: '100%', height: 320, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="threatGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#FF3D71" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#FF3D71" stopOpacity={0.05}/>
                </linearGradient>
                <linearGradient id="allowedGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00D4AA" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00D4AA" stopOpacity={0.05}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="time" 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="blocked"
                stroke="#FF3D71"
                strokeWidth={2}
                fill="url(#threatGradient)"
                dot={{ fill: '#FF3D71', r: 4 }}
                activeDot={{ r: 6, stroke: '#FF3D71', strokeWidth: 2 }}
              />
              <Area
                type="monotone"
                dataKey="allowed"
                stroke="#00D4AA"
                strokeWidth={2}
                fill="url(#allowedGradient)"
                dot={{ fill: '#00D4AA', r: 4 }}
                activeDot={{ r: 6, stroke: '#00D4AA', strokeWidth: 2 }}
              />
            </AreaChart>
            </ResponsiveContainer>
          </Box>
        </motion.div>
      </CardContent>
    </Card>
  );
};

export const ThreatDistributionChart = ({ data, title }) => {
  const COLORS = [
    '#FF3D71', '#FFB800', '#00D4AA', '#3B82F6', 
    '#9C27B0', '#FF5722', '#607D8B', '#795548'
  ];

  const renderLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null; // Hide labels for slices < 5%
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="500"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <Card sx={{ height: '100%', width: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <motion.div variants={chartVariants} initial="hidden" animate="visible">
          <Box sx={{ width: '100%', height: 320, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                animationBegin={0}
                animationDuration={1000}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
            </ResponsiveContainer>
          </Box>
        </motion.div>
        
        {/* Legend */}
        <Box display="flex" flexWrap="wrap" gap={1} mt={2}>
          {data.map((entry, index) => (
            <Box key={entry.name} display="flex" alignItems="center">
              <Box
                width={12}
                height={12}
                borderRadius="50%"
                bgcolor={COLORS[index % COLORS.length]}
                mr={0.5}
              />
              <Typography variant="caption" color="text.secondary">
                {entry.name}
              </Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export const RiskGaugeChart = ({ value, title, max = 100 }) => {
  const gaugeData = [
    { name: 'Risk', value: value, fill: value >= 70 ? '#FF3D71' : value >= 40 ? '#FFB800' : '#00D4AA' }
  ];

  return (
    <Card sx={{ height: '100%', width: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" gutterBottom textAlign="center">
          {title}
        </Typography>
        <motion.div variants={chartVariants} initial="hidden" animate="visible">
          <Box sx={{ width: '100%', height: 200, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              barSize={20}
              data={gaugeData}
              startAngle={180}
              endAngle={0}
            >
              <RadialBar
                dataKey="value"
                cornerRadius={10}
                fill={gaugeData[0].fill}
                background={{ fill: 'rgba(255,255,255,0.1)' }}
              />
              <text
                x="50%"
                y="50%"
                textAnchor="middle"
                dominantBaseline="middle"
                className="progress-label"
                fontSize="24"
                fontWeight="bold"
                fill={gaugeData[0].fill}
              >
                {value}
              </text>
              <text
                x="50%"
                y="60%"
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="12"
                fill="#A8B2D1"
              >
                Risk Score
              </text>
            </RadialBarChart>
            </ResponsiveContainer>
          </Box>
        </motion.div>
      </CardContent>
    </Card>
  );
};

export const PerformanceBarChart = ({ data, title }) => {
  return (
    <Card sx={{ height: '100%', width: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <motion.div variants={chartVariants} initial="hidden" animate="visible">
          <Box sx={{ width: '100%', height: 320, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="name" 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="requests" 
                fill="#3B82F6"
                radius={[4, 4, 0, 0]}
                animationDuration={1000}
              />
              <Bar 
                dataKey="blocked" 
                fill="#FF3D71"
                radius={[4, 4, 0, 0]}
                animationDuration={1200}
              />
            </BarChart>
            </ResponsiveContainer>
          </Box>
        </motion.div>
      </CardContent>
    </Card>
  );
};

export const RealTimeActivityChart = ({ data, title }) => {
  return (
    <Card sx={{ height: '100%', width: '100%' }}>
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <motion.div variants={chartVariants} initial="hidden" animate="visible">
          <Box sx={{ width: '100%', height: 320, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis 
                dataKey="time" 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                stroke="#A8B2D1"
                fontSize={12}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="activity"
                stroke="#00D4AA"
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, stroke: '#00D4AA', strokeWidth: 2 }}
                strokeDasharray="0"
                animationDuration={1500}
              />
            </LineChart>
            </ResponsiveContainer>
          </Box>
        </motion.div>
      </CardContent>
    </Card>
  );
};