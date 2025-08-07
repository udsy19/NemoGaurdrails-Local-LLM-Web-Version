/**
 * Test utility for handling data edge cases and validation
 */

export const validateDashboardData = (data) => {
  const errors = [];
  const warnings = [];

  if (!data) {
    errors.push('Data is null or undefined');
    return { valid: false, errors, warnings };
  }

  // Check for required fields
  if (!data.recent_events) {
    warnings.push('recent_events array is missing');
  } else if (!Array.isArray(data.recent_events)) {
    errors.push('recent_events is not an array');
  }

  if (data.total_requests === undefined) {
    warnings.push('total_requests is missing');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    data: sanitizeData(data)
  };
};

export const sanitizeData = (data) => {
  if (!data) {
    return getEmptyDashboardData();
  }

  return {
    recent_events: Array.isArray(data.recent_events) ? data.recent_events : [],
    total_requests: typeof data.total_requests === 'number' ? data.total_requests : 0,
    blocked_requests: typeof data.blocked_requests === 'number' ? data.blocked_requests : 0,
    allowed_requests: typeof data.allowed_requests === 'number' ? data.allowed_requests : 0,
    risk_metrics: data.risk_metrics || {},
    ...data
  };
};

export const getEmptyDashboardData = () => ({
  recent_events: [],
  total_requests: 0,
  blocked_requests: 0,
  allowed_requests: 0,
  risk_metrics: {
    pii_detection: 0,
    prompt_injection: 0,
    toxicity: 0,
    hate_speech: 0,
    privacy_violations: 0
  }
});

export const getEmptyUserData = () => ({
  overview_stats: {
    total_users: 0,
    high_risk_users: 0,
    medium_risk_users: 0,
    avg_risk_score: 0
  },
  users_list: []
});

export const generateSampleData = () => {
  const detectionTypes = ['pii', 'prompt_injection', 'toxicity', 'hate_speech', 'privacy'];
  const statuses = ['blocked', 'allowed'];
  
  const events = [];
  for (let i = 0; i < 10; i++) {
    events.push({
      id: i + 1,
      detection_type: detectionTypes[Math.floor(Math.random() * detectionTypes.length)],
      status: statuses[Math.floor(Math.random() * statuses.length)],
      confidence: Math.random(),
      timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      user_id: `user_${Math.floor(Math.random() * 1000)}`,
      ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
      message: 'Sample detection event'
    });
  }

  return {
    recent_events: events,
    total_requests: 1000,
    blocked_requests: events.filter(e => e.status === 'blocked').length,
    allowed_requests: events.filter(e => e.status === 'allowed').length,
    risk_metrics: {
      pii_detection: Math.floor(Math.random() * 20) + 5,
      prompt_injection: Math.floor(Math.random() * 15) + 3,
      toxicity: Math.floor(Math.random() * 30) + 10,
      hate_speech: Math.floor(Math.random() * 10) + 2,
      privacy_violations: Math.floor(Math.random() * 25) + 8
    }
  };
};

// Test chart data generation functions
export const testChartDataGeneration = () => {
  console.log('🧪 Testing chart data generation functions...');
  
  // Test with empty data
  const emptyData = getEmptyDashboardData();
  console.log('Empty dashboard data:', emptyData);
  
  // Test with sample data
  const sampleData = generateSampleData();
  console.log('Sample dashboard data:', sampleData);
  
  // Test validation
  const validation1 = validateDashboardData(null);
  console.log('Validation of null data:', validation1);
  
  const validation2 = validateDashboardData(sampleData);
  console.log('Validation of sample data:', validation2);
  
  return {
    emptyData,
    sampleData,
    validations: [validation1, validation2]
  };
};