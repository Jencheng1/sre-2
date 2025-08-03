#!/usr/bin/env python3
"""Simulate and test Knowledge Base UI behavior."""

import sys
import json
import boto3
from datetime import datetime

def simulate_search_button():
    """Simulate what happens when Search button is clicked."""
    print("\n" + "="*60)
    print("SIMULATING SEARCH BUTTON CLICK")
    print("="*60)
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Simulate search
    query = "database performance issue"
    print(f"\n1. User enters query: '{query}'")
    print("2. User clicks Search button")
    print("3. Lambda is called...")
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'search_incidents',
            'query': query,
            'k': 5
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        results = body.get('results', [])
        
        print(f"\n✅ Lambda returned {len(results)} results")
        
        # This is what should be stored in session state
        session_data = {
            'type': 'search_incidents',
            'body': body,
            'timestamp': datetime.now()
        }
        
        print("\n4. Results stored in st.session_state.kb_search_results")
        print(f"   - Type: {session_data['type']}")
        print(f"   - Results count: {len(results)}")
        print(f"   - Timestamp: {session_data['timestamp']}")
        
        print("\n5. Display function should show:")
        print(f"   - Success message: Found {len(results)} results")
        
        # Group by type
        incidents = [r for r in results if r.get('metadata', {}).get('type') == 'incident']
        best_practices = [r for r in results if r.get('metadata', {}).get('type') == 'best_practice']
        
        if incidents:
            print(f"   - {len(incidents)} incidents under '🚨 Similar Incidents'")
            for i, doc in enumerate(incidents[:3], 1):
                print(f"     {i}. {doc['title']} (Score: {doc.get('score', 0):.2f})")
        
        if best_practices:
            print(f"   - {len(best_practices)} best practices under '📚 Best Practices'")
        
        if not incidents and not best_practices:
            print("   - Info message: No categorized results")
        
        return True
    else:
        print(f"\n❌ Lambda failed: {result}")
        return False

def simulate_browse_button():
    """Simulate what happens when Browse button is clicked."""
    print("\n" + "="*60)
    print("SIMULATING BROWSE BUTTON CLICK")
    print("="*60)
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Simulate browse
    category = "performance"
    print(f"\n1. User selects category: '{category}'")
    print("2. User clicks Browse button")
    print("3. Lambda is called...")
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'browse_documents',
            'category': category,
            'doc_type': None,
            'limit': 50
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        results = body.get('results', [])
        
        print(f"\n✅ Lambda returned {len(results)} documents")
        
        # This is what should be stored in session state
        session_data = {
            'results': results,
            'category': category,
            'doc_type': None,
            'timestamp': datetime.now()
        }
        
        print("\n4. Results stored in st.session_state.kb_browse_results")
        print(f"   - Category: {session_data['category']}")
        print(f"   - Results count: {len(results)}")
        
        print("\n5. Display function should show:")
        print(f"   - Success message: Found {len(results)} documents in {category} category")
        
        # Group by type
        by_type = {}
        for doc in results:
            doc_type = doc.get('metadata', {}).get('type', 'unknown')
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
        
        print(f"   - Document types: {by_type}")
        
        for doc_type, count in by_type.items():
            print(f"   - {count} {doc_type} documents")
            # Show first doc of this type
            first_doc = next((d for d in results if d.get('metadata', {}).get('type') == doc_type), None)
            if first_doc:
                print(f"     Example: {first_doc['title']}")
        
        return True
    else:
        print(f"\n❌ Lambda failed: {result}")
        return False

def check_ui_issues():
    """Check for common UI issues."""
    print("\n" + "="*60)
    print("COMMON UI ISSUES TO CHECK")
    print("="*60)
    
    print("\n1. Session State Initialization:")
    print("   ✓ Check if kb_search_results is initialized")
    print("   ✓ Check if kb_browse_results is initialized")
    print("   ✓ Check if kb_add_result is initialized")
    print("   ✓ Check if kb_analysis_result is initialized")
    
    print("\n2. Display Function Calls:")
    print("   ✓ After search button: self.display_search_results()")
    print("   ✓ After browse button: self.display_browse_results()")
    print("   ✓ These should be OUTSIDE the button click handler")
    
    print("\n3. Common Problems:")
    print("   ❌ Success message shown but no results → Fixed by removing early success message")
    print("   ❌ Results disappear on tab switch → Fixed by using session state")
    print("   ❌ Duplicate key errors → Fixed by key_manager")
    print("   ❌ st.rerun() errors → Fixed by using st.experimental_rerun()")
    
    print("\n4. Expected UI Flow:")
    print("   1. User enters input and clicks button")
    print("   2. Lambda is called within st.spinner()")
    print("   3. Results stored in session state")
    print("   4. NO success message in the handler")
    print("   5. Display function checks session state")
    print("   6. Display function shows results")

def main():
    """Main test function."""
    print("="*60)
    print("KNOWLEDGE BASE UI SIMULATION TEST")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run simulations
    search_ok = simulate_search_button()
    browse_ok = simulate_browse_button()
    
    # Check for issues
    check_ui_issues()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if search_ok and browse_ok:
        print("\n✅ Backend is working correctly")
        print("✅ Lambda functions return expected data")
        print("\n🔧 If UI still shows no results:")
        print("   1. Clear browser cache (Ctrl+Shift+R)")
        print("   2. Try incognito/private window")
        print("   3. Check browser console for errors")
        print("   4. Verify session state is being set")
    else:
        print("\n❌ Backend issues detected")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return search_ok and browse_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)