# SRE Copilot - Complete System Flow Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Complete Demo Flow](#complete-demo-flow)
4. [Incident Creation Flow](#incident-creation-flow)
5. [EventBridge and Lambda Triggers](#eventbridge-and-lambda-triggers)
6. [Lambda Functions Details](#lambda-functions-details)
7. [Bedrock Agents and Action Groups](#bedrock-agents-and-action-groups)
8. [Knowledge Base Implementation](#knowledge-base-implementation)
9. [Code Locations and Directory Structure](#code-locations-and-directory-structure)
10. [How Everything Works Together](#how-everything-works-together)

---

## 1. System Overview

The SRE Copilot is an AI-powered Site Reliability Engineering assistant that:
- Monitors AWS services through CloudWatch metrics and logs
- Automatically creates incidents in AWS Systems Manager OpsItems
- Triggers AI-powered root cause analysis using AWS Bedrock
- Correlates data from multiple AWS services
- Maintains a searchable knowledge base of past incidents
- Provides actionable recommendations for incident resolution

### Key Technologies:
- **AWS Bedrock**: Claude 3 Sonnet for AI analysis
- **AWS Lambda**: Serverless compute for all agents
- **DynamoDB**: Serverless vector database for knowledge base
- **CloudWatch**: Metrics and logs monitoring
- **Systems Manager**: OpsItems for incident tracking
- **EventBridge**: Event-driven triggers
- **Streamlit**: Web dashboard interface

---

## 2. Architecture Components

```
┌─────────────────────────┐
│   Streamlit Dashboard   │ Port: 8501
│  (streamlit_app.py)     │
└───────────┬─────────────┘
            │ Creates OpsItem
            ▼
┌─────────────────────────┐
│ AWS Systems Manager     │
│      OpsItems           │
└───────────┬─────────────┘
            │ Triggers
            ▼
┌─────────────────────────┐
│   Supervisor Lambda     │
│ (sre-supervisor-lambda) │
└───────────┬─────────────┘
            │ Orchestrates
            ▼
┌─────────────────────────────────────────────┐
│         Specialized Agent Lambdas           │
├─────────────────────┬───────────────────────┤
│ • CloudWatch Logs   │ • CloudTrail          │
│ • VPC Flow Logs     │ • Trusted Advisor     │
│ • Personal Health   │ • VPC Analyzer        │
└─────────────────────┴───────────────────────┘
            │
            ▼
┌─────────────────────────┐
│   Knowledge Base        │
│  (DynamoDB + Vectors)   │
└─────────────────────────┘
```

---

## 3. Complete Demo Flow

### Step 1: Incident Generation
**Location**: `/home/ec2-user/sre/sre_mcp/streamlit_app.py`

```python
# User clicks "Generate Incident" button in Streamlit
# Method: generate_incident() - Line 1210

def generate_incident(self, scenario_type='performance'):
    # Generate CloudWatch metrics (CPU spike, memory issues)
    # Create CloudWatch logs with errors
    # Create OpsItem in Systems Manager
    ops_item_id = self.create_opsitem(title, description, severity)
```

### Step 2: OpsItem Creation
**Location**: `/home/ec2-user/sre/sre_mcp/streamlit_app.py` - Line 470

```python
def create_opsitem(self, title, description, severity='3'):
    """Create SSM OpsItem."""
    response = self.clients['ssm'].create_ops_item(
        Title=title,
        Description=description,
        Priority=int(severity),
        Source='SRE-Demo-Streamlit',
        Category='Performance',
        Severity=severity,
        OperationalData={
            'start_time': {'Value': start_time},
            'service': {'Value': 'sre-demo-app'},
            'environment': {'Value': 'demo'}
        }
    )
    return response['OpsItemId']
```

### Step 3: Manual Analysis Trigger
**Location**: `/home/ec2-user/sre/sre_mcp/streamlit_app.py` - Line 945

```python
def invoke_supervisor_analysis(self, ops_item, collected_data):
    """Invoke the supervisor agent for analysis."""
    payload = {
        'action': 'analyze',
        'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
        'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        'end_time': datetime.utcnow().isoformat(),
        'service': 'sre-demo-app',
        'environment': 'demo',
        'enable_kb': True,
        'additional_context': {
            'ops_item_id': ops_item.get('OpsItemId'),
            'severity': ops_item.get('Severity')
        }
    }
    
    response = self.lambda_client.invoke(
        FunctionName='sre-supervisor-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
```

---

## 4. Incident Creation Flow

### Important Note: No Automatic CloudWatch Alarm Creation
The system does **NOT** create CloudWatch alarms automatically. Instead:

1. **Manual Incident Creation**: 
   - User clicks "Generate Incident" in Streamlit dashboard
   - System creates demo metrics and logs in CloudWatch
   - OpsItem is created in Systems Manager

2. **Manual Analysis Trigger**:
   - User selects an OpsItem from the dashboard
   - User clicks "Analyze Root Cause" button
   - This invokes the Supervisor Lambda for analysis

### Code Flow for Incident Creation:

**File**: `/home/ec2-user/sre/sre_mcp/streamlit_app.py`

```python
# Line 1210 - Generate incident button
if st.button("🎲 Generate Random Incident"):
    scenario = random.choice(scenarios)
    incident = self.generate_scenario_incident(scenario)
    
# Line 1350 - Generate scenario incident
def generate_scenario_incident(self, scenario):
    # Create metrics and logs
    # Create OpsItem
    ops_item_id = self.create_opsitem(title, description, scenario['severity'])
```

---

## 5. EventBridge and Lambda Triggers

### EventBridge Rule Configuration
**Location**: `/home/ec2-user/sre/sre_mcp/deploy_knowledge_base_serverless.sh` - Line 151

```bash
# Create CloudWatch Events rule for OpsItem auto-indexing
aws events put-rule \
    --name sre-opsitem-indexing \
    --description "Auto-index OpsItems to knowledge base" \
    --event-pattern '{
        "source": ["aws.ssm"],
        "detail-type": ["AWS API Call via CloudTrail"],
        "detail": {
            "eventName": ["CreateOpsItem", "UpdateOpsItem"]
        }
    }'

# Add Lambda as target
# Note: The actual target should be sre-opsitem-indexer, not knowledge-base directly
aws events put-targets \
    --rule sre-opsitem-indexing \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:*:function:sre-opsitem-indexer"
```

### What This Rule Does:
- Monitors CloudTrail for OpsItem creation/update events
- Automatically triggers the **OpsItem Indexer Lambda** (`sre-opsitem-indexer`)
- OpsItem Indexer then calls the Knowledge Base Lambda to index incidents
- Does NOT trigger the supervisor analysis
- Creates a two-step process: EventBridge → OpsItem Indexer → Knowledge Base

---

## 6. Lambda Functions Details

### 6.1 Supervisor Lambda
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/supervisor/lambda_function.py`

```python
def lambda_handler(event, context):
    """Enhanced Lambda handler for supervisor agent."""
    # Extract incident information
    incident_description = event.get('incident_description', '')
    
    # Determine incident type
    incident_type = analyze_incident_type(incident_description)
    
    # Get metrics from CloudWatch
    metrics_data = get_demo_metrics()
    
    # Get logs from CloudWatch
    log_data = get_demo_logs()
    
    # Get knowledge base context
    kb_context = get_knowledge_base_context(incident_description, incident_type)
    
    # Analyze with Bedrock AI
    ai_analysis = analyze_with_bedrock(incident_description, context_data, incident_type)
    
    # Invoke specialized agents
    agent_analyses = invoke_specialized_agents(incident_description, incident_type)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'ai_analysis': ai_analysis,
            'agent_analyses': agent_analyses,
            'metrics_data': metrics_data,
            'log_data': log_data,
            'kb_context': kb_context
        })
    }
```

### 6.2 CloudWatch Logs Agent
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/cloudwatch_logs_agent/lambda_function.py`

```python
def lambda_handler(event, context):
    """Process CloudWatch Logs analysis requests."""
    action = event.get('action', '')
    
    if action == 'get_error_logs':
        return get_error_logs(event)
    elif action == 'analyze_log_group':
        return analyze_log_group(event)
```

### 6.3 OpsItem Indexer Lambda
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/opsitem-indexer/lambda_function.py`

This Lambda is triggered by EventBridge and handles the auto-indexing of OpsItems:

```python
def lambda_handler(event, context):
    """Auto-index OpsItems when created/updated."""
    # Extract OpsItem ID from CloudTrail event
    detail = event.get('detail', {})
    event_name = detail.get('eventName')
    
    if event_name == 'CreateOpsItem':
        ops_item_id = detail['responseElements']['opsItemId']
    elif event_name == 'UpdateOpsItem':
        ops_item_id = detail['requestParameters']['opsItemId']
    
    # Get full OpsItem details
    response = ssm_client.get_ops_item(OpsItemId=ops_item_id)
    ops_item = response['OpsItem']
    
    # Invoke Knowledge Base Lambda
    kb_response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'index_opsitem',
            'ops_item': ops_item
        })
    )
```

### 6.4 Knowledge Base Lambda
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/knowledge-base-agent/lambda_function_serverless.py`

```python
def lambda_handler(event, context):
    """Handle knowledge base operations."""
    kb = ServerlessKnowledgeBase()
    action = event.get('action', 'search')
    
    if action == 'index_opsitem':
        # Called by OpsItem Indexer
        ops_item = event.get('ops_item')
        result = kb.index_opsitem(ops_item)
        return {'statusCode': 200, 'body': json.dumps(result)}
    
    elif action == 'search':
        # Called by Supervisor Lambda
        query = event.get('query', '')
        results = kb.search_similar_documents(query, k=5)
        return {'statusCode': 200, 'body': json.dumps({'results': results})}
```

---

## 7. Bedrock Agents and Action Groups

### Agent Configuration
**Location**: `/home/ec2-user/sre/sre_mcp/configure_bedrock_agents.py`

```python
AGENTS = [
    {
        "name": "SRE-Supervisor",
        "lambda_function": "sre-supervisor-lambda",
        "action_group": "supervisor-actions",
        "instructions": "You are the main SRE supervisor agent..."
    },
    {
        "name": "SRE-CloudTrail-Analyzer",
        "lambda_function": "sre-cloudtrail-agent-lambda",
        "action_group": "cloudtrail-analysis-actions",
        "instructions": "Analyze CloudTrail events for security incidents..."
    },
    # ... more agents
]
```

### Action Group Creation
**Location**: `/home/ec2-user/sre/sre_mcp/src/create_action_groups.py`

```python
def create_action_group(agent_name, action_group_name, lambda_function):
    """Create action group for Bedrock agent."""
    bedrock_agent.create_agent_action_group(
        agentId=agent_id,
        actionGroupName=action_group_name,
        actionGroupExecutor={
            'lambda': lambda_function_arn
        },
        apiSchema={
            'openapi': '3.0.0',
            'paths': {
                '/analyze': {
                    'post': {
                        'operationId': 'analyzeIncident',
                        'requestBody': {
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'incident_description': {'type': 'string'},
                                            'start_time': {'type': 'string'},
                                            'end_time': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
```

---

## 8. Knowledge Base Implementation

### 8.1 Vector Search Implementation
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/knowledge-base-agent/lambda_function_serverless.py`

```python
class ServerlessKnowledgeBase:
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Amazon Titan."""
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({"inputText": text})
        )
        return json.loads(response['body'].read())['embedding']
    
    def search_similar_documents(self, query: str, k: int = 5):
        """Search for similar documents using vector similarity."""
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Get all documents and calculate similarities
        documents = self.kb_table.scan()['Items']
        
        similarities = []
        for doc in documents:
            # Get document embedding
            vector_response = self.vectors_table.get_item(
                Key={'document_id': doc['document_id']}
            )
            if 'Item' in vector_response:
                doc_embedding = vector_response['Item']['embedding']
                similarity = self.cosine_similarity(query_embedding, doc_embedding)
                similarities.append({
                    'document': doc,
                    'similarity': similarity
                })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:k]
```

### 8.2 Auto-Indexing OpsItems
**Location**: `/home/ec2-user/sre/sre_mcp/src/lambdas/opsitem-indexer/lambda_function.py`

```python
def lambda_handler(event, context):
    """Auto-index OpsItems to knowledge base."""
    # Extract OpsItem from CloudTrail event
    detail = event['detail']
    ops_item_id = detail['requestParameters']['opsItemId']
    
    # Get OpsItem details
    ops_item = ssm.describe_ops_items(OpsItemId=ops_item_id)
    
    # Create knowledge base document
    document = {
        'document_id': f'opsitem-{ops_item_id}',
        'title': ops_item['Title'],
        'content': ops_item['Description'],
        'metadata': {
            'category': 'incident',
            'type': 'opsitem',
            'severity': ops_item['Severity'],
            'tags': ['auto-indexed', 'incident']
        }
    }
    
    # Index to knowledge base
    kb = ServerlessKnowledgeBase()
    kb.index_document(document)
```

---

## 9. Code Locations and Directory Structure

```
/home/ec2-user/sre/sre_mcp/
├── streamlit_app.py                    # Main dashboard application
├── incident_generator_demo.py          # Demo incident generator
├── configure_bedrock_agents.py         # Bedrock agent configuration
├── deploy_knowledge_base_serverless.sh # KB deployment script
├── src/
│   ├── lambdas/
│   │   ├── supervisor/
│   │   │   └── lambda_function.py     # Main orchestrator Lambda
│   │   ├── cloudwatch_logs_agent/
│   │   │   └── lambda_function.py     # CloudWatch logs analyzer
│   │   ├── cloudtrail_agent/
│   │   │   └── lambda_function.py     # CloudTrail analyzer
│   │   ├── vpc_agent/
│   │   │   └── lambda_function.py     # VPC analyzer
│   │   ├── vpc_flow_logs_agent/
│   │   │   └── lambda_function.py     # VPC Flow Logs analyzer
│   │   ├── trusted_advisor_agent/
│   │   │   └── lambda_function.py     # Trusted Advisor analyzer
│   │   ├── personal_health_agent/
│   │   │   └── lambda_function.py     # Personal Health analyzer
│   │   ├── knowledge-base-agent/
│   │   │   └── lambda_function_serverless.py # KB search/index
│   │   └── opsitem-indexer/
│   │       └── lambda_function.py     # Auto-index OpsItems
│   ├── core/
│   │   ├── configure_agents.py        # Agent configuration
│   │   └── validate_agents.py         # Agent validation
│   └── create_action_groups.py        # Action group creation
├── orchestration/
│   └── incident_analyzer.py           # Enhanced incident analysis
└── utils/
    └── ip_masker.py                  # IP masking utility
```

---

## 10. How Everything Works Together

### Enhanced Automatic End-to-End Flow:

1. **User Initiates Incident**:
   - Opens Streamlit dashboard (http://localhost:8501)
   - Clicks "Generate Random Incident" button
   - System creates demo metrics/logs in CloudWatch

2. **OpsItem Creation**:
   - Streamlit calls `create_opsitem()` method
   - Creates OpsItem in AWS Systems Manager
   - Returns OpsItem ID to dashboard

3. **Automatic AI Analysis Triggered** (NEW - Fully Automatic):
   - EventBridge rule detects OpsItem creation via CloudTrail
   - Triggers enhanced `sre-opsitem-indexer` Lambda
   - OpsItem Indexer performs THREE actions:
     * Indexes OpsItem to Knowledge Base
     * **Automatically invokes Supervisor Lambda for AI analysis**
     * Updates OpsItem with analysis results

4. **Automatic Root Cause Analysis** (No User Action Required):
   - Supervisor Lambda automatically:
     * Collects CloudWatch metrics and logs
     * Searches Knowledge Base for similar incidents
     * **Invokes ALL specialized agent Lambdas**
     * Generates AI-powered analysis using Bedrock Claude 3
   - Results automatically stored in OpsItem and Knowledge Base

5. **Automatic Agent Orchestration** (Enhanced):
   - Supervisor Lambda automatically invokes ALL applicable agents:
     * CloudWatch Logs Agent - analyzes application logs
     * CloudTrail Agent - checks security events
     * VPC Agent - analyzes network configurations
     * VPC Flow Logs Agent - checks network traffic
     * Trusted Advisor Agent - gets AWS recommendations
     * Personal Health Agent - checks AWS service health
   - All agents run in parallel for faster analysis

6. **Comprehensive AI Analysis**:
   - Supervisor sends ALL collected data to Bedrock Claude 3:
     * Metrics from CloudWatch
     * Logs with error patterns
     * Findings from all 6+ specialized agents
     * Similar incidents from Knowledge Base
   - AI generates comprehensive root cause analysis
   - Provides specific, actionable recommendations

7. **Automatic Results Storage**:
   - OpsItem updated with:
     * AI analysis summary
     * Root cause determination
     * Recommendations
     * Agent findings
   - Full analysis indexed to Knowledge Base
   - Available immediately in Streamlit dashboard

8. **Manual Review (Optional)**:
   - User can view automatic analysis in dashboard
   - No action required - analysis already complete
   - Can trigger additional analysis if needed

### Key Integration Points:

1. **No Grafana Integration**: System uses CloudWatch directly
2. **Manual Triggers**: Analysis requires user action
3. **EventBridge**: Only for KB indexing, not analysis
4. **Bedrock AI**: Central to intelligent analysis
5. **DynamoDB KB**: Cost-effective vector search
6. **Correlation**: Defects, changes, and incidents linked

### Configuration Requirements:

1. **AWS Credentials**: Proper IAM roles for all services
2. **Region**: us-east-1 (hardcoded in many places)
3. **Python**: Version 3.x required
4. **Dependencies**: boto3, streamlit, plotly, pandas
5. **Network**: Access to AWS services and Bedrock

This documentation provides a complete understanding of the SRE Copilot system without requiring access to the repository.

---

## 11. Deploying the Enhanced Automatic AI Analysis

To enable the automatic AI analysis flow:

### Step 1: Deploy Enhanced OpsItem Indexer
```bash
cd /home/ec2-user/sre/sre_mcp
./deploy_enhanced_opsitem_indexer.sh
```

This will:
- Update the OpsItem Indexer Lambda with automatic AI triggering
- Configure EventBridge rule to use the enhanced indexer
- Set up proper IAM permissions

### Step 2: Update Supervisor Lambda
```bash
./update_supervisor_for_auto_analysis.sh
```

This will:
- Update Supervisor Lambda to automatically invoke all agents
- Configure longer timeout for comprehensive analysis
- Enable parallel agent invocation

### Step 3: Test the Automatic Flow
```bash
python3 test_automatic_ai_analysis.py
```

This will:
- Create a test OpsItem
- Monitor the automatic analysis progress
- Display results when complete
- Verify Knowledge Base indexing

### Expected Timeline:
1. OpsItem Creation: Immediate
2. EventBridge Trigger: ~30-60 seconds (CloudTrail delay)
3. Knowledge Base Indexing: ~10 seconds
4. AI Analysis: ~60-120 seconds
5. Total Time: ~2-3 minutes for complete analysis

### Monitoring:
- Check CloudWatch Logs for each Lambda
- View OpsItem in Systems Manager console
- Monitor Streamlit dashboard for updates

The system is now fully automated - every incident gets AI-powered root cause analysis without any manual intervention!