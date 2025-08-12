#!/usr/bin/env python3
"""
Quick test to show how to access incident generation in Streamlit
"""

print("""
🚀 HOW TO TEST INCIDENT SCENARIOS IN STREAMLIT
=============================================

The Streamlit UI structure has changed. Here's the correct way to test:

1. Access Streamlit at: http://localhost:8501

2. The tabs are:
   - 🚨 Incident Management (first tab - this is where you generate incidents)
   - 🔍 Analyze Incident
   - 🔧 Recent Changes
   - 📚 Knowledge Base
   - 📊 Analytics

3. To generate test incidents:
   a) Click on "🚨 Incident Management" tab
   b) Look for "🚀 Generate Incident" section
   c) Select incident type from dropdown
   d) Click "🔥 Generate Real Incident" button

4. Available incident types in the UI:
   - Performance Issues (Database, High CPU, etc.)
   - Security Incidents (Unauthorized access, etc.)
   - Outage Scenarios
   - Data Issues

5. To test our specific scenarios:
   - EC2 Quota: Look for "Performance" category → "High CPU/Memory"
   - Security Group: Look for "Security" category → incidents
   - API Throttling: Look for "Performance" category → incidents

6. After generating an incident:
   - It will appear in "Recent Incidents" section
   - Select it and click "Analyze" to see root cause
   - Check the "🔍 Analyze Incident" tab for detailed analysis

Note: The exact incident types depend on what's configured in the 
incident_scenarios.py file. The UI dynamically loads available scenarios.
""")