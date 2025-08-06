import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  IconButton,
  InputAdornment,
  LinearProgress,
  Fade,
  Tooltip,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Shield,
  Computer,
  Lock,
  DeveloperMode,
  Bolt,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../hooks/useAuth';

interface LoginPageProps {
  onLoginSuccess: (sessionData: any) => void;
  onRequireLicense: (sessionData: any) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({
  onLoginSuccess,
  onRequireLicense,
}) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showBypass, setShowBypass] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { login, isAuthenticated } = useAuth();

  // Show bypass in development mode
  useEffect(() => {
    // Check if in development mode
    const isDev = process.env.NODE_ENV === 'development' || 
                  window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1';
    setShowBypass(isDev);
  }, []);

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('Attempting login with:', { email: formData.email });
      const response = await login(formData.email, formData.password, false);
      
      console.log('Login response:', response);
      
      if (response.success) {
        if (response.requires_license) {
          onRequireLicense(response.session);
        } else {
          onLoginSuccess(response.session);
        }
      } else {
        console.error('Login failed:', response.error);
        if (response.error) {
          setError(response.error);
        }
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(`Login failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBypassLogin = async () => {
    setIsLoading(true);
    
    try {
      console.log('Attempting bypass login...');
      const response = await login('bypass@dev.com', 'bypass123', true); // Use bypass with valid dummy credentials
      
      console.log('Bypass response:', response);
      
      if (response.success) {
        if (response.requires_license) {
          onRequireLicense(response.session);
        } else {
          onLoginSuccess(response.session);
        }
      } else {
        console.error('Bypass login failed:', response.error);
        // Show error message to user
        if (response.error) {
          setError(response.error);
        }
      }
    } catch (err) {
      console.error('Bypass login error:', err);
      setError(`Bypass failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
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
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          style={{
            position: 'absolute',
            width: Math.random() * 4 + 1,
            height: Math.random() * 4 + 1,
            background: 'rgba(0, 212, 170, 0.3)',
            borderRadius: '50%',
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.3, 0.8, 0.3],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 2,
            ease: 'easeInOut',
          }}
        />
      ))}
      
      {/* Main Container Animation */}
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
            maxWidth: 450,
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
                <Shield
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
                AI Safety System
              </Typography>
              
              <Typography
                variant="body1"
                sx={{
                  color: 'rgba(255, 255, 255, 0.7)',
                  mb: 1,
                }}
              >
                Secure Authentication Portal
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Computer sx={{ fontSize: 16, color: '#00D4AA' }} />
                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                    Enterprise Grade
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Lock sx={{ fontSize: 16, color: '#00D4AA' }} />
                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                    Encrypted
                  </Typography>
                </Box>
              </Box>
            </Box>

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

            {/* Login Form */}
            <Box component="form" onSubmit={handleSubmit}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                <TextField
                fullWidth
                label="Email Address"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
                error={Boolean(errors.email)}
                helperText={errors.email}
                disabled={isLoading}
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
                  '& .MuiFormHelperText-root': {
                    color: '#ef4444',
                  },
                }}
              />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4, duration: 0.5 }}
              >
                <TextField
                fullWidth
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleInputChange('password')}
                error={Boolean(errors.password)}
                helperText={errors.password}
                disabled={isLoading}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={togglePasswordVisibility}
                        edge="end"
                        sx={{ color: 'rgba(255, 255, 255, 0.7)' }}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 4,
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
                  '& .MuiFormHelperText-root': {
                    color: '#ef4444',
                  },
                }}
              />
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6, duration: 0.5 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Button
                  fullWidth
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={isLoading}
                  startIcon={!isLoading ? <Bolt /> : null}
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
                  {isLoading ? 'Authenticating...' : 'Sign In'}
                </Button>
              </motion.div>

              {/* Development Bypass Button */}
              {showBypass && (
                <Fade in={showBypass}>
                  <Box sx={{ mt: 2 }}>
                    <Tooltip title="Development bypass - uses test credentials">
                      <Button
                        fullWidth
                        variant="outlined"
                        size="small"
                        onClick={handleBypassLogin}
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
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Typography
                variant="caption"
                sx={{
                  color: 'rgba(255, 255, 255, 0.5)',
                  fontSize: '11px',
                }}
              >
                Powered by Supabase • Certificate Protected
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default LoginPage;