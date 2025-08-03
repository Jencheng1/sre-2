# Complete Demo Flow: Change → Incident → KB → Resolution

## Overview
This demo shows the complete lifecycle of how a change leads to an incident, gets automatically indexed to the Knowledge Base, and provides correlation and timeline visualization.

## Demo Steps

### Step 1: Create a Change that Causes an Incident
Run the change-to-incident demo script:
```bash
python3 change_incident_demo.py
```

This will:
- Create a change request (e.g., CHG-30032)
- Show a realistic timeline of how the change leads to an incident
- Create a correlated incident with full context
- Automatically index to the Knowledge Base

### Step 2: View in Streamlit - Incident Analysis

1. **Go to Streamlit** (http://your-instance:8501)
2. **Incident Management Tab** → **Analyze Incident**
3. **Enter the OpsItem ID** from the demo (e.g., oi-d7fe305645ea)
4. **Click "🔍 Analyze Root Cause"**

You'll see:
- **Timeline Visualization**: Shows the change 15 minutes before the incident
- **Correlation Info**: Change ID, time to incident, pattern
- **Root Cause Analysis**: AI identifies the configuration mismatch
- **Full Context**: Change details, deployment info, error patterns

### Step 3: Search Knowledge Base

1. **Go to Knowledge Base Tab** → **Search**
2. **Search Type**: "Similar Incidents"
3. **Query**: "database connection configuration change"
4. **Click "🔍 Search"**

Results show:
- Your new incident with change correlation
- Similar past incidents
- Pattern recognition

### Step 4: Browse by Category

1. **Go to Knowledge Base Tab** → **Browse**
2. **Category**: "performance" (or "All")
3. **Document Type**: "incident"
4. **Click "📖 Browse"**

You'll see:
- All performance incidents including the new one
- Change correlations highlighted
- Root causes and resolutions

### Step 5: Test Knowledge-Enhanced Analysis

1. **Go to Knowledge Base Tab** → **Test Analysis**
2. **Enter**: "Database connection pool errors after deployment"
3. **Type**: "performance"
4. **Click "🔬 Analyze"**

The analysis will:
- Find your incident as a similar case
- Suggest checking for configuration mismatches
- Recommend best practices
- Provide resolution steps

## What Makes This Demo Powerful

### 1. **Change Tracking**
- Every change is tracked with an ID
- Changes are linked to incidents they cause
- Full audit trail maintained

### 2. **Timeline Correlation**
- Visual timeline shows change → incident progression
- Clear 15-minute gap demonstrates causation
- Each event type has distinct visualization

### 3. **Automatic Learning**
- Incidents are auto-indexed to KB
- Future similar issues benefit from this knowledge
- Patterns emerge over time

### 4. **Root Cause Clarity**
- Configuration mismatch clearly identified
- Change ID directly linked to incident
- Evidence-based correlation

## Key Insights Demonstrated

1. **Prevention**: Similar changes can be flagged as risky
2. **Faster Resolution**: Past incidents guide current solutions
3. **Pattern Recognition**: Repeated issues become obvious
4. **Change Impact**: Clear visualization of change consequences

## Try These Scenarios

### Scenario 1: Security Change Leading to Outage
```python
# Modify security group → Blocks legitimate traffic → Service outage
```

### Scenario 2: Performance Tuning Gone Wrong
```python
# Increase cache size → Memory exhaustion → Application crashes
```

### Scenario 3: Network Configuration Error
```python
# Update routing → Connectivity loss → Multi-service impact
```

## Benefits for SRE Teams

1. **Reduced MTTR**: Historical context speeds resolution
2. **Change Risk Assessment**: Learn from past change impacts
3. **Knowledge Retention**: No incident resolution is lost
4. **Proactive Prevention**: Identify risky change patterns
5. **Clear Communication**: Visual timelines for stakeholders

## Next Steps

1. Create multiple change-induced incidents
2. Build a library of change patterns
3. Use KB to prevent similar issues
4. Track improvement in MTTR
5. Share learnings across teams