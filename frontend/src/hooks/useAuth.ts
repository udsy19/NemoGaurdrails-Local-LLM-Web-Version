import { useState, useCallback } from 'react';
import api from '../services/api';

export interface LoginResponse {
  success: boolean;
  message: string;
  session?: any;
  requires_license: boolean;
  error?: string;
}

export interface LicenseVerificationResponse {
  success: boolean;
  message: string;
  license_id?: string;
  system_info?: any;
  error?: string;
}

export interface SessionResponse {
  is_authenticated: boolean;
  session_info?: any;
  license_validated: boolean;
  certificate_status?: any;
}

export interface SystemInfoResponse {
  system_info: any;
  certificate_status: any;
  timestamp: string;
}

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<any>(null);

  const login = useCallback(async (
    email: string,
    password: string,
    useBypass: boolean = false
  ): Promise<LoginResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await api.login(email, password, useBypass);

      if (data.success) {
        setIsAuthenticated(true);
        setSession(data.session);
        setError(null);
      } else {
        setError(data.error || 'Login failed');
      }

      return data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed';
      setError(errorMessage);
      return {
        success: false,
        message: 'Login failed',
        requires_license: false,
        error: errorMessage,
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const verifyLicense = useCallback(async (
    licenseUuid: string,
    useBypass: boolean = false
  ): Promise<LicenseVerificationResponse> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.verifyLicense(licenseUuid, useBypass);
      const data = response.data;

      if (!data.success) {
        setError(data.error || 'License verification failed');
      }

      return data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'License verification failed';
      setError(errorMessage);
      return {
        success: false,
        message: 'License verification failed',
        error: errorMessage,
      };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);

    try {
      await api.logout();
      setIsAuthenticated(false);
      setSession(null);
      setError(null);
      return true;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Logout failed';
      setError(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getSession = useCallback(async (): Promise<SessionResponse | null> => {
    try {
      const response = await api.getSession();
      return response.data;
    } catch (err) {
      console.error('Failed to get session:', err);
      return null;
    }
  }, []);

  const getSystemInfo = useCallback(async (): Promise<SystemInfoResponse> => {
    const response = await api.getSystemInfo();
    return response.data;
  }, []);

  const refreshSession = useCallback(async (): Promise<boolean> => {
    try {
      const sessionData = await getSession();
      if (sessionData?.is_authenticated) {
        setIsAuthenticated(true);
        setSession(sessionData.session_info);
        return true;
      } else {
        setIsAuthenticated(false);
        setSession(null);
        return false;
      }
    } catch (err) {
      console.error('Session refresh failed:', err);
      setIsAuthenticated(false);
      setSession(null);
      return false;
    }
  }, [getSession]);

  return {
    isAuthenticated,
    isLoading,
    error,
    session,
    login,
    verifyLicense,
    logout,
    getSession,
    getSystemInfo,
    refreshSession,
  };
};