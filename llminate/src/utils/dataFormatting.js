/**
 * Data Formatting Utilities for LLMinate Dashboard
 * Transforms raw WebSocket data into chart-ready formats
 */

export class DataFormatter {
  /**
   * Format timestamp for display
   */
  static formatTimestamp(timestamp, format = 'short') {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      
      switch (format) {
        case 'short':
          return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        
        case 'long':
          return date.toLocaleString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          });
        
        case 'time':
          return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
          });
        
        case 'date':
          return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
          });
        
        default:
          return date.toLocaleString();
      }
    } catch (error) {
      return 'Invalid date';
    }
  }

  /**
   * Format numbers with appropriate units
   */
  static formatNumber(num, options = {}) {
    if (num === null || num === undefined) return '0';
    
    const {
      precision = 0,
      useAbbreviation = false,
      unit = '',
      percentage = false
    } = options;

    let formattedNum = parseFloat(num);

    if (percentage) {
      formattedNum = formattedNum * 100;
      return `${formattedNum.toFixed(precision)}%`;
    }

    if (useAbbreviation) {
      const abbrev = ['', 'K', 'M', 'B', 'T'];
      let tier = Math.log10(Math.abs(formattedNum)) / 3 | 0;
      
      if (tier === 0) {
        return `${formattedNum.toFixed(precision)}${unit}`;
      }
      
      const suffix = abbrev[tier];
      const scale = Math.pow(10, tier * 3);
      const scaled = formattedNum / scale;
      
      return `${scaled.toFixed(precision)}${suffix}${unit}`;
    }

    return `${formattedNum.toFixed(precision)}${unit}`;
  }

  /**
   * Format chart data for time series
   */
  static formatTimeSeriesData(rawData, options = {}) {
    if (!Array.isArray(rawData)) return [];

    const {
      xField = 'timestamp',
      yField = 'value',
      timeFormat = 'short'
    } = options;

    return rawData.map(item => ({
      ...item,
      [xField]: this.formatTimestamp(item[xField], timeFormat),
      [yField]: parseFloat(item[yField]) || 0
    }));
  }

  /**
   * Transform dashboard data for charts
   */
  static transformDashboardData(dashboardData, timeframe = '24h') {
    if (!dashboardData || !dashboardData.time_ranges) {
      return {
        guardrailTrend: [],
        sensitiveDataBreakdown: [],
        providerAnalysis: [],
        threatTimeline: []
      };
    }

    const timeRangeData = dashboardData.time_ranges[timeframe] || {};

    return {
      guardrailTrend: this.formatGuardrailTrendData(timeRangeData.guardrail_analysis || {}),
      sensitiveDataBreakdown: this.formatSensitiveDataBreakdown(timeRangeData.sensitive_data || {}),
      providerAnalysis: this.formatProviderAnalysis(timeRangeData.provider_performance || {}),
      threatTimeline: this.formatThreatTimeline(timeRangeData.summary || {})
    };
  }

  /**
   * Format guardrail trend data for line charts
   */
  static formatGuardrailTrendData(guardrailData) {
    if (!guardrailData || typeof guardrailData !== 'object') return [];

    return Object.entries(guardrailData).map(([guardrailName, data]) => ({
      name: guardrailName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      effectiveness: data.effectiveness_percentage || 0,
      triggers: data.triggers || 0,
      confidence: data.avg_confidence || 0
    }));
  }

  /**
   * Format sensitive data breakdown for pie charts
   */
  static formatSensitiveDataBreakdown(sensitiveData) {
    if (!sensitiveData || typeof sensitiveData !== 'object') return [];

    const colors = [
      '#FF6B6B', // Red for high-risk data
      '#FFB800', // Yellow for medium-risk data
      '#00D4AA', // Green for low-risk data
      '#3B82F6', // Blue for informational
      '#9C27B0', // Purple for other
      '#FF5722'  // Deep orange for critical
    ];

    return Object.entries(sensitiveData)
      .map(([dataType, count], index) => ({
        name: this.formatDataTypeName(dataType),
        value: count,
        color: colors[index % colors.length]
      }))
      .sort((a, b) => b.value - a.value);
  }

  /**
   * Format provider analysis data for bar charts
   */
  static formatProviderAnalysis(providerData) {
    if (!providerData || typeof providerData !== 'object') return [];

    return Object.entries(providerData).map(([provider, data]) => ({
      name: provider,
      requests: data.total_requests || 0,
      blocked: data.blocked_responses || 0,
      responseTime: data.avg_response_time_ms || 0,
      errorRate: (data.error_rate * 100) || 0,
      cost: data.total_cost || 0
    }));
  }

  /**
   * Format threat timeline data
   */
  static formatThreatTimeline(summaryData) {
    if (!summaryData) return [];

    const threats = [
      {
        type: 'Data Exfiltration',
        count: summaryData.data_exfiltration_attempts || 0,
        severity: 'high'
      },
      {
        type: 'Prompt Injection',
        count: summaryData.prompt_injection_attempts || 0,
        severity: 'medium'
      },
      {
        type: 'Toxic Content',
        count: summaryData.toxicity_triggers || 0,
        severity: 'medium'
      }
    ];

    return threats
      .filter(threat => threat.count > 0)
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Format user data for tables
   */
  static formatUserData(userData) {
    if (!Array.isArray(userData)) return [];

    return userData.map(user => ({
      ...user,
      risk_score: parseInt(user.risk_score) || 0,
      blocked_percentage: parseFloat(user.blocked_percentage) || 0,
      last_active: this.formatTimestamp(user.last_active, 'long'),
      total_requests: parseInt(user.total_requests) || 0
    }));
  }

  /**
   * Format data type names for display
   */
  static formatDataTypeName(dataType) {
    const typeMap = {
      'PII_DETECTION': 'Personal Information',
      'CREDIT_CARD': 'Credit Cards',
      'EMAIL_ADDRESS': 'Email Addresses',
      'API_KEYS': 'API Keys',
      'TOXIC_CONTENT': 'Toxic Content',
      'PROMPT_INJECTION': 'Prompt Injection',
      'HATE_SPEECH': 'Hate Speech',
      'BIAS_CONTENT': 'Biased Content'
    };

    return typeMap[dataType] || dataType.replace(/_/g, ' ').toLowerCase()
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Create color scale for risk visualization
   */
  static getRiskColorScale(value, max = 100) {
    const percentage = (value / max) * 100;
    
    if (percentage >= 70) return '#FF3D71';  // High risk - red
    if (percentage >= 40) return '#FFB800';  // Medium risk - yellow
    return '#00D4AA';                        // Low risk - green
  }

  /**
   * Format bytes to human readable format
   */
  static formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * Calculate percentage change
   */
  static calculatePercentageChange(current, previous) {
    if (!previous || previous === 0) return 0;
    return ((current - previous) / previous) * 100;
  }

  /**
   * Format trend indicators
   */
  static formatTrendIndicator(current, previous) {
    const change = this.calculatePercentageChange(current, previous);
    
    return {
      value: Math.abs(change).toFixed(1),
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
      color: change > 0 ? 'error' : change < 0 ? 'success' : 'info'
    };
  }

  /**
   * Sanitize and validate data
   */
  static sanitizeData(data) {
    if (data === null || data === undefined) return null;
    
    if (typeof data === 'string') {
      // Remove potential XSS content
      return data.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                 .replace(/javascript:/gi, '')
                 .replace(/on\w+=/gi, '');
    }
    
    if (typeof data === 'object' && !Array.isArray(data)) {
      const sanitized = {};
      Object.keys(data).forEach(key => {
        sanitized[key] = this.sanitizeData(data[key]);
      });
      return sanitized;
    }
    
    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeData(item));
    }
    
    return data;
  }
}

export default DataFormatter;