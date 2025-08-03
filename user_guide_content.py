"""
User Guide Content for SRE Copilot
Contains all help documentation and tutorials
"""

USER_GUIDES = {
    "overview": {
        "title": "🚀 SRE Copilot Overview",
        "content": """
## Welcome to SRE Copilot!

SRE Copilot is an AI-powered incident management system that helps you:
- 🔍 **Analyze Root Causes**: Automatically correlate events across AWS services
- 📚 **Manage Knowledge**: Build and search a knowledge base of incidents and solutions
- 🎯 **Generate Test Incidents**: Create realistic scenarios for training and testing
- 📊 **Visualize Impact**: Understand business and technical impact of incidents

### Key Features:
1. **Real-time Analysis**: Uses AWS Bedrock agents to analyze live data
2. **Multi-Source Correlation**: Combines CloudWatch, CloudTrail, VPC Flow Logs, and more
3. **Historical Context**: Learns from past incidents to improve recommendations
4. **Business Impact Assessment**: Quantifies revenue and customer impact

### Getting Started:
- Use the **sidebar** to navigate between features
- Start with **Generate Incident** to create a test scenario
- Then use **Analyze Incident** to see AI-powered root cause analysis
- Build your knowledge base with resolved incidents
"""
    },
    
    "incident_analysis": {
        "title": "🔍 Incident Root Cause Analysis Guide",
        "content": """
## How to Perform Root Cause Analysis

### Step 1: Select or Generate an Incident
1. Go to **"Analyze Incident"** tab
2. Either:
   - Select an existing incident from the dropdown
   - Enter an OpsItem ID manually
   - Generate a new incident using the "Generate Incident" tab

### Step 2: Analyze the Incident
1. Click **"Analyze Root Cause"** button
2. The system will:
   - Query 7 different AWS data sources
   - Correlate events across services
   - Identify patterns and anomalies
   - Generate actionable recommendations

### Step 3: Review Analysis Results
The analysis provides multiple views:

#### 🎯 Root Cause Tab
- Primary cause identification
- Contributing factors
- Business impact assessment (revenue loss, SLA risk)
- Affected services and regions

#### 📊 Data Analysis Tab
- Metrics visualization (CPU, Memory, Errors)
- Log analysis with relevant entries
- Performance trends and anomalies

#### 🔗 Correlations Tab
- Related changes (if any)
- Similar past incidents
- Pattern detection results
- Timeline of events

#### 💡 Recommendations Tab
- Immediate actions to resolve
- Long-term improvements
- Preventive measures
- Relevant runbooks

### Understanding Incident Types:

**Performance Incidents** 🐌
- High CPU/Memory usage
- Slow response times
- Database bottlenecks
- Signs: Degraded user experience, timeout errors

**Security Incidents** 🔒
- Unauthorized access attempts
- Configuration changes
- Suspicious API calls
- Signs: Failed auth attempts, unexpected changes

**Outage Incidents** 🚨
- Service unavailable
- Critical errors
- Infrastructure failures
- Signs: 5xx errors, health check failures

### Pro Tips:
- 🕐 Check the timeline for change correlation
- 📈 Look for patterns in metrics before the incident
- 🔄 Compare with similar past incidents
- 📋 Export analysis for post-mortem reviews
"""
    },
    
    "knowledge_management": {
        "title": "📚 Knowledge Management Guide",
        "content": """
## Building and Using the Knowledge Base

### What is the Knowledge Base?
A searchable repository of:
- Past incidents and their resolutions
- Best practices and runbooks
- Common patterns and solutions
- Team knowledge and expertise

### How to Search the Knowledge Base

#### 1. Navigate to Knowledge Base Tab
Click on **"Knowledge Base"** in the main navigation

#### 2. Choose Your Search Method

**Option A: Search by Similar Incident**
1. Select an incident from the dropdown
2. Click **"Load Query"** to auto-populate search terms
3. Choose search type:
   - **Similar Incidents**: Find comparable past issues
   - **Best Practices**: Get relevant procedures
   - **Resolution Guides**: Find specific fixes

**Option B: Manual Search**
1. Enter keywords in the search box
2. Examples:
   - "database connection timeout"
   - "high CPU utilization EC2"
   - "security group misconfiguration"

#### 3. Filter Results (Optional)
- Select category: performance, security, outage, data
- Adjust max results (1-20)

#### 4. Review Search Results
Each result shows:
- 📊 **Similarity Score**: How closely it matches (0-100%)
- 📄 **Title and Description**: Quick overview
- 🏷️ **Category and Type**: Classification
- 🔧 **Resolution**: How it was fixed
- 📈 **Impact**: Business consequences

### Adding to the Knowledge Base

#### Automatic Addition
- All resolved OpsItems are automatically indexed
- Includes incident details, root cause, and resolution

#### Manual Addition
1. Go to **"Add Document"** tab
2. Fill in:
   - **Title**: Clear, searchable title
   - **Category**: performance/security/outage/data
   - **Type**: incident/best_practice/resolution_guide
   - **Content**: Detailed description
   - **Tags**: Keywords for search

### Best Practices for Knowledge Management

#### 🎯 Writing Good Titles
- Be specific: "RDS Connection Pool Exhaustion" not "Database Issue"
- Include service names: "ELB 504 Gateway Timeout Error"
- Add impact level: "Critical: Payment Service Outage"

#### 📝 Content Guidelines
- **Problem**: Describe symptoms and impact
- **Root Cause**: Explain why it happened
- **Resolution**: Step-by-step fix
- **Prevention**: How to avoid recurrence

#### 🏷️ Effective Tagging
- Use service names: ec2, rds, lambda, elb
- Include error codes: OOM, 504, ConnectionTimeout
- Add patterns: memory-leak, ddos, misconfiguration

### Using KB for Incident Response

1. **During an Incident**:
   - Search for similar past incidents
   - Find immediate remediation steps
   - Check for known workarounds

2. **Post-Incident**:
   - Document new findings
   - Update existing guides
   - Share lessons learned

3. **Proactive Improvement**:
   - Review common incidents
   - Identify automation opportunities
   - Update runbooks regularly

### Search Tips:
- 🔍 Use specific error messages
- 🎯 Include AWS service names
- 📊 Filter by category for faster results
- ⏱️ Sort by date for recent issues
"""
    },
    
    "generating_incidents": {
        "title": "🎮 Generating Test Incidents",
        "content": """
## How to Generate Test Incidents

### Why Generate Test Incidents?
- 🧪 Test your incident response procedures
- 📚 Train team members safely
- 🔧 Validate monitoring and alerting
- 📊 Build knowledge base content

### Step-by-Step Guide

#### 1. Access Incident Generator
- Click **"Generate Incident"** in the sidebar
- Or use the Incident Generator section on the main dashboard

#### 2. Choose Incident Type
Select from three categories:

**Performance Issues** 🐌
- High CPU utilization
- Memory exhaustion  
- Slow response times
- Database bottlenecks

**Security Events** 🔒
- Unauthorized access attempts
- Security group changes
- Suspicious API activity
- Configuration violations

**Service Outages** 🚨
- Complete service failures
- Critical component crashes
- Network connectivity loss
- Infrastructure problems

#### 3. Configure Parameters (Optional)
- **Severity**: How critical (1-5)
- **Duration**: How long it lasts
- **Services**: Which AWS services to involve
- **Region**: Where to simulate

#### 4. Generate the Incident
1. Click **"Generate Incident"** button
2. System will create:
   - CloudWatch metrics and logs
   - VPC Flow Log entries
   - CloudTrail events
   - Systems Manager OpsItem

#### 5. View Generated Components
After generation, you'll see:
- ✅ OpsItem ID for tracking
- ✅ Metrics created
- ✅ Log entries generated
- ✅ Timeline of events

### Understanding Generated Data

#### Metrics Created
- **CPUUtilization**: Spikes for performance issues
- **MemoryUtilization**: High usage patterns
- **ErrorRate**: Increased for outages
- **ResponseTime**: Latency spikes

#### Log Patterns
- Error messages matching the scenario
- Stack traces for debugging
- Warning signs before the incident
- Recovery indicators

#### Timeline
- **T-15min**: Initial warning signs
- **T-5min**: Escalating issues
- **T-0**: Full incident
- **T+30min**: Resolution metrics

### Best Practices

#### For Training
1. Start with low severity incidents
2. Progress to complex scenarios
3. Practice during business hours
4. Document response times

#### For Testing
1. Generate different types regularly
2. Verify alert triggering
3. Test automation responses
4. Validate runbook procedures

#### For Knowledge Building
1. Generate realistic scenarios
2. Document resolution steps
3. Create best practices
4. Update based on real incidents

### Important Notes:
- 📍 All test data goes to **SREDemo** namespace
- 🏷️ Tagged as test data for easy cleanup
- 💰 Minimal AWS costs (CloudWatch storage)
- 🧹 Auto-cleanup after 24 hours
"""
    },
    
    "recent_changes": {
        "title": "🔄 Recent Changes & Correlation",
        "content": """
## Understanding Change Correlation

### Why Track Changes?
Studies show that 80% of incidents are caused by changes:
- Configuration updates
- Code deployments
- Infrastructure modifications
- Security policy changes

### Using the Recent Changes Feature

#### 1. View Recent Changes
- Click **"Recent Changes"** tab
- Shows all changes from last 24 hours
- Includes both manual and automated changes

#### 2. Understanding Change Information
Each change displays:
- **Change ID**: Unique identifier
- **Type**: Configuration/Deployment/Security
- **Time**: When it occurred
- **Description**: What was changed
- **Risk Level**: Potential impact

#### 3. Correlating with Incidents
The system automatically:
- Matches changes to incidents by time
- Identifies configuration drifts
- Highlights risky changes
- Shows change-to-incident timeline

### Timeline Visualization
The timeline shows:
- 🔧 **Changes** (15 min before incident)
- ⚠️ **Warning signs** (5 min before)
- 🚨 **Incident start**
- 📈 **Impact escalation**
- ✅ **Resolution**

### How Correlation Works

#### Time-Based Matching
- Looks for changes 0-60 min before incident
- Weighs proximity (closer = more likely)
- Considers change completion time

#### Pattern Recognition
- Similar changes causing similar incidents
- Repeated failure patterns
- Service dependency impacts

#### Risk Scoring
- **High Risk**: Database/Security changes
- **Medium Risk**: Application updates
- **Low Risk**: Monitoring changes

### Best Practices

#### Before Making Changes
1. Check recent incident history
2. Review similar past changes
3. Assess blast radius
4. Plan rollback strategy

#### During Changes
1. Monitor key metrics
2. Watch for early warnings
3. Be ready to rollback
4. Document everything

#### After Changes
1. Verify system stability
2. Update change records
3. Monitor for delayed impact
4. Share lessons learned

### Using for Root Cause Analysis
1. **Check timeline**: Did a change precede the incident?
2. **Review details**: What exactly was changed?
3. **Assess impact**: Could this change cause the symptoms?
4. **Verify correlation**: Check logs during change window

### Change Management Integration
The system integrates with:
- AWS Systems Manager Change Manager
- Service deployment pipelines
- Infrastructure as Code tools
- Configuration management systems
"""
    },
    
    "tips_tricks": {
        "title": "💡 Tips & Tricks",
        "content": """
## Power User Tips

### Keyboard Shortcuts
- **Ctrl/Cmd + K**: Quick search
- **Ctrl/Cmd + Enter**: Analyze incident
- **Esc**: Close modals

### Search Operators
- **Quotes**: "exact phrase match"
- **OR**: error OR failure
- **Service prefix**: ec2:timeout
- **Severity**: severity:high

### Time Savers

#### 1. Incident Templates
Save common incident patterns:
```python
# Performance template
"High CPU on production ECS cluster"

# Security template  
"Unusual API calls from unknown IP"

# Outage template
"Complete service unavailability"
```

#### 2. Quick Filters
Bookmark these searches:
- `category:performance AND severity:high`
- `resolved:false AND age:<1h`
- `service:rds AND error:timeout`

#### 3. Bulk Operations
- Select multiple incidents with checkboxes
- Apply actions: Analyze, Export, Assign

### Advanced Features

#### Custom Metrics
Add your own metrics to analysis:
1. CloudWatch custom metrics
2. Application performance metrics
3. Business KPIs

#### Automation Hooks
Integrate with your tools:
- Send to Slack/Teams
- Create JIRA tickets
- Trigger Lambda functions
- Update runbooks

#### Export Options
- **PDF**: For reports and reviews
- **JSON**: For further analysis
- **CSV**: For spreadsheet tools

### Troubleshooting

**If analysis is slow:**
- Check time range (smaller = faster)
- Reduce number of services queried
- Use specific filters

**If no results found:**
- Broaden search terms
- Check time range
- Verify service permissions

**If correlation missed:**
- Manually link in the UI
- Adjust correlation window
- Check timezone settings

### Best Practices

#### Daily Routine
1. Check Recent Changes (5 min)
2. Review Open Incidents (10 min)
3. Update Knowledge Base (5 min)

#### Weekly Tasks
1. Review incident trends
2. Update runbooks
3. Share learnings with team
4. Clean up test data

#### Monthly Goals
1. Reduce MTTR by 10%
2. Increase KB articles by 20%
3. Automate 1 manual process
4. Conduct incident review

### Pro Configuration

#### Environment Variables
```bash
# Increase analysis depth
ANALYSIS_DEPTH=deep

# Add more services
ENABLED_SERVICES=all

# Custom thresholds
CORRELATION_WINDOW=120
```

#### Performance Tuning
- Cache frequent searches
- Pre-aggregate metrics
- Archive old incidents
- Optimize queries

### Getting Help
- 📧 Hover over any element for tooltips
- 📚 Check the guide section
- 🔍 Search knowledge base
- 💬 Contact support team
"""
    }
}

def get_all_guides():
    """Get all user guides"""
    return USER_GUIDES

def get_guide(guide_id):
    """Get a specific guide by ID"""
    return USER_GUIDES.get(guide_id, {
        "title": "Guide Not Found",
        "content": "The requested guide was not found."
    })

def get_guide_titles():
    """Get list of guide titles for navigation"""
    return [(guide_id, guide["title"]) for guide_id, guide in USER_GUIDES.items()]