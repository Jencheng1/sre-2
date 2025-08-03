#!/usr/bin/env python3
"""Debug the display function with actual data."""

import json
import boto3

def test_display_logic():
    """Test the exact display logic with real data."""
    print("Testing display logic with real Lambda data...")
    
    # Get real data from Lambda
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'search_incidents',
            'query': 'performance issue',
            'k': 5
        })
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') != 200:
        print(f"❌ Lambda failed: {result}")
        return False
    
    body = json.loads(result['body'])
    results = body.get('results', [])
    
    print(f"✅ Got {len(results)} results from Lambda")
    
    # Simulate the session state structure
    results_data = {
        'type': 'search_incidents',
        'body': body
    }
    
    # Test the display logic step by step
    print("\n🔍 Testing display logic...")
    
    try:
        # Check if results_data exists
        if not results_data:
            print("❌ results_data is None/empty")
            return False
        print("✅ results_data exists")
        
        # Extract action and body
        action = results_data['type']
        body = results_data['body']
        print(f"✅ action = {action}")
        print(f"✅ body has {len(body)} keys")
        
        # Check resolution guide path
        if action == "get_resolution" and body.get('guide'):
            print("📋 Would display resolution guide")
            guide = body['guide']
            print(f"   Title: {guide['title']}")
        else:
            print("📊 Would display search results")
            
            # Extract results
            results = body.get('results', [])
            print(f"   Found {len(results)} results")
            
            if not results:
                print("   ❌ No results to display")
                return False
            
            # Test grouping logic
            print("\n🔍 Testing result grouping...")
            
            incidents = []
            best_practices = []
            resolutions = []
            
            for i, r in enumerate(results):
                print(f"   Result {i}: {r.get('title', 'No title')}")
                print(f"      Has metadata: {'metadata' in r}")
                
                if 'metadata' in r:
                    metadata = r['metadata']
                    doc_type = metadata.get('type')
                    print(f"      Type: {doc_type}")
                    
                    try:
                        if doc_type == 'incident':
                            incidents.append(r)
                        elif doc_type == 'best_practice':
                            best_practices.append(r)
                        elif doc_type == 'resolution_guide':
                            resolutions.append(r)
                        print(f"      ✅ Grouped as {doc_type}")
                    except Exception as e:
                        print(f"      ❌ Error grouping: {e}")
                else:
                    print("      ❌ No metadata field")
            
            print(f"\n📊 Grouping results:")
            print(f"   🚨 Incidents: {len(incidents)}")
            print(f"   📚 Best practices: {len(best_practices)}")
            print(f"   🔧 Resolution guides: {len(resolutions)}")
            
            # Test display sections
            print(f"\n🖥️  Testing display sections...")
            
            if incidents:
                print(f"   ✅ Would show 'Similar Incidents' section with {len(incidents)} items")
                for idx, doc in enumerate(incidents[:2], 1):
                    try:
                        title = doc['title']
                        score = doc.get('score', 0)
                        category = doc['metadata'].get('category', 'N/A')
                        content = doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content']
                        print(f"      {idx}. {title} (Score: {score:.2f})")
                        print(f"         Category: {category}")
                        print(f"         Content: {content}")
                    except Exception as e:
                        print(f"      ❌ Error displaying incident {idx}: {e}")
            else:
                print(f"   ⚠️  No incidents to display")
            
            if best_practices:
                print(f"   ✅ Would show 'Best Practices' section with {len(best_practices)} items")
                for idx, doc in enumerate(best_practices[:2], 1):
                    try:
                        title = doc['title']
                        tags = doc['metadata'].get('tags', [])
                        content = doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content']
                        print(f"      {idx}. {title}")
                        print(f"         Tags: {', '.join(tags) if tags else 'None'}")
                        print(f"         Content: {content}")
                    except Exception as e:
                        print(f"      ❌ Error displaying best practice {idx}: {e}")
            else:
                print(f"   ⚠️  No best practices to display")
            
            if resolutions:
                print(f"   ✅ Would show 'Resolution Guides' section with {len(resolutions)} items")
            else:
                print(f"   ⚠️  No resolution guides to display")
    
    except Exception as e:
        print(f"❌ Error in display logic: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ Display logic test completed successfully")
    return True

if __name__ == "__main__":
    success = test_display_logic()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")