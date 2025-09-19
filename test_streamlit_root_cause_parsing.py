#!/usr/bin/env python3
"""Test script to verify root cause analysis parsing fix in Streamlit app."""

import json
import re

def test_parse_supervisor_response():
    """Test the parse_supervisor_response logic with real lambda response format."""
    
    # Simulate the response from supervisor lambda
    lambda_response = {
        'incident_type': 'performance',
        'incident_description': 'Test incident: Application experiencing high CPU utilization',
        'root_cause_analysis': """1. **Root Cause Analysis**:
Based on the provided metrics and logs, the most likely root cause of the high CPU utilization is request timeouts and database connection issues. The logs show multiple errors related to request timeouts and a database connection timeout, which could lead to increased CPU usage as the application tries to handle these failed requests and retries. The high error rate (12.8% on average) and long response times (average of 3.8 seconds) further support this hypothesis.

2. **Impact Assessment**:
The high CPU utilization is causing severe performance degradation affecting all users of the application. Response times have increased significantly, and the error rate indicates that many requests are failing, directly impacting customer experience and potentially leading to revenue loss.

3. **Immediate Mitigation Steps**:
- Restart the application servers to clear any stuck processes
- Increase the database connection pool size temporarily
- Enable request throttling to reduce load
- Scale out the application by adding more instances
- Clear any blocked database queries

4. **Long-term Recommendations**:
- Implement proper connection pooling with timeout configurations
- Add circuit breakers for external service calls
- Optimize database queries that are causing timeouts
- Implement better monitoring and alerting for CPU spikes
- Consider caching frequently accessed data""",
        'metrics_summary': {
            'CPUUtilization': {'latest_value': 85.5, 'max_value': 95.2},
            'MemoryUtilization': {'latest_value': 72.3, 'max_value': 78.9}
        },
        'log_summary': {
            'error_count': 156,
            'warning_count': 234,
            'sample_errors': ['Connection timeout', 'Request failed', 'Database error']
        }
    }
    
    # Simulate the parse_supervisor_response logic
    analysis = {
        'root_cause': 'Analyzing...',
        'contributing_factors': [],
        'affected_services': [],
        'recommendations': [],
        'timeline': [],
        'correlations': [],
        'agent_findings': {}
    }
    
    # Extract root_cause_analysis
    if 'root_cause_analysis' in lambda_response:
        root_cause_data = lambda_response['root_cause_analysis']
        
        if isinstance(root_cause_data, str):
            analysis['ai_analysis'] = root_cause_data
            
            # Extract root cause using the patterns
            root_cause_text = None
            
            # Pattern 2: Look for numbered section "1. **Root Cause Analysis**:"
            pattern2 = r'1\.\s*\*\*Root Cause Analysis\*\*:\s*\n?(.+?)(?=\n\n|\n\d+\.|\Z)'
            match2 = re.search(pattern2, root_cause_data, re.DOTALL)
            if match2:
                root_cause_text = match2.group(1).strip()
            
            # Pattern 3: Look for any "root cause" mention and get the sentence
            if not root_cause_text:
                pattern3 = r'root cause[^.]*?is\s+([^.]+\.)'
                match3 = re.search(pattern3, root_cause_data, re.IGNORECASE)
                if match3:
                    root_cause_text = match3.group(1).strip()
            
            # Clean up and extract first sentence
            if root_cause_text:
                first_sentence = root_cause_text.split('. ')[0]
                if first_sentence:
                    root_cause_text = first_sentence + '.' if not first_sentence.endswith('.') else first_sentence
                
                root_cause_text = root_cause_text.replace('**', '').replace('*', '').strip()
                
                if len(root_cause_text) > 200:
                    root_cause_text = root_cause_text[:197] + '...'
                    
                analysis['root_cause'] = root_cause_text
            else:
                analysis['root_cause'] = "Root cause identified in analysis (see full analysis below)"
    
    # Print results
    print("Test Results:")
    print("=" * 80)
    print(f"Original root_cause_analysis length: {len(lambda_response['root_cause_analysis'])}")
    print(f"\nExtracted root cause: {analysis['root_cause']}")
    print(f"\nRoot cause extraction successful: {analysis['root_cause'] != 'Analyzing...'}")
    print(f"\nAI analysis stored: {'ai_analysis' in analysis}")
    
    # Test edge cases
    print("\n\nEdge Case Tests:")
    print("=" * 80)
    
    # Test with fallback format (dict instead of string)
    fallback_response = {
        'root_cause_analysis': {
            'root_cause': 'High CPU utilization due to memory leak',
            'evidence': ['Memory usage increasing over time', 'GC pressure detected'],
            'recommendations': ['Restart application', 'Fix memory leak'],
            'impact': ['Performance degradation', 'Potential outage']
        }
    }
    
    analysis2 = {'root_cause': 'Analyzing...'}
    if isinstance(fallback_response['root_cause_analysis'], dict):
        root_cause_dict = fallback_response['root_cause_analysis']
        if 'root_cause' in root_cause_dict:
            analysis2['root_cause'] = root_cause_dict['root_cause']
    
    print(f"Fallback format test - Root cause: {analysis2['root_cause']}")
    print(f"Fallback extraction successful: {analysis2['root_cause'] != 'Analyzing...'}")

if __name__ == "__main__":
    test_parse_supervisor_response()