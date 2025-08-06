import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface LLMModel {
  id: string;
  name: string;
  description: string;
  context_length: number;
  pricing?: {
    input: number;
    output: number;
  };
}

interface Provider {
  id: string;
  name: string;
  display_name: string;
  description: string;
  port: number;
  requires_api_key: boolean;
  models: LLMModel[];
  enabled: boolean;
  api_key: string;
  selected_model: string;
  status: 'connected' | 'disconnected' | 'testing' | 'error';
  last_tested?: string;
  error_message?: string;
}

interface ProviderStats {
  total_providers: number;
  enabled_providers: number;
  connected_providers: number;
  port_mappings: Record<number, string>;
  provider_summary: Array<{
    id: string;
    name: string;
    port: number;
    enabled: boolean;
    status: string;
    model: string;
  }>;
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const useProviders = () => {
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  const [stats, setStats] = useState<ProviderStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Load provider configurations from localStorage
  const loadProviderConfigs = useCallback(() => {
    try {
      const saved = localStorage.getItem('provider_configs');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load provider configs from localStorage:', error);
    }
    return {};
  }, []);
  
  // Save provider configurations to localStorage
  const saveProviderConfigs = useCallback((updatedProviders: Record<string, Provider>) => {
    try {
      const configsToSave = Object.values(updatedProviders || {}).reduce((acc, provider) => {
        acc[provider.id] = {
          api_key: provider.api_key,
          selected_model: provider.selected_model,
          enabled: provider.enabled
        };
        return acc;
      }, {} as Record<string, any>);
      
      localStorage.setItem('provider_configs', JSON.stringify(configsToSave));
    } catch (error) {
      console.error('Failed to save provider configs to localStorage:', error);
    }
  }, []);

  const fetchProviders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${BACKEND_URL}/api/providers/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Force update providers to ensure state sync
        console.log('🔄 Fetched providers:', Object.keys(data.providers).length, 'providers');
        console.log('🔗 Connected providers:', Object.values(data.providers || {}).filter((p: any) => p.status === 'connected').length);
        
        // Merge with saved configurations from localStorage
        const savedConfigs = loadProviderConfigs();
        const mergedProviders = { ...data.providers };
        
        Object.keys(mergedProviders).forEach(providerId => {
          const savedConfig = savedConfigs[providerId];
          if (savedConfig) {
            mergedProviders[providerId] = {
              ...mergedProviders[providerId],
              api_key: savedConfig.api_key || mergedProviders[providerId].api_key,
              selected_model: savedConfig.selected_model || mergedProviders[providerId].selected_model,
              enabled: savedConfig.enabled !== undefined ? savedConfig.enabled : mergedProviders[providerId].enabled
            };
          }
        });
        
        setProviders(mergedProviders);
        setStats(data.stats);
      } else {
        throw new Error('Failed to fetch providers');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast.error(`Failed to load providers: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProviderConfig = useCallback(async (
    providerId: string,
    config: {
      enabled?: boolean;
      api_key?: string;
      selected_model?: string;
    }
  ) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/${providerId}/config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state
        const updatedProviders = {
          ...providers,
          [providerId]: data.provider
        };
        setProviders(updatedProviders as Record<string, Provider>);
        
        // Save to localStorage
        saveProviderConfigs(updatedProviders);
        
        toast.success(data.message);
        return true;
      } else {
        throw new Error('Failed to update provider configuration');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to update provider: ${errorMessage}`);
      return false;
    }
  }, [providers, saveProviderConfigs]);

  const testConnection = useCallback(async (providerId: string) => {
    if (!providerId || providerId === 'undefined') {
      console.error('Invalid providerId for testConnection:', providerId);
      toast.error('Invalid provider ID');
      return false;
    }
    
    try {
      // Update local state to show testing
      setProviders(prev => ({
        ...prev,
        [providerId]: {
          ...prev[providerId],
          status: 'testing',
          error_message: undefined
        }
      }));
      
      const response = await fetch(`${BACKEND_URL}/api/providers/${providerId}/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state with test result
        setProviders(prev => ({
          ...prev,
          [providerId]: data.provider
        }));
        
        if (data.connection_success) {
          toast.success(`${data.provider.display_name} connection successful!`);
        } else {
          toast.error(`${data.provider.display_name} connection failed: ${data.error_message}`);
        }
        
        return data.connection_success;
      } else {
        throw new Error('Failed to test connection');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      // Update local state with error
      setProviders(prev => ({
        ...prev,
        [providerId]: {
          ...prev[providerId],
          status: 'error',
          error_message: errorMessage
        }
      }));
      
      toast.error(`Connection test failed: ${errorMessage}`);
      return false;
    }
  }, []);

  const enableProvider = useCallback(async (providerId: string, forcePort: boolean = false) => {
    if (!providerId || providerId === 'undefined') {
      console.error('Invalid providerId for enableProvider:', providerId);
      toast.error('Invalid provider ID');
      return { success: false, error: 'Invalid provider ID' };
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/${providerId}/enable${forcePort ? '?force_port=true' : ''}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state
        const updatedProviders = {
          ...providers,
          [providerId]: {
            ...providers[providerId],
            enabled: true,
            status: 'connected' as const
          }
        };
        setProviders(updatedProviders as Record<string, Provider>);
        
        // Save to localStorage
        saveProviderConfigs(updatedProviders);
        
        toast.success(data.message);
        return { success: true, data };
      } else {
        // Handle port conflict
        if (data.conflict) {
          return { success: false, conflict: true, data };
        }
        throw new Error(data.message || 'Failed to enable provider');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to enable provider: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }, [providers, saveProviderConfigs]);

  const disableProvider = useCallback(async (providerId: string) => {
    if (!providerId || providerId === 'undefined') {
      console.error('Invalid providerId for disableProvider:', providerId);
      toast.error('Invalid provider ID');
      return { success: false, error: 'Invalid provider ID' };
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/${providerId}/disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state
        const updatedProviders = {
          ...providers,
          [providerId]: {
            ...providers[providerId],
            enabled: false,
            status: 'disconnected' as const
          }
        };
        setProviders(updatedProviders as Record<string, Provider>);
        
        // Save to localStorage
        saveProviderConfigs(updatedProviders);
        
        toast.success(data.message);
        return { success: true, data };
      } else {
        throw new Error(data.message || 'Failed to disable provider');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to disable provider: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }, [providers, saveProviderConfigs]);

  const enableProviderWithPortSelection = useCallback(async (providerId: string, useNextAvailable: boolean = false) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/${providerId}/enable-with-port-selection${useNextAvailable ? '?use_next_available=true' : ''}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state
        setProviders(prev => ({
          ...prev,
          [providerId]: {
            ...prev[providerId],
            enabled: true,
            status: 'connected',
            port: data.new_port || prev[providerId].port
          }
        }));
        
        toast.success(data.message);
        return { success: true, data };
      } else {
        throw new Error(data.error || 'Failed to enable provider');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to enable provider: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }, []);

  const setApiKey = useCallback(async (providerId: string, apiKey: string) => {
    return await updateProviderConfig(providerId, { api_key: apiKey });
  }, [updateProviderConfig]);

  const selectModel = useCallback(async (providerId: string, modelId: string) => {
    return await updateProviderConfig(providerId, { selected_model: modelId });
  }, [updateProviderConfig]);

  const testAllConnections = useCallback(async () => {
    try {
      const enabledProviders = Object.values(providers || {}).filter(p => p.enabled);
      
      if (enabledProviders.length === 0) {
        toast('No enabled providers to test', { icon: 'ℹ️' });
        return;
      }

      // Update all enabled providers to testing state
      setProviders(prev => {
        const updated = { ...prev };
        enabledProviders.forEach(provider => {
          updated[provider.id] = {
            ...provider,
            status: 'testing',
            error_message: undefined
          };
        });
        return updated;
      });

      const response = await fetch(`${BACKEND_URL}/api/providers/test-all-connections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update all provider states
        setProviders(data.providers);
        
        const successCount = data.results.filter((r: any) => r.success).length;
        const totalCount = data.results.length;
        
        if (successCount === totalCount) {
          toast.success(`All ${totalCount} providers connected successfully!`);
        } else {
          toast(`${successCount}/${totalCount} providers connected successfully`, { icon: '⚠️' });
        }
        
        return data.results;
      } else {
        throw new Error('Failed to test all connections');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to test connections: ${errorMessage}`);
      return null;
    }
  }, [providers]);

  const getProviderByPort = useCallback(async (port: number) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/port/${port}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.provider;
      } else {
        throw new Error('Failed to get provider by port');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error(`Failed to get provider by port ${port}: ${errorMessage}`);
      return null;
    }
  }, []);

  const getProviderStats = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/providers/stats/summary`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setStats(data.stats);
        return data.stats;
      } else {
        throw new Error('Failed to get provider stats');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error(`Failed to get provider stats: ${errorMessage}`);
      return null;
    }
  }, []);

  // Load providers on mount
  useEffect(() => {
    fetchProviders();
  }, [fetchProviders, loadProviderConfigs]);

  // Auto-refresh stats every 30 seconds
  useEffect(() => {
    if (Object.keys(providers || {}).length > 0) {
      const interval = setInterval(getProviderStats, 30000);
      return () => clearInterval(interval);
    }
  }, [providers, getProviderStats]);

  return {
    providers: Object.values(providers || {}),
    providersMap: providers,
    stats,
    loading,
    error,
    
    // Actions
    fetchProviders,
    updateProviderConfig,
    testConnection,
    enableProvider,
    disableProvider,
    enableProviderWithPortSelection,
    setApiKey,
    selectModel,
    testAllConnections,
    getProviderByPort,
    getProviderStats,
    
    // Computed values
    enabledProviders: Object.values(providers || {}).filter(p => p.enabled),
    connectedProviders: Object.values(providers || {}).filter(p => p.enabled && p.status === 'connected'),
    availablePorts: Object.values(providers || {}).map(p => p.port),
  };
};