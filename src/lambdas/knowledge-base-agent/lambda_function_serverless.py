import json
import logging
import boto3
import os
from datetime import datetime
# import numpy as np  # Removed numpy dependency
from typing import List, Dict, Any
import hashlib
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

# DynamoDB table names
KB_TABLE = os.environ.get('KB_TABLE_NAME', 'sre-knowledge-base')
KB_VECTORS_TABLE = os.environ.get('KB_VECTORS_TABLE_NAME', 'sre-knowledge-base-vectors')

# Helper class for DynamoDB Decimal handling
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

class ServerlessKnowledgeBase:
    """Serverless knowledge base using DynamoDB instead of OpenSearch."""
    
    def __init__(self):
        self.kb_table = dynamodb.Table(KB_TABLE)
        self.vectors_table = dynamodb.Table(KB_VECTORS_TABLE)
        
    def create_tables_if_not_exist(self):
        """Create DynamoDB tables for knowledge base."""
        try:
            # Main knowledge base table
            dynamodb.create_table(
                TableName=KB_TABLE,
                KeySchema=[
                    {'AttributeName': 'document_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'document_id', 'AttributeType': 'S'},
                    {'AttributeName': 'category', 'AttributeType': 'S'},
                    {'AttributeName': 'doc_type', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'category-index',
                        'KeySchema': [
                            {'AttributeName': 'category', 'KeyType': 'HASH'},
                            {'AttributeName': 'doc_type', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            logger.info(f"Created table: {KB_TABLE}")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info(f"Table {KB_TABLE} already exists")
            
        try:
            # Vectors table for embeddings
            dynamodb.create_table(
                TableName=KB_VECTORS_TABLE,
                KeySchema=[
                    {'AttributeName': 'document_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'document_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            logger.info(f"Created table: {KB_VECTORS_TABLE}")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            logger.info(f"Table {KB_VECTORS_TABLE} already exists")
            
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Amazon Titan."""
        try:
            # Truncate text if too long
            if len(text) > 8000:
                text = text[:8000]
                
            response = bedrock_runtime.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "inputText": text
                })
            )
            
            result = json.loads(response['body'].read())
            return result['embedding']
            
        except Exception as e:
            logger.warning(f"Using mock embedding due to: {str(e)}")
            # Return deterministic mock embedding based on text hash
            import hashlib
            import random
            
            # Use text hash as seed for consistent embeddings
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            seed = int(text_hash[:8], 16)
            random.seed(seed)
            
            # Generate deterministic embedding
            embedding = [random.random() for _ in range(1536)]
            random.seed()  # Reset seed
            
            return embedding
            
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Manual cosine similarity calculation without numpy
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
        
    def index_document(self, document: Dict[str, Any]):
        """Index a document with its embedding in DynamoDB."""
        try:
            # Generate embedding
            embedding_text = f"{document.get('title', '')} {document.get('content', '')}"
            embedding = self.generate_embedding(embedding_text)
            
            # Prepare main document
            doc_item = {
                'document_id': document['document_id'],
                'title': document['title'],
                'content': document['content'],
                'category': document.get('metadata', {}).get('category', 'general'),
                'doc_type': document.get('metadata', {}).get('type', 'general'),
                'tags': document.get('metadata', {}).get('tags', []),
                'severity': document.get('metadata', {}).get('severity', 'medium'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Add additional metadata
            if 'root_cause' in document.get('metadata', {}):
                doc_item['root_cause'] = document['metadata']['root_cause']
                
            # Store document
            self.kb_table.put_item(Item=doc_item)
            
            # Store embedding separately (DynamoDB has 400KB item limit)
            # Split embedding into chunks if needed
            embedding_chunks = []
            chunk_size = 500  # Store 500 dimensions per chunk
            
            for i in range(0, len(embedding), chunk_size):
                chunk = embedding[i:i + chunk_size]
                embedding_chunks.append([Decimal(str(x)) for x in chunk])
                
            vector_item = {
                'document_id': document['document_id'],
                'embedding_chunks': embedding_chunks,
                'chunk_count': len(embedding_chunks)
            }
            
            self.vectors_table.put_item(Item=vector_item)
            
            logger.info(f"Indexed document: {document['document_id']}")
            return {
                'success': True,
                'document_id': document['document_id']
            }
            
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise
            
    def search_similar_documents(self, query: str, category: str = None, k: int = 5) -> List[Dict]:
        """Search for similar documents using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Get all documents (with optional category filter)
            if category and category != 'All':
                response = self.kb_table.query(
                    IndexName='category-index',
                    KeyConditionExpression='category = :cat',
                    ExpressionAttributeValues={':cat': category}
                )
            else:
                response = self.kb_table.scan()
                
            documents = response.get('Items', [])
            
            # Calculate similarities
            similarities = []
            
            for doc in documents:
                # Get embedding for this document
                vector_response = self.vectors_table.get_item(
                    Key={'document_id': doc['document_id']}
                )
                
                if 'Item' in vector_response:
                    vector_item = vector_response['Item']
                    
                    # Reconstruct embedding from chunks
                    full_embedding = []
                    for chunk in vector_item['embedding_chunks']:
                        full_embedding.extend([float(x) for x in chunk])
                        
                    # Calculate similarity
                    similarity = self.cosine_similarity(query_embedding, full_embedding)
                    
                    # Ensure score is a valid float (not NaN or Infinity)
                    if similarity != similarity:  # Check for NaN
                        similarity = 0.0
                    elif similarity == float('inf') or similarity == float('-inf'):
                        similarity = 0.0
                    else:
                        similarity = max(0.0, min(1.0, float(similarity)))  # Clamp to [0, 1]
                    
                    similarities.append({
                        'document': doc,
                        'score': similarity
                    })
                    
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            results = []
            for item in similarities[:k]:
                doc = item['document']
                
                # Ensure score is a valid, finite number
                score = item['score']
                if not isinstance(score, (int, float)) or score != score or score == float('inf') or score == float('-inf'):
                    score = 0.0
                else:
                    score = float(score)
                    
                results.append({
                    'document_id': doc['document_id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'metadata': {
                        'category': doc.get('category'),
                        'type': doc.get('doc_type'),
                        'tags': doc.get('tags', []),
                        'severity': doc.get('severity'),
                        'root_cause': doc.get('root_cause')
                    },
                    'score': score
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
            
    def search_by_type_and_tags(self, doc_type: str, tags: List[str] = None, query: str = None) -> List[Dict]:
        """Search documents by type and tags."""
        try:
            # Scan with filters (not optimal for large datasets)
            filter_expression = 'doc_type = :doc_type'
            expression_values = {':doc_type': doc_type}
            
            if tags:
                # Check if any tag matches
                filter_expression += ' AND ('
                tag_conditions = []
                for i, tag in enumerate(tags):
                    tag_key = f':tag{i}'
                    expression_values[tag_key] = tag
                    tag_conditions.append(f'contains(tags, {tag_key})')
                filter_expression += ' OR '.join(tag_conditions) + ')'
                
            response = self.kb_table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values
            )
            
            documents = response.get('Items', [])
            
            # If query provided, filter by text similarity
            if query:
                query_lower = query.lower()
                scored_docs = []
                
                for doc in documents:
                    # Simple text matching score
                    title_score = query_lower.count(doc['title'].lower())
                    content_score = query_lower.count(doc['content'].lower()[:500])
                    total_score = title_score * 2 + content_score  # Title matches worth more
                    
                    if total_score > 0:
                        scored_docs.append({
                            'document': doc,
                            'score': total_score
                        })
                        
                # Sort by score
                scored_docs.sort(key=lambda x: x['score'], reverse=True)
                
                results = []
                for item in scored_docs[:10]:
                    doc = item['document']
                    results.append({
                        'document_id': doc['document_id'],
                        'title': doc['title'],
                        'content': doc['content'],
                        'metadata': {
                            'category': doc.get('category'),
                            'type': doc.get('doc_type'),
                            'tags': doc.get('tags', [])
                        },
                        'score': item['score']
                    })
                    
                return results
            else:
                # Return all matching documents
                return [{
                    'document_id': doc['document_id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'metadata': {
                        'category': doc.get('category'),
                        'type': doc.get('doc_type'),
                        'tags': doc.get('tags', [])
                    }
                } for doc in documents]
                
        except Exception as e:
            logger.error(f"Error searching by type and tags: {str(e)}")
            return []
            
    def get_document_by_id(self, document_id: str) -> Dict:
        """Get a specific document by ID."""
        try:
            response = self.kb_table.get_item(
                Key={'document_id': document_id}
            )
            
            if 'Item' in response:
                doc = response['Item']
                return {
                    'document_id': doc['document_id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'metadata': {
                        'category': doc.get('category'),
                        'type': doc.get('doc_type'),
                        'tags': doc.get('tags', [])
                    }
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            return None
            
    def index_opsitem(self, ops_item: Dict) -> Dict:
        """Index an OpsItem as an incident document."""
        try:
            # Extract relevant information from OpsItem
            ops_item_id = ops_item.get('OpsItemId', 'Unknown')
            title = ops_item.get('Title', 'Untitled Incident')
            description = ops_item.get('Description', '')
            severity = str(ops_item.get('Severity', '3'))
            
            # Get operational data
            operational_data = ops_item.get('OperationalData', {})
            
            # Create incident document
            document = {
                'document_id': f'OPS-{ops_item_id}',
                'title': title,
                'content': f"""
Incident: {title}
OpsItem ID: {ops_item_id}
Severity: {severity}
Status: {ops_item.get('Status', 'Unknown')}

Description:
{description}

Created: {ops_item.get('CreatedTime', 'Unknown')}
Last Modified: {ops_item.get('LastModifiedTime', 'Unknown')}

Operational Data:
{json.dumps(operational_data, indent=2)}
""",
                'metadata': {
                    'type': 'incident',
                    'category': self._determine_category(title, description),
                    'severity': severity,
                    'tags': ['opsitem', 'incident', 'automated'],
                    'ops_item_id': ops_item_id,
                    'status': ops_item.get('Status', 'Unknown')
                }
            }
            
            # Index the document
            return self.index_document(document)
            
        except Exception as e:
            logger.error(f"Error indexing OpsItem: {str(e)}")
            raise
            
    def browse_documents(self, category: str = None, doc_type: str = None, limit: int = 50) -> List[Dict]:
        """Browse documents by category and type."""
        try:
            # Build scan filter
            filter_parts = []
            expression_values = {}
            
            if category:
                filter_parts.append('category = :cat')
                expression_values[':cat'] = category
                
            if doc_type:
                filter_parts.append('doc_type = :dtype')
                expression_values[':dtype'] = doc_type
                
            # Scan with filter
            if filter_parts:
                response = self.kb_table.scan(
                    FilterExpression=' AND '.join(filter_parts),
                    ExpressionAttributeValues=expression_values,
                    Limit=limit
                )
            else:
                response = self.kb_table.scan(Limit=limit)
                
            documents = response.get('Items', [])
            
            # Format results
            results = []
            for doc in documents:
                results.append({
                    'document_id': doc['document_id'],
                    'title': doc['title'],
                    'content': doc['content'],
                    'metadata': {
                        'category': doc.get('category'),
                        'type': doc.get('doc_type'),
                        'tags': doc.get('tags', []),
                        'severity': doc.get('severity'),
                        'root_cause': doc.get('root_cause'),
                        'created_at': doc.get('created_at'),
                        'updated_at': doc.get('updated_at')
                    }
                })
                
            # Sort by created_at (newest first)
            results.sort(key=lambda x: x['metadata'].get('created_at', ''), reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error browsing documents: {str(e)}")
            return []
    
    def _determine_category(self, title: str, description: str) -> str:
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


def lambda_handler(event, context):
    """Lambda handler for serverless knowledge base operations."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Initialize knowledge base
        kb = ServerlessKnowledgeBase()
        
        # Get action from event
        action = event.get('action', 'search')
        
        if action == 'create_tables':
            # Create DynamoDB tables
            kb.create_tables_if_not_exist()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Tables created successfully',
                    'tables': [KB_TABLE, KB_VECTORS_TABLE]
                })
            }
            
        elif action == 'index_document':
            # Index a document
            document = event.get('document')
            if not document:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Document is required'})
                }
                
            result = kb.index_document(document)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Document indexed successfully',
                    'result': result
                })
            }
            
        elif action == 'index_opsitem':
            # Index an OpsItem
            ops_item = event.get('ops_item')
            if not ops_item:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'OpsItem is required'})
                }
                
            result = kb.index_opsitem(ops_item)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'OpsItem indexed successfully',
                    'result': result
                })
            }
            
        elif action == 'search_incidents':
            # Search for similar incidents
            query = event.get('query', '')
            category = event.get('category')
            k = event.get('k', 5)
            
            results = kb.search_similar_documents(query, category, k)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'query': query,
                    'results': results,
                    'count': len(results)
                }, cls=DecimalEncoder)
            }
            
        elif action == 'search_best_practices':
            # Search for best practices
            query = event.get('query', '')
            tags = event.get('tags', [])
            
            results = kb.search_by_type_and_tags('best_practice', tags, query)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'query': query,
                    'results': results,
                    'count': len(results)
                })
            }
            
        elif action == 'get_resolution':
            # Get resolution guide for incident type
            incident_type = event.get('incident_type')
            if not incident_type:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Incident type is required'})
                }
                
            # Search for resolution guides in the category
            results = kb.search_by_type_and_tags('resolution_guide', [], incident_type)
            
            # Filter by category (prefer exact match)
            guide = None
            fallback_guide = None
            
            for result in results:
                if result.get('metadata', {}).get('category') == incident_type:
                    guide = result
                    break
                elif result.get('metadata', {}).get('type') == 'resolution_guide':
                    # Keep first resolution guide as fallback
                    if fallback_guide is None:
                        fallback_guide = result
                        
            # If no exact match, use fallback or create a generic guide
            if guide is None:
                if fallback_guide:
                    guide = fallback_guide
                else:
                    # Create a generic resolution guide
                    guide = {
                        'title': f'Generic Resolution Guide for {incident_type.title()} Issues',
                        'content': f"""
Generic Resolution Steps for {incident_type.title()} Issues:

1. **Immediate Assessment**
   - Check system metrics and alerts
   - Review recent changes or deployments
   - Identify affected components

2. **Initial Response**
   - Implement immediate mitigation if possible
   - Communicate status to stakeholders
   - Gather additional diagnostics

3. **Investigation**
   - Analyze logs and metrics
   - Check for known issues in knowledge base
   - Escalate if needed

4. **Resolution**
   - Apply fix based on root cause
   - Monitor for improvement
   - Document resolution steps

5. **Post-Incident**
   - Conduct post-mortem if significant
   - Update monitoring and alerting
   - Add learnings to knowledge base
   
For specific guidance, search the knowledge base for similar {incident_type} incidents.
""",
                        'metadata': {
                            'type': 'resolution_guide',
                            'category': incident_type,
                            'generated': True
                        }
                    }
                    
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'incident_type': incident_type,
                    'guide': guide
                }, cls=DecimalEncoder)
            }
            
        elif action == 'browse_documents':
            # Browse documents by category and type
            category = event.get('category')
            doc_type = event.get('doc_type')
            limit = event.get('limit', 50)
            
            results = kb.browse_documents(category, doc_type, limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'category': category,
                    'doc_type': doc_type,
                    'results': results,
                    'count': len(results)
                }, cls=DecimalEncoder)
            }
            
        elif action == 'analyze_with_context':
            # Analyze with knowledge base context
            incident_description = event.get('incident_description', '')
            incident_type = event.get('incident_type', 'general')
            
            # Get similar incidents
            similar_incidents = kb.search_similar_documents(incident_description, incident_type, 3)
            
            # Get best practices
            best_practices = kb.search_by_type_and_tags('best_practice', [incident_type], incident_description)[:2]
            
            # Get resolution guide
            resolution_results = kb.search_by_type_and_tags('resolution_guide', [], None)
            resolution_guide = None
            for result in resolution_results:
                if result['metadata'].get('category') == incident_type:
                    resolution_guide = result
                    break
                    
            # Generate enhanced analysis
            analysis = generate_contextual_analysis(incident_description, {
                'similar_incidents': similar_incidents,
                'best_practices': best_practices,
                'resolution_guide': resolution_guide
            })
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'incident_description': incident_description,
                    'analysis': analysis,
                    'context_used': {
                        'similar_incidents_count': len(similar_incidents),
                        'best_practices_count': len(best_practices),
                        'has_resolution_guide': resolution_guide is not None
                    }
                })
            }
            
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }


def generate_contextual_analysis(incident_description: str, context: Dict) -> str:
    """Generate analysis using knowledge base context."""
    analysis = f"""
## Knowledge-Based Root Cause Analysis

### Incident Description
{incident_description}

### Analysis Based on Historical Data
"""
    
    # Add similar incidents
    if context['similar_incidents']:
        analysis += "\n#### Similar Past Incidents:\n"
        for idx, incident in enumerate(context['similar_incidents'][:2], 1):
            analysis += f"\n{idx}. **{incident['title']}**\n"
            if incident.get('metadata', {}).get('root_cause'):
                analysis += f"   - Root Cause: {incident['metadata']['root_cause']}\n"
            analysis += f"   - Similarity Score: {incident['score']:.2f}\n"
            
    # Add best practices
    if context['best_practices']:
        analysis += "\n#### Relevant Best Practices:\n"
        for bp in context['best_practices']:
            analysis += f"\n- **{bp['title']}**\n"
            # Extract key points
            content_lines = bp['content'].split('\n')
            for line in content_lines[:5]:
                if line.strip() and not line.startswith('#'):
                    analysis += f"  {line.strip()}\n"
                    break
                    
    # Add resolution guide
    if context['resolution_guide']:
        analysis += f"\n#### Recommended Resolution Steps:\n"
        analysis += f"Based on: {context['resolution_guide']['title']}\n\n"
        # Extract immediate actions
        content = context['resolution_guide']['content']
        if 'Immediate Actions:' in content:
            immediate_section = content.split('Immediate Actions:')[1].split('\n\n')[0]
            analysis += immediate_section
            
    analysis += "\n### Recommendations\n"
    analysis += "1. Review similar incidents for proven resolution patterns\n"
    analysis += "2. Apply relevant best practices to prevent recurrence\n"
    analysis += "3. Follow the resolution guide for systematic recovery\n"
    analysis += "4. Document lessons learned for knowledge base improvement\n"
    
    return analysis