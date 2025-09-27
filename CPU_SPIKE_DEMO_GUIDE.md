# CPU Spike Demo - Complete User Guide

## 🎯 Overview

The CPU Spike Demo is an advanced feature of the SRE Copilot that demonstrates real-world incident management by:
- Triggering actual CPU spikes on EC2 instances (no simulation!)
- Monitoring metrics in real-time through Grafana
- Creating incidents in AWS Systems Manager OpsItems
- Running AI-powered root cause analysis
- Searching historical incidents for remediation guidance

## 📋 Prerequisites

### Required AWS Resources
1. **EC2 Instances**: At least one running Linux EC2 instance
2. **SSM Agent**: Must be installed and running on target instances
3. **IAM Permissions**: 
   - EC2: DescribeInstances
   - SSM: SendCommand, GetCommandInvocation, CreateOpsItem
   - CloudWatch: GetMetricStatistics, PutMetricData

### Required Services
- Docker & Docker Compose (for Grafana stack)
- Python 3.7+ with boto3
- Streamlit application

## 🚀 Quick Start

### Step 1: Validate System Readiness
```bash
cd /home/ec2-user/sre/sre_mcp
python3 validate_cpu_spike_demo.py
```

Expected output shows system readiness percentage. 70%+ is required for basic functionality.

### Step 2: Start Grafana Stack
```bash
./start_grafana.sh
```

This starts:
- **Grafana** (port 3000): Visualization dashboard
- **Prometheus** (port 9090): Metrics collection
- **Node Exporter** (port 9100): System metrics

### Step 3: Launch Streamlit Application
```bash
export AWS_DEFAULT_REGION=us-east-1
python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Step 4: Access CPU Spike Demo
1. Open browser: http://localhost:8501
2. Navigate to "🛠️ Advanced Tools" in the navigation
3. Click "🚨 CPU Spike Demo" tab

## 📖 Detailed Usage Guide

### 1. Target Selection

The demo automatically discovers EC2 instances in your AWS account.

**Instance Requirements**:
- Running state
- Linux-based OS
- SSM Agent installed and running
- Proper IAM role attached

**What You'll See**:
```
🎯 Target Selection
Select EC2 Instance: [Dropdown with instance names]
```

**Instance Details Panel** shows:
- Instance Type (e.g., t2.micro, m5.large)
- Private IP address
- Current state

### 2. Spike Configuration

Configure the CPU spike parameters:

**Target CPU %** (10-100%):
- 50-60%: Light load testing
- 70-80%: Moderate stress (recommended)
- 90-100%: Heavy stress

**Duration** (30-300 seconds):
- 30-60s: Quick test
- 120s: Standard test
- 300s: Extended stress test

**CPU Cores** (0-16):
- 0: All available cores (default)
- 1-N: Specific number of cores

### 3. Triggering the Spike

Click **"🚀 Trigger CPU Spike"** to:

1. **Install stress tool** (if needed):
   ```bash
   sudo yum install -y stress || sudo apt-get install -y stress
   ```

2. **Execute stress command**:
   ```bash
   stress --cpu <workers> --timeout <duration>s
   ```

3. **Create CloudWatch metric**:
   - Namespace: SREDemo/CPUSpike
   - Metric: CPUSpikeTriggered
   - Dimensions: InstanceId, TargetCPU

4. **Create OpsItem**:
   - Title: "High CPU Alert - {instance_name}"
   - Severity: High (2)
   - Category: Performance

### 4. Real-Time Monitoring

**Active Spike Monitoring** shows:
- Target CPU percentage
- Elapsed time with countdown
- Progress bar
- Command execution status

**CPU Metrics Chart** displays:
- Average CPU utilization (blue line)
- Maximum CPU utilization (red dashed line)
- Alert threshold at 80% (orange dotted line)

### 5. Root Cause Analysis

Click **"🔍 Run Root Cause Analysis"** to trigger the AI-powered analysis:

**What Happens**:
1. Invokes sre-supervisor-lambda
2. Collects data from multiple sources:
   - CloudWatch Logs
   - CloudWatch Metrics
   - CloudTrail events
   - VPC Flow Logs
3. Runs correlation analysis
4. Searches knowledge base

**Results Include**:
- **Root Cause**: Identified issue (e.g., "CPU stress test executed via SSM")
- **Impact**: Service degradation assessment
- **Recommendations**: Remediation steps
- **Related Knowledge Base Articles**: Historical context

### 6. Grafana Dashboard

Access at: http://localhost:3000 (admin/admin123)

**CPU Monitoring Dashboard** features:
- EC2 instance selector (dropdown)
- CPU usage by instance (time series)
- Current CPU gauge
- CloudWatch metrics integration

## 🔧 Troubleshooting

### No EC2 Instances Showing

**Issue**: Dropdown is empty or shows "No EC2 instances found"

**Solutions**:
1. Verify AWS credentials:
   ```bash
   aws sts get-caller-identity
   ```

2. Check EC2 instances exist:
   ```bash
   aws ec2 describe-instances --query 'Reservations[].Instances[?State.Name==`running`].[InstanceId,Tags[?Key==`Name`].Value|[0]]' --output table
   ```

3. Ensure proper IAM permissions

### SSM Agent Not Available

**Issue**: "No EC2 instances with SSM agent available"

**Solutions**:
1. Install SSM agent on EC2:
   ```bash
   # Amazon Linux 2
   sudo yum install -y amazon-ssm-agent
   sudo systemctl start amazon-ssm-agent
   
   # Ubuntu
   sudo snap install amazon-ssm-agent --classic
   sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent
   ```

2. Verify agent status:
   ```bash
   sudo systemctl status amazon-ssm-agent
   ```

3. Check IAM role has AmazonSSMManagedInstanceCore policy

### CPU Spike Fails to Trigger

**Issue**: Error when clicking "Trigger CPU Spike"

**Common Causes**:
1. **No internet access**: Instance needs to download stress package
2. **Insufficient permissions**: Check IAM role
3. **SSM timeout**: Increase execution timeout

**Debug Steps**:
1. Check SSM command history:
   ```bash
   aws ssm list-command-invocations --instance-id <instance-id>
   ```

2. View command output:
   ```bash
   aws ssm get-command-invocation --command-id <command-id> --instance-id <instance-id>
   ```

### Grafana Not Accessible

**Issue**: Cannot access http://localhost:3000

**Solutions**:
1. Check container status:
   ```bash
   docker ps | grep grafana
   ```

2. View logs:
   ```bash
   docker logs sre-grafana
   ```

3. Restart container:
   ```bash
   docker restart sre-grafana
   ```

## 📊 Monitoring & Metrics

### CloudWatch Metrics
The demo creates custom metrics in the `SREDemo/CPUSpike` namespace:
- **CPUSpikeTriggered**: Count of spike events
- **CPUUtilization**: Standard EC2 metric

### Prometheus Metrics
Node Exporter provides system-level metrics:
- `node_cpu_seconds_total`: CPU time in various modes
- `node_load1`, `node_load5`, `node_load15`: System load averages
- `node_memory_MemAvailable_bytes`: Available memory

### Grafana Visualizations
Pre-configured dashboards show:
- Real-time CPU usage
- Historical trends
- Alert thresholds
- Multi-instance comparison

## 🔐 Security Considerations

1. **IP Masking**: All logs are processed with IP masking for privacy
2. **Audit Trail**: All actions logged in CloudTrail
3. **Least Privilege**: Use minimal required IAM permissions
4. **Temporary Access**: SSM sessions are time-limited
5. **No Persistent Changes**: Stress tool doesn't modify system configuration

## 📚 Integration Points

### With Knowledge Base
- Spike incidents are automatically indexed
- Historical searches find similar incidents
- Resolution guides are suggested

### With Incident Management
- OpsItems created automatically
- Severity and category pre-configured
- Integration with existing workflows

### With AI Analysis
- Supervisor Lambda processes incidents
- Multiple data sources correlated
- Intelligent recommendations provided

## 🎓 Best Practices

1. **Start Small**: Begin with 50% CPU for 30 seconds
2. **Monitor Actively**: Watch both Streamlit and Grafana
3. **Document Results**: Save analysis for future reference
4. **Clean Up**: Stop spikes when testing complete
5. **Review Logs**: Check CloudTrail for audit trail

## 📝 Example Workflow

1. **Select Target Instance**: 
   - Choose "WebServer-01 (i-0123456789abcdef)"

2. **Configure Spike**:
   - Target CPU: 80%
   - Duration: 60 seconds
   - Cores: 0 (all)

3. **Trigger and Monitor**:
   - Click "Trigger CPU Spike"
   - Watch real-time metrics
   - Observe Grafana dashboard

4. **Analyze Results**:
   - Run root cause analysis
   - Review AI recommendations
   - Check knowledge base

5. **Document Findings**:
   - Save OpsItem ID
   - Export analysis results
   - Update runbooks if needed

## 🚨 Emergency Stop

To immediately stop all CPU spikes:

1. **Via UI**: Click "🛑 Stop CPU Spike"

2. **Via AWS Console**: 
   - Go to Systems Manager > Run Command
   - Cancel active commands

3. **Via CLI**:
   ```bash
   # Stop specific instance
   aws ssm send-command \
     --instance-ids <instance-id> \
     --document-name "AWS-RunShellScript" \
     --parameters 'commands=["sudo pkill -f stress"]'
   ```

4. **Direct SSH** (if available):
   ```bash
   ssh ec2-user@<instance-ip>
   sudo pkill -f stress
   ```

## 📋 Validation Checklist

Before demo:
- [ ] AWS credentials configured
- [ ] At least one EC2 instance with SSM
- [ ] Grafana stack running
- [ ] Streamlit application accessible
- [ ] Validation script shows 70%+ readiness

During demo:
- [ ] Instance selected successfully
- [ ] CPU spike triggered
- [ ] Metrics visible in real-time
- [ ] OpsItem created
- [ ] Root cause analysis completed

After demo:
- [ ] CPU spike stopped
- [ ] Results documented
- [ ] Knowledge base updated
- [ ] System returned to normal

## 🔗 Related Documentation

- [SRE Copilot Main Documentation](README.md)
- [Knowledge Base Guide](KNOWLEDGE_BASE_CONTEXT.md)
- [Incident Management Guide](INCIDENT_MANAGEMENT_GUIDE.md)
- [AWS SSM Documentation](https://docs.aws.amazon.com/systems-manager/)

## 💡 Tips & Tricks

1. **Multi-Instance Testing**: Select different instance types to see varying performance
2. **Correlation Testing**: Trigger spikes during high traffic to test correlation
3. **Knowledge Building**: Each test adds to your knowledge base
4. **Custom Metrics**: Extend with additional CloudWatch metrics
5. **Automation**: Use the CPU spike API programmatically for chaos engineering

---

**Version**: 1.0
**Last Updated**: September 27, 2025
**Author**: SRE Team