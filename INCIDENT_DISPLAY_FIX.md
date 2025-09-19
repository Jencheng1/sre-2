# Incident Root Cause Display Fix

**Date**: August 19, 2025  
**Issue**: Root cause analysis stuck at "Analyzing..." in Streamlit UI

## Problem Summary
The incident root cause analysis was getting stuck at "Analyzing..." without showing the actual results, even though the Lambda function was returning proper AI-generated analysis.

## Root Cause
The supervisor Lambda returns a field called `root_cause_analysis`, but the Streamlit app's `parse_supervisor_response` method was looking for a field called `analysis`.

## Fix Applied

### 1. Updated `streamlit_app.py`
Modified the `parse_supervisor_response` method to:
- Check for `root_cause_analysis` field (new) in addition to `analysis` field (old)
- Handle both string format (AI analysis) and dict format (fallback analysis)
- Extract the actual root cause text using regex patterns
- Provide meaningful fallbacks

### 2. Updated `streamlit_app_problem_management.py`
Applied the same fix to ensure consistency across all Streamlit apps.

## Code Changes

```python
# Before (incorrect field name)
if 'analysis' in result:
    root_cause = result['analysis']

# After (correct field name with fallback)
root_cause_analysis = result.get('root_cause_analysis', result.get('analysis', ''))
```

## Verification

1. **Automated Test**: Run `python3 test_incident_display_fix.py`
2. **Manual Test**:
   - Go to Streamlit UI (http://localhost:8501)
   - Create or find an incident
   - Click "Analyze"
   - Verify root cause is displayed (not "Analyzing...")

## Technical Details

The fix handles multiple AI response formats:
- Numbered lists: `1. **Root Cause Analysis**: ...`
- Markdown headers: `### Identified Root Cause`
- Plain text with keywords: `The root cause is...`

## Files Modified
- `/home/ec2-user/sre/sre_mcp/streamlit_app.py`
- `/home/ec2-user/sre/sre_mcp/streamlit_app_problem_management.py`

## Test Files Created
- `/home/ec2-user/sre/sre_mcp/test_streamlit_parsing.py`
- `/home/ec2-user/sre/sre_mcp/test_incident_display_fix.py`