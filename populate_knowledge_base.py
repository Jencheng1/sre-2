#!/usr/bin/env python3
"""
Populate the knowledge base with incidents, best practices, and resolution guides.
"""

import boto3
import json
import time
from incident_scenarios import IncidentScenarios
from knowledge_base_documents import KnowledgeBaseDocuments

class KnowledgeBasePopulator:
    """Populate OpenSearch knowledge base via Lambda function."""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.function_name = 'sre-knowledge-base-agent-lambda'
        
    def invoke_lambda(self, action, payload):
        """Invoke the knowledge base Lambda function."""
        event = {
            'action': action,
            **payload
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error invoking Lambda: {str(e)}")
            return None
            
    def create_index(self):
        """Create the OpenSearch index."""
        print("Creating OpenSearch index...")
        result = self.invoke_lambda('create_index', {})
        if result:
            print(f"Index creation result: {result.get('body')}")
        time.sleep(2)
        
    def populate_incidents(self):
        """Populate incident scenarios."""
        print("\nPopulating incident scenarios...")
        scenarios = IncidentScenarios()
        
        for scenario in scenarios.scenarios:
            print(f"Indexing incident: {scenario['id']} - {scenario['title']}")
            
            document = {
                'document_id': scenario['id'],
                'title': scenario['title'],
                'content': f"""
Incident: {scenario['title']}
Category: {scenario['category']}
Severity: {scenario['severity']}

Description: {scenario['description']}

Timeline:
{self._format_timeline(scenario['timeline'])}

Root Cause: {scenario['root_cause']}

Correlated Changes:
{self._format_list(scenario['correlated_changes'])}

Resolution: {scenario['resolution']}

Best Practices:
{self._format_list(scenario['best_practices'])}
""",
                'metadata': {
                    'type': 'incident',
                    'category': scenario['category'],
                    'severity': scenario['severity'],
                    'root_cause': scenario['root_cause'],
                    'tags': [scenario['category'], scenario['severity'], 'incident']
                }
            }
            
            result = self.invoke_lambda('index_document', {'document': document})
            if result and result.get('statusCode') == 200:
                print(f"  ✓ Indexed successfully")
            else:
                print(f"  ✗ Failed to index: {result}")
                
            time.sleep(1)  # Rate limiting
            
    def populate_best_practices(self):
        """Populate best practices and resolution guides."""
        print("\nPopulating best practices and resolution guides...")
        kb_docs = KnowledgeBaseDocuments()
        
        # Index best practices
        for bp in kb_docs.best_practices:
            print(f"Indexing best practice: {bp['id']} - {bp['title']}")
            
            document = {
                'document_id': bp['id'],
                'title': bp['title'],
                'content': bp['content'],
                'metadata': {
                    'type': 'best_practice',
                    'category': bp['category'],
                    'tags': bp['tags']
                }
            }
            
            result = self.invoke_lambda('index_document', {'document': document})
            if result and result.get('statusCode') == 200:
                print(f"  ✓ Indexed successfully")
            else:
                print(f"  ✗ Failed to index: {result}")
                
            time.sleep(1)
            
        # Index resolution guides
        for rg in kb_docs.resolution_guides:
            print(f"Indexing resolution guide: {rg['id']} - {rg['title']}")
            
            document = {
                'document_id': rg['id'],
                'title': rg['title'],
                'content': rg['content'],
                'metadata': {
                    'type': 'resolution_guide',
                    'category': rg['category'],
                    'tags': rg['tags']
                }
            }
            
            result = self.invoke_lambda('index_document', {'document': document})
            if result and result.get('statusCode') == 200:
                print(f"  ✓ Indexed successfully")
            else:
                print(f"  ✗ Failed to index: {result}")
                
            time.sleep(1)
            
    def test_search(self):
        """Test search functionality."""
        print("\n" + "="*60)
        print("Testing Knowledge Base Search")
        print("="*60)
        
        # Test incident search
        print("\n1. Testing incident search for 'database connection pool':")
        result = self.invoke_lambda('search_incidents', {
            'query': 'database connection pool exhaustion timeout',
            'k': 3
        })
        
        if result and result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"Found {body['count']} similar incidents:")
            for idx, doc in enumerate(body['results'], 1):
                print(f"  {idx}. {doc['title']} (Score: {doc['score']:.2f})")
                
        # Test best practices search
        print("\n2. Testing best practices search for 'security':")
        result = self.invoke_lambda('search_best_practices', {
            'query': 'security group configuration',
            'tags': ['security']
        })
        
        if result and result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print(f"Found {body['count']} best practices:")
            for idx, doc in enumerate(body['results'], 1):
                print(f"  {idx}. {doc['title']}")
                
        # Test contextual analysis
        print("\n3. Testing contextual analysis:")
        result = self.invoke_lambda('analyze_with_context', {
            'incident_description': 'Application experiencing severe slowdown with database timeouts',
            'incident_type': 'performance'
        })
        
        if result and result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print("Context used:")
            print(f"  - Similar incidents: {body['context_used']['similar_incidents_count']}")
            print(f"  - Best practices: {body['context_used']['best_practices_count']}")
            print(f"  - Has resolution guide: {body['context_used']['has_resolution_guide']}")
            
    def _format_timeline(self, timeline):
        """Format timeline for display."""
        return '\n'.join([f"  {e['time']}: {e['event']} ({e['type']})" for e in timeline])
        
    def _format_list(self, items):
        """Format list items for display."""
        return '\n'.join([f"  - {item}" for item in items])


def main():
    """Main execution function."""
    populator = KnowledgeBasePopulator()
    
    print("SRE Knowledge Base Population Tool")
    print("="*60)
    
    # Check if Lambda function exists
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        lambda_client.get_function(FunctionName='sre-knowledge-base-agent-lambda')
        print("✓ Knowledge base Lambda function found")
    except lambda_client.exceptions.ResourceNotFoundException:
        print("✗ Knowledge base Lambda function not found")
        print("Please deploy the Lambda function first")
        return
    
    # Menu
    while True:
        print("\nOptions:")
        print("1. Create OpenSearch index")
        print("2. Populate all data (incidents, best practices, resolution guides)")
        print("3. Populate incidents only")
        print("4. Populate best practices only")
        print("5. Test search functionality")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            populator.create_index()
            
        elif choice == '2':
            populator.create_index()
            populator.populate_incidents()
            populator.populate_best_practices()
            print("\n✓ Knowledge base population complete!")
            
        elif choice == '3':
            populator.populate_incidents()
            
        elif choice == '4':
            populator.populate_best_practices()
            
        elif choice == '5':
            populator.test_search()
            
        elif choice == '6':
            print("\nExiting...")
            break
            
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    main()