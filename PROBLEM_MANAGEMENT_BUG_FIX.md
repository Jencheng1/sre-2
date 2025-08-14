# Problem Management Bug Fix - August 14, 2025

## Issue Description
The Problem Management and Synthetic Transactions tabs were showing "No recent incidents available" even after incidents were generated. This was due to a mismatch in how incidents were stored and accessed.

## Root Cause
1. The main Streamlit app stores incidents in `st.session_state.generated_incidents`
2. The problem management module was looking for `st.session_state.incident_history` (which doesn't exist)
3. The incident data structure was inconsistent:
   - Main app uses `ops_item_id` as the incident identifier
   - Problem management expected `id` field
   - Main app uses `description` field
   - Problem management expected `title` field

## Solution Implemented

### 1. Fixed Session State Access
Changed all occurrences of:
```python
if hasattr(st.session_state, 'incident_history'):
    recent_incidents = st.session_state.incident_history
```

To:
```python
if hasattr(st.session_state, 'generated_incidents'):
    recent_incidents = st.session_state.generated_incidents
```

### 2. Added Incident Normalization
Created a `_normalize_incident()` method that handles the data structure differences:

```python
def _normalize_incident(self, incident):
    """Normalize incident data structure"""
    return {
        'id': incident.get('ops_item_id', incident.get('id', 'Unknown')),
        'title': incident.get('title', incident.get('description', 'No title')[:100]),
        'description': incident.get('description', ''),
        'service': incident.get('service', 'Unknown'),
        'impact': incident.get('severity', 'Unknown'),
        'type': incident.get('type', 'unknown')
    }
```

### 3. Applied Normalization
Updated all three methods that access incidents:
- `_render_create_problem()`
- `_render_correlate_problem()`
- `render_synthetic_transactions()`

Each now normalizes incidents before use:
```python
recent_incidents = [self._normalize_incident(inc) for inc in st.session_state.generated_incidents]
```

## Verification
Created comprehensive tests that verify:
1. Incident normalization handles all data formats correctly
2. Long descriptions are truncated to 100 characters for titles
3. Missing fields get appropriate defaults
4. Both `ops_item_id` and `id` fields are handled

## Result
The Problem Management and Synthetic Transactions features now correctly:
- Display all generated incidents in dropdowns
- Handle different incident data formats
- Show meaningful titles even when only descriptions are available
- Work seamlessly with incidents generated from the main Incident Management tab

## Files Modified
- `streamlit_app_problem_management.py` - Added normalization and fixed session state access

## Files Created
- `test_incident_fix.py` - Comprehensive test suite for the fix
- `PROBLEM_MANAGEMENT_BUG_FIX.md` - This documentation