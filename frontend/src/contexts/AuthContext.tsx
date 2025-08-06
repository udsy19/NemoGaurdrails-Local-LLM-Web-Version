import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth, SessionResponse } from '../hooks/useAuth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLicenseValidated: boolean;
  isLoading: boolean;
  error: string | null;
  session: any;
  login: (email: string, password: string, useBypass?: boolean) => Promise<any>;
  verifyLicense: (licenseUuid: string, useBypass?: boolean) => Promise<any>;
  logout: () => Promise<boolean>;
  refreshSession: () => Promise<boolean>;
  getSystemInfo: () => Promise<any>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const {
    isAuthenticated,
    isLoading,
    error,
    session,
    login,
    verifyLicense,
    logout,
    refreshSession,
    getSystemInfo,
  } = useAuth();

  const [isLicenseValidated, setIsLicenseValidated] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Check session on app load
  useEffect(() => {
    const checkSession = async () => {
      try {
        const sessionData = await refreshSession();
        if (sessionData) {
          // Check if license is validated
          // This would typically come from the session data
          setIsLicenseValidated(true); // Placeholder - adjust based on actual session structure
        }
      } catch (err) {
        console.error('Session check failed:', err);
      } finally {
        setIsInitialized(true);
      }
    };

    checkSession();
  }, [refreshSession]);

  // Enhanced login function
  const enhancedLogin = async (email: string, password: string, useBypass: boolean = false) => {
    try {
      const result = await login(email, password, useBypass);
      return result;
    } catch (err) {
      console.error('Login failed:', err);
      throw err;
    }
  };

  // Enhanced license verification
  const enhancedVerifyLicense = async (licenseUuid: string, useBypass: boolean = false) => {
    try {
      const result = await verifyLicense(licenseUuid, useBypass);
      if (result.success) {
        setIsLicenseValidated(true);
      }
      return result;
    } catch (err) {
      console.error('License verification failed:', err);
      throw err;
    }
  };

  // Enhanced logout
  const enhancedLogout = async () => {
    try {
      const result = await logout();
      if (result) {
        setIsLicenseValidated(false);
      }
      return result;
    } catch (err) {
      console.error('Logout failed:', err);
      return false;
    }
  };

  const contextValue: AuthContextType = {
    isAuthenticated,
    isLicenseValidated,
    isLoading,
    error,
    session,
    login: enhancedLogin,
    verifyLicense: enhancedVerifyLicense,
    logout: enhancedLogout,
    refreshSession,
    getSystemInfo,
  };

  // Don't render children until authentication state is determined
  if (!isInitialized && !isAuthenticated) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0A0E1A 0%, #1A1F2E 50%, #2D1B3D 100%)',
        color: '#ffffff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '3px solid rgba(0, 212, 170, 0.3)',
            borderTop: '3px solid #00D4AA',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }} />
          <div>Initializing Authentication...</div>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};