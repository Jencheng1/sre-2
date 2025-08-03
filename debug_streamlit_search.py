#!/usr/bin/env python3
"""Debug Streamlit search flow."""

import json
import boto3
from datetime import datetime

def simulate_streamlit_search():
    """Simulate exactly what Streamlit does."""
    print("🔍 Simulating Streamlit search flow...")
    
    # Step 1: Prepare action (like Streamlit does)
    search_type = "Similar Incidents"
    query = "performance issue"
    category = "All"
    max_results = 5
    
    print(f"🔍 Input: search_type={search_type}, query={query}")
    
    if search_type == "Similar Incidents":
        action = "search_incidents"
        params = {
            'query': query,
            'k': max_results
        }
        if category != "All":
            params['category'] = category
    
    print(f"🔍 Lambda action: {action}")
    print(f"🔍 Lambda params: {params}")
    
    # Step 2: Call Lambda (like Streamlit does)
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        payload = {
            'action': action,
            **params
        }
        print(f"🔍 Full payload: {payload}")
        
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"🔍 Lambda response status: {result.get('statusCode')}")
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            results = body.get('results', [])
            print(f"🔍 Lambda body has {len(results)} results")
            
            # Check for any invalid scores
            for i, r in enumerate(results):
                score = r.get('score', 0)
                title = r.get('title', 'No title')
                print(f"   {i+1}. {title} - Score: {score}")
                
                # Check for problematic values
                if str(score) == 'nan':
                    print(f"      ⚠️  NaN score detected!")
                elif str(score) in ['inf', '-inf']:
                    print(f"      ⚠️  Infinite score detected!")
                elif not isinstance(score, (int, float)):
                    print(f"      ⚠️  Non-numeric score: {type(score)}")
            
            # Step 3: Store in session state (like Streamlit does)
            session_state_data = {
                'type': action,
                'body': body,
                'timestamp': datetime.now()
            }
            
            print(f"🔍 Session state data created with {len(session_state_data)} keys")
            print(f"🔍 Session state type: {session_state_data['type']}")
            print(f"🔍 Session state body keys: {list(session_state_data['body'].keys())}")
            
            return True, session_state_data
        else:
            print(f"❌ Lambda failed: {result}")
            return False, None
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_display_logic(session_data):
    """Test the display logic."""
    print(f"\n🖥️  Testing display logic...")
    
    if not session_data:
        print("❌ No session data to display")
        return False
    
    print(f"✅ Session data exists")
    
    action = session_data['type']
    body = session_data['body']
    
    print(f"✅ Action: {action}")
    print(f"✅ Body keys: {list(body.keys())}")
    
    if action == "get_resolution" and body.get('guide'):
        print("📋 Would display resolution guide")
    else:
        results = body.get('results', [])
        print(f"📊 Would display {len(results)} search results")
        
        if results:
            # Test grouping
            incidents = [r for r in results if r.get('metadata', {}).get('type') == 'incident']
            best_practices = [r for r in results if r.get('metadata', {}).get('type') == 'best_practice']
            resolutions = [r for r in results if r.get('metadata', {}).get('type') == 'resolution_guide']
            
            print(f"   🚨 Incidents: {len(incidents)}")
            print(f"   📚 Best practices: {len(best_practices)}")
            print(f"   🔧 Resolutions: {len(resolutions)}")
            
            # Test score handling for first few results
            for i, doc in enumerate(results[:3]):
                score = doc.get('score', 0)
                title = doc.get('title', 'No title')
                
                # Test safe score handling
                if not isinstance(score, (int, float)) or str(score) == 'nan' or str(score) in ['inf', '-inf']:
                    score_str = "N/A"
                    print(f"   ⚠️  {i+1}. {title} - Invalid score converted to: {score_str}")
                else:
                    score_str = f"{float(score):.2f}"
                    print(f"   ✅ {i+1}. {title} - Valid score: {score_str}")
        else:
            print("   ❌ No results to display")
    
    return True

def main():
    """Main test function."""
    print("="*60)
    print("STREAMLIT SEARCH FLOW DEBUG")
    print("="*60)
    
    # Test the search flow
    success, session_data = simulate_streamlit_search()
    
    if success:
        print(f"\n✅ Search flow successful")
        
        # Test display logic
        display_success = test_display_logic(session_data)
        
        if display_success:
            print(f"\n✅ Display logic successful")
            print(f"\n🎉 All tests passed - the issue might be in Streamlit's UI flow")
        else:
            print(f"\n❌ Display logic failed")
    else:
        print(f"\n❌ Search flow failed")
    
    print(f"\n" + "="*60)

if __name__ == "__main__":
    main()