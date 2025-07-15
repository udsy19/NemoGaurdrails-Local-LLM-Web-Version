import { toast } from 'react-hot-toast';

export interface DownloadProgress {
  model: string;
  status: 'downloading' | 'completed' | 'error' | 'cancelled';
  total: number;
  completed: number;
  percentage: number;
  speed?: string;
  eta?: string;
  message?: string;
  error?: string;
}

export type ProgressCallback = (progress: DownloadProgress) => void;

class OllamaDownloadService {
  private activeDownloads: Map<string, AbortController> = new Map();

  async downloadModel(
    modelName: string,
    onProgress: ProgressCallback
  ): Promise<void> {
    // Check if model is already being downloaded
    if (this.activeDownloads.has(modelName)) {
      throw new Error(`Model ${modelName} is already being downloaded`);
    }

    const controller = new AbortController();
    this.activeDownloads.set(modelName, controller);

    try {
      const response = await fetch(`http://localhost:8000/api/ollama/pull/${modelName}`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process each line in the buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              const progress = this.parseOllamaProgress(modelName, data);
              onProgress(progress);
              
              // Check if download completed
              if (data.status === 'success' || progress.status === 'completed') {
                this.activeDownloads.delete(modelName);
                return;
              }
            } catch (parseError) {
              console.warn('Failed to parse progress line:', line, parseError);
            }
          }
        }
      }
      
      // If we reach here, download completed
      onProgress({
        model: modelName,
        status: 'completed',
        total: 100,
        completed: 100,
        percentage: 100,
        message: 'Download completed successfully'
      });
      
      this.activeDownloads.delete(modelName);
      
    } catch (error) {
      this.activeDownloads.delete(modelName);
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          onProgress({
            model: modelName,
            status: 'cancelled',
            total: 100,
            completed: 0,
            percentage: 0,
            message: 'Download cancelled'
          });
        } else {
          onProgress({
            model: modelName,
            status: 'error',
            total: 100,
            completed: 0,
            percentage: 0,
            error: error.message
          });
        }
      }
      
      throw error;
    }
  }

  cancelDownload(modelName: string): void {
    const controller = this.activeDownloads.get(modelName);
    if (controller) {
      controller.abort();
      this.activeDownloads.delete(modelName);
      toast.success(`Download cancelled for ${modelName}`);
    }
  }

  isDownloading(modelName: string): boolean {
    return this.activeDownloads.has(modelName);
  }

  getActiveDownloads(): string[] {
    return Array.from(this.activeDownloads.keys());
  }

  private parseOllamaProgress(modelName: string, data: any): DownloadProgress {
    const progress: DownloadProgress = {
      model: modelName,
      status: 'downloading',
      total: data.total || 100,
      completed: data.completed || 0,
      percentage: 0,
      message: data.status || 'Downloading...'
    };

    // Calculate percentage
    if (progress.total > 0) {
      progress.percentage = Math.round((progress.completed / progress.total) * 100);
    }

    // Parse different Ollama progress formats
    if (data.status === 'pulling manifest') {
      progress.message = 'Pulling manifest...';
      progress.percentage = 10;
    } else if (data.status === 'downloading') {
      progress.message = `Downloading... ${this.formatBytes(data.completed)}/${this.formatBytes(data.total)}`;
      if (data.total > 0) {
        progress.percentage = Math.round((data.completed / data.total) * 100);
      }
    } else if (data.status === 'verifying sha256 digest') {
      progress.message = 'Verifying integrity...';
      progress.percentage = 95;
    } else if (data.status === 'writing manifest') {
      progress.message = 'Writing manifest...';
      progress.percentage = 98;
    } else if (data.status === 'removing any unused layers') {
      progress.message = 'Cleaning up...';
      progress.percentage = 99;
    } else if (data.status === 'success') {
      progress.status = 'completed';
      progress.percentage = 100;
      progress.message = 'Download completed successfully';
    }

    // Handle error status
    if (data.error) {
      progress.status = 'error';
      progress.error = data.error;
      progress.message = `Error: ${data.error}`;
    }

    return progress;
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

export const ollamaDownloadService = new OllamaDownloadService();
export default ollamaDownloadService;