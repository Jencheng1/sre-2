# SRE Copilot Usage Guide

This guide provides detailed instructions on how to use the SRE Copilot system for root cause analysis of incidents in AWS environments.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Analyzing Incidents](#analyzing-incidents)
3. [Working with the Knowledge Base](#working-with-the-knowledge-base)
4. [Advanced Usage](#advanced-usage)
5. [Best Practices](#best-practices)
6. [Command Reference](#command-reference)

## Getting Started

### Accessing the SRE Copilot

After completing the setup process, you can access the SRE Copilot through:

1. **Command Line Interface**:
   - Use the provided Python modules or console scripts
   - All functionality is available through the CLI

2. **API Integration**:
   - Use the Python classes directly in your code
   - Example Python code:

```python
from src.core.incident_analyzer import SRECopilotAnalyzer

# Initialize the analyzer
analyzer = SRECopilotAnalyzer()

# Analyze an incident
result = analyzer.analyze_incident(
    "Our e-commerce website is experiencing high latency (>2s) for product page loads since 2:00 PM today.",
    log_data="2025-04-06 14:02:17 WARN [DatabaseConnector] Connection pool reaching capacity (85%)",
    metrics_data="Database connection pool utilization increased from 60% to 95%",
    dashboard_data="The CloudWatch dashboard shows a spike in database CPU utilization at 2:00 PM"
)

print(result)
```

### Initial Configuration

Before using the SRE Copilot for the first time:

1. **Set up data sources**:
   - Configure CloudWatch log groups for monitoring
   - Set up CloudWatch metrics for your services
   - Create dashboards for visualization

2. **Seed the knowledge base** (optional):
   - Add historical incident data to improve recommendations
   - Use the provided script:

```bash
python -m src.core.knowledge_base_manager add \
  --incident-id "INC-12345" \
  --description "Database connection timeout" \
  --root-cause "Connection pool exhaustion" \
  --resolution "Increased connection pool size" \
  --services "RDS, Application Server"
```

## Analyzing Incidents

### Starting a New Analysis

1. **Initiate the analysis**:
   - Use the incident_analyzer module:

```bash
python -m src.core.incident_analyzer analyze \
  --description "Our e-commerce website is experiencing high latency (>2s) for product page loads since 2:00 PM today. The issue seems to affect approximately 30% of users."
```

2. **Provide context**:
   - Include relevant timeframes
   - Specify affected services
   - Mention any recent changes or deployments

### Providing Data Sources

For comprehensive analysis, provide the SRE Copilot with access to:

1. **Log data**:
   - Create a file with relevant log snippets:

```
# logs.txt
2025-04-06 13:55:23 INFO  [ProductService] Average response time: 120ms
2025-04-06 14:02:17 WARN  [DatabaseConnector] Connection pool reaching capacity (85%)
2025-04-06 14:05:42 ERROR [DatabaseConnector] Connection timeout after 3000ms
2025-04-06 14:06:13 ERROR [ProductService] Failed to retrieve product data: Database connection timeout
```

```bash
python -m src.core.incident_analyzer analyze \
  --description "High latency on product pages" \
  --logs logs.txt
```

2. **Metrics data**:
   - Create a file with metrics information:

```
# metrics.txt
Database connection pool utilization increased from 60% to 95%
Database query latency increased from 50ms to 500ms
Product service error rate increased from 0.1% to 5%
```

```bash
python -m src.core.incident_analyzer analyze \
  --description "High latency on product pages" \
  --logs logs.txt \
  --metrics metrics.txt
```

3. **Dashboard information**:
   - Create a file with dashboard descriptions:

```
# dashboard.txt
The CloudWatch dashboard shows:
- A spike in database CPU utilization at 2:00 PM
- Increased memory usage on the application servers
- Correlation between database connections and latency
```

```bash
python -m src.core.incident_analyzer analyze \
  --description "High latency on product pages" \
  --logs logs.txt \
  --metrics metrics.txt \
  --dashboard dashboard.txt
```

### Automatic Data Source Fetching

You can also have the SRE Copilot automatically fetch data from CloudWatch:

```bash
python -m src.core.incident_analyzer analyze-with-sources \
  --description "High latency on product pages" \
  --log-groups "/aws/lambda/product-service" "/aws/rds/instance/prod-db/error" \
  --metrics-config metrics_config.json
```

Where metrics_config.json contains:

```json
[
  {
    "namespace": "AWS/RDS",
    "metric_name": "CPUUtilization",
    "dimensions": [
      {
        "Name": "DBInstanceIdentifier",
        "Value": "prod-db"
      }
    ]
  },
  {
    "namespace": "AWS/RDS",
    "metric_name": "DatabaseConnections",
    "dimensions": [
      {
        "Name": "DBInstanceIdentifier",
        "Value": "prod-db"
      }
    ]
  }
]
```

### Interpreting Results

The SRE Copilot will provide:

1. **Analysis from each specialized agent**:
   - Log Analysis: Patterns and anomalies in logs
   - Metrics Analysis: Statistical anomalies and correlations
   - Dashboard Analysis: Visual insights from dashboards
   - Knowledge Base: Similar past incidents

2. **Root cause identification**:
   - Primary cause of the incident
   - Contributing factors
   - Evidence supporting the conclusion

3. **Recommended actions**:
   - Immediate mitigation steps
   - Long-term fixes
   - Preventive measures

### Saving Analysis Results

You can save the analysis results to a file:

```bash
python -m src.core.incident_analyzer analyze \
  --description "High latency on product pages" \
  --logs logs.txt \
  --metrics metrics.txt \
  --dashboard dashboard.txt \
  --output analysis_results.txt
```

## Working with the Knowledge Base

### Querying the Knowledge Base

To find information about past incidents:

```bash
python -m src.core.knowledge_base_manager query \
  --query "Find similar incidents to the current database connection timeout."
```

```bash
python -m src.core.knowledge_base_manager query \
  --query "What was the resolution for previous high latency issues?" \
  --limit 3
```

### Adding New Incidents

After resolving an incident, add it to the knowledge base:

```bash
python -m src.core.knowledge_base_manager add \
  --incident-id "INC-67890" \
  --description "Payment processing delays during peak traffic" \
  --root-cause "Redis cache eviction due to memory pressure" \
  --resolution "Increased Redis memory allocation and optimized caching strategy" \
  --services "Payment Service, Redis Cache"
```

### Updating Incident Information

To update information about an existing incident:

```bash
python -m src.core.knowledge_base_manager update \
  --incident-id "INC-67890" \
  --field "resolution" \
  --value "Increased Redis memory allocation, optimized caching strategy, and implemented circuit breaker pattern"
```

### Backing Up and Restoring the Knowledge Base

To backup the knowledge base:

```bash
python -m src.core.knowledge_base_manager backup \
  --output "kb_backup_2025_04_06.json"
```

To restore from a backup:

```bash
python -m src.core.knowledge_base_manager restore \
  --input "kb_backup_2025_04_06.json"
```

## Advanced Usage

### Scheduled Analysis

Set up scheduled analysis for proactive monitoring:

1. Create a Lambda function that invokes the SRE Copilot:

```python
import boto3
import json
from src.core.incident_analyzer import SRECopilotAnalyzer

def lambda_handler(event, context):
    analyzer = SRECopilotAnalyzer()
    
    # Analyze with automatically fetched data
    result = analyzer.analyze_with_data_sources(
        "Daily health check for e-commerce platform",
        log_groups=["/aws/lambda/product-service", "/aws/rds/instance/prod-db/error"],
        metrics=[
            {
                "namespace": "AWS/RDS",
                "metric_name": "CPUUtilization",
                "dimensions": [{"Name": "DBInstanceIdentifier", "Value": "prod-db"}]
            }
        ]
    )
    
    # Store the result
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket='sre-copilot-reports',
        Key=f"daily-report-{event['time']}.txt",
        Body=result
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Analysis completed successfully')
    }
```

2. Set up a CloudWatch Events rule to trigger the Lambda function:

```bash
aws events put-rule \
  --name "DailyServiceHealthCheck" \
  --schedule-expression "cron(0 8 * * ? *)"

aws events put-targets \
  --rule "DailyServiceHealthCheck" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:SRECopilotDailyCheck"
```

### Integration with Incident Management Systems

Integrate the SRE Copilot with incident management systems like PagerDuty or ServiceNow:

```python
def handle_incident_webhook(event, context):
    # Extract incident details from the webhook
    incident_id = event['incident']['id']
    description = event['incident']['description']
    
    # Initialize the analyzer
    analyzer = SRECopilotAnalyzer()
    
    # Analyze the incident
    result = analyzer.analyze_incident(
        f"Incident {incident_id}: {description}"
    )
    
    # Update the incident management system with findings
    # This depends on the specific API of your incident management system
    update_incident(incident_id, result)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Analysis completed successfully')
    }
```

### Custom Prompting Strategies

For more effective analysis, use these prompting strategies:

1. **Structured incident reports**:

```
Analyze this incident:
- ID: INC-12345
- Time: 2025-04-06 14:00 UTC
- Symptoms: High latency (>2s) on product pages
- Affected services: Web frontend, Product service, Database
- Recent changes: Deployed new product search feature at 13:30 UTC
- Current metrics: 
  * Database connections: 95/100
  * API error rate: 5%
  * Average response time: 2.3s
```

2. **Step-by-step analysis requests**:

```
Please analyze this incident in the following steps:
1. First, examine the logs to identify any error patterns
2. Then, analyze the metrics to find anomalies
3. Next, review the dashboards for visual patterns
4. Check the knowledge base for similar past incidents
5. Finally, synthesize all findings to determine the root cause
```

## Best Practices

### Effective Incident Analysis

1. **Provide comprehensive context**:
   - Include timeframes (when did the issue start, any patterns)
   - List affected services and components
   - Mention recent changes or deployments
   - Include relevant metrics and thresholds

2. **Use structured data**:
   - Format logs with timestamps and severity levels
   - Organize metrics by service and component
   - Provide clear dashboard screenshots or descriptions

3. **Ask specific questions**:
   - "What caused the spike in latency at 2:00 PM?"
   - "Why did the database connections increase suddenly?"
   - "Is this related to the deployment we did this morning?"

### Knowledge Base Management

1. **Regular maintenance**:
   - Review and update incident records monthly
   - Add tags and categories for better organization
   - Remove outdated or irrelevant incidents

2. **Standardized incident documentation**:
   - Use consistent terminology
   - Include quantitative data when possible
   - Document both symptoms and root causes
   - Detail the resolution steps taken

3. **Continuous improvement**:
   - Update resolutions as better solutions are found
   - Link related incidents together
   - Add preventive measures taken after each incident

## Command Reference

### SRE Copilot CLI Commands

```bash
# Incident Analysis
python -m src.core.incident_analyzer analyze --description "DESC" [--logs FILE] [--metrics FILE] [--dashboard FILE] [--output FILE]
python -m src.core.incident_analyzer analyze-with-sources --description "DESC" [--log-groups GROUP...] [--metrics-config FILE] [--dashboard-description FILE] [--output FILE]

# Knowledge Base Management
python -m src.core.knowledge_base_manager add --incident-id "ID" --description "DESC" --root-cause "RC" --resolution "RES" --services "SVC"
python -m src.core.knowledge_base_manager update --incident-id "ID" --field "FIELD" --value "VALUE"
python -m src.core.knowledge_base_manager query --query "QUERY" [--limit N]
python -m src.core.knowledge_base_manager backup --output "FILE"
python -m src.core.knowledge_base_manager restore --input "FILE"

# Agent Configuration and Testing
python -m src.core.configure_agents [--config FILE] [--region REGION]
python -m src.core.test_functionality [--config FILE] [--region REGION] [--test {all,supervisor,collaboration,knowledge_base}]
```

### Console Scripts (if installed via pip)

```bash
# Incident Analysis
sre-analyze analyze --description "DESC" [--logs FILE] [--metrics FILE] [--dashboard FILE] [--output FILE]
sre-analyze analyze-with-sources --description "DESC" [--log-groups GROUP...] [--metrics-config FILE] [--dashboard-description FILE] [--output FILE]

# Knowledge Base Management
sre-kb add --incident-id "ID" --description "DESC" --root-cause "RC" --resolution "RES" --services "SVC"
sre-kb update --incident-id "ID" --field "FIELD" --value "VALUE"
sre-kb query --query "QUERY" [--limit N]
sre-kb backup --output "FILE"
sre-kb restore --input "FILE"

# Agent Configuration and Testing
sre-configure [--config FILE] [--region REGION]
sre-test [--config FILE] [--region REGION] [--test {all,supervisor,collaboration,knowledge_base}]
```

---

This usage guide provides comprehensive instructions for effectively using the SRE Copilot system. For setup and installation instructions, refer to the [Complete Setup Guide](complete_setup_guide.md).
