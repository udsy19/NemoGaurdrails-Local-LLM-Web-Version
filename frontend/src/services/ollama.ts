import axios from 'axios';

export interface OllamaModel {
  name: string;
  tag: string;
  size: number;
  modified_at: string;
  digest: string;
  details?: {
    parent_model?: string;
    format?: string;
    family?: string;
    families?: string[];
    parameter_size?: string;
    quantization_level?: string;
  };
}

export interface ModelSearchResult {
  name: string;
  description?: string;
  tags: string[];
  size: number;
  pulls: number;
  updated_at: string;
  featured?: boolean;
  popular?: boolean;
}

export interface SystemInfo {
  gpu?: {
    vendor: string;
    model: string;
    memory: number;
  };
  cpu: {
    cores: number;
    model: string;
  };
  memory: {
    total: number;
    available: number;
  };
  platform: string;
}

export interface ModelRecommendation {
  model: ModelSearchResult;
  reason: string;
  performance: 'excellent' | 'good' | 'acceptable' | 'poor';
  compatibility: 'perfect' | 'good' | 'partial' | 'incompatible';
}

class OllamaService {
  private baseURL: string;
  
  constructor(baseURL: string = 'http://localhost:11434') {
    this.baseURL = baseURL;
  }

  // Get locally installed models
  async getLocalModels(): Promise<OllamaModel[]> {
    try {
      const response = await axios.get(`${this.baseURL}/api/tags`);
      return response.data.models || [];
    } catch (error) {
      console.error('Failed to fetch local models:', error);
      return [];
    }
  }

  // Get system information for hardware detection
  async getSystemInfo(): Promise<SystemInfo> {
    try {
      // Try to get system info from backend first
      const response = await axios.get('http://localhost:8000/api/system/info');
      return response.data;
    } catch (error) {
      // Fallback to browser-based detection
      return this.detectBrowserSystemInfo();
    }
  }

  private detectBrowserSystemInfo(): SystemInfo {
    const nav = navigator as any;
    const platform = nav.platform || nav.userAgentData?.platform || 'unknown';
    
    // Estimate system specs (rough browser-based detection)
    const hardwareConcurrency = nav.hardwareConcurrency || 4;
    const memory = (nav.deviceMemory || 8) * 1024; // Convert GB to MB
    
    return {
      cpu: {
        cores: hardwareConcurrency,
        model: 'Browser detected CPU',
      },
      memory: {
        total: memory,
        available: memory * 0.7, // Estimate 70% available
      },
      platform: platform,
    };
  }

  // Search for available models (mock implementation - would need actual Ollama API)
  async searchModels(query?: string): Promise<ModelSearchResult[]> {
    // This would normally fetch from https://ollama.com/api/models or similar
    // For now, return popular models with mock data
    const popularModels: ModelSearchResult[] = [
      {
        name: 'llama3.2',
        description: 'Meta\'s latest Llama model with improved performance',
        tags: ['3b', '1b', '11b', '90b'],
        size: 2000000000, // 2GB
        pulls: 1500000,
        updated_at: '2024-09-25T00:00:00Z',
        featured: true,
        popular: true,
      },
      {
        name: 'phi3',
        description: 'Microsoft\'s efficient small language model',
        tags: ['mini', 'small', 'medium'],
        size: 2300000000,
        pulls: 800000,
        updated_at: '2024-08-15T00:00:00Z',
        popular: true,
      },
      {
        name: 'mistral',
        description: 'High-performance open-source model',
        tags: ['7b', '8x7b', '8x22b'],
        size: 4100000000,
        pulls: 1200000,
        updated_at: '2024-09-10T00:00:00Z',
        featured: true,
      },
      {
        name: 'codellama',
        description: 'Specialized model for code generation',
        tags: ['7b', '13b', '34b'],
        size: 3800000000,
        pulls: 900000,
        updated_at: '2024-08-20T00:00:00Z',
      },
      {
        name: 'gemma2',
        description: 'Google\'s latest Gemma model',
        tags: ['2b', '9b', '27b'],
        size: 1600000000,
        pulls: 600000,
        updated_at: '2024-09-01T00:00:00Z',
      },
      {
        name: 'qwen2.5',
        description: 'Alibaba\'s multilingual model',
        tags: ['0.5b', '1.5b', '3b', '7b', '14b', '32b', '72b'],
        size: 900000000,
        pulls: 400000,
        updated_at: '2024-09-15T00:00:00Z',
      },
      {
        name: 'llama3.1',
        description: 'Previous generation Llama model',
        tags: ['8b', '70b', '405b'],
        size: 4700000000,
        pulls: 2000000,
        updated_at: '2024-07-15T00:00:00Z',
      },
      {
        name: 'deepseek-coder',
        description: 'Specialized for coding tasks',
        tags: ['1.3b', '6.7b', '33b'],
        size: 1300000000,
        pulls: 300000,
        updated_at: '2024-08-05T00:00:00Z',
      },
    ];

    if (query) {
      return popularModels.filter(model => 
        model.name.toLowerCase().includes(query.toLowerCase()) ||
        model.description?.toLowerCase().includes(query.toLowerCase())
      );
    }

    return popularModels;
  }

