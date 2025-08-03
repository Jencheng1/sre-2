# MCP Integration Architecture for SRE Copilot

## Overview
This document outlines the integration of Model Context Protocol (MCP) servers with the SRE Copilot to enable correlation with external services and enhance root cause analysis capabilities.

## MCP Servers

### 1. Splunk MCP Server
- **Purpose**: Network latency monitoring and analysis
- **Endpoints**:
  - `/search` - Search for network latency events
  - `/metrics` - Get network performance metrics
  - `/alerts` - Retrieve network-related alerts

### 2. Dynatrace MCP Server
- **Purpose**: MQ (Message Queue) metrics and application performance
- **Endpoints**:
  - `/mq/metrics` - Get MQ performance metrics
  - `/apm/traces` - Application performance traces
  - `/problems` - Active problems and anomalies

### 3. ServiceNow MCP Server
- **Purpose**: Incident and change management
- **Endpoints**:
  - `/incidents` - Query and create incidents
  - `/changes` - Query change requests
  - `/cmdb` - Configuration management database

### 4. Confluence MCP Server
- **Purpose**: Knowledge base articles and documentation
- **Endpoints**:
  - `/search` - Search knowledge articles
  - `/pages` - Get page content
  - `/spaces` - List and search spaces

### 5. GitLab MCP Server
- **Purpose**: Source code analysis and correlation
- **Endpoints**:
  - `/repos` - Search repositories
  - `/commits` - Get recent commits
  - `/merge_requests` - Check merge requests
  - `/code_search` - Search code for patterns

## Integration Flow

```
┌─────────────────┐
│   Streamlit UI  │
└────────┬────────┘
         │
┌────────▼────────┐
│ Supervisor Lambda│
└────────┬────────┘
         │
┌────────▼────────────────────────────┐
│       MCP Orchestrator              │
│  ┌─────────┬──────────┬─────────┐  │
│  │ Splunk  │Dynatrace │ServiceNow│  │
│  │   MCP   │   MCP    │   MCP   │  │
│  └─────────┴──────────┴─────────┘  │
│  ┌─────────────┬──────────────┐    │
│  │ Confluence  │    GitLab    │    │
│  │     MCP     │      MCP     │    │
│  └─────────────┴──────────────┘    │
└─────────────────────────────────────┘
```

## Human-in-the-Loop Feedback System

### Components:
1. **Feedback Collection**: UI components in Streamlit for rating and commenting on analysis
2. **Context Storage**: DynamoDB table for storing feedback with embeddings
3. **Context Enhancement**: Integration with Knowledge Base for improved future analysis
4. **Feedback Loop**: Automatic incorporation of validated feedback into KB

### Feedback Flow:
1. User receives root cause analysis
2. User provides feedback (rating, corrections, additional context)
3. Feedback is stored with incident correlation
4. Future similar incidents benefit from historical feedback
5. Continuous improvement of accuracy

## Configuration System

### MCP Configuration Schema:
```json
{
  "mcp_servers": {
    "splunk": {
      "enabled": true,
      "endpoint": "http://localhost:8080/splunk",
      "auth": "bearer_token",
      "test_mode": true
    },
    "dynatrace": {
      "enabled": true,
      "endpoint": "http://localhost:8081/dynatrace",
      "auth": "api_token",
      "test_mode": true
    }
  },
  "external_data_sources": {
    "custom_api": {
      "type": "rest",
      "endpoint": "https://api.example.com",
      "auth_type": "oauth2"
    }
  }
}
```

## Test Data Strategy
- Each MCP server will have a test data generator
- Test data mimics real production patterns
- Configurable scenarios for different incident types
- Real API calls with test data responses