export interface OllamaModel {
  name: string;
  library_path: string;
  description: string;
  capabilities: string[];
  sizes: string[];
  pull_count: string;
  tag_count: number;
  updated: string;
  compatibility_score: number;
  compatibility_label: 'Excellent' | 'Good' | 'Fair' | 'Limited';
  estimated_memory_usage: string;
  recommended_for: string[];
  performance_tier: 'Ultra Fast' | 'Fast' | 'Moderate' | 'Slow';
}

export interface SystemSpecs {
  totalMemoryGB: number;
  availableMemoryGB: number;
  cpuCores: number;
  platform: string;
  architecture: string;
  hasGPU: boolean;
  gpuMemoryGB?: number;
}

class OllamaModelsService {
  private modelsCache: OllamaModel[] = [];
  private cacheTimestamp: number = 0;
  private readonly CACHE_DURATION = 10 * 60 * 1000; // 10 minutes

  /**
   * Fetch models from Ollama search page (via backend proxy to avoid CORS)
   */
  async fetchAvailableModels(): Promise<OllamaModel[]> {
    // Check cache first
    if (this.modelsCache.length > 0 && Date.now() - this.cacheTimestamp < this.CACHE_DURATION) {
      return this.modelsCache;
    }

    try {
      // Call our backend endpoint that will proxy the Ollama search
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/models/search`);
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const models = await response.json();
      
      // Get system specs for compatibility scoring
      const systemSpecs = await this.getSystemSpecs();
      
      // Process and score models
      this.modelsCache = models.map((model: any) => this.processModel(model, systemSpecs));
      this.cacheTimestamp = Date.now();
      
      return this.modelsCache;
    } catch (error) {
      console.error('Failed to fetch Ollama models:', error);
      // Return fallback popular models if fetch fails
      return this.getFallbackModels();
    }
  }

  /**
   * Get system specifications for compatibility scoring
   */
  private async getSystemSpecs(): Promise<SystemSpecs> {
    try {
      // Try to get system info from our backend
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/system/info`);
      if (response.ok) {
        const systemInfo = await response.json();
        return {
          totalMemoryGB: systemInfo.memory?.total ? systemInfo.memory.total / 1024 : 8,
          availableMemoryGB: systemInfo.memory?.available ? systemInfo.memory.available / 1024 : 4,
          cpuCores: systemInfo.cpu?.cores || 4,
          platform: systemInfo.platform || 'unknown',
          architecture: systemInfo.arch || 'x64',
          hasGPU: systemInfo.gpu?.available || false,
          gpuMemoryGB: systemInfo.gpu?.memory ? systemInfo.gpu.memory / 1024 : undefined,
        };
      }
    } catch (error) {
      console.error('Failed to get system specs:', error);
    }