  // Get model recommendations based on system specs
  async getRecommendations(systemInfo: SystemInfo): Promise<ModelRecommendation[]> {
    const models = await this.searchModels();
    const recommendations: ModelRecommendation[] = [];

    const { memory, cpu } = systemInfo;
    const availableMemory = memory.available;
    const cores = cpu.cores;

    for (const model of models) {
      const modelSizeGB = model.size / (1024 * 1024 * 1024);
      let performance: ModelRecommendation['performance'] = 'poor';
      let compatibility: ModelRecommendation['compatibility'] = 'incompatible';
      let reason = '';

      // Memory-based compatibility
      if (availableMemory > modelSizeGB * 1024 * 2) { // 2x model size for comfortable operation
        compatibility = 'perfect';
        if (cores >= 8) {
          performance = 'excellent';
          reason = `Perfect fit! You have ${(availableMemory/1024).toFixed(1)}GB RAM and ${cores} CPU cores.`;
        } else if (cores >= 4) {
          performance = 'good';
          reason = `Good performance expected with ${cores} CPU cores and sufficient RAM.`;
        } else {
          performance = 'acceptable';
          reason = `Will run but may be slower with ${cores} CPU cores.`;
        }
      } else if (availableMemory > modelSizeGB * 1024 * 1.5) {
        compatibility = 'good';
        performance = cores >= 4 ? 'good' : 'acceptable';
        reason = `Should work well, but monitor memory usage (${(availableMemory/1024).toFixed(1)}GB available).`;
      } else if (availableMemory > modelSizeGB * 1024) {
        compatibility = 'partial';
        performance = 'acceptable';
        reason = `Minimal memory for this model. Consider a smaller variant.`;
      } else {
        compatibility = 'incompatible';
        performance = 'poor';
        reason = `Not enough memory. Need at least ${modelSizeGB.toFixed(1)}GB, have ${(availableMemory/1024).toFixed(1)}GB.`;
      }

      recommendations.push({
        model,
        reason,
        performance,
        compatibility,
      });
    }

    // Sort by compatibility and performance
    return recommendations.sort((a, b) => {
      const compatOrder = { perfect: 4, good: 3, partial: 2, incompatible: 1 };
      const perfOrder = { excellent: 4, good: 3, acceptable: 2, poor: 1 };
      
      const aScore = compatOrder[a.compatibility] * 10 + perfOrder[a.performance];
      const bScore = compatOrder[b.compatibility] * 10 + perfOrder[b.performance];
      
      return bScore - aScore;
    });
  }

  // Pull/download a model
  async pullModel(modelName: string, onProgress?: (progress: any) => void): Promise<void> {
    try {
      const response = await fetch(`${this.baseURL}/api/pull`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: modelName }),
      });

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (onProgress) {
              onProgress(data);
            }
          } catch (e) {
            // Ignore malformed JSON lines
          }
        }
      }
    } catch (error) {
      console.error('Failed to pull model:', error);
      throw error;
    }
  }

  // Delete a model
  async deleteModel(modelName: string): Promise<void> {
    try {
      await axios.delete(`${this.baseURL}/api/delete`, {
        data: { name: modelName }
      });
    } catch (error) {
      console.error('Failed to delete model:', error);
      throw error;
    }
  }

  // Check if Ollama is running
  async isOllamaRunning(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseURL}/api/tags`, { timeout: 3000 });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  // Get model info
  async getModelInfo(modelName: string): Promise<any> {
    try {
      const response = await axios.post(`${this.baseURL}/api/show`, {
        name: modelName
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get model info:', error);
      throw error;
    }
  }
}

export const ollamaService = new OllamaService();
export default ollamaService;