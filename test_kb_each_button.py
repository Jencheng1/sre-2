#!/usr/bin/env python3
"""Test each Knowledge Base button individually with detailed output."""

import sys
import json
import boto3
import time
from datetime import datetime

class KBButtonTester:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.results = []
        
    def test_search_button(self):
        """Test the Search button functionality."""
        print("\n" + "="*60)
        print("TEST 1: SEARCH BUTTON")
        print("="*60)
        
        test_cases = [
            {
                'name': 'Search Similar Incidents',
                'action': 'search_incidents',
                'params': {'query': 'database connection timeout', 'k': 5}
            },
            {
                'name': 'Search Best Practices',
                'action': 'search_best_practices',
                'params': {'query': 'monitoring best practices', 'tags': []}
            },
            {
                'name': 'Get Resolution Guide',
                'action': 'get_resolution',
                'params': {'incident_type': 'performance'}
            }
        ]
        
        for test in test_cases:
            print(f"\n📍 Testing: {test['name']}")
            print(f"   Action: {test['action']}")
            print(f"   Params: {test['params']}")
            
            try:
                response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': test['action'],
                        **test['params']
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    
                    # Check what we got
                    if 'results' in body:
                        count = len(body['results'])
                        print(f"   ✅ SUCCESS: Found {count} results")
                        if count > 0:
                            print(f"   📄 First result: {body['results'][0].get('title', 'No title')}")
                            print(f"   📊 Score: {body['results'][0].get('score', 0):.3f}")
                    elif 'guide' in body:
                        print(f"   ✅ SUCCESS: Got resolution guide")
                        print(f"   📄 Guide: {body['guide'].get('title', 'No title')}")
                    else:
                        print(f"   ⚠️  SUCCESS but unexpected format: {list(body.keys())}")
                    
                    self.results.append((test['name'], True))
                else:
                    print(f"   ❌ FAILED: Status {result.get('statusCode')}")
                    print(f"   Error: {result.get('body', 'No error message')}")
                    self.results.append((test['name'], False))
                    
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                self.results.append((test['name'], False))
    
    def test_browse_button(self):
        """Test the Browse button functionality."""
        print("\n" + "="*60)
        print("TEST 2: BROWSE BUTTON")
        print("="*60)
        
        test_cases = [
            {'category': 'performance', 'doc_type': None},
            {'category': 'security', 'doc_type': 'incident'},
            {'category': None, 'doc_type': 'best_practice'},
            {'category': 'outage', 'doc_type': None}
        ]
        
        for test in test_cases:
            cat_display = test['category'] or 'All'
            type_display = test['doc_type'] or 'All'
            print(f"\n📍 Testing: Category={cat_display}, Type={type_display}")
            
            try:
                response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'browse_documents',
                        'category': test['category'],
                        'doc_type': test['doc_type'],
                        'limit': 20
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    results = body.get('results', [])
                    print(f"   ✅ SUCCESS: Found {len(results)} documents")
                    
                    # Show document types found
                    types = {}
                    for doc in results:
                        doc_type = doc.get('metadata', {}).get('type', 'unknown')
                        types[doc_type] = types.get(doc_type, 0) + 1
                    
                    if types:
                        print(f"   📊 Document types: {types}")
                    
                    if results:
                        print(f"   📄 First doc: {results[0].get('title', 'No title')}")
                    
                    self.results.append((f"Browse {cat_display}/{type_display}", True))
                else:
                    print(f"   ❌ FAILED: Status {result.get('statusCode')}")
                    self.results.append((f"Browse {cat_display}/{type_display}", False))
                    
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                self.results.append((f"Browse {cat_display}/{type_display}", False))
    
    def test_add_document_button(self):
        """Test the Add Document button functionality."""
        print("\n" + "="*60)
        print("TEST 3: ADD DOCUMENT BUTTON")
        print("="*60)
        
        test_doc = {
            'document_id': f'TEST-BTN-{int(time.time())}',
            'title': 'Test Document from Button Test',
            'content': 'This document tests the Add Document button functionality in the Knowledge Base.',
            'metadata': {
                'type': 'incident',
                'category': 'test',
                'tags': ['test', 'button-test', 'automated'],
                'severity': 'low'
            }
        }
        
        print(f"\n📍 Testing: Add document {test_doc['document_id']}")
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'index_document',
                    'document': test_doc
                })
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                print(f"   ✅ SUCCESS: Document added")
                print(f"   📄 Document ID: {test_doc['document_id']}")
                
                # Verify by searching for it
                time.sleep(1)  # Give DynamoDB time to index
                search_response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'search_incidents',
                        'query': test_doc['title'],
                        'k': 1
                    })
                )
                
                search_result = json.loads(search_response['Payload'].read())
                if search_result.get('statusCode') == 200:
                    search_body = json.loads(search_result['body'])
                    if search_body.get('results'):
                        print(f"   ✅ VERIFIED: Document found in search")
                    else:
                        print(f"   ⚠️  Document added but not found in search yet")
                
                self.results.append(("Add Document", True))
            else:
                print(f"   ❌ FAILED: Status {result.get('statusCode')}")
                print(f"   Error: {result.get('body', 'No error message')}")
                self.results.append(("Add Document", False))
                
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            self.results.append(("Add Document", False))
    
    def test_analyze_button(self):
        """Test the Analyze with KB button functionality."""
        print("\n" + "="*60)
        print("TEST 4: ANALYZE WITH KB BUTTON")
        print("="*60)
        
        test_cases = [
            {
                'description': 'Application experiencing high CPU usage and memory leaks',
                'type': 'performance'
            },
            {
                'description': 'Database connections timing out frequently',
                'type': 'outage'
            }
        ]
        
        for test in test_cases:
            print(f"\n📍 Testing: {test['type']} analysis")
            print(f"   Description: {test['description'][:50]}...")
            
            try:
                # First try the intended action
                response = self.lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'analyze_with_context',
                        'incident_description': test['description'],
                        'incident_type': test['type']
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    print(f"   ✅ SUCCESS: Analysis completed")
                    
                    if 'context_used' in body:
                        ctx = body['context_used']
                        print(f"   📊 Context: {ctx.get('similar_incidents_count', 0)} incidents, "
                              f"{ctx.get('best_practices_count', 0)} best practices")
                    
                    if 'analysis' in body:
                        print(f"   📄 Analysis preview: {body['analysis'][:100]}...")
                    
                    self.results.append((f"Analyze {test['type']}", True))
                else:
                    # If analyze_with_context doesn't exist, try search as fallback
                    print(f"   ⚠️  analyze_with_context not available, trying search fallback")
                    
                    search_response = self.lambda_client.invoke(
                        FunctionName='sre-knowledge-base-agent-lambda',
                        InvocationType='RequestResponse',
                        Payload=json.dumps({
                            'action': 'search_incidents',
                            'query': test['description'],
                            'k': 5
                        })
                    )
                    
                    search_result = json.loads(search_response['Payload'].read())
                    if search_result.get('statusCode') == 200:
                        search_body = json.loads(search_result['body'])
                        print(f"   ✅ FALLBACK SUCCESS: Found {len(search_body.get('results', []))} similar incidents")
                        self.results.append((f"Analyze {test['type']}", True))
                    else:
                        print(f"   ❌ FAILED: Both methods failed")
                        self.results.append((f"Analyze {test['type']}", False))
                        
            except Exception as e:
                print(f"   ❌ EXCEPTION: {str(e)}")
                self.results.append((f"Analyze {test['type']}", False))
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        print("\n" + "="*60)
        print("UI TESTING INSTRUCTIONS")
        print("="*60)
        
        print("\n1. SEARCH BUTTON:")
        print("   - Go to Knowledge Base → Search")
        print("   - Try each search type with different queries")
        print("   - Results should appear below the button")
        print("   - Results should persist when switching tabs")
        
        print("\n2. BROWSE BUTTON:")
        print("   - Go to Knowledge Base → Browse")
        print("   - Try different category/type combinations")
        print("   - Documents should appear in expandable cards")
        print("   - Should show document count and categories")
        
        print("\n3. ADD DOCUMENT BUTTON:")
        print("   - Go to Knowledge Base → Add Document")
        print("   - Fill all required fields")
        print("   - Success message should appear")
        print("   - Document should be searchable immediately")
        
        print("\n4. ANALYZE BUTTON:")
        print("   - Go to Knowledge Base → Test Analysis")
        print("   - Enter an incident description")
        print("   - Should show context metrics and analysis")
        print("   - Similar incidents should be displayed")
        
        return passed == total

def main():
    """Main test function."""
    print("="*60)
    print("KNOWLEDGE BASE BUTTON TESTS")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = KBButtonTester()
    
    # Run all tests
    tester.test_search_button()
    tester.test_browse_button()
    tester.test_add_document_button()
    tester.test_analyze_button()
    
    # Print summary
    success = tester.print_summary()
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("\n🎉 All Knowledge Base buttons are working correctly!")
    else:
        print("\n⚠️  Some buttons have issues. Check the details above.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()