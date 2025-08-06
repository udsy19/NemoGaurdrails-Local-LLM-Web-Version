import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  LinearProgress,
  Fade,
  Tooltip,
  Chip,
  Divider,
} from '@mui/material';
import {
  Security,
  Computer,
  Wifi,
  Fingerprint,
  CheckCircle,
  ErrorOutline,
  DeveloperMode,
  VpnKey,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../hooks/useAuth';

interface LicenseVerificationProps {
  sessionData: any;
  onVerificationSuccess: (licenseData: any) => void;
  onBack: () => void;
}

interface SystemInfo {
  macAddress: string;
  ipAddress: string;
  fingerprint: string;
  platform: string;
  hostname: string;
}

const LicenseVerification: React.FC<LicenseVerificationProps> = ({
  sessionData,
  onVerificationSuccess,
  onBack,
}) => {
  const [licenseKey, setLicenseKey] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [showBypass, setShowBypass] = useState(false);

  const { verifyLicense, getSystemInfo } = useAuth();

  // Load system info on component mount
  useEffect(() => {
    const loadSystemInfo = async () => {
      try {
        const info = await getSystemInfo();
        setSystemInfo(info.system_info);
      } catch (err) {
        console.error('Failed to load system info:', err);
      }
    };

    loadSystemInfo();

    // Check if in development mode
    const isDev = process.env.NODE_ENV === 'development' || 
                  window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1';
    setShowBypass(isDev);
  }, [getSystemInfo]);

  const validateLicenseKey = (key: string): boolean => {
    // UUID4 format validation
    const uuidPattern = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    return uuidPattern.test(key);
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setLicenseKey(value);
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!licenseKey.trim()) {
      setError('License key is required');
      return;
    }

    if (!validateLicenseKey(licenseKey.trim())) {
      setError('Invalid license key format. Please enter a valid UUID.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await verifyLicense(licenseKey.trim(), false);
      
      if (response.success) {
        onVerificationSuccess({
          ...response,
          licenseKey: licenseKey.trim(),
        });
      } else {
        setError(response.error || 'License verification failed');
      }
    } catch (err) {
      console.error('License verification error:', err);
      setError('Failed to verify license. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBypassVerification = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await verifyLicense('00000000-0000-0000-0000-000000000000', true); // Use bypass with valid UUID format
      
      if (response.success) {
        onVerificationSuccess({
          ...response,
          licenseKey: 'dev-bypass-license',
        });
      } else {
        setError(response.error || 'Bypass verification failed');
      }
    } catch (err) {
      console.error('Bypass verification error:', err);
      setError('Failed to bypass verification. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatMacAddress = (mac: string) => {
    return mac.toUpperCase().replace(/(.{2})/g, '$1:').slice(0, -1);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 3,
        fontFamily: '"Inter", system-ui, sans-serif',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Animated Background Particles */}
      {[...Array(15)].map((_, i) => (
        <motion.div
          key={i}
          style={{
            position: 'absolute',
            width: Math.random() * 3 + 1,
            height: Math.random() * 3 + 1,
            background: 'rgba(0, 212, 170, 0.4)',
            borderRadius: '50%',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            x: [0, 20, 0],
            y: [0, -40, 0],
            opacity: [0.4, 0.9, 0.4],
          }}
          transition={{
            duration: 4 + Math.random() * 3,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: 'easeInOut',
          }}
        />
      ))}
      
      <motion.div
        initial={{ opacity: 0, y: 50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ 
          duration: 0.8, 
          ease: [0.25, 0.1, 0.25, 1],
          type: 'spring',
          stiffness: 100,
        }}
      >
        <Card
          sx={{
            maxWidth: 550,
            width: '100%',
            background: 'rgba(255, 255, 255, 0.02)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          }}
        >
          <CardContent sx={{ p: 4 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <motion.div
                animate={{
                  scale: [1, 1.05, 1],
                  rotate: [0, 2, -2, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <VpnKey
                  sx={{
                    fontSize: 64,
                    color: '#00D4AA',
                    mb: 2,
                    filter: 'drop-shadow(0 0 20px rgba(0, 212, 170, 0.3))',
                  }}
                />
              </motion.div>
              
              <Typography
                variant="h4"
                sx={{
                  color: '#ffffff',
                  fontWeight: 700,
                  mb: 1,
                  background: 'linear-gradient(135deg, #00D4AA 0%, #00A085 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                License Verification
              </Typography>
              
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  mb: 2,
                }}
              >
                Enter your license key to activate the system
              </Typography>
              
              {/* User Info */}
              <Chip
                icon={<CheckCircle />}
                label={`Authenticated as ${sessionData?.email || 'User'}`}
                size="small"
                sx={{
                  backgroundColor: 'rgba(34, 197, 94, 0.2)',
                  color: '#22c55e',
                  border: '1px solid rgba(34, 197, 94, 0.3)',
                }}
              />
            </Box>

            {/* System Information */}
            {systemInfo && (
              <Card
                sx={{
                  mb: 3,
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <CardContent sx={{ p: 2 }}>
                  <Typography
                    variant="subtitle2"
                    sx={{
                      color: '#00D4AA',
                      mb: 1,
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <Security sx={{ fontSize: 16 }} />
                    System Information
                  </Typography>
                  
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Computer sx={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' }} />
                        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                          MAC Address
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#ffffff', fontFamily: 'monospace' }}>
                        {formatMacAddress(systemInfo.macAddress)}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Wifi sx={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' }} />
                        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                          IP Address
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#ffffff', fontFamily: 'monospace' }}>
                        {systemInfo.ipAddress}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ gridColumn: 'span 2' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Fingerprint sx={{ fontSize: 14, color: 'rgba(255, 255, 255, 0.6)' }} />
                        <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                          System Fingerprint
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#ffffff', fontFamily: 'monospace' }}>
                        {systemInfo.fingerprint}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Loading Bar */}
            {isLoading && (
              <Box sx={{ mb: 2 }}>
                <LinearProgress
                  sx={{
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
                    },
                  }}
                />
              </Box>
            )}

            {/* Error Alert */}
            {error && (
              <Fade in={Boolean(error)}>
                <Alert
                  severity="error"
                  icon={<ErrorOutline />}
                  sx={{
                    mb: 3,
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#ffffff',
                    '& .MuiAlert-icon': {
                      color: '#ef4444',
                    },
                  }}
                >
                  {error}
                </Alert>
              </Fade>
            )}

            {/* License Form */}
            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="License Key"
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                value={licenseKey}
                onChange={handleInputChange}
                disabled={isLoading}
                inputProps={{
                  style: { fontFamily: 'monospace', fontSize: '14px' },
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: 'none',
                    borderRadius: 2,
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#00D4AA',
                    },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                      borderColor: '#00D4AA',
                      borderWidth: '2px',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&.Mui-focused': {
                      color: '#00D4AA',
                    },
                  },
                  '& .MuiOutlinedInput-input': {
                    color: '#ffffff',
                  },
                }}
              />

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  style={{ flex: 1 }}
                >
                  <Button
                    fullWidth
                    type="submit"
                    variant="contained"
                    size="large"
                    disabled={isLoading || !licenseKey.trim()}
                    startIcon={!isLoading ? <Security /> : null}
                    sx={{
                      py: 1.5,
                      background: 'linear-gradient(135deg, #00D4AA 0%, #007A6B 100%)',
                      borderRadius: 2,
                      textTransform: 'none',
                      fontSize: '16px',
                      fontWeight: 600,
                      color: '#000000',
                      boxShadow: '0 4px 20px rgba(0, 212, 170, 0.3)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #00B894 0%, #005A4B 100%)',
                        boxShadow: '0 6px 25px rgba(0, 212, 170, 0.4)',
                      },
                      '&:disabled': {
                        background: 'rgba(255, 255, 255, 0.1)',
                        color: 'rgba(255, 255, 255, 0.3)',
                      },
                    }}
                  >
                    {isLoading ? 'Verifying...' : 'Verify License'}
                  </Button>
                </motion.div>

                <Button
                  variant="outlined"
                  onClick={onBack}
                  disabled={isLoading}
                  sx={{
                    px: 3,
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    color: 'rgba(255, 255, 255, 0.7)',
                    '&:hover': {
                      borderColor: 'rgba(255, 255, 255, 0.4)',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    },
                  }}
                >
                  Back
                </Button>
              </Box>

              {/* Development Bypass Button */}
              {showBypass && (
                <Fade in={showBypass}>
                  <Box>
                    <Divider sx={{ mb: 2, borderColor: 'rgba(255, 255, 255, 0.1)' }} />
                    <Tooltip title="Development bypass - skips license verification">
                      <Button
                        fullWidth
                        variant="outlined"
                        size="small"
                        onClick={handleBypassVerification}
                        disabled={isLoading}
                        startIcon={<DeveloperMode />}
                        sx={{
                          py: 1,
                          borderColor: 'rgba(255, 255, 255, 0.2)',
                          color: 'rgba(255, 255, 255, 0.6)',
                          textTransform: 'none',
                          fontSize: '12px',
                          '&:hover': {
                            borderColor: '#00D4AA',
                            backgroundColor: 'rgba(0, 212, 170, 0.1)',
                            color: '#00D4AA',
                          },
                        }}
                      >
                        Developer Bypass
                      </Button>
                    </Tooltip>
                  </Box>
                </Fade>
              )}
            </Box>

            {/* Footer */}
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255, 255, 255, 0.5)',
                  fontSize: '11px',
                }}
              >
                License verification secured with certificate validation
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default LicenseVerification;