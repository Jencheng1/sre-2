#!/usr/bin/env python3
"""Test Knowledge Base UI functionality."""

import sys
import json
import boto3
import requests
from datetime import datetime

def test_kb_lambda():
    """Test Knowledge Base Lambda directly."""
    print("=" * 60)
    print("Knowledge Base UI Test")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check Streamlit
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit is running")
        else:
            print("❌ Streamlit not responding")
            return False
    except:
        print("❌ Streamlit not accessible")
        return False
    
    # Test Lambda functions
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    tests = []
    
    # Test 1: Search incidents
    print("\n1. Testing Search Incidents:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search_incidents',
                'query': 'performance issue',
                'k': 3
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"   ✅ Found {len(body.get('results', []))} results")
            tests.append(True)
        else:
            print(f"   ❌ Search failed: {result}")
            tests.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests.append(False)
    
    # Test 2: Browse documents
    print("\n2. Testing Browse Documents:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'browse_documents',
                'category': 'performance',
                'limit': 5
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"   ✅ Found {len(body.get('results', []))} documents")
            tests.append(True)
        else:
            print(f"   ❌ Browse failed: {result}")
            tests.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests.append(False)
    
    # Test 3: Get resolution guide
    print("\n3. Testing Get Resolution Guide:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'get_resolution',
                'incident_type': 'performance'
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            if body.get('guide'):
                print(f"   ✅ Got resolution guide: {body['guide']['title']}")
                tests.append(True)
            else:
                print("   ⚠️  No resolution guide found")
                tests.append(True)  # Not an error if no guide exists
        else:
            print(f"   ❌ Get resolution failed: {result}")
            tests.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests.append(False)
    
    # Test 4: Check DynamoDB table
    print("\n4. Testing DynamoDB Table:")
    try:
        dynamodb = boto3.client('dynamodb', region_name='us-east-1')
        response = dynamodb.describe_table(TableName='sre-knowledge-base-vectors')
        if response['Table']['TableStatus'] == 'ACTIVE':
            item_count = response['Table'].get('ItemCount', 0)
            print(f"   ✅ Table active with {item_count} items")
            tests.append(True)
        else:
            print(f"   ❌ Table status: {response['Table']['TableStatus']}")
            tests.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests.append(False)
    
    # Check for UI issues
    print("\n" + "=" * 60)
    print("STREAMLIT UI CHECKLIST")
    print("=" * 60)
    
    print("\n✅ Fixed Issues:")
    print("   • st.rerun() → st.experimental_rerun()")
    print("   • All buttons have unique keys")
    print("   • Search query persistence in session state")
    
    print("\n📋 Manual Testing Steps:")
    print("\n1. Knowledge Base Search:")
    print("   a. Go to Knowledge Base tab")
    print("   b. Enter 'high CPU' in search box")
    print("   c. Click Search button")
    print("   d. Should see results without errors")
    
    print("\n2. Browse by Category:")
    print("   a. Click Browse tab")
    print("   b. Select 'performance' category")
    print("   c. Click Browse button")
    print("   d. Should see documents listed")
    
    print("\n3. Add Document:")
    print("   a. Click Add Document tab")
    print("   b. Fill in all fields")
    print("   c. Click Add Document button")
    print("   d. Should see success message")
    
    print("\n4. Test Analysis:")
    print("   a. Click Test Analysis tab")
    print("   b. Enter incident description")
    print("   c. Click Analyze button")
    print("   d. Should see enhanced analysis")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(tests)
    total = len(tests)
    print(f"\nBackend Tests: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All backend tests passed!")
        print("✅ Knowledge Base Lambda is working")
        print("✅ DynamoDB table is accessible")
        print("\n⚠️  If UI still not working, check:")
        print("   1. Browser console for JavaScript errors")
        print("   2. Clear browser cache (Ctrl+Shift+R)")
        print("   3. Try incognito/private window")
        print("   4. Check if session state is initialized")
    else:
        print("\n❌ Some backend tests failed")
        print("   Check the errors above")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

def main():
    """Main test function."""
    success = test_kb_lambda()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()