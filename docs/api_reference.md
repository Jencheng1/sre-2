# SRE Copilot API Reference

This document provides a comprehensive reference for the SRE Copilot API, including all classes, methods, and parameters.

## Table of Contents

1. [Core Modules](#core-modules)
   - [configure_agents](#configure_agents)
   - [test_functionality](#test_functionality)
   - [knowledge_base_manager](#knowledge_base_manager)
   - [incident_analyzer](#incident_analyzer)
2. [Utility Modules](#utility-modules)
3. [Configuration](#configuration)
4. [Error Handling](#error-handling)

## Core Modules

### configure_agents

The `configure_agents` module provides functionality for creating and configuring AWS Bedrock agents for the SRE Copilot system.

#### Classes

##### `SREAgentConfigurator`

```python
class SREAgentConfigurator:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1')
```

**Parameters:**
- `config_file` (str): Path to the configuration file. Default: 'sre_copilot_config.json'
- `region` (str): AWS region. Default: 'us-east-1'

**Methods:**

```python
def create_supervisor_agent(self)
```
Creates the Supervisor Agent that coordinates the specialized agents.

**Returns:** Agent ID (str)

```python
def create_log_analysis_agent(self)
```
Creates the Log Analysis Agent for analyzing log data.

**Returns:** Agent ID (str)

```python
def create_metrics_analysis_agent(self)
```
Creates the Metrics Analysis Agent for analyzing time-series metrics.

**Returns:** Agent ID (str)

```python
def create_dashboard_analysis_agent(self)
```
Creates the Dashboard Analysis Agent for interpreting dashboard visualizations.

**Returns:** Agent ID (str)

```python
def create_knowledge_base_agent(self)
```
Creates the Knowledge Base Agent for maintaining and querying historical incident data.

**Returns:** Agent ID (str)

```python
def create_knowledge_base(self)
```
Creates the knowledge base for storing historical incident data.

**Returns:** Knowledge Base ID (str)

```python
def configure_agent_collaboration(self)
```
Configures the collaboration between the specialized agents.

**Returns:** Boolean indicating success

```python
def save_configuration(self)
```
Saves the configuration to a JSON file.

**Returns:** Boolean indicating success

### test_functionality

The `test_functionality` module provides functionality for testing the SRE Copilot agents.

#### Classes

##### `SREAgentTester`

```python
class SREAgentTester:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1')
```

**Parameters:**
- `config_file` (str): Path to the configuration file. Default: 'sre_copilot_config.json'
- `region` (str): AWS region. Default: 'us-east-1'

**Methods:**

```python
def test_supervisor_agent(self)
```
Tests the Supervisor Agent functionality.

**Returns:** Test results (dict)

```python
def test_agent_collaboration(self)
```
Tests the collaboration between the specialized agents.

**Returns:** Test results (dict)

```python
def test_knowledge_base(self)
```
Tests the knowledge base functionality.

**Returns:** Test results (dict)

```python
def run_all_tests(self)
```
Runs all tests.

**Returns:** Test results (dict)

### knowledge_base_manager

The `knowledge_base_manager` module provides functionality for managing the SRE Copilot knowledge base.

#### Classes

##### `SREKnowledgeBaseManager`

```python
class SREKnowledgeBaseManager:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1')
```

**Parameters:**
- `config_file` (str): Path to the configuration file. Default: 'sre_copilot_config.json'
- `region` (str): AWS region. Default: 'us-east-1'

**Methods:**

```python
def add_incident(self, incident_id, description, root_cause, resolution, services)
```
Adds an incident to the knowledge base.

**Parameters:**
- `incident_id` (str): Unique identifier for the incident
- `description` (str): Description of the incident
- `root_cause` (str): Root cause of the incident
- `resolution` (str): Resolution steps
- `services` (str or list): Affected services

**Returns:** Boolean indicating success

```python
def update_incident(self, incident_id, field, value)
```
Updates a field in an existing incident.

**Parameters:**
- `incident_id` (str): Unique identifier for the incident
- `field` (str): Field to update
- `value` (str): New value for the field

**Returns:** Boolean indicating success

```python
def query_incidents(self, query_text, limit=5)
```
Queries incidents by semantic similarity.

**Parameters:**
- `query_text` (str): Query text
- `limit` (int): Maximum number of results. Default: 5

**Returns:** List of matching incidents

```python
def backup_knowledge_base(self, output_file)
```
Backs up all incidents in the knowledge base to a file.

**Parameters:**
- `output_file` (str): Output file path

**Returns:** Boolean indicating success

```python
def restore_knowledge_base(self, input_file)
```
Restores incidents from a backup file to the knowledge base.

**Parameters:**
- `input_file` (str): Input file path

**Returns:** Boolean indicating success

### incident_analyzer

The `incident_analyzer` module provides functionality for analyzing incidents with the SRE Copilot.

#### Classes

##### `SRECopilotAnalyzer`

```python
class SRECopilotAnalyzer:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1')
```

**Parameters:**
- `config_file` (str): Path to the configuration file. Default: 'sre_copilot_config.json'
- `region` (str): AWS region. Default: 'us-east-1'

**Methods:**

```python
def analyze_incident(self, incident_description, log_data=None, metrics_data=None, dashboard_data=None)
```
Analyzes an incident using the SRE Copilot.

**Parameters:**
- `incident_description` (str): Description of the incident
- `log_data` (str, optional): Log data
- `metrics_data` (str, optional): Metrics data
- `dashboard_data` (str, optional): Dashboard data

**Returns:** Analysis result (str)

```python
def fetch_cloudwatch_logs(self, log_group, start_time, end_time, filter_pattern=None, limit=100)
```
Fetches logs from CloudWatch Logs.

**Parameters:**
- `log_group` (str): CloudWatch log group
- `start_time` (float): Start time in seconds since epoch
- `end_time` (float): End time in seconds since epoch
- `filter_pattern` (str, optional): Filter pattern
- `limit` (int): Maximum number of log events. Default: 100

**Returns:** Log messages (str)

```python
def fetch_cloudwatch_metrics(self, namespace, metric_name, dimensions, start_time, end_time, period=60, statistic='Average')
```
Fetches metrics from CloudWatch.

**Parameters:**
- `namespace` (str): Metric namespace
- `metric_name` (str): Metric name
- `dimensions` (list): Metric dimensions
- `start_time` (datetime): Start time
- `end_time` (datetime): End time
- `period` (int): Period in seconds. Default: 60
- `statistic` (str): Statistic. Default: 'Average'

**Returns:** Metric data (str)

```python
def analyze_with_data_sources(self, incident_description, log_groups=None, metrics=None, dashboard_description=None)
```
Analyzes an incident with automatically fetched data sources.

**Parameters:**
- `incident_description` (str): Description of the incident
- `log_groups` (list, optional): CloudWatch log groups
- `metrics` (list, optional): Metrics configuration
- `dashboard_description` (str, optional): Dashboard description

**Returns:** Analysis result (str)

## Utility Modules

The SRE Copilot includes utility modules for common tasks:

- **Logging**: Standardized logging configuration
- **AWS Authentication**: Helpers for AWS authentication
- **Data Processing**: Utilities for processing logs and metrics
- **Error Handling**: Common error handling patterns

## Configuration

The SRE Copilot uses a JSON configuration file with the following structure:

```json
{
  "supervisor_agent": {
    "id": "string",
    "name": "string",
    "instructions": "string"
  },
  "specialized_agents": {
    "log_analysis": {
      "id": "string",
      "name": "string",
      "instructions": "string"
    },
    "metrics_analysis": {
      "id": "string",
      "name": "string",
      "instructions": "string"
    },
    "dashboard_analysis": {
      "id": "string",
      "name": "string",
      "instructions": "string"
    },
    "knowledge_base": {
      "id": "string",
      "name": "string",
      "instructions": "string"
    }
  },
  "knowledge_base": {
    "id": "string",
    "name": "string",
    "data_source_config": {
      "collectionId": "string",
      "vectorIndexName": "string"
    }
  }
}
```

## Error Handling

The SRE Copilot uses a standardized error handling approach:

1. **Specific Exceptions**: Each module defines specific exceptions for different error types
2. **Logging**: All errors are logged with appropriate context
3. **Retry Logic**: Critical operations include retry logic with exponential backoff
4. **Graceful Degradation**: The system can operate with reduced functionality if some components fail

Common exceptions include:

- `ConfigurationError`: Error in the configuration
- `AgentCreationError`: Error creating an agent
- `KnowledgeBaseError`: Error with the knowledge base
- `AnalysisError`: Error during incident analysis
- `AWSResourceError`: Error with AWS resources

Example error handling:

```python
try:
    result = analyzer.analyze_incident(incident_description)
except AnalysisError as e:
    logger.error(f"Analysis failed: {e}")
    # Fallback to basic analysis
    result = analyzer.analyze_incident(incident_description, use_fallback=True)
```

For more detailed information on using the SRE Copilot API, refer to the [Usage Guide](usage_guide.md).
