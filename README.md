# SRE Copilot Agent Management

This repository contains scripts for managing AWS Bedrock agents for SRE (Site Reliability Engineering) automation. The scripts help you create, configure, validate, and test agents for log analysis, metrics analysis, and incident response coordination.

## Overview

The SRE Copilot system consists of three main agents:

1. **Log Analysis Agent**: Analyzes log data for patterns and anomalies
2. **Metrics Analysis Agent**: Analyzes time-series metrics data for trends and anomalies
3. **Supervisor Agent**: Coordinates incident response and delegates tasks to specialized agents

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.8 or higher
- Required Python packages: `boto3`, `botocore`

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The system uses a JSON configuration file (`sre_copilot_config.json`) to store agent configurations. You can create this file manually or use the default configuration provided by the scripts.

Example configuration:
```json
{
  "aws_region": "us-east-1",
  "supervisor_agent": {
    "name": "SRE-Supervisor",
    "description": "Coordinates analysis and response for SRE incidents",
    "instruction": "You are an SRE supervisor agent responsible for coordinating incident analysis and response. Your role is to delegate tasks to specialized agents and synthesize their findings.",
    "model": "anthropic.claude-v2"
  },
  "log_analysis_agent": {
    "name": "SRE-Log-Analyzer",
    "description": "Analyzes log data for patterns and anomalies",
    "instruction": "You are a log analysis agent specialized in identifying patterns, anomalies, and root causes in system logs. Focus on extracting meaningful insights from log data.",
    "model": "anthropic.claude-v2"
  },
  "metrics_analysis_agent": {
    "name": "SRE-Metrics-Analyzer",
    "description": "Analyzes time-series metrics data",
    "instruction": "You are a metrics analysis agent specialized in analyzing time-series data, identifying trends, and detecting anomalies in system metrics.",
    "model": "anthropic.claude-v2"
  }
}
```

## Usage

### 1. Configure Agents

To create and configure the agents:

```bash
python -m src.core.configure_agents --config sre_copilot_config.json --region us-east-1
```

This script will:
- Create the agents in AWS Bedrock
- Create action groups for each agent
- Associate Lambda functions with the action groups
- Save the agent IDs to the configuration file

### 2. Validate Agent Setup

To validate that the agents are properly configured:

```bash
python -m src.core.validate_agents --config sre_copilot_config.json --region us-east-1
```

This script will:
- Check if all agents exist and are properly configured
- Verify that action groups are correctly set up
- Validate that Lambda functions are accessible
- Provide a summary of the validation results and next steps

### 3. Test Agents

To test the agents with sample data:

```bash
python -m src.core.test_agents --config sre_copilot_config.json --region us-east-1
```

This script will:
- Test each agent with sample data (logs, metrics, incidents)
- Set up CloudWatch alarms for monitoring
- Provide a summary of the test results and next steps

## Lambda Functions

The agents rely on the following Lambda functions:

1. `sre-log-analyzer-lambda`: Processes log data for the Log Analysis Agent
2. `sre-metrics-analyzer-lambda`: Processes metrics data for the Metrics Analysis Agent
3. `sre-supervisor-lambda`: Coordinates incident response for the Supervisor Agent

Make sure these Lambda functions are deployed and accessible before configuring the agents.

## Troubleshooting

If you encounter issues:

1. Check the logs for error messages
2. Verify that the Lambda functions exist and are accessible
3. Ensure that the AWS credentials have the necessary permissions
4. Run the validation script to identify specific issues

## Next Steps

After setting up the agents:

1. Create a real incident to test the agents in production
2. Set up a dashboard to monitor agent performance
3. Configure notifications for agent alerts
4. Integrate the agents with your existing monitoring and incident response systems

## License

This project is licensed under the MIT License - see the LICENSE file for details.