    // Fallback to reasonable defaults
    return {
      totalMemoryGB: 16,
      availableMemoryGB: 8,
      cpuCores: 8,
      platform: 'darwin',
      architecture: 'arm64',
      hasGPU: false,
    };
  }

  /**
   * Process raw model data and add compatibility scoring
   */
  private processModel(rawModel: any, systemSpecs: SystemSpecs): OllamaModel {
    const sizes = rawModel.sizes || [];
    const compatibility = this.calculateCompatibility(sizes, rawModel.capabilities, systemSpecs);
    
    return {
      name: rawModel.name,
      library_path: rawModel.library_path,
      description: rawModel.description,
      capabilities: rawModel.capabilities || [],
      sizes: sizes,
      pull_count: rawModel.pull_count || '0',
      tag_count: rawModel.tag_count || 0,
      updated: rawModel.updated || 'Unknown',
      compatibility_score: compatibility.score,
      compatibility_label: compatibility.label,
      estimated_memory_usage: compatibility.memoryUsage,
      recommended_for: this.getRecommendedUse(rawModel.capabilities, compatibility.score),
      performance_tier: compatibility.performanceTier,
    };
  }

  /**
   * Calculate compatibility score based on model requirements and system specs
   */
  private calculateCompatibility(sizes: string[], capabilities: string[], systemSpecs: SystemSpecs) {
    let score = 100;
    let memoryUsage = 'Unknown';
    let performanceTier: 'Ultra Fast' | 'Fast' | 'Moderate' | 'Slow' = 'Fast';

    if (sizes.length === 0) {
      return {
        score: 50,
        label: 'Fair' as const,
        memoryUsage: 'Unknown',
        performanceTier: 'Moderate' as const,
      };
    }

    // Find the largest and smallest model sizes
    const modelSizes = sizes
      .map(size => this.parseModelSize(size))
      .filter(size => size > 0)
      .sort((a, b) => a - b);

    if (modelSizes.length === 0) {
      return {
        score: 60,
        label: 'Fair' as const,
        memoryUsage: 'Unknown',
        performanceTier: 'Moderate' as const,
      };
    }

    const smallestModel = modelSizes[0];
    const largestModel = modelSizes[modelSizes.length - 1];

    // Estimate memory usage (rough approximation)
    const estimatedMemoryGB = smallestModel * 1.5; // Models typically need 1.5x their size in memory
    memoryUsage = `~${estimatedMemoryGB.toFixed(1)}GB`;

    // Score based on memory compatibility
    const memoryRatio = estimatedMemoryGB / systemSpecs.availableMemoryGB;
    
    if (memoryRatio <= 0.5) {
      score = 100; // Excellent - plenty of memory
      performanceTier = 'Ultra Fast';
    } else if (memoryRatio <= 0.8) {
      score = 85;  // Good - comfortable fit
      performanceTier = 'Fast';
    } else if (memoryRatio <= 1.2) {
      score = 70;  // Fair - might work but tight
      performanceTier = 'Moderate';
    } else {
      score = 40;  // Limited - likely too large
      performanceTier = 'Slow';
    }

    // Adjust score based on CPU cores
    if (systemSpecs.cpuCores >= 8) {
      score += 5;
    } else if (systemSpecs.cpuCores <= 4) {
      score -= 10;
    }

    // Adjust score for special capabilities
    if (capabilities.includes('vision') && !systemSpecs.hasGPU) {
      score -= 15; // Vision models work better with GPU
    }
    
    if (capabilities.includes('thinking')) {
      score -= 5; // Thinking models are generally more resource intensive
    }

    // Determine compatibility label
    let label: 'Excellent' | 'Good' | 'Fair' | 'Limited';
    if (score >= 90) label = 'Excellent';
    else if (score >= 75) label = 'Good';
    else if (score >= 60) label = 'Fair';
    else label = 'Limited';

    return {
      score: Math.max(0, Math.min(100, score)),
      label,
      memoryUsage,
      performanceTier,
    };
  }

  /**
   * Parse model size string (e.g., "7b", "120b") to number in GB
   */
  private parseModelSize(sizeStr: string): number {
    const match = sizeStr.match(/(\d+(?:\.\d+)?)\s*([bkmg]?)/i);
    if (!match) return 0;

    const value = parseFloat(match[1]);
    const unit = match[2].toLowerCase();

    switch (unit) {
      case 'b': return value; // Assume billions of parameters ≈ GB
      case 'k': return value / 1000;
      case 'm': return value / 1000;
      case 'g': return value;
      default: return value; // Default to GB
    }
  }

  /**
   * Get recommended use cases based on capabilities and compatibility
   */
  private getRecommendedUse(capabilities: string[], compatibilityScore: number): string[] {
    const recommendations: string[] = [];

    if (compatibilityScore >= 90) {
      recommendations.push('Production Use');
    }
    
    if (capabilities.includes('tools')) {
      recommendations.push('Code Generation', 'API Integration');
    }
    
    if (capabilities.includes('vision')) {
      recommendations.push('Image Analysis', 'Document Processing');
    }
    
    if (capabilities.includes('thinking')) {
      recommendations.push('Complex Reasoning', 'Problem Solving');
    }
    
    if (capabilities.includes('embedding')) {
      recommendations.push('Semantic Search', 'Text Analysis');
    }

    if (recommendations.length === 0) {
      recommendations.push('General Chat', 'Text Generation');
    }

    return recommendations;
  }

  /**
   * Get fallback models if API fetch fails
   */
  private getFallbackModels(): OllamaModel[] {
    const fallbackModels = [
      {
        name: 'llama3.2',
        library_path: '/library/llama3.2',
        description: 'Meta\'s Llama 3.2 model - efficient and capable',
        capabilities: ['tools'],
        sizes: ['1b', '3b'],
        pull_count: '2.1M',
        tag_count: 6,
        updated: 'a month ago',
      },
      {
        name: 'qwen2.5',
        library_path: '/library/qwen2.5',
        description: 'Alibaba\'s latest Qwen model with strong reasoning',
        capabilities: ['tools', 'thinking'],
        sizes: ['0.5b', '1.5b', '7b', '14b'],
        pull_count: '1.8M',
        tag_count: 8,
        updated: '2 months ago',
      },
      {
        name: 'gemma2',
        library_path: '/library/gemma2',
        description: 'Google\'s Gemma 2 - fast and efficient',
        capabilities: ['tools'],
        sizes: ['2b', '9b', '27b'],
        pull_count: '1.5M',
        tag_count: 5,
        updated: '3 months ago',
      },
    ];

    return fallbackModels.map(model => this.processModel(model, {
      totalMemoryGB: 16,
      availableMemoryGB: 8,
      cpuCores: 8,
      platform: 'darwin',
      architecture: 'arm64',
      hasGPU: false,
    }));
  }

  /**
   * Get top recommended models for the current system
   */
  async getTopRecommendations(limit: number = 6): Promise<OllamaModel[]> {
    const allModels = await this.fetchAvailableModels();
    
    return allModels
      .sort((a, b) => b.compatibility_score - a.compatibility_score)
      .slice(0, limit);
  }

  /**
   * Search models by name or description
   */
  async searchModels(query: string): Promise<OllamaModel[]> {
    const allModels = await this.fetchAvailableModels();
    const lowerQuery = query.toLowerCase();
    
    return allModels.filter(model => 
      model.name.toLowerCase().includes(lowerQuery) ||
      model.description.toLowerCase().includes(lowerQuery) ||
      model.capabilities.some(cap => cap.toLowerCase().includes(lowerQuery))
    );
  }

  /**
   * Filter models by capabilities
   */
  async filterByCapabilities(capabilities: string[]): Promise<OllamaModel[]> {
    const allModels = await this.fetchAvailableModels();
    
    return allModels.filter(model =>
      capabilities.every(cap => model.capabilities.includes(cap))
    );
  }

  /**
   * Get models by compatibility level
   */
  async getModelsByCompatibility(level: 'Excellent' | 'Good' | 'Fair' | 'Limited'): Promise<OllamaModel[]> {
    const allModels = await this.fetchAvailableModels();
    
    return allModels.filter(model => model.compatibility_label === level);
  }
}

export const ollamaModelsService = new OllamaModelsService();