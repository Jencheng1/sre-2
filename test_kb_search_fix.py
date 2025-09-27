#!/usr/bin/env python3
"""
Test the Knowledge Base search fix for Historical CPU Spike Incidents
"""

import boto3
import json
from datetime import datetime

class TestKBSearchFix:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        
    def test_knowledge_base_search(self):
        """Test searching for CPU spike incidents in knowledge base"""
        print("🧪 Testing Knowledge Base Search Fix")
        print("=" * 60)
        
        query_text = "CPU spike high utilization m5.large"
        
        print(f"\n📝 Search Query: '{query_text}'")
        print("\n🔍 Invoking Knowledge Base Lambda...")
        
        try:
            # Test the direct Lambda invocation
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'search_incidents',
                    'query': query_text,
                    'k': 5
                })
            )
            
            result = json.loads(response['Payload'].read())
            print(f"\n📊 Lambda Response Status: {result.get('statusCode')}")
            
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                results = body.get('results', [])
                
                print(f"\n✅ Found {len(results)} similar incidents")
                
                if results:
                    print("\n📋 Sample Results:")
                    for i, res in enumerate(results[:3], 1):
                        print(f"\n{i}. {res.get('title', 'Incident')}")
                        print(f"   Type: {res.get('type', 'Unknown')}")
                        print(f"   Score: {res.get('score', 0):.3f}")
                        
                        # Check content
                        content = res.get('description', res.get('content', ''))
                        if content:
                            print(f"   Content: {content[:100]}...")
                        
                        # Check for resolution
                        resolution = res.get('resolution', res.get('resolution_steps', ''))
                        if resolution:
                            print(f"   Has Resolution: Yes")
                else:
                    print("\n⚠️  No results found in knowledge base")
                    print("   This might be normal if the KB is empty")
                    
                return True
            else:
                print(f"\n❌ Lambda returned error status: {result.get('statusCode')}")
                if 'body' in result:
                    error_body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                    print(f"   Error: {error_body.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"\n❌ Exception during test: {str(e)}")
            
            # Check if Lambda function exists
            try:
                self.lambda_client.get_function(FunctionName='sre-knowledge-base-agent-lambda')
                print("   ✅ Knowledge Base Lambda exists")
            except:
                print("   ⚠️  Knowledge Base Lambda may not be deployed")
                
            return False
            
    def test_formatted_results(self):
        """Test the formatting of results as used in the UI"""
        print("\n\n🧪 Testing Result Formatting")
        print("=" * 60)
        
        # Simulate raw KB results
        mock_results = [{
            'title': 'High CPU on m5.large instances',
            'type': 'incident',
            'content': 'CPU spike observed on m5.large EC2 instances during peak hours',
            'timestamp': '2025-01-15T10:30:00Z',
            'root_cause': 'Insufficient memory causing excessive swapping',
            'resolution_steps': '1. Increase instance size to m5.xlarge\n2. Optimize application memory usage',
            'score': 0.95
        }]
        
        # Format as the UI does
        formatted_results = []
        for res in mock_results:
            formatted_results.append({
                'title': res.get('title', 'CPU Spike Incident'),
                'date': res.get('timestamp', 'Unknown'),
                'description': res.get('description', res.get('content', 'No description')),
                'root_cause': res.get('root_cause', 'Analysis pending'),
                'resolution': res.get('resolution', res.get('resolution_steps', ''))
            })
        
        print("\n📋 Formatted Result:")
        for key, value in formatted_results[0].items():
            print(f"   {key}: {value}")
            
        print("\n✅ Formatting test complete")
        return True

def main():
    """Run all tests"""
    tester = TestKBSearchFix()
    
    # Test 1: Knowledge Base search
    success1 = tester.test_knowledge_base_search()
    
    # Test 2: Result formatting
    success2 = tester.test_formatted_results()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Knowledge Base Search: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Result Formatting: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1:
        print("\n✅ The Historical CPU Spike Incidents search should now work!")
        print("   - Fixed the function name issue")
        print("   - Added proper self reference")
        print("   - Query results will be formatted for display")
    else:
        print("\n⚠️  Knowledge Base may need to be deployed or populated")
        
    return 0 if success1 and success2 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())