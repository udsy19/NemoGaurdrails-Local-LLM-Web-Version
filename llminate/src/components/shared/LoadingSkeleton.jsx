import React from 'react';
import { 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Skeleton,
  Typography 
} from '@mui/material';
import { motion } from 'framer-motion';

const AnimatedCard = ({ children, delay = 0 }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay, duration: 0.5 }}
  >
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {children}
      </CardContent>
    </Card>
  </motion.div>
);

const LoadingSkeleton = ({ type = 'dashboard' }) => {
  if (type === 'dashboard') {
    return (
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Box display="flex" alignItems="center" mb={3}>
            <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
            <Box>
              <Skeleton variant="text" width={200} height={32} />
              <Skeleton variant="text" width={120} height={20} />
            </Box>
          </Box>
        </motion.div>

        {/* Risk Score & Threats */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={3}>
            <AnimatedCard delay={0.1}>
              <Skeleton variant="text" width="80%" height={24} />
              <Box display="flex" alignItems="center" my={2}>
                <Skeleton variant="text" width={60} height={60} />
                <Skeleton variant="rectangular" width={80} height={32} sx={{ ml: 2, borderRadius: 2 }} />
              </Box>
              <Skeleton variant="rectangular" width="100%" height={8} sx={{ borderRadius: 1 }} />
            </AnimatedCard>
          </Grid>
          
          <Grid item xs={12} md={9}>
            <AnimatedCard delay={0.2}>
              <Skeleton variant="text" width="60%" height={24} mb={2} />
              {[1, 2, 3].map(i => (
                <Box key={i} display="flex" alignItems="center" py={1}>
                  <Skeleton variant="circular" width={24} height={24} sx={{ mr: 2 }} />
                  <Box flex={1}>
                    <Skeleton variant="text" width="40%" height={20} />
                    <Skeleton variant="text" width="60%" height={16} />
                  </Box>
                  <Skeleton variant="circular" width={20} height={20} />
                </Box>
              ))}
            </AnimatedCard>
          </Grid>
        </Grid>

        {/* Metrics */}
        <Grid container spacing={3} mb={3}>
          {[1, 2, 3, 4].map(i => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <AnimatedCard delay={0.3 + i * 0.1}>
                <Box display="flex" alignItems="center" mb={1}>
                  <Skeleton variant="circular" width={24} height={24} sx={{ mr: 1 }} />
                  <Skeleton variant="text" width="70%" height={16} />
                </Box>
                <Skeleton variant="text" width="50%" height={32} />
              </AnimatedCard>
            </Grid>
          ))}
        </Grid>

        {/* Charts */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <AnimatedCard delay={0.7}>
              <Skeleton variant="text" width="60%" height={24} mb={2} />
              <Skeleton variant="rectangular" width="100%" height={280} sx={{ borderRadius: 2 }} />
            </AnimatedCard>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <AnimatedCard delay={0.8}>
              <Skeleton variant="text" width="60%" height={24} mb={2} />
              <Skeleton variant="rectangular" width="100%" height={280} sx={{ borderRadius: 2 }} />
            </AnimatedCard>
          </Grid>
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Skeleton variant="rectangular" width="100%" height={400} />
    </Box>
  );
};

export default LoadingSkeleton;