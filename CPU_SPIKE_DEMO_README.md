# CPU Spike Demo for SRE Copilot

## Overview
The CPU Spike Demo is a powerful feature that allows you to trigger **real CPU spikes** on EC2 instances and observe the entire incident lifecycle through the SRE Copilot system.

## Features
- **Real CPU Spike Generation**: Uses AWS Systems Manager to run stress tests on EC2 instances
- **Grafana Integration**: Monitor CPU metrics in real-time through Grafana dashboards
- **Automatic Incident Creation**: Creates OpsItems in AWS Systems Manager
- **AI Root Cause Analysis**: Triggers the SRE Copilot's AI-powered analysis
- **Historical Context**: Searches knowledge base for similar incidents and remediation

## Prerequisites
1. EC2 instances with SSM agent installed and running
2. Proper IAM permissions for SSM, CloudWatch, and EC2
3. Docker and docker-compose installed (for Grafana)

## Quick Start

### 1. Start Grafana
```bash
cd /home/ec2-user/sre/sre_mcp
./start_grafana.sh
```

Access Grafana at: http://localhost:3000 (admin/admin123)

### 2. Launch Streamlit
```bash
export AWS_DEFAULT_REGION=us-east-1
python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### 3. Navigate to CPU Spike Demo
1. Go to "🛠️ Advanced Tools" in the navigation
2. Click on "🚨 CPU Spike Demo" tab

## Usage

### Triggering a CPU Spike
1. **Select Target Instance**: Choose an EC2 instance with SSM agent enabled
2. **Configure Parameters**:
   - **Target CPU %**: How high to spike the CPU (10-100%)
   - **Duration**: How long to maintain the spike (30-300 seconds)
   - **CPU Cores**: Number of cores to stress (0 = all cores)
3. **Click "🚀 Trigger CPU Spike"** to start the test

### Monitoring the Spike
- View real-time progress in the "Active Spike Monitoring" section
- Check Grafana dashboard for live CPU metrics
- Click "🔄 Check Status" to see command execution details

### Running Root Cause Analysis
1. After triggering a spike, an OpsItem is automatically created
2. Click "🔍 Run Root Cause Analysis" to invoke the AI analysis
3. View results including:
   - Identified root cause
   - Impact assessment
   - Recommendations
   - Related knowledge base articles

### Stopping a Spike
- Click "🛑 Stop CPU Spike" to immediately terminate the stress test

## Architecture

### Components
1. **CPU Spike Generator** (`cpu_spike_generator.py`):
   - Uses boto3 to interact with EC2 and SSM
   - Executes stress commands via SSM Run Command
   - Monitors CloudWatch metrics

2. **Grafana Stack**:
   - **Prometheus**: Collects metrics from EC2 instances
   - **Node Exporter**: Exposes system metrics
   - **Grafana**: Visualizes CPU metrics with pre-configured dashboards

3. **Streamlit Integration**:
   - New tab in Advanced Tools section
   - Real-time status updates
   - Integration with existing root cause analysis

## Security Considerations
- Only instances with SSM agent can be targeted
- Requires proper IAM permissions
- All actions are logged in CloudTrail
- IP addresses in logs are masked for privacy

## Troubleshooting

### No EC2 instances showing
- Ensure SSM agent is installed: `sudo yum install -y amazon-ssm-agent`
- Check agent status: `sudo systemctl status amazon-ssm-agent`
- Verify IAM role has SSM permissions

### Grafana not accessible
- Check if containers are running: `docker-compose ps`
- Verify port 3000 is not in use: `netstat -tlnp | grep 3000`
- Check logs: `docker-compose logs grafana`

### CPU spike fails to trigger
- Verify instance has internet access (for stress package installation)
- Check SSM command history in AWS Console
- Ensure instance has sufficient permissions

## Metrics Pushed to Grafana
1. **From Prometheus/Node Exporter**:
   - CPU usage per core
   - System load averages
   - Memory utilization

2. **From CloudWatch**:
   - EC2 CPUUtilization metric
   - Custom metrics from SREDemo/CPUSpike namespace

## Best Practices
1. Start with lower CPU percentages (50-60%) for testing
2. Keep spike durations short initially (30-60 seconds)
3. Monitor the instance during spikes to ensure it remains responsive
4. Always stop spikes when done testing
5. Review generated OpsItems for documentation

## Integration with Existing Features
- **Knowledge Base**: Spike incidents are searchable
- **Defect Management**: Can create defects from spike incidents
- **Post-Mortem**: Generate reports for spike incidents
- **Analytics**: View spike trends in analytics dashboard

## Cleanup
To remove all CPU spike demo components:
```bash
# Stop any running spikes
# (Use the UI or manually kill stress processes)

# Stop Grafana stack
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Backup created at: backup_sre_mcp_20250927_011446.tar.gz
```

## Future Enhancements
- Support for memory and disk I/O stress tests
- Scheduled spike tests for chaos engineering
- Integration with AWS FIS (Fault Injection Simulator)
- Custom stress test scenarios
- Multi-instance coordinated spikes