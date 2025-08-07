/**
 * Risk Calculation Engine for LLMinate Dashboard
 * Implements the risk scoring algorithms defined in IMPLEMENTATION_MAP.md
 */

export class RiskCalculator {
  static calculateExecutiveRiskScore(data) {
    const weights = {
      dataExfiltration: 0.4,      // 40% - PII/Privacy triggers
      promptInjection: 0.3,       // 30% - Direct AI attacks
      blockedRequests: 0.2,       // 20% - General threat activity
      guardrailTrend: 0.1         // 10% - Declining effectiveness
    };

    // Ensure we have valid data
    const totalRequests = data.totalRequests || 1;
    const dataExfiltrationAttempts = data.dataExfiltrationAttempts || 0;
    const promptInjectionAttempts = data.promptInjectionAttempts || 0;
    const blockedRequests = data.blockedRequests || 0;
    const guardrailTrendSlope = data.guardrailTrendSlope || 0;

    // Normalize each metric to 0-100 scale
    const dataExfiltrationScore = Math.min(100, 
      (dataExfiltrationAttempts / totalRequests) * 500
    );

    const promptInjectionScore = Math.min(100,
      (promptInjectionAttempts / totalRequests) * 400
    );

    const blockedRequestsScore = Math.min(100,
      (blockedRequests / totalRequests) * 200
    );

    // Trend score: penalize declining effectiveness
    const trendScore = guardrailTrendSlope < 0 ? 100 : 0;

    // Calculate weighted final score
    const riskScore = Math.round(
      (dataExfiltrationScore * weights.dataExfiltration) +
      (promptInjectionScore * weights.promptInjection) +
      (blockedRequestsScore * weights.blockedRequests) +
      (trendScore * weights.guardrailTrend)
    );

    return Math.min(100, Math.max(0, riskScore));
  }

  static calculateUserRiskScore(userData) {
    // User-specific risk calculation
    // Based on: blocked percentage, violation severity, frequency
    const totalRequests = userData.totalRequests || 1;
    const blockedRequests = userData.blockedRequests || 0;
    const violationTypes = userData.violationTypes || {};
    const requestPattern = userData.requestPattern || {};

    const blockedPercentage = (blockedRequests / totalRequests) * 100;
    const violationSeverity = this.calculateViolationSeverity(violationTypes);
    const frequencyScore = this.calculateFrequencyScore(requestPattern);

    return Math.min(100, Math.max(0, 
      (blockedPercentage * 0.5) + 
      (violationSeverity * 0.3) + 
      (frequencyScore * 0.2)
    ));
  }

  static calculateViolationSeverity(violationTypes) {
    // Calculate severity based on violation types and counts
    if (!violationTypes || Object.keys(violationTypes).length === 0) {
      return 0;
    }

    const severityWeights = {
      'pii': 90,                    // PII violations are critical
      'data_exfiltration': 95,      // Data exfiltration is highest severity
      'prompt_injection': 80,       // Prompt injection attempts
      'toxicity': 60,               // Toxic content
      'hate_speech': 70,            // Hate speech
      'bias': 50,                   // Bias content
      'privacy': 85                 // Privacy violations
    };

    let totalSeverity = 0;
    let totalViolations = 0;

    Object.entries(violationTypes).forEach(([type, count]) => {
      const weight = severityWeights[type.toLowerCase()] || 40;
      totalSeverity += weight * count;
      totalViolations += count;
    });

    return totalViolations > 0 ? totalSeverity / totalViolations : 0;
  }

  static calculateFrequencyScore(requestPattern) {
    // Calculate frequency score based on request patterns
    if (!requestPattern) return 0;

    const requestsPerHour = requestPattern.requestsPerHour || 0;
    const burstiness = requestPattern.burstiness || 0;
    const timeSpread = requestPattern.timeSpread || 0;

    // High frequency = higher risk
    const frequencyFactor = Math.min(100, requestsPerHour * 2);
    
    // Bursty patterns (many requests in short time) = higher risk
    const burstFactor = Math.min(100, burstiness * 50);
    
    // Concentrated time patterns = higher risk
    const timeFactor = Math.min(100, (1 - timeSpread) * 100);

    return (frequencyFactor * 0.5) + (burstFactor * 0.3) + (timeFactor * 0.2);
  }

  static getRiskLevel(riskScore) {
    if (riskScore >= 70) return 'HIGH';
    if (riskScore >= 40) return 'MEDIUM';
    return 'LOW';
  }

  static getRiskColor(riskScore) {
    if (riskScore >= 70) return 'error';
    if (riskScore >= 40) return 'warning';
    return 'success';
  }

  static formatRiskScore(riskScore) {
    return Math.round(riskScore || 0);
  }

  // Helper methods for trend analysis
  static calculateTrendSlope(dataPoints) {
    if (!dataPoints || dataPoints.length < 2) return 0;

    const n = dataPoints.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    dataPoints.forEach((point, index) => {
      sumX += index;
      sumY += point.value;
      sumXY += index * point.value;
      sumX2 += index * index;
    });

    return (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  }

  static calculateTrendPercentage(dataPoints) {
    if (!dataPoints || dataPoints.length < 2) return 0;

    const firstValue = dataPoints[0].value;
    const lastValue = dataPoints[dataPoints.length - 1].value;
    
    if (firstValue === 0) return 0;
    
    return ((lastValue - firstValue) / firstValue) * 100;
  }

  // Data validation helpers
  static validateRiskData(data) {
    const requiredFields = ['totalRequests'];
    const errors = [];

    requiredFields.forEach(field => {
      if (!(field in data) || data[field] < 0) {
        errors.push(`Invalid or missing field: ${field}`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static normalizeToScale(value, max, scale = 100) {
    return Math.min(scale, Math.max(0, (value / max) * scale));
  }
}

export default RiskCalculator;