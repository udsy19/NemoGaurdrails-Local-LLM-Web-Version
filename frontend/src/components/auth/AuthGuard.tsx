import React, { useState } from 'react';
import { useAuthContext } from '../../contexts/AuthContext';
import LoginPage from './LoginPage';
import LicenseVerification from './LicenseVerification';
import { Box, Fade, Alert, IconButton } from '@mui/material';
import { Close } from '@mui/icons-material';

interface AuthGuardProps {
  children: React.ReactNode;
}

enum AuthState {
  LOGIN = 'login',
  LICENSE_VERIFICATION = 'license_verification',
  AUTHENTICATED = 'authenticated'
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { 
    isAuthenticated, 
    isLicenseValidated, 
    login, 
    verifyLicense, 
    error 
  } = useAuthContext();

  const [authState, setAuthState] = useState<AuthState>(AuthState.LOGIN);
  const [sessionData, setSessionData] = useState<any>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Determine current authentication state
  React.useEffect(() => {
    if (isAuthenticated && isLicenseValidated) {
      setAuthState(AuthState.AUTHENTICATED);
    } else if (isAuthenticated && !isLicenseValidated) {
      setAuthState(AuthState.LICENSE_VERIFICATION);
    } else {
      setAuthState(AuthState.LOGIN);
    }
  }, [isAuthenticated, isLicenseValidated]);

  const handleLoginSuccess = (sessionData: any) => {
    setSessionData(sessionData);
    setAuthError(null);
    
    if (sessionData.requires_license || !isLicenseValidated) {
      setAuthState(AuthState.LICENSE_VERIFICATION);
    } else {
      setAuthState(AuthState.AUTHENTICATED);
    }
  };

  const handleRequireLicense = (sessionData: any) => {
    setSessionData(sessionData);
    setAuthError(null);
    setAuthState(AuthState.LICENSE_VERIFICATION);
  };

  const handleLicenseVerificationSuccess = (licenseData: any) => {
    setAuthError(null);
    setAuthState(AuthState.AUTHENTICATED);
  };

  const handleBackToLogin = () => {
    setAuthState(AuthState.LOGIN);
    setSessionData(null);
    setAuthError(null);
  };

  const clearError = () => {
    setAuthError(null);
  };

  // Show error alert if there's an authentication error
  const ErrorAlert = () => {
    if (!authError && !error) return null;

    return (
      <Fade in={Boolean(authError || error)}>
        <Alert
          severity="error"
          action={
            <IconButton
              size="small"
              onClick={clearError}
              sx={{ color: 'inherit' }}
            >
              <Close />
            </IconButton>
          }
          sx={{
            position: 'fixed',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 9999,
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#ffffff',
            backdropFilter: 'blur(10px)',
            '& .MuiAlert-icon': {
              color: '#ef4444',
            },
          }}
        >
          {authError || error}
        </Alert>
      </Fade>
    );
  };

  // Render based on authentication state
  const renderAuthFlow = () => {
    switch (authState) {
      case AuthState.LOGIN:
        return (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onRequireLicense={handleRequireLicense}
          />
        );
      
      case AuthState.LICENSE_VERIFICATION:
        return (
          <LicenseVerification
            sessionData={sessionData}
            onVerificationSuccess={handleLicenseVerificationSuccess}
            onBack={handleBackToLogin}
          />
        );
      
      case AuthState.AUTHENTICATED:
        return (
          <Fade in={true} timeout={500}>
            <Box>
              {children}
            </Box>
          </Fade>
        );
      
      default:
        return (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onRequireLicense={handleRequireLicense}
          />
        );
    }
  };

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh' }}>
      <ErrorAlert />
      {renderAuthFlow()}
    </Box>
  );
};

export default AuthGuard;