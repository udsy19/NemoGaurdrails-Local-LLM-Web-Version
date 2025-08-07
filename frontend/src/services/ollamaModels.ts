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

  // Force cache clear method
  clearCache() {
    this.modelsCache = [];
    this.cacheTimestamp = 0;
    localStorage.removeItem('ollamaModelsCache');
    localStorage.removeItem('ollamaCacheTime');
    console.log('🧹 Models cache cleared');
  }

  /**
   * Fetch models from Ollama search page (via backend proxy to avoid CORS)
   */
  async fetchAvailableModels(forceRefresh: boolean = false): Promise<OllamaModel[]> {
    // Clear cache if force refresh requested
    if (forceRefresh) {
      this.clearCache();
    }

    // Check cache first - completely disabled for debugging
    if (!forceRefresh) {
      console.log('⚡ Cache disabled - forcing fresh fetch');  
    }

    try {
      // Get system specs first (with caching)
      const systemSpecs = await this.getSystemSpecs();
      
      // Call our backend endpoint with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const apiUrl = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/models/search`;
      console.log('📡 Fetching models from:', apiUrl);
      console.log('🔄 Force refresh:', forceRefresh);
      
      const response = await fetch(apiUrl, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'max-age=600' // Prefer cached response if available
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📡 Raw API response:', { 
        type: typeof data, 
        isArray: Array.isArray(data),
        hasModels: !!data.models,
        dataKeys: Object.keys(data),
        modelsLength: Array.isArray(data.models) ? data.models.length : 'not array'
      });
      
      const models = data.models || data; // Handle both wrapper and direct array
      
      if (!Array.isArray(models)) {
        console.error('❌ Invalid response format:', data);
        throw new Error(`Invalid response format: expected array, got ${typeof models}`);
      }
      
      // Process and score models
      this.modelsCache = models.map((model: any) => this.processModel(model, systemSpecs));
      this.cacheTimestamp = Date.now();
      
      console.log(`✓ Fetched ${this.modelsCache.length} models from Ollama`);
      return this.modelsCache;
      
    } catch (error) {
      console.error('❌ Failed to fetch Ollama models:', error);
      console.error('Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : 'No stack'
      });
      
      // Return fallback popular models if fetch fails
      const fallback = this.getFallbackModels();
      console.log(`⚠️ Using ${fallback.length} fallback models due to error:`, error);
      
      // Cache fallback models to avoid repeated failures
      this.modelsCache = fallback;
      this.cacheTimestamp = Date.now();
      
      return fallback;
    }
  }

  /**
   * Get system specifications for compatibility scoring
   */
  private async getSystemSpecs(): Promise<SystemSpecs> {
    // Use cached system specs if available
    const cached = localStorage.getItem('systemSpecs');
    const cacheTime = localStorage.getItem('systemSpecsTime');
    
    if (cached && cacheTime && Date.now() - parseInt(cacheTime) < 5 * 60 * 1000) {
      return JSON.parse(cached);
    }

    try {
      // Try to get system info from our backend with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // 2 second timeout
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'}/api/system/info`, {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const systemInfo = await response.json();
        const specs = {
          totalMemoryGB: systemInfo.memory?.total ? systemInfo.memory.total / 1024 : 16,
          availableMemoryGB: systemInfo.memory?.available ? systemInfo.memory.available / 1024 : 8,
          cpuCores: systemInfo.cpu?.cores || 8,
          platform: systemInfo.platform || 'darwin',
          architecture: systemInfo.arch || 'arm64',
          hasGPU: systemInfo.gpu?.available || false,
          gpuMemoryGB: systemInfo.gpu?.memory ? systemInfo.gpu.memory / 1024 : undefined,
        };
        
        // Cache the result
        localStorage.setItem('systemSpecs', JSON.stringify(specs));
        localStorage.setItem('systemSpecsTime', Date.now().toString());
        
        return specs;
      }
    } catch (error) {
      // Silently fail - use defaults
    }

    // Fallback to reasonable defaults (optimized for modern systems)
    const defaultSpecs = {
      totalMemoryGB: 16,
      availableMemoryGB: 8,
      cpuCores: 8,
      platform: 'darwin',
      architecture: 'arm64',
      hasGPU: false,
    };
    
    // Cache defaults to avoid repeated failed requests
    localStorage.setItem('systemSpecs', JSON.stringify(defaultSpecs));
    localStorage.setItem('systemSpecsTime', Date.now().toString());
    
    return defaultSpecs;
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
    console.log('🛡️ Generating fallback models...');
    
    const fallbackModels = [
      {
        name: 'llama3.2',
        library_path: '/library/llama3.2',
        description: 'Meta\'s Llama 3.2 model - efficient and capable for most tasks',
        capabilities: ['tools'],
        sizes: ['1b', '3b'],
        pull_count: '28.5M',
        tag_count: 63,
        updated: '10 months ago',
      },
      {
        name: 'qwen2.5',
        library_path: '/library/qwen2.5',
        description: 'Alibaba\'s latest Qwen model with strong reasoning capabilities',
        capabilities: ['tools'],
        sizes: ['0.5b', '1.5b', '7b', '14b', '32b', '72b'],
        pull_count: '12M',
        tag_count: 133,
        updated: '10 months ago',
      },
      {
        name: 'gemma2',
        library_path: '/library/gemma2',
        description: 'Google Gemma 2 is a high-performing and efficient model',
        capabilities: [],
        sizes: ['2b', '9b', '27b'],
        pull_count: '6.2M',
        tag_count: 72,
        updated: '5 months ago',
      },
      {
        name: 'llama3.1',
        library_path: '/library/llama3.1',
        description: 'Llama 3.1 is a new state-of-the-art model from Meta',
        capabilities: ['tools'],
        sizes: ['8b', '70b', '405b'],
        pull_count: '99.5M',
        tag_count: 93,
        updated: '8 months ago',
      },
      {
        name: 'mistral',
        library_path: '/library/mistral',
        description: 'The 7B model released by Mistral AI, updated to version 0.3',
        capabilities: ['tools'],
        sizes: ['7b'],
        pull_count: '17.5M',
        tag_count: 84,
        updated: '3 weeks ago',
      },
      {
        name: 'gemma3',
        library_path: '/library/gemma3',
        description: 'The current, most capable model that runs on a single GPU',
        capabilities: ['vision'],
        sizes: ['1b', '4b', '12b', '27b'],
        pull_count: '10.9M',
        tag_count: 21,
        updated: '3 months ago',
      },
      {
        name: 'deepseek-r1',
        library_path: '/library/deepseek-r1',
        description: 'DeepSeek-R1 is a family of open reasoning models with performance approaching that of leading models',
        capabilities: ['tools', 'thinking'],
        sizes: ['1.5b', '7b', '8b', '14b', '32b', '70b', '671b'],
        pull_count: '56.2M',
        tag_count: 35,
        updated: '1 month ago',
      },
      {
        name: 'llava',
        library_path: '/library/llava',
        description: 'LLaVA is a novel end-to-end trained large multimodal model that combines vision and language understanding',
        capabilities: ['vision'],
        sizes: ['7b', '13b', '34b'],
        pull_count: '8.4M',
        tag_count: 98,
        updated: '1 year ago',
      }
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