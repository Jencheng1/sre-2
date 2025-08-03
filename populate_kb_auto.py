#!/usr/bin/env python3
"""
Automatically populate the knowledge base with initial documents.
"""

import boto3
import json
import time
from incident_scenarios import IncidentScenarios
from knowledge_base_documents import KnowledgeBaseDocuments

def invoke_kb_lambda(action, payload):
    """Invoke the knowledge base Lambda function."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    event = {
        'action': action,
        **payload
    }
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    return json.loads(response['Payload'].read())

def main():
    print("Populating Knowledge Base...")
    print("=" * 60)
    
    # Get data sources
    scenarios = IncidentScenarios()
    kb_docs = KnowledgeBaseDocuments()
    
    # Track progress
    total_indexed = 0
    
    # Index incident scenarios
    print("\nIndexing incident scenarios...")
    for scenario in scenarios.scenarios:
        scenario_id = scenario['id']
        document = {
            'document_id': scenario_id,
            'title': scenario['title'],
            'content': f"""
{scenario['description']}

Timeline:
{json.dumps(scenario['timeline'], indent=2)}

Root Cause: {scenario['root_cause']}

Resolution: {scenario.get('resolution', 'See resolution guide')}
""",
            'metadata': {
                'type': 'incident',
                'category': scenario['category'],
                'severity': scenario['severity'],
                'tags': [scenario['category'], 'incident', scenario['severity']],
                'root_cause': scenario['root_cause']
            }
        }
        
        result = invoke_kb_lambda('index_document', {'document': document})
        if result.get('statusCode') == 200:
            print(f"  ✓ {scenario_id}: {scenario['title']}")
            total_indexed += 1
        else:
            print(f"  ✗ {scenario_id}: Failed to index")
        
        time.sleep(0.1)  # Avoid throttling
    
    # Index best practices
    print("\nIndexing best practices...")
    for bp in kb_docs.best_practices:
        bp_id = bp['id']
        document = {
            'document_id': bp_id,
            'title': bp['title'],
            'content': bp['content'],
            'metadata': {
                'type': 'best_practice',
                'category': bp['category'],
                'tags': bp['tags']
            }
        }
        
        result = invoke_kb_lambda('index_document', {'document': document})
        if result.get('statusCode') == 200:
            print(f"  ✓ {bp_id}: {bp['title']}")
            total_indexed += 1
        else:
            print(f"  ✗ {bp_id}: Failed to index")
        
        time.sleep(0.1)
    
    # Index resolution guides
    print("\nIndexing resolution guides...")
    for guide in kb_docs.resolution_guides:
        guide_id = guide['id']
        document = {
            'document_id': guide_id,
            'title': guide['title'],
            'content': guide['content'],
            'metadata': {
                'type': 'resolution_guide',
                'category': guide['category'],
                'tags': guide['tags']
            }
        }
        
        result = invoke_kb_lambda('index_document', {'document': document})
        if result.get('statusCode') == 200:
            print(f"  ✓ {guide_id}: {guide['title']}")
            total_indexed += 1
        else:
            print(f"  ✗ {guide_id}: Failed to index")
        
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print(f"Population complete! Indexed {total_indexed} documents.")
    
    # Test search
    print("\nTesting search functionality...")
    test_result = invoke_kb_lambda('search_incidents', {
        'query': 'database connection pool',
        'k': 3
    })
    
    if test_result.get('statusCode') == 200:
        body = json.loads(test_result['body'])
        results = body.get('results', [])
        print(f"Found {len(results)} results for 'database connection pool'")
        for result in results[:3]:
            print(f"  - {result['title']} (Score: {result.get('score', 0):.3f})")
    else:
        print("Search test failed")

if __name__ == "__main__":
    main()