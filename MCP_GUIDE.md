# Model Context Protocol (MCP) Guide for SRE Copilot

## What is MCP?

Model Context Protocol (MCP) is a communication framework that enables:
- **Standardized messaging** between AI agents
- **Context preservation** across agent interactions
- **Structured data exchange** for complex workflows
- **Agent orchestration** with clear communication patterns

## Why Use MCP?

### 1. **Agent-to-Agent Communication** 🔄
MCP enables different monitoring agents to communicate effectively:
- CloudTrail agent can notify VPC agent about security events
- Personal Health agent can alert other agents about maintenance windows
- Supervisor can coordinate responses from multiple agents

### 2. **Context Preservation** 📝
MCP maintains context across interactions:
```python
# Example: MCP preserves incident context
incident_context = {
    "incident_id": "INC-12345",
    "start_time": "2024-01-15T10:00:00Z",
    "affected_services": ["API", "Database"],
    "previous_analyses": [...],
    "correlated_events": [...]
}
```

### 3. **Structured Communication** 📊
MCP provides structured message formats:
```python
mcp_message = {
    "header": {
        "message_id": "msg-123",
        "timestamp": "2024-01-15T10:30:00Z",
        "sender": "cloudtrail-agent",
        "recipient": "supervisor-agent",
        "correlation_id": "incident-456"
    },
    "body": {
        "event_type": "security_alert",
        "severity": "high",
        "data": {...}
    }
}
```

### 4. **Workflow Orchestration** 🎯
MCP enables complex incident response workflows:
1. Supervisor receives incident report
2. Broadcasts to all monitoring agents via MCP
3. Agents analyze their domains and respond via MCP
4. Supervisor correlates responses
5. Generates unified action plan

## Where MCP is Used in SRE Copilot

### 1. **Inter-Agent Communication**
```python
# CloudTrail agent detects suspicious activity
mcp_alert = MCPMessage(
    sender="cloudtrail-agent",
    recipient="supervisor-agent",
    event_type="security_alert",
    data={
        "event": "UnauthorizedAPICall",
        "source_ip": "192.168.1.100",
        "severity": "high"
    }
)
```

### 2. **Incident Correlation**
```python
# Supervisor correlates events from multiple agents
correlations = [
    {"agent": "cloudtrail", "event": "API errors spike"},
    {"agent": "vpc-flow-logs", "event": "Network traffic anomaly"},
    {"agent": "cloudwatch", "event": "High CPU usage"}
]
# MCP helps identify related events across services
```

### 3. **Knowledge Sharing**
```python
# Agent shares learned pattern via MCP
knowledge_share = MCPMessage(
    sender="trusted-advisor-agent",
    recipient="all-agents",
    event_type="pattern_detected",
    data={
        "pattern": "Cost spike after auto-scaling",
        "mitigation": "Review scaling policies"
    }
)
```

### 4. **Coordinated Response**
```python
# Supervisor coordinates response actions
response_plan = MCPMessage(
    sender="supervisor-agent",
    recipient="all-agents",
    event_type="execute_response",
    data={
        "actions": [
            {"agent": "cloudwatch", "action": "increase_monitoring"},
            {"agent": "vpc", "action": "tighten_security_groups"},
            {"agent": "personal-health", "action": "check_service_health"}
        ]
    }
)
```

## Benefits of MCP in SRE Copilot

### 1. **Faster Incident Resolution** ⚡
- Parallel analysis by multiple agents
- Instant correlation of related events
- Automated response coordination

### 2. **Better Context Understanding** 🧠
- Full incident history preserved
- Cross-service impact analysis
- Pattern recognition across agents

### 3. **Scalability** 📈
- Easy to add new agents
- Standardized communication protocol
- Decoupled agent architecture

### 4. **Reliability** 🛡️
- Message delivery guarantees
- Error handling and retries
- Audit trail of all communications

## MCP Architecture in SRE Copilot

```
┌─────────────────────┐
│   Supervisor Agent  │ ← Master Coordinator
└──────────┬──────────┘
           │ MCP
    ┌──────┴──────┐
    │             │
┌───▼───┐    ┌───▼───┐
│CloudTrail│  │  VPC   │
│ Agent  │    │ Agent  │
└───┬───┘    └───┬───┘
    │ MCP        │ MCP
    │            │
┌───▼───────────▼───┐
│   Message Broker   │ ← Central MCP Hub
└───┬───────────┬───┘
    │           │
┌───▼───┐   ┌──▼────┐
│Health  │   │Trusted│
│Agent   │   │Advisor│
└────────┘   └───────┘
```

## MCP Message Types

### 1. **Alert Messages**
- Security alerts
- Performance degradation
- Service failures

### 2. **Query Messages**
- Status requests
- Data queries
- Configuration checks

### 3. **Response Messages**
- Analysis results
- Recommended actions
- Status updates

### 4. **Control Messages**
- Start/stop monitoring
- Configuration updates
- Coordination commands

## Best Practices for MCP Usage

### 1. **Message Design**
- Keep messages focused and specific
- Include correlation IDs for tracking
- Use consistent data schemas

### 2. **Error Handling**
- Implement retry logic
- Handle timeouts gracefully
- Log all communication failures

### 3. **Performance**
- Use asynchronous messaging
- Batch related messages
- Implement message priorities

### 4. **Security**
- Encrypt sensitive data
- Validate message sources
- Implement access controls

## Example: MCP in Action

```python
# Incident Detection Flow with MCP

# 1. CloudWatch detects high CPU
cpu_alert = MCPMessage(
    sender="cloudwatch-agent",
    event_type="performance_alert",
    data={"cpu_usage": 95, "duration": "10min"}
)

# 2. Supervisor receives and broadcasts
supervisor.broadcast_investigation_request(
    incident_id="INC-789",
    symptoms=["high_cpu"],
    affected_services=["web-api"]
)

# 3. Agents respond via MCP
responses = [
    {"agent": "cloudtrail", "finding": "Spike in API calls"},
    {"agent": "vpc", "finding": "DDoS pattern detected"},
    {"agent": "health", "finding": "No AWS issues"}
]

# 4. Supervisor correlates and responds
action_plan = supervisor.generate_response_plan(responses)
supervisor.broadcast_execute_actions(action_plan)
```

## Conclusion

MCP is essential for:
- ✅ Coordinated incident response
- ✅ Cross-agent communication
- ✅ Context-aware analysis
- ✅ Scalable agent architecture
- ✅ Reliable message delivery

It transforms individual monitoring agents into a coordinated, intelligent SRE team.