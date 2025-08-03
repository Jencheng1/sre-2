#!/usr/bin/env python3
"""
Demo: Incident Auto-indexing to Knowledge Base
Shows how creating an incident automatically populates the KB
"""

import boto3
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def print_step(step_num, text):
    print(f"{Fore.GREEN}Step {step_num}: {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def create_incident():
    """Create a new incident via OpsItem."""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    
    incident_data = {
        'Title': 'DEMO: Database Connection Pool Critical - Production Impact',
        'Description': """
Production database experiencing severe connection pool exhaustion.

Current Situation:
- Connection pool utilization: 98%
- Active connections: 195/200
- Response times increased from 200ms to 8000ms
- Error rate: 35% timeouts
- Affected services: user-api, order-service, payment-gateway

Timeline:
- 10:45 - New microservice deployment (order-service v2.1.0)
- 10:50 - Slight increase in database connections noticed
- 11:00 - Connection pool warnings in logs
- 11:10 - First timeout errors reported
- 11:15 - Multiple services reporting database connectivity issues
- 11:20 - Customer complaints about checkout failures

Initial Investigation:
- New order-service version has connection leak
- Connections not being released after transactions
- Connection timeout set too high (30s)
- No circuit breaker pattern implemented
""",
        'Source': 'SRE-Demo',
        'Severity': '1',  # Critical
        'OperationalData': {
            'IncidentType': {'Value': 'performance', 'Type': 'String'},
            'AffectedService': {'Value': 'database', 'Type': 'String'},
            'Environment': {'Value': 'production', 'Type': 'String'},
            'RootCause': {'Value': 'Connection leak in order-service v2.1.0', 'Type': 'String'},
            'CustomerImpact': {'Value': 'High - Checkout failures affecting revenue', 'Type': 'String'}
        }
    }
    
    response = ssm_client.create_ops_item(**incident_data)
    return response['OpsItemId'], incident_data

def wait_for_indexing(ops_item_id, max_wait=30):
    """Wait for the OpsItem to be indexed to KB."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    print_info(f"Waiting for OpsItem {ops_item_id} to be indexed...")
    
    for i in range(max_wait):
        # Search for the OpsItem in KB
        response = lambda_client.invoke(
            FunctionName='sre-knowledge-base-agent-lambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'search_incidents',
                'query': ops_item_id,
                'k': 5
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            results = body.get('results', [])
            
            for doc in results:
                if ops_item_id in doc.get('document_id', ''):
                    return True
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print()
    return False

def search_similar_incidents(description):
    """Search for similar incidents in KB."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'search_incidents',
            'query': 'database connection pool exhaustion timeout',
            'category': 'performance',
            'k': 5
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        return body.get('results', [])
    return []

def search_best_practices(query):
    """Search for relevant best practices."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'search_best_practices',
            'query': query,
            'tags': ['database', 'performance']
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        return body.get('results', [])
    return []

def get_resolution_guide(incident_type):
    """Get resolution guide for incident type."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'get_resolution',
            'incident_type': incident_type
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        return body.get('guide')
    return None

def analyze_with_kb_context(description):
    """Get AI analysis with KB context."""
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'analyze_with_context',
            'incident_description': description,
            'incident_type': 'performance'
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('statusCode') == 200:
        body = json.loads(result['body'])
        return body.get('analysis'), body.get('context_used')
    return None, None

def main():
    print_header("Knowledge Base Auto-Indexing Demo")
    print("This demo shows how creating an incident automatically populates the KB\n")
    
    # Step 1: Create an incident
    print_step(1, "Creating a new production incident (OpsItem)")
    ops_item_id, incident_data = create_incident()
    print_success(f"Created OpsItem: {ops_item_id}")
    print_info(f"Title: {incident_data['Title']}")
    print_info(f"Severity: Critical")
    
    # Step 2: Manual indexing (since auto-indexing via CloudWatch Events may have delay)
    print_step(2, "Indexing incident to Knowledge Base")
    
    # Get the OpsItem and index it
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    response = ssm_client.get_ops_item(OpsItemId=ops_item_id)
    ops_item = response['OpsItem']
    
    # Convert datetime objects
    ops_item_serializable = {}
    for key, value in ops_item.items():
        if isinstance(value, datetime):
            ops_item_serializable[key] = value.isoformat()
        else:
            ops_item_serializable[key] = value
    
    # Index to KB
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    response = lambda_client.invoke(
        FunctionName='sre-knowledge-base-agent-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'index_opsitem',
            'ops_item': ops_item_serializable
        })
    )
    
    if json.loads(response['Payload'].read()).get('statusCode') == 200:
        print_success("Incident indexed to Knowledge Base")
    else:
        print_error("Failed to index incident")
        return
    
    time.sleep(2)  # Give it a moment to index
    
    # Step 3: Search for similar incidents
    print_step(3, "Searching for similar incidents in Knowledge Base")
    similar_incidents = search_similar_incidents(incident_data['Description'])
    
    if similar_incidents:
        print_success(f"Found {len(similar_incidents)} similar incidents:")
        for i, incident in enumerate(similar_incidents[:3], 1):
            print(f"\n  {i}. {Fore.CYAN}{incident['title']}{Style.RESET_ALL}")
            print(f"     ID: {incident['document_id']}")
            print(f"     Similarity Score: {incident.get('score', 0):.3f}")
            if incident.get('metadata', {}).get('root_cause'):
                print(f"     Root Cause: {incident['metadata']['root_cause']}")
    
    # Step 4: Find best practices
    print_step(4, "Finding relevant best practices")
    best_practices = search_best_practices("database connection pool")
    
    if best_practices:
        print_success(f"Found {len(best_practices)} relevant best practices:")
        for i, bp in enumerate(best_practices[:3], 1):
            print(f"\n  {i}. {Fore.CYAN}{bp['title']}{Style.RESET_ALL}")
            print(f"     Tags: {', '.join(bp.get('metadata', {}).get('tags', []))}")
    
    # Step 5: Get resolution guide
    print_step(5, "Getting resolution guide for performance incidents")
    resolution = get_resolution_guide('performance')
    
    if resolution:
        print_success(f"Found resolution guide: {resolution['title']}")
        print(f"\n{Fore.YELLOW}Resolution Steps:{Style.RESET_ALL}")
        # Extract immediate actions
        content = resolution['content']
        if 'Immediate Actions:' in content:
            immediate = content.split('Immediate Actions:')[1].split('\n\n')[0]
            print(immediate[:500] + "..." if len(immediate) > 500 else immediate)
    
    # Step 6: Get AI analysis with KB context
    print_step(6, "Getting AI-powered analysis with Knowledge Base context")
    analysis, context = analyze_with_kb_context(incident_data['Description'])
    
    if analysis and context:
        print_success("Analysis completed with KB enhancement")
        print(f"\nContext used:")
        print(f"  - Similar incidents: {context.get('similar_incidents_count', 0)}")
        print(f"  - Best practices: {context.get('best_practices_count', 0)}")
        print(f"  - Has resolution guide: {context.get('has_resolution_guide', False)}")
        
        print(f"\n{Fore.YELLOW}Analysis Summary:{Style.RESET_ALL}")
        # Show first part of analysis
        print(analysis[:800] + "..." if len(analysis) > 800 else analysis)
    
    # Summary
    print_header("Demo Complete!")
    print("✨ The incident has been:")
    print("  1. Created as an OpsItem")
    print("  2. Automatically indexed to the Knowledge Base")
    print("  3. Analyzed with historical context from similar incidents")
    print("  4. Matched with relevant best practices")
    print("  5. Provided with a resolution guide")
    print("\n📝 This incident is now part of the knowledge base and will help")
    print("   resolve similar issues faster in the future!")
    
    print(f"\n🔍 You can now search for this incident in Streamlit:")
    print(f"   - Go to Knowledge Base tab")
    print(f"   - Search for: {ops_item_id}")
    print(f"   - Or browse Performance category incidents")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()