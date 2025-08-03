import json
import logging
import boto3
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
ssm_client = boto3.client('ssm')
lambda_client = boto3.client('lambda')

KB_LAMBDA_NAME = 'sre-knowledge-base-agent-lambda'

def lambda_handler(event, context):
    """
    Lambda function to automatically index OpsItems to the knowledge base.
    Triggered by CloudWatch Events when OpsItems are created or updated.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract event details
        detail = event.get('detail', {})
        event_name = detail.get('eventName')
        
        # Extract OpsItem ID from the event
        request_params = detail.get('requestParameters', {})
        ops_item_id = None
        
        if event_name == 'CreateOpsItem':
            # For CreateOpsItem, the ID is in the response
            response_elements = detail.get('responseElements', {})
            ops_item_id = response_elements.get('opsItemId')
        elif event_name == 'UpdateOpsItem':
            # For UpdateOpsItem, the ID is in the request
            ops_item_id = request_params.get('opsItemId')
            
        if not ops_item_id:
            logger.warning("Could not extract OpsItem ID from event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No OpsItem ID found'})
            }
            
        logger.info(f"Processing OpsItem: {ops_item_id}")
        
        # Get OpsItem details
        try:
            response = ssm_client.get_ops_item(OpsItemId=ops_item_id)
            ops_item = response['OpsItem']
        except Exception as e:
            logger.error(f"Error getting OpsItem: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to get OpsItem: {str(e)}'})
            }
            
        # Check if this is a resolved item
        status = ops_item.get('Status', '')
        
        # Add resolution information if resolved
        if status in ['Resolved', 'Closed']:
            # Get resolution details from operational data
            operational_data = ops_item.get('OperationalData', {})
            resolution_data = operational_data.get('/aws/resolution', {})
            
            if resolution_data:
                resolution_value = json.loads(resolution_data.get('Value', '{}'))
                ops_item['ResolutionDetails'] = resolution_value
                
        # Index to knowledge base
        logger.info(f"Indexing OpsItem {ops_item_id} to knowledge base")
        
        try:
            # Invoke knowledge base Lambda
            kb_response = lambda_client.invoke(
                FunctionName=KB_LAMBDA_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'index_opsitem',
                    'ops_item': ops_item
                })
            )
            
            kb_result = json.loads(kb_response['Payload'].read())
            
            if kb_result.get('statusCode') == 200:
                logger.info(f"Successfully indexed OpsItem {ops_item_id}")
                
                # If this is a resolution, also index as a resolution guide
                if status in ['Resolved', 'Closed'] and 'ResolutionDetails' in ops_item:
                    index_resolution_guide(ops_item)
                    
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f'OpsItem {ops_item_id} indexed successfully',
                        'status': status
                    })
                }
            else:
                logger.error(f"Failed to index OpsItem: {kb_result}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'Failed to index OpsItem'})
                }
                
        except Exception as e:
            logger.error(f"Error invoking KB Lambda: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to invoke KB Lambda: {str(e)}'})
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def index_resolution_guide(ops_item):
    """
    Create a resolution guide from a resolved OpsItem.
    """
    try:
        ops_item_id = ops_item.get('OpsItemId')
        title = ops_item.get('Title', 'Untitled')
        description = ops_item.get('Description', '')
        resolution_details = ops_item.get('ResolutionDetails', {})
        
        # Determine category from title/description
        category = determine_category(title, description)
        
        # Create resolution guide document
        resolution_doc = {
            'document_id': f'RG-AUTO-{ops_item_id}',
            'title': f'Resolution Guide: {title}',
            'content': f"""
Resolution Guide Auto-Generated from OpsItem {ops_item_id}

Original Incident:
{description}

Resolution Steps:
{resolution_details.get('steps', 'No steps documented')}

Root Cause:
{resolution_details.get('root_cause', 'Not specified')}

Time to Resolution:
Created: {ops_item.get('CreatedTime')}
Resolved: {ops_item.get('LastModifiedTime')}

Lessons Learned:
{resolution_details.get('lessons_learned', 'None documented')}

Prevention:
{resolution_details.get('prevention', 'No prevention steps documented')}
""",
            'metadata': {
                'type': 'resolution_guide',
                'category': category,
                'tags': ['auto-generated', 'opsitem', category],
                'source_ops_item': ops_item_id
            }
        }
        
        # Index the resolution guide
        lambda_client.invoke(
            FunctionName=KB_LAMBDA_NAME,
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'action': 'index_document',
                'document': resolution_doc
            })
        )
        
        logger.info(f"Created resolution guide from OpsItem {ops_item_id}")
        
    except Exception as e:
        logger.error(f"Error creating resolution guide: {str(e)}")


def determine_category(title, description):
    """Determine category based on title and description."""
    text = f"{title} {description}".lower()
    
    if 'performance' in text or 'slow' in text or 'latency' in text:
        return 'performance'
    elif 'security' in text or 'unauthorized' in text or 'breach' in text:
        return 'security'
    elif 'outage' in text or 'down' in text or 'unavailable' in text:
        return 'outage'
    elif 'data' in text or 'database' in text or 'replication' in text:
        return 'data'
    else:
        return 'general'