"""
Context Enhancement using feedback to improve analysis accuracy
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import boto3
from decimal import Decimal

class ContextEnhancer:
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.feedback_table = self.dynamodb.Table('sre-copilot-feedback')
        self.context_table_name = 'sre-copilot-enhanced-context'
        self.ensure_context_table_exists()
        self.context_table = self.dynamodb.Table(self.context_table_name)
        self.embeddings_cache = {}
        
    def ensure_context_table_exists(self):
        """Create context table if it doesn't exist"""
        try:
            self.dynamodb.meta.client.describe_table(TableName=self.context_table_name)
        except:
            # Create table
            self.dynamodb.create_table(
                TableName=self.context_table_name,
                KeySchema=[
                    {'AttributeName': 'context_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'context_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        
    def add_feedback_to_context(self, feedback: Dict[str, Any]) -> bool:
        """Add validated feedback to enhanced context"""
        try:
            # Generate embedding for the feedback
            embedding = self._generate_embedding(json.dumps({
                'incident_type': feedback.get('incident_type', ''),
                'root_cause': feedback.get('root_cause', ''),
                'resolution': feedback.get('resolution', '')
            }))
            
            # Store in context table
            # Convert numpy array to list of Decimal for DynamoDB
            embedding_list = [Decimal(str(float(x))) for x in embedding.tolist()]
            
            item = {
                'context_id': f"ctx-{datetime.now().timestamp()}",
                'incident_type': feedback.get('incident_type', 'unknown'),
                'root_cause': feedback.get('root_cause', ''),
                'resolution': feedback.get('resolution', ''),
                'effectiveness': Decimal(str(feedback.get('effectiveness', 0))),
                'embedding': embedding_list,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'symptoms': feedback.get('symptoms', []),
                    'contributing_factors': feedback.get('contributing_factors', []),
                    'prevention_measures': feedback.get('prevention_measures', [])
                }
            }
            
            self.context_table.put_item(Item=item)
            return True
            
        except Exception as e:
            print(f"Error adding feedback to context: {e}")
            return False
    
    def get_enhanced_context(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced context for an incident based on historical feedback"""
        # Generate embedding for the current incident
        incident_embedding = self._generate_embedding(json.dumps({
            'type': incident.get('type', ''),
            'symptoms': incident.get('symptoms', [])
        }))
        
        # Find similar historical incidents
        similar_contexts = self._find_similar_contexts(incident_embedding, incident.get('type'))
        
        # Aggregate insights from similar incidents
        enhanced_context = {
            'historical_resolutions': [],
            'probable_root_causes': [],
            'recommended_actions': [],
            'things_to_check': [],
            'common_patterns': [],
            'confidence_boost': 0
        }
        
        for context in similar_contexts[:5]:  # Top 5 most similar
            if context['effectiveness'] >= 4:  # Only use highly effective resolutions
                enhanced_context['historical_resolutions'].append({
                    'root_cause': context['root_cause'],
                    'resolution': context['resolution'],
                    'similarity_score': context['similarity_score']
                })
                
                # Extract insights
                if context.get('metadata'):
                    enhanced_context['things_to_check'].extend(
                        context['metadata'].get('contributing_factors', [])
                    )
                    enhanced_context['recommended_actions'].extend(
                        context['metadata'].get('prevention_measures', [])
                    )
        
        # Calculate confidence boost based on historical data
        if similar_contexts:
            avg_effectiveness = np.mean([c['effectiveness'] for c in similar_contexts[:3]])
            enhanced_context['confidence_boost'] = min(0.2, avg_effectiveness / 25)  # Max 20% boost
        
        # Deduplicate and rank
        enhanced_context['things_to_check'] = list(set(enhanced_context['things_to_check']))
        enhanced_context['recommended_actions'] = list(set(enhanced_context['recommended_actions']))
        
        # Identify patterns
        enhanced_context['common_patterns'] = self._identify_patterns(similar_contexts)
        
        return enhanced_context
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using Bedrock Titan"""
        # Check cache first
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.bedrock.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    'inputText': text
                })
            )
            
            result = json.loads(response['body'].read())
            embedding = np.array(result['embedding'])
            
            # Cache the result
            self.embeddings_cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return random embedding as fallback for testing
            return np.random.rand(1536)  # Titan embedding dimension
    
    def _find_similar_contexts(self, query_embedding: np.ndarray, incident_type: str) -> List[Dict[str, Any]]:
        """Find similar contexts using vector similarity"""
        try:
            # Scan the context table (in production, use a vector DB)
            response = self.context_table.scan()
            contexts = response.get('Items', [])
            
            # Filter by incident type if specified
            if incident_type:
                contexts = [c for c in contexts if c.get('incident_type') == incident_type]
            
            # Calculate similarities
            similarities = []
            for context in contexts:
                if 'embedding' in context:
                    context_embedding = np.array(context['embedding'])
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        context_embedding.reshape(1, -1)
                    )[0][0]
                    
                    context['similarity_score'] = float(similarity)
                    similarities.append(context)
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similarities
            
        except Exception as e:
            print(f"Error finding similar contexts: {e}")
            return []
    
    def _identify_patterns(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common patterns from similar incidents"""
        patterns = []
        
        # Group by root cause
        root_cause_groups = {}
        for ctx in contexts[:10]:  # Analyze top 10
            root_cause = ctx.get('root_cause', 'unknown')
            if root_cause not in root_cause_groups:
                root_cause_groups[root_cause] = []
            root_cause_groups[root_cause].append(ctx)
        
        # Find patterns
        for root_cause, group in root_cause_groups.items():
            if len(group) >= 2:  # Pattern needs at least 2 occurrences
                patterns.append({
                    'pattern': f"Frequent root cause: {root_cause}",
                    'occurrences': len(group),
                    'avg_effectiveness': np.mean([g.get('effectiveness', 0) for g in group]),
                    'common_symptoms': self._extract_common_symptoms(group)
                })
        
        return sorted(patterns, key=lambda x: x['occurrences'], reverse=True)
    
    def _extract_common_symptoms(self, contexts: List[Dict[str, Any]]) -> List[str]:
        """Extract common symptoms from a group of contexts"""
        all_symptoms = []
        for ctx in contexts:
            if ctx.get('metadata') and ctx['metadata'].get('symptoms'):
                all_symptoms.extend(ctx['metadata']['symptoms'])
        
        # Count occurrences
        symptom_counts = {}
        for symptom in all_symptoms:
            symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        
        # Return symptoms that appear in >50% of contexts
        threshold = len(contexts) / 2
        return [s for s, count in symptom_counts.items() if count >= threshold]


class ContextualRecommender:
    """Provide contextual recommendations based on feedback"""
    
    def __init__(self):
        self.enhancer = ContextEnhancer()
    
    def get_recommendations(self, incident: Dict[str, Any], initial_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations based on context and initial analysis"""
        enhanced_context = self.enhancer.get_enhanced_context(incident)
        
        recommendations = {
            'confidence_level': self._calculate_confidence(initial_analysis, enhanced_context),
            'additional_checks': [],
            'alternative_causes': [],
            'preventive_actions': [],
            'similar_incident_resolutions': []
        }
        
        # Add additional checks based on historical data
        if enhanced_context['things_to_check']:
            recommendations['additional_checks'] = [
                {
                    'check': check,
                    'reason': 'Historically important for similar incidents'
                }
                for check in enhanced_context['things_to_check'][:5]
            ]
        
        # Suggest alternative root causes
        for resolution in enhanced_context['historical_resolutions'][:3]:
            if resolution['similarity_score'] > 0.8:
                recommendations['alternative_causes'].append({
                    'cause': resolution['root_cause'],
                    'confidence': resolution['similarity_score'],
                    'historical_effectiveness': 'High'
                })
        
        # Add preventive actions
        recommendations['preventive_actions'] = enhanced_context['recommended_actions'][:5]
        
        # Include similar incident resolutions
        recommendations['similar_incident_resolutions'] = [
            {
                'root_cause': r['root_cause'],
                'resolution': r['resolution'],
                'similarity': f"{r['similarity_score']*100:.0f}%"
            }
            for r in enhanced_context['historical_resolutions'][:3]
        ]
        
        return recommendations
    
    def _calculate_confidence(self, initial_analysis: Dict[str, Any], enhanced_context: Dict[str, Any]) -> str:
        """Calculate confidence level based on analysis and context"""
        base_confidence = initial_analysis.get('confidence', 0.7)
        boost = enhanced_context.get('confidence_boost', 0)
        
        final_confidence = min(0.95, base_confidence + boost)
        
        if final_confidence >= 0.9:
            return 'Very High'
        elif final_confidence >= 0.8:
            return 'High'
        elif final_confidence >= 0.7:
            return 'Medium'
        else:
            return 'Low'