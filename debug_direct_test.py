#!/usr/bin/env python3
"""Direct test of search functionality."""

import sys
import json
import boto3

# Simulate what streamlit does
class SessionState:
    def __init__(self):
        self.kb_search_results = None

# Mock session state
st_session_state = SessionState()

def search_knowledge_base(search_type, query, category, max_results):
    """Mock the search function from streamlit app."""
    print(f"🔍 Searching for: '{query}' (type: {search_type})")
    
    # Map search type to action
    action_mapping = {
        "Similar Incidents": "search_incidents",
        "Best Practices": "search_best_practices", 
        "Resolution Guides": "get_resolution"
    }
    
    action = action_mapping.get(search_type, "search_incidents")
    print(f"Lambda action: {action}")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Build payload
        payload = {'action': action}
        
        if action == "get_resolution":
            payload['incident_category'] = category or 'performance'
        else:
            payload['query'] = query
            payload['k'] = max_results
        
        print(f"Payload: {payload}")
        
        # Call Lambda
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Lambda status: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            
            # Store in session state (like Streamlit does)
            st_session_state.kb_search_results = {
                'type': action,
                'body': body,
                'search_type': search_type,
                'query': query,
                'category': category
            }
            
            print(f"✅ Success! Results count: {len(body.get('results', []))}")
            return True
        else:
            print(f"❌ Failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def display_search_results(results_data):
    """Mock the display function."""
    print("\n" + "="*50)
    print("DISPLAY_SEARCH_RESULTS CALLED")
    print("="*50)
    
    if not results_data:
        print("❌ results_data is empty/None")
        return
    
    print(f"✅ results_data exists")
    print(f"Type: {results_data.get('type')}")
    
    action = results_data['type']
    body = results_data['body']
    
    if action == "get_resolution" and body.get('guide'):
        print("📋 Single resolution guide")
        guide = body['guide']
        print(f"Title: {guide['title']}")
    else:
        results = body.get('results', [])
        print(f"📊 Search results: {len(results)} items")
        
        # Group by type
        incidents = [r for r in results if r['metadata'].get('type') == 'incident']
        best_practices = [r for r in results if r['metadata'].get('type') == 'best_practice']
        resolutions = [r for r in results if r['metadata'].get('type') == 'resolution_guide']
        
        print(f"🚨 Incidents: {len(incidents)}")
        print(f"📚 Best Practices: {len(best_practices)}")
        print(f"📋 Resolutions: {len(resolutions)}")
        
        if incidents:
            print("\nFirst incident:")
            print(f"  - {incidents[0]['title']}")
            print(f"  - Score: {incidents[0].get('score', 0):.3f}")

def main():
    print("DIRECT SEARCH TEST")
    print("="*50)
    
    # Test 1: Search for incidents
    success1 = search_knowledge_base(
        search_type="Similar Incidents",
        query="database performance issue",
        category="performance", 
        max_results=5
    )
    
    if success1 and st_session_state.kb_search_results:
        display_search_results(st_session_state.kb_search_results)
    
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    if success1:
        print("✅ Direct search works")
        print("✅ Display function called")
        print("✅ Session state populated")
        print("\n🔧 If Streamlit UI shows nothing:")
        print("   1. Check if display function is called in UI")
        print("   2. Check if session state is preserved")
        print("   3. Check browser console for errors")
    else:
        print("❌ Direct search failed")

if __name__ == "__main__":
    main()