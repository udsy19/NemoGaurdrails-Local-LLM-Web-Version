import { useState, useEffect, useCallback } from 'react';
import { ollamaModelsService, OllamaModel } from '../services/ollamaModels';

interface UseOllamaModelsResult {
  models: OllamaModel[];
  topRecommended: OllamaModel[];
  isLoading: boolean;
  error: string | null;
  refreshModels: () => Promise<void>;
  searchModels: (query: string) => Promise<OllamaModel[]>;
  filterByCapabilities: (capabilities: string[]) => Promise<OllamaModel[]>;
  getModelsByCompatibility: (level: 'Excellent' | 'Good' | 'Fair' | 'Limited') => Promise<OllamaModel[]>;
}

interface UseOllamaModelsOptions {
  autoFetch?: boolean;
  topRecommendedCount?: number;
}

export const useOllamaModels = (options: UseOllamaModelsOptions = {}): UseOllamaModelsResult => {
  const { autoFetch = true, topRecommendedCount = 6 } = options;
  
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [topRecommended, setTopRecommended] = useState<OllamaModel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshModels = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const [allModels, recommendedModels] = await Promise.all([
        ollamaModelsService.fetchAvailableModels(),
        ollamaModelsService.getTopRecommendations(topRecommendedCount),
      ]);
      
      console.log(`✓ useOllamaModels: Fetched ${allModels.length} models, ${recommendedModels.length} recommended`);
      
      setModels(allModels);
      setTopRecommended(recommendedModels);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch models';
      setError(errorMessage);
      console.error('Error fetching Ollama models:', err);
    } finally {
      setIsLoading(false);
    }
  }, [topRecommendedCount]);

  const searchModels = useCallback(async (query: string): Promise<OllamaModel[]> => {
    try {
      return await ollamaModelsService.searchModels(query);
    } catch (err) {
      console.error('Error searching models:', err);
      return [];
    }
  }, []);

  const filterByCapabilities = useCallback(async (capabilities: string[]): Promise<OllamaModel[]> => {
    try {
      return await ollamaModelsService.filterByCapabilities(capabilities);
    } catch (err) {
      console.error('Error filtering models by capabilities:', err);
      return [];
    }
  }, []);

  const getModelsByCompatibility = useCallback(async (level: 'Excellent' | 'Good' | 'Fair' | 'Limited'): Promise<OllamaModel[]> => {
    try {
      return await ollamaModelsService.getModelsByCompatibility(level);
    } catch (err) {
      console.error('Error getting models by compatibility:', err);
      return [];
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      refreshModels();
    }
  }, [refreshModels, autoFetch]);

  return {
    models,
    topRecommended,
    isLoading,
    error,
    refreshModels,
    searchModels,
    filterByCapabilities,
    getModelsByCompatibility,
  };
};