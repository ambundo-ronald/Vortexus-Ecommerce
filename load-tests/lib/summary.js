function value(data, metricName, field, fallback = 0) {
  return data.metrics?.[metricName]?.values?.[field] ?? fallback;
}

function percent(number) {
  return `${(Number(number || 0) * 100).toFixed(2)}%`;
}

export function summaryHandler(testName) {
  return (data) => {
    const requests = value(data, 'http_reqs', 'count');
    const requestRate = value(data, 'http_reqs', 'rate').toFixed(2);
    const p95 = value(data, 'http_req_duration', 'p(95)').toFixed(2);
    const p99 = value(data, 'http_req_duration', 'p(99)').toFixed(2);
    const failureRate = percent(value(data, 'http_req_failed', 'rate'));
    const checkRate = percent(value(data, 'checks', 'rate'));
    const businessErrorRate = percent(value(data, 'business_errors', 'rate'));
    const throttleRate = percent(value(data, 'throttled_requests', 'rate'));

    const report = [
      '',
      `Vortexus k6: ${testName}`,
      `Requests: ${requests} (${requestRate}/second)`,
      `Latency: p95 ${p95} ms, p99 ${p99} ms`,
      `HTTP failures: ${failureRate}`,
      `Checks passed: ${checkRate}`,
      `Business errors: ${businessErrorRate}`,
      `Throttled responses: ${throttleRate}`,
      '',
    ].join('\n');

    const summaryFile = __ENV.SUMMARY_FILE || `results/${testName}-summary.json`;
    return {
      stdout: report,
      [summaryFile]: JSON.stringify(data, null, 2),
    };
  };
}
