import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const validationSuccessRate = new Rate('validation_success');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 20 },   // Ramp up to 20 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% of requests under 500ms
    errors: ['rate<0.1'],                            // Error rate under 10%
    validation_success: ['rate>0.9'],                // Success rate over 90%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test_token';

// Helper function to generate random validation data
function generateValidationData() {
  const objectTypes = ['wall', 'door', 'window', 'room', 'column'];
  const validationTypes = ['dimension', 'type', 'material', 'relationship'];
  
  return {
    object_id: `obj_${Math.floor(Math.random() * 1000)}`,
    validation_type: validationTypes[Math.floor(Math.random() * validationTypes.length)],
    data: {
      length: Math.random() * 10 + 1,
      width: Math.random() * 5 + 0.5,
      material: ['concrete', 'steel', 'wood', 'glass'][Math.floor(Math.random() * 4)],
    },
    validator: `user_${__VU}`, // Virtual user ID
    confidence: Math.random() * 0.5 + 0.5, // 0.5 to 1.0
    timestamp: new Date().toISOString(),
  };
}

// Test scenarios
export default function () {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  // Scenario 1: Get pending validations
  let response = http.get(`${BASE_URL}/api/validations/pending`, { headers });
  
  check(response, {
    'pending validations status is 200': (r) => r.status === 200,
    'pending validations returned': (r) => {
      const body = JSON.parse(r.body);
      return body.validations !== undefined;
    },
  });
  
  errorRate.add(response.status !== 200);
  
  sleep(1);

  // Scenario 2: Flag object for validation
  const flagData = {
    object_id: `obj_${Math.floor(Math.random() * 1000)}`,
    reason: 'Low confidence detected during load test',
    priority: Math.floor(Math.random() * 5) + 5,
  };
  
  response = http.post(
    `${BASE_URL}/api/validations/flag`,
    JSON.stringify(flagData),
    { headers }
  );
  
  check(response, {
    'flag validation status is 200': (r) => r.status === 200,
    'flag validation successful': (r) => {
      const body = JSON.parse(r.body);
      return body.success === true;
    },
  });
  
  errorRate.add(response.status !== 200);
  
  sleep(1);

  // Scenario 3: Submit validation
  const validationData = generateValidationData();
  
  response = http.post(
    `${BASE_URL}/api/validations/submit`,
    JSON.stringify(validationData),
    { headers }
  );
  
  const isSuccess = response.status === 200;
  validationSuccessRate.add(isSuccess);
  errorRate.add(!isSuccess);
  
  check(response, {
    'validation submission status is 200': (r) => r.status === 200,
    'validation impact calculated': (r) => {
      if (r.status !== 200) return false;
      const body = JSON.parse(r.body);
      return body.impact !== undefined && body.impact.confidence_improvement !== undefined;
    },
    'confidence improved': (r) => {
      if (r.status !== 200) return false;
      const body = JSON.parse(r.body);
      return body.impact.new_confidence > body.impact.old_confidence;
    },
  });
  
  sleep(2);

  // Scenario 4: Get validation history
  response = http.get(
    `${BASE_URL}/api/validations/history?validator=user_${__VU}`,
    { headers }
  );
  
  check(response, {
    'history status is 200': (r) => r.status === 200,
    'history contains records': (r) => {
      const body = JSON.parse(r.body);
      return Array.isArray(body.history);
    },
  });
  
  errorRate.add(response.status !== 200);
  
  sleep(1);

  // Scenario 5: Get leaderboard (less frequent)
  if (Math.random() < 0.1) { // 10% of iterations
    response = http.get(`${BASE_URL}/api/validations/leaderboard`, { headers });
    
    check(response, {
      'leaderboard status is 200': (r) => r.status === 200,
      'leaderboard has entries': (r) => {
        const body = JSON.parse(r.body);
        return body.leaderboard && body.leaderboard.length > 0;
      },
    });
    
    errorRate.add(response.status !== 200);
  }
  
  sleep(Math.random() * 3 + 1); // Random sleep between 1-4 seconds
}

// Stress test scenario for spike testing
export function stress() {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };

  // Rapid-fire validation submissions
  for (let i = 0; i < 10; i++) {
    const validationData = generateValidationData();
    
    const response = http.post(
      `${BASE_URL}/api/validations/submit`,
      JSON.stringify(validationData),
      { headers, timeout: '5s' }
    );
    
    validationSuccessRate.add(response.status === 200);
    errorRate.add(response.status !== 200);
    
    sleep(0.1); // Very short sleep
  }
}

// WebSocket test scenario
export function websocket() {
  const ws = new WebSocket(`ws://localhost:8080/api/ws/validation`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
    
    // Send test message
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: Date.now(),
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    check(data, {
      'websocket message received': (d) => d !== null,
      'confidence update received': (d) => d.type === 'confidence_update',
    });
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    errorRate.add(1);
  };
  
  sleep(10);
  ws.close();
}

// Summary report
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
    'summary.html': htmlReport(data),
  };
}

function textSummary(data, options) {
  // Generate text summary
  let summary = '\n=== Confidence API Load Test Results ===\n\n';
  
  summary += `Duration: ${data.state.testRunDurationMs}ms\n`;
  summary += `VUs: ${data.metrics.vus.values.max}\n`;
  summary += `Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `Success Rate: ${(data.metrics.validation_success.values.rate * 100).toFixed(2)}%\n`;
  summary += `Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%\n`;
  summary += `Avg Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  
  return summary;
}

function htmlReport(data) {
  // Generate HTML report
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Load Test Report</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .metric { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
      </style>
    </head>
    <body>
      <h1>Confidence API Load Test Report</h1>
      <div class="metric">
        <h3>Test Duration</h3>
        <p>${data.state.testRunDurationMs}ms</p>
      </div>
      <div class="metric">
        <h3>Peak Virtual Users</h3>
        <p>${data.metrics.vus.values.max}</p>
      </div>
      <div class="metric">
        <h3>Total Requests</h3>
        <p>${data.metrics.http_reqs.values.count}</p>
      </div>
      <div class="metric">
        <h3>Success Rate</h3>
        <p class="${data.metrics.validation_success.values.rate > 0.9 ? 'success' : 'warning'}">
          ${(data.metrics.validation_success.values.rate * 100).toFixed(2)}%
        </p>
      </div>
      <div class="metric">
        <h3>Error Rate</h3>
        <p class="${data.metrics.errors.values.rate < 0.1 ? 'success' : 'error'}">
          ${(data.metrics.errors.values.rate * 100).toFixed(2)}%
        </p>
      </div>
      <div class="metric">
        <h3>Response Times</h3>
        <ul>
          <li>Average: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms</li>
          <li>P95: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms</li>
          <li>P99: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms</li>
        </ul>
      </div>
    </body>
    </html>
  `;
}