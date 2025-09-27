# Java Memory Leak Correlation Demo

## Overview

This demo showcases a complete correlation analysis scenario where a Java Spring Boot application experiences a memory leak after a code change, leading to a CPU spike. The system demonstrates how to correlate:

1. **Code Changes** → 2. **Memory Leak** → 3. **CPU Spike** → 4. **Root Cause Analysis**

## Demo Components

### 1. Java Memory Leak Test Case (`java_memory_leak_test_case.py`)
- Creates a code change OpsItem for deploying payment-service v2.1.0
- Simulates gradual memory growth pattern in CloudWatch metrics
- Generates application logs showing OutOfMemoryError
- Creates CPU spike incident correlated with the change

### 2. Java Monitoring Setup (`setup_java_metrics_monitoring.py`)
- Configures CloudWatch agent for JVM metrics collection
- Sets up Spring Boot Actuator metrics script
- Creates Grafana dashboard for Java application monitoring
- Tracks: Heap usage, GC pause times, thread count, cache size

### 3. Change Management Integration (`create_change_record_demo.py`)
- Creates change records in AWS Systems Manager OpsCenter
- Pushes change events to CloudWatch for visualization
- Creates Grafana dashboard showing change timeline
- Enables correlation between changes and incidents

### 4. Complete Demo Runner (`run_complete_correlation_demo.py`)
- Orchestrates all components in the correct sequence
- Sets up monitoring, creates changes, simulates incident
- Provides clear output and next steps

## Running the Demo

### Quick Start
```bash
# Run the complete demo
python3 run_complete_correlation_demo.py
```

### Individual Components
```bash
# 1. Setup Java monitoring
python3 setup_java_metrics_monitoring.py

# 2. Create change records
python3 create_change_record_demo.py

# 3. Simulate memory leak scenario
python3 java_memory_leak_test_case.py
```

## Demo Scenario

### Timeline
- **T-2 hours**: Deploy payment-service v2.1.0 with new TransactionCache
- **T-1 hour**: Memory usage starts growing, cache entries accumulating
- **T-30 min**: GC pause times increasing, CPU usage climbing
- **T-0**: CPU spike to 95%, OutOfMemoryError in logs

### Root Cause Chain
1. **Code Change**: New TransactionCache lacks eviction policy
2. **Memory Leak**: Cache grows unbounded, holding all transactions
3. **GC Pressure**: JVM spends excessive time in garbage collection
4. **CPU Spike**: GC overhead causes CPU utilization to spike

## Grafana Dashboards

### 1. Java Application Monitoring
- **URL**: http://localhost:3000/d/java-app-monitoring
- **Metrics**: JVM heap, GC pause time, thread count, cache size
- **Purpose**: Monitor Java application health

### 2. Change Management Dashboard
- **URL**: http://localhost:3000/d/change-management
- **Shows**: Change timeline, risk scores, correlation with incidents
- **Purpose**: Track deployments and their impact

### 3. EC2 CPU Dashboard
- **URL**: http://localhost:3000/d/ec2-max-cpu
- **Shows**: Maximum CPU utilization
- **Purpose**: Identify CPU spikes

## Correlation Analysis in Streamlit

1. Navigate to **Advanced Tools** > **CPU Spike Demo**
2. Select **SRE-DEMO** instance
3. Click **Run Root Cause Analysis**

### Expected Analysis Results

The supervisor Lambda will identify:

1. **Recent Code Change**
   - Deployment 2 hours before incident
   - Modified TransactionCache.java

2. **Memory Pattern**
   - Gradual increase since deployment
   - Heap usage correlation with time

3. **GC Metrics**
   - High pause times
   - Excessive GC overhead

4. **Log Evidence**
   - OutOfMemoryError stack traces
   - Points to TransactionCache.put()

5. **Root Cause**
   - Unbounded cache growth
   - Missing eviction policy

## Key Metrics Collected

### JVM Metrics (JavaApp/SpringBoot namespace)
- `JVM_HeapUsedPercent` - Heap memory utilization
- `JVM_GCPauseTime` - Garbage collection pause duration
- `JVM_ThreadsLive` - Active thread count
- `App_CacheSize` - Transaction cache entry count
- `App_HttpRequests` - HTTP request rate

### Change Metrics (ChangeManagement namespace)
- `ChangeEvent` - Change occurrence tracking
- `ChangeRiskScore` - Risk level quantification
- `DeploymentDuration` - Deployment time tracking

### Standard Metrics
- `AWS/EC2::CPUUtilization` - EC2 CPU usage
- `AWS/EC2::MemoryUtilization` - System memory usage

## Knowledge Base Integration

The demo automatically creates a knowledge base entry:
- **Title**: Java Spring Boot Memory Leak - TransactionCache
- **Symptoms**: Gradual CPU increase, high GC pause, OOM errors
- **Root Cause**: Unbounded cache growth
- **Resolution**: Implement cache size limits and TTL eviction

## Testing the Correlation

### Verify Change Tracking
```bash
# Check OpsItems in Systems Manager
aws ssm describe-ops-items --filters Key=Title,Values="[CHANGE]",Operator=Contains
```

### Verify Metrics
```bash
# Check CloudWatch metrics
aws cloudwatch list-metrics --namespace JavaApp/SpringBoot
aws cloudwatch list-metrics --namespace ChangeManagement
```

### Verify Logs
```bash
# Check application logs
aws logs filter-log-events --log-group-name /aws/ec2/payment-service
```

## Troubleshooting

### If Grafana dashboards don't show data:
1. Wait 2-3 minutes for metrics to populate
2. Refresh the dashboard (F5)
3. Check time range is set to "Last 3 hours"

### If correlation analysis is incomplete:
1. Ensure all components ran successfully
2. Wait for CloudWatch data propagation
3. Check Lambda logs for errors

### If changes don't appear:
1. Verify OpsItems were created in Systems Manager
2. Check CloudWatch metrics namespace
3. Refresh Grafana dashboard

## Demo Benefits

1. **Realistic Scenario**: Based on common Java application issues
2. **Full Correlation**: Links changes → metrics → logs → incidents
3. **Visual Analysis**: Grafana dashboards show the complete picture
4. **Automated Detection**: AI-powered root cause analysis
5. **Knowledge Capture**: Incidents become searchable knowledge

## Next Steps

After running the demo:
1. Explore the Grafana dashboards
2. Test the root cause analysis in Streamlit
3. Search for similar incidents in Knowledge Base
4. Review the correlation timeline
5. Examine the generated OpsItems

This demo provides a template for implementing comprehensive monitoring and correlation analysis in production environments.