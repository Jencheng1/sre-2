# Streamlit Tab Verification Guide

## Current Status
- **Streamlit Running:** Yes (PID: 15255)
- **File:** streamlit_app.py
- **URL:** http://localhost:8501

## Expected Tabs (in order):
1. 🚨 **Incident Management** ✓
   - Generate Real Incident button
   - Incident type selection
   - AWS resource integration

2. 🔍 **Analyze Incident** ✓
   - Analyze existing incidents
   - OpsItem selection
   - Root cause analysis

3. 🔧 **Recent Changes** ✓
   - Change tracking
   - Change-incident correlation

4. 📚 **Knowledge Base** ✓
   - Search, Browse, Add Document
   - Test Analysis

5. 📊 **Analytics** ✓
   - Incident trends
   - Service metrics

6. 🐛 **Defect Management** ✓
   - ALM Octane integration
   - Jira integration

7. 🔗 **Defect Correlation** ✓
   - AI-powered correlation
   - Confidence scoring

8. 🧪 **Correlation Scenarios** ✓
   - Test scenarios
   - Correlation validation

9. 📋 **Post-Mortem** ✓
   - Generate Report
   - View Reports
   - Analyze OpsItem

10. 🔐 **IP Masking** ✓ (NEW)
    - Mask Logs
    - Configuration
    - Statistics

11. 🧪 **Test Scenarios** ✓ (NEW)
    - Predefined Scenarios
    - Custom Scenario
    - Batch Testing

12. ❓ **User Guide** ✓
    - Help documentation

## Incident Generation Features:
- **Location:** Incident Management tab (Tab 1)
- **Button:** "🔥 Generate Real Incident"
- **Options:** Multiple incident types in sidebar

## Root Cause Analysis Features:
- **Location:** Analyze Incident tab (Tab 2)
- **Process:** 
  1. Generate incident in Tab 1
  2. Switch to Tab 2
  3. Select the incident
  4. Click analyze

## Troubleshooting:
If tabs are not visible:
1. Clear browser cache
2. Refresh page (Ctrl+F5)
3. Check browser console for errors
4. Verify URL: http://localhost:8501

## Quick Test:
1. Go to Tab 11 (Test Scenarios)
2. Select "Predefined Scenarios"
3. Choose any scenario
4. Click "Generate Incident"
5. Then click "Analyze Now" to test root cause analysis