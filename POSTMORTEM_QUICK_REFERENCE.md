# Post-Mortem Analysis Quick Reference

## 🚀 Quick Access
```bash
# Access Streamlit UI
http://localhost:8501
# Navigate to: 📋 Post-Mortem tab

# Run tests
python3 test_postmortem_analysis.py

# Run demo
python3 demo_postmortem.py
```

## 📍 Key Files
- **Agent**: `postmortem/postmortem_agent.py`
- **UI Integration**: `streamlit_app.py` (methods at line ~3568)
- **Tests**: `test_postmortem_analysis.py`
- **Demo**: `demo_postmortem.py`

## 🎯 Main Features

### 1. Generate Report
- Manual incident input form
- AI-powered analysis
- Real-time generation
- Export options (Markdown/JSON)

### 2. View Reports
- Interactive report viewer
- Timeline visualization
- Action item tracking
- Metrics charts

### 3. Analyze OpsItem
- Generate from resolved incidents
- Automatic data extraction
- Sample analysis available

## 💻 Quick Usage

### Generate Post-Mortem Programmatically
```python
from postmortem.postmortem_agent import PostMortemAgent
from datetime import datetime, timedelta

agent = PostMortemAgent()

incident = {
    'incident_id': 'INC-001',
    'type': 'outage',  # outage, performance, security
    'severity': 'HIGH',  # CRITICAL, HIGH, MEDIUM, LOW
    'description': 'Service outage description',
    'start_time': datetime.now() - timedelta(hours=2),
    'resolution_time': datetime.now().isoformat(),
    'service': 'api-gateway'
}

report = agent.analyze_incident(incident)
markdown = agent.generate_markdown_report(report)
print(markdown)
```

### Report Structure
```python
PostMortemReport:
    - incident_id, title, severity
    - timeline (start, end, duration)
    - impact (services, users, revenue, SLA)
    - root_cause, contributing_factors
    - what_went_well, what_went_wrong
    - lessons_learned, action_items
    - preventive_measures, monitoring_improvements
```

## 📊 Report Components

### Executive Summary
- Incident overview
- Impact assessment
- Root cause summary

### Timeline
- Event sequence
- Critical moments
- Response actions

### Analysis
- Root cause details
- Contributing factors
- What went well/wrong

### Action Items
- Prioritized tasks
- Assigned owners
- Due dates

### Prevention
- Preventive measures
- Monitoring improvements
- Process updates

## 🧪 Test Status
```
✅ 12/12 tests passing
✅ All incident types covered
✅ Export formats validated
✅ UI integration verified
```

## 🔗 Integration Points
- **OpsItems**: Auto-generate from resolved incidents
- **Knowledge Base**: Lessons learned can be indexed
- **Defect Management**: Action items → defects
- **Change Management**: Link related changes
- **IP Masking**: Logs are masked before analysis