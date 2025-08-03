#!/usr/bin/env python3
"""
Verify Knowledge Base contents.
"""

import boto3
import json

def test_browse():
    """Test browse functionality."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print("Knowledge Base Contents Summary")
    print("=" * 60)
    
    # Test browsing all documents
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'browse_documents',
            'limit': 100
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        all_docs = body.get('results', [])
        
        # Count by type
        by_type = {}
        by_category = {}
        
        for doc in all_docs:
            doc_type = doc['metadata'].get('type', 'unknown')
            category = doc['metadata'].get('category', 'unknown')
            
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
        
        print(f"\nTotal documents: {len(all_docs)}")
        
        print("\nBy Type:")
        for doc_type, count in sorted(by_type.items()):
            print(f"  - {doc_type}: {count}")
        
        print("\nBy Category:")
        for category, count in sorted(by_category.items()):
            print(f"  - {category}: {count}")
        
        # Show sample documents
        print("\nSample Documents:")
        
        # Show one of each type
        shown_types = set()
        for doc in all_docs:
            doc_type = doc['metadata'].get('type')
            if doc_type not in shown_types:
                print(f"\n{doc_type.upper()}:")
                print(f"  ID: {doc['document_id']}")
                print(f"  Title: {doc['title']}")
                print(f"  Category: {doc['metadata'].get('category')}")
                print(f"  Tags: {', '.join(doc['metadata'].get('tags', []))}")
                shown_types.add(doc_type)
                
                if len(shown_types) >= 3:
                    break
    else:
        print(f"Error: {result}")

if __name__ == "__main__":
    test_browse()