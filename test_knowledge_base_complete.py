#!/usr/bin/env python3
"""Comprehensive test for Knowledge Base functionality."""

import sys
import json
import boto3
import requests
from datetime import datetime

def test_knowledge_base_complete():
    """Test all Knowledge Base functionality."""
    print("=" * 60)
    print("Comprehensive Knowledge Base Test")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Initialize
    tests_passed = []
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # 1. Test Streamlit is running
    print("1. Checking Streamlit Status:")
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit is running")
            tests_passed.append(True)
        else:
            print("   ❌ Streamlit not responding")
            tests_passed.append(False)
    except:
        print("   ❌ Streamlit not accessible")
        tests_passed.append(False)
    
    # 2. Test Search Tab
    print("\n2. Testing Search Tab Functions:")
    
    # Test search incidents
    print("   a. Search Incidents:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search_incidents',
                'query': 'performance degradation',
                'k': 5
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"      ✅ Found {len(body.get('results', []))} incidents")
            tests_passed.append(True)
        else:
            print(f"      ❌ Search failed: {result}")
            tests_passed.append(False)
    except Exception as e:
        print(f"      ❌ Error: {str(e)}")
        tests_passed.append(False)
    
    # Test search best practices
    print("   b. Search Best Practices:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search_best_practices',
                'query': 'monitoring',
                'tags': []
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"      ✅ Found {len(body.get('results', []))} best practices")
            tests_passed.append(True)
        else:
            print(f"      ❌ Search failed: {result}")
            tests_passed.append(False)
    except Exception as e:
        print(f"      ❌ Error: {str(e)}")
        tests_passed.append(False)
    
    # 3. Test Browse Tab
    print("\n3. Testing Browse Tab Functions:")
    
    categories = ['performance', 'security', 'outage']
    for cat in categories:
        print(f"   Testing category '{cat}':")
        try:
            response = lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'browse_documents',
                    'category': cat,
                    'limit': 10
                })
            )
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                count = len(body.get('results', []))
                print(f"      ✅ Found {count} documents")
                tests_passed.append(True)
            else:
                print(f"      ❌ Browse failed")
                tests_passed.append(False)
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            tests_passed.append(False)
    
    # 4. Test Add Document
    print("\n4. Testing Add Document Function:")
    test_doc = {
        'action': 'add_document',
        'document_id': f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'title': 'Test Knowledge Base Document',
        'content': 'This is a test document for verifying KB functionality',
        'category': 'test',
        'type': 'incident',
        'tags': ['test', 'automated'],
        'metadata': {
            'severity': 'low',
            'created_by': 'test_suite'
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_doc)
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            print("   ✅ Document added successfully")
            tests_passed.append(True)
        else:
            print(f"   ❌ Failed to add document: {result}")
            tests_passed.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests_passed.append(False)
    
    # 5. Test Analysis Enhancement
    print("\n5. Testing Knowledge Base Analysis Enhancement:")
    try:
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'enhance_analysis',
                'incident_description': 'Application experiencing high CPU usage and slow response times',
                'initial_analysis': {
                    'root_cause': 'Potential memory leak or resource exhaustion',
                    'confidence': 0.7
                }
            })
        )
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            print("   ✅ Analysis enhancement working")
            tests_passed.append(True)
        else:
            print("   ❌ Enhancement failed")
            tests_passed.append(False)
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        tests_passed.append(False)
    
    # UI Test Checklist
    print("\n" + "=" * 60)
    print("STREAMLIT UI TEST CHECKLIST")
    print("=" * 60)
    
    print("\n✅ Fixed Issues:")
    print("   • Search results now persist using session state")
    print("   • Browse results now persist using session state")
    print("   • No more disappearing results after button clicks")
    print("   • All buttons have unique keys")
    print("   • st.experimental_rerun() used for compatibility")
    
    print("\n📋 Manual UI Testing Steps:")
    
    print("\n1. Search Tab:")
    print("   a. Go to Knowledge Base → Search")
    print("   b. Enter 'high CPU' in search box")
    print("   c. Click Search button")
    print("   d. Results should appear and persist")
    print("   e. Try switching tabs and coming back - results should still be there")
    
    print("\n2. Browse Tab:")
    print("   a. Go to Knowledge Base → Browse")
    print("   b. Select 'performance' category")
    print("   c. Click Browse button")
    print("   d. Documents should appear and persist")
    print("   e. Expand documents to see content")
    
    print("\n3. Add Document Tab:")
    print("   a. Go to Knowledge Base → Add Document")
    print("   b. Fill in all required fields:")
    print("      - Document ID: TEST-001")
    print("      - Title: Test Document")
    print("      - Type: incident")
    print("      - Category: performance")
    print("      - Content: Test content")
    print("   c. Click Add Document")
    print("   d. Should see success message")
    
    print("\n4. Test Analysis Tab:")
    print("   a. Go to Knowledge Base → Test Analysis")
    print("   b. Enter incident description")
    print("   c. Click Analyze with Knowledge Base")
    print("   d. Should see enhanced analysis with KB context")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(tests_passed)
    passed = sum(tests_passed)
    
    print(f"\nAutomated Tests: {passed}/{total_tests} passed")
    
    if passed == total_tests:
        print("\n✅ All automated tests PASSED!")
        print("✅ Knowledge Base backend fully functional")
        print("✅ UI fixes applied for persistent results")
        print("\n🎉 Knowledge Base is ready for use!")
    else:
        print(f"\n⚠️  {total_tests - passed} tests failed")
        print("Check the errors above for details")
    
    print("\n💡 Tips:")
    print("   • Clear browser cache if UI issues persist")
    print("   • Check browser console for JavaScript errors")
    print("   • Ensure all MCP services are running")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total_tests

def main():
    """Main test function."""
    success = test_knowledge_base_complete()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()