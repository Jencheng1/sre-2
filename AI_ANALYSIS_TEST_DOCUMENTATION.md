# AI Root Cause Analysis Test Suite Documentation

## Overview
This document describes the comprehensive test suite for the enhanced AI root cause analysis system that correlates JVM memory leaks, deployments, and CPU spikes.

## Test Suite: `test_ai_analysis_correlation.py`

### Purpose
Validates that the enhanced supervisor Lambda correctly:
- Detects JVM-specific metrics and memory patterns
- Correlates incidents with recent code deployments
- Identifies the complete chain: deployment → memory leak → GC overhead → CPU spike
- Provides actionable remediation recommendations

### Test Coverage

#### Test 1: JVM Metrics Detection
**Purpose**: Verify supervisor recognizes JVM/Java-specific issues

**Validates**:
- Detection of heap memory terminology
- Recognition of JVM/Java keywords
- Understanding of garbage collection concepts

**Expected Output**:
```
✅ Found JVM terms: ['jvm', 'heap', 'garbage collection']
```

#### Test 2: Memory Leak Pattern Detection
**Purpose**: Test identification of memory leak patterns

**Validates**:
- Recognition of unbounded memory growth
- Cache-related memory issues
- Pattern analysis (increasing trends)

**Expected Output**:
```
✅ Detected patterns: ['unbounded', 'growth', 'increasing']
```

#### Test 3: GC-CPU Correlation
**Purpose**: Verify correlation between GC overhead and CPU spikes

**Validates**:
- Links GC pause times to CPU utilization
- Identifies GC overhead as CPU consumption cause
- Recognizes the performance impact chain

**Expected Output**:
```
✅ GC-CPU correlation identified
```

#### Test 4: Change/Deployment Correlation
**Purpose**: Test linking of incidents to recent deployments

**Validates**:
- Queries recent change records
- Associates deployments with incidents
- Identifies version numbers (v2.1.0)

**Expected Output**:
```
✅ Deployment correlation found
```

#### Test 5: Cache Eviction Policy Detection
**Purpose**: Verify detection of cache management issues

**Validates**:
- Identifies missing eviction policies
- Recognizes unbounded cache growth
- Suggests TTL/eviction solutions

**Expected Output**:
```
✅ Cache eviction issue identified
```

#### Test 6: Comprehensive Correlation Chain
**Purpose**: Test complete end-to-end correlation

**Validates the full chain**:
1. Deployment (v2.2.0) ✅
2. Memory leak detection ✅
3. Cache issue identification ✅
4. GC overhead recognition ✅
5. CPU impact correlation ✅

**Expected Output**:
```
Correlation Chain Validation:
✅ deployment
✅ memory_leak
✅ cache_issue
✅ gc_overhead
✅ cpu_impact
✅ Complete correlation chain verified!
```

#### Test 7: Remediation Recommendations
**Purpose**: Ensure actionable fixes are provided

**Validates**:
- Immediate actions (restart, rollback)
- Long-term fixes (eviction policy, monitoring)
- Specific technical recommendations

**Expected Output**:
```
✅ Remediation keywords found: ['restart', 'rollback', 'eviction', 'cache size']
```

#### Test 8: Business Impact Assessment
**Purpose**: Verify business context understanding

**Validates**:
- Customer impact recognition
- Revenue/transaction implications
- User experience considerations

**Expected Output**:
```
✅ Business impact terms: ['customer', 'payment', 'transaction', 'impact']
```

## Running the Tests

### Prerequisites
1. Enhanced supervisor Lambda deployed
2. Java application running on SRE-DEMO instance
3. CloudWatch metrics flowing
4. AWS credentials configured

### Execution

**Run all tests**:
```bash
python3 test_ai_analysis_correlation.py
```

**Run specific test**:
```bash
python3 -m unittest test_ai_analysis_correlation.TestAIAnalysisCorrelation.test_01_jvm_metrics_detection
```

### Expected Output
```
🧪 ENHANCED AI ANALYSIS TEST SUITE
Testing JVM memory leak detection and correlation capabilities
================================================================================

🧪 Test 1: JVM Metrics Detection
   ✅ Found JVM terms: ['memory', 'heap', 'gc']

🧪 Test 2: Memory Leak Pattern Detection
   ✅ Detected patterns: ['unbounded', 'growth']

... [continues for all 8 tests] ...

================================================================================
TEST EXECUTION SUMMARY
================================================================================

Total Tests: 8
Passed: 8 ✅
Failed: 0 ❌
Success Rate: 100.0%
Total Execution Time: 45.32s

Detailed Results:
  ✅ test_01_jvm_metrics_detection: 5.21s
  ✅ test_02_memory_leak_pattern_detection: 6.43s
  ✅ test_03_gc_cpu_correlation: 4.87s
  ✅ test_04_change_deployment_correlation: 5.92s
  ✅ test_05_cache_eviction_issue: 4.65s
  ✅ test_06_comprehensive_correlation: 8.34s
  ✅ test_07_remediation_recommendations: 4.98s
  ✅ test_08_business_impact_assessment: 4.92s

🎉 ALL TESTS PASSED! The enhanced AI analysis is working correctly!
```

## Test Data Management

### Created Resources
Each test creates:
- OpsItems for incidents
- Change records for deployments
- CloudWatch metrics for patterns

### Cleanup
- OpsItems remain for audit trail
- Metrics expire automatically
- No manual cleanup required

## Validation Criteria

### Success Criteria
- All 8 tests must pass
- Each correlation element must be detected
- Business and technical impacts identified
- Remediation steps provided

### Failure Investigation
If tests fail:

1. **Check Lambda deployment**:
   ```bash
   aws lambda get-function --function-name sre-supervisor-lambda --region us-east-1
   ```

2. **Verify metrics flow**:
   ```bash
   aws cloudwatch list-metrics --namespace JavaApp/SpringBoot --region us-east-1
   ```

3. **Review Lambda logs**:
   ```bash
   aws logs filter-log-events --log-group-name /aws/lambda/sre-supervisor-lambda --start-time $(date -d '5 minutes ago' +%s)000
   ```

## Integration with CI/CD

### Automated Testing
```yaml
# .github/workflows/test-ai-analysis.yml
name: Test AI Analysis
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install boto3 unittest
      - name: Run AI analysis tests
        env:
          AWS_DEFAULT_REGION: us-east-1
        run: |
          python3 test_ai_analysis_correlation.py
```

### Performance Benchmarks
- Average test execution: 5-6 seconds per test
- Total suite execution: < 60 seconds
- Lambda invocation latency: < 2 seconds

## Troubleshooting

### Common Issues

1. **"Analysis should not be None" failures**
   - Check Lambda is deployed
   - Verify IAM permissions
   - Review Lambda timeout settings

2. **Pattern detection failures**
   - Ensure CloudWatch metrics exist
   - Check metric namespace spelling
   - Verify time ranges

3. **Correlation failures**
   - Confirm change records exist
   - Check OpsItem filters
   - Review timestamp alignment

### Debug Mode
Add verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Maintenance

### Regular Tasks
1. Review test coverage monthly
2. Update patterns for new scenarios
3. Add tests for new correlation types
4. Monitor test execution times

### Version Compatibility
- Python: 3.7+
- boto3: 1.26+
- AWS Lambda: Python 3.8 runtime
- Enhanced supervisor: v2.0+

---
Documentation created: September 27, 2025
Last updated: September 27, 2025