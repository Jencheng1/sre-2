#!/usr/bin/env python3
"""
Multi-Source Knowledge Base Search Module
Integrates all MCP external data sources for comprehensive incident analysis
"""

import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

class MultiSourceKnowledgeSearch:
    """
    Searches across multiple knowledge sources including:
    - Fed Launch Pad Pro (Fed LPP)
    - FedSearch
    - Stack Overflow Enterprise
    - GitHub Knowledge Base
    - AWS Knowledge Base (DynamoDB)
    """
    
    def __init__(self):
        self.sources = {
            'fed_lpp': {
                'name': 'Fed Launch Pad Pro',
                'base_url': 'http://localhost:9087',
                'enabled': True
            },
            'fedsearch': {
                'name': 'FedSearch',
                'base_url': 'http://localhost:9088',
                'enabled': True
            },
            'stackoverflow': {
                'name': 'Stack Overflow Enterprise',
                'base_url': 'http://localhost:9089',
                'enabled': True
            },
            'github_kb': {
                'name': 'GitHub Knowledge Base',
                'base_url': 'http://localhost:9090',
                'enabled': True
            }
        }
        
        self.search_timeout = 10  # seconds
        
    def multi_search_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive multi-source search for incident analysis
        """
        start_time = time.time()
        
        # Extract search parameters from incident
        search_params = self._extract_search_params(incident_data)
        
        # Initialize results
        results = {
            'incident_id': incident_data.get('id', 'unknown'),
            'search_params': search_params,
            'sources_searched': [],
            'total_results': 0,
            'search_results': {},
            'consolidated_insights': {},
            'recommendations': [],
            'search_metadata': {
                'start_time': datetime.now().isoformat(),
                'sources_available': len([s for s in self.sources.values() if s['enabled']])
            }
        }
        
        # Perform parallel searches across all sources
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            
            # Submit search tasks
            for source_key, source_config in self.sources.items():
                if source_config['enabled']:
                    future = executor.submit(
                        self._search_source,
                        source_key,
                        source_config,
                        search_params
                    )
                    future_to_source[future] = source_key
            
            # Collect results
            for future in as_completed(future_to_source):
                source_key = future_to_source[future]
                try:
                    source_results = future.result()
                    if source_results:
                        results['search_results'][source_key] = source_results
                        results['sources_searched'].append(source_key)
                        results['total_results'] += source_results.get('count', 0)
                except Exception as e:
                    logger.error(f"Error searching {source_key}: {str(e)}")
                    results['search_results'][source_key] = {
                        'error': str(e),
                        'status': 'failed'
                    }
        
        # Consolidate insights from all sources
        results['consolidated_insights'] = self._consolidate_insights(results['search_results'])
        
        # Generate AI-powered recommendations
        results['recommendations'] = self._generate_recommendations(
            incident_data,
            results['search_results'],
            results['consolidated_insights']
        )
        
        # Add execution time
        results['search_metadata']['execution_time'] = time.time() - start_time
        
        return results
    
    def _extract_search_params(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant search parameters from incident data"""
        description = incident_data.get('description', '')
        title = incident_data.get('title', '')
        
        # Extract keywords
        keywords = self._extract_keywords(f"{title} {description}")
        
        # Determine incident type
        incident_type = self._determine_incident_type(description)
        
        # Extract technical components
        components = self._extract_components(description)
        
        return {
            'query': f"{title} {description}"[:200],  # Limit query length
            'keywords': keywords,
            'incident_type': incident_type,
            'components': components,
            'severity': incident_data.get('severity', 'Medium'),
            'timestamp': incident_data.get('created_time', datetime.now().isoformat())
        }
    
    def _search_source(self, source_key: str, source_config: Dict, 
                      search_params: Dict) -> Optional[Dict[str, Any]]:
        """Search a specific knowledge source"""
        try:
            if source_key == 'fed_lpp':
                return self._search_fed_lpp(source_config, search_params)
            elif source_key == 'fedsearch':
                return self._search_fedsearch(source_config, search_params)
            elif source_key == 'stackoverflow':
                return self._search_stackoverflow(source_config, search_params)
            elif source_key == 'github_kb':
                return self._search_github_kb(source_config, search_params)
            else:
                return None
        except Exception as e:
            logger.error(f"Search error for {source_key}: {str(e)}")
            return {'error': str(e), 'count': 0}
    
    def _search_fed_lpp(self, config: Dict, params: Dict) -> Dict[str, Any]:
        """Search Fed Launch Pad Pro"""
        try:
            # Search federal knowledge
            response = requests.post(
                f"{config['base_url']}/fedlpp/search",
                json={
                    'query': params['query'],
                    'domains': ['federal_regulations', 'compliance_policies', 'security_protocols'],
                    'filters': {'min_relevance': 0.5}
                },
                timeout=self.search_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Also analyze for compliance
                compliance_response = requests.post(
                    f"{config['base_url']}/fedlpp/analyze-incident",
                    json={
                        'incident_id': params.get('incident_id', 'temp'),
                        'incident_data': {
                            'description': params['query'],
                            'type': params['incident_type']
                        }
                    },
                    timeout=self.search_timeout
                )
                
                compliance_data = {}
                if compliance_response.status_code == 200:
                    compliance_data = compliance_response.json()
                
                return {
                    'source': 'Fed Launch Pad Pro',
                    'count': data.get('total_results', 0),
                    'results': data.get('results', [])[:5],  # Top 5
                    'insights': data.get('insights', {}),
                    'compliance_analysis': compliance_data.get('compliance_analysis', {}),
                    'federal_requirements': compliance_data.get('federal_knowledge_matches', [])
                }
            
        except Exception as e:
            logger.error(f"Fed LPP search error: {str(e)}")
        
        return {'error': 'Search failed', 'count': 0}
    
    def _search_fedsearch(self, config: Dict, params: Dict) -> Dict[str, Any]:
        """Search FedSearch"""
        try:
            # Perform intelligent federal search
            response = requests.post(
                f"{config['base_url']}/fedsearch/search",
                json={
                    'query': params['query'],
                    'search_type': 'hybrid',  # Use hybrid search
                    'sources': ['NIST', 'CISA', 'GAO', 'OPM'],
                    'filters': {}
                },
                timeout=self.search_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Also get compliance mapping
                compliance_response = requests.post(
                    f"{config['base_url']}/fedsearch/compliance-mapping",
                    json={
                        'incident_data': {
                            'description': params['query'],
                            'type': params['incident_type']
                        },
                        'system_description': ' '.join(params.get('components', [])),
                        'frameworks': ['NIST', 'FISMA', 'FedRAMP']
                    },
                    timeout=self.search_timeout
                )
                
                compliance_mapping = {}
                if compliance_response.status_code == 200:
                    compliance_mapping = compliance_response.json()
                
                return {
                    'source': 'FedSearch',
                    'count': data.get('total_results', 0),
                    'results': data.get('results', [])[:5],
                    'insights': data.get('insights', {}),
                    'compliance_mapping': compliance_mapping.get('compliance_mapping', {}),
                    'compliance_scores': compliance_mapping.get('compliance_scores', {})
                }
            
        except Exception as e:
            logger.error(f"FedSearch error: {str(e)}")
        
        return {'error': 'Search failed', 'count': 0}
    
    def _search_stackoverflow(self, config: Dict, params: Dict) -> Dict[str, Any]:
        """Search Stack Overflow Enterprise"""
        try:
            # Search for technical solutions
            response = requests.post(
                f"{config['base_url']}/so/search",
                json={
                    'query': params['query'],
                    'tags': self._map_components_to_tags(params.get('components', [])),
                    'min_score': 5
                },
                timeout=self.search_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Get specific solutions for incident
                solutions_response = requests.post(
                    f"{config['base_url']}/so/solutions",
                    json={
                        'description': params['query'],
                        'type': params['incident_type']
                    },
                    timeout=self.search_timeout
                )
                
                solutions = {}
                if solutions_response.status_code == 200:
                    solutions = solutions_response.json()
                
                return {
                    'source': 'Stack Overflow Enterprise',
                    'count': data.get('total_results', 0),
                    'results': data.get('results', [])[:5],
                    'solutions': solutions.get('solutions', [])[:3],
                    'confidence_score': solutions.get('confidence_score', 0),
                    'code_snippets': self._get_relevant_code_snippets(config, params)
                }
            
        except Exception as e:
            logger.error(f"Stack Overflow search error: {str(e)}")
        
        return {'error': 'Search failed', 'count': 0}
    
    def _search_github_kb(self, config: Dict, params: Dict) -> Dict[str, Any]:
        """Search GitHub Knowledge Base"""
        try:
            # Search GitHub KB
            response = requests.post(
                f"{config['base_url']}/github/search",
                json={
                    'query': params['query'],
                    'types': ['issue', 'discussion', 'wiki'],
                    'labels': ['incident', 'runbook', 'postmortem']
                },
                timeout=self.search_timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Search for similar postmortems
                postmortem_response = requests.post(
                    f"{config['base_url']}/github/postmortems",
                    json={
                        'description': params['query'],
                        'type': params['incident_type']
                    },
                    timeout=self.search_timeout
                )
                
                postmortems = {}
                if postmortem_response.status_code == 200:
                    postmortems = postmortem_response.json()
                
                # Get relevant runbooks
                runbooks = self._get_runbooks(config, params)
                
                return {
                    'source': 'GitHub Knowledge Base',
                    'count': data.get('total_results', 0),
                    'results': data.get('results', [])[:5],
                    'similar_postmortems': postmortems.get('similar_postmortems', [])[:3],
                    'key_learnings': postmortems.get('key_learnings', []),
                    'runbooks': runbooks
                }
            
        except Exception as e:
            logger.error(f"GitHub KB search error: {str(e)}")
        
        return {'error': 'Search failed', 'count': 0}
    
    def _consolidate_insights(self, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate insights from all search results"""
        consolidated = {
            'common_patterns': [],
            'technical_solutions': [],
            'compliance_requirements': [],
            'best_practices': [],
            'historical_precedents': [],
            'confidence_score': 0.0
        }
        
        # Extract patterns
        all_keywords = []
        
        for source, results in search_results.items():
            if 'error' not in results:
                # Collect keywords and patterns
                if 'insights' in results:
                    insights = results['insights']
                    if 'key_themes' in insights:
                        all_keywords.extend(insights['key_themes'])
                
                # Collect technical solutions
                if 'solutions' in results:
                    consolidated['technical_solutions'].extend(results['solutions'][:2])
                
                # Collect compliance requirements
                if 'compliance_analysis' in results:
                    consolidated['compliance_requirements'].append({
                        'source': source,
                        'requirements': results['compliance_analysis']
                    })
                
                # Collect postmortems
                if 'similar_postmortems' in results:
                    consolidated['historical_precedents'].extend(
                        results['similar_postmortems'][:2]
                    )
        
        # Find common patterns
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        consolidated['common_patterns'] = [
            k for k, v in sorted(keyword_counts.items(), 
                               key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Calculate overall confidence
        total_results = sum(
            r.get('count', 0) for r in search_results.values() 
            if 'error' not in r
        )
        
        if total_results > 50:
            consolidated['confidence_score'] = 0.9
        elif total_results > 20:
            consolidated['confidence_score'] = 0.7
        elif total_results > 10:
            consolidated['confidence_score'] = 0.5
        else:
            consolidated['confidence_score'] = 0.3
        
        return consolidated
    
    def _generate_recommendations(self, incident_data: Dict, 
                                search_results: Dict, 
                                insights: Dict) -> List[str]:
        """Generate AI-powered recommendations based on search results"""
        recommendations = []
        
        # Technical recommendations from Stack Overflow
        so_results = search_results.get('stackoverflow', {})
        if so_results.get('confidence_score', 0) > 0.7:
            recommendations.append(
                "🔧 High-confidence technical solutions found in Stack Overflow - review top solutions"
            )
        
        # Compliance recommendations from federal sources
        fed_compliance = any(
            'compliance' in r 
            for r in search_results.get('fed_lpp', {}).get('results', [])
        )
        if fed_compliance:
            recommendations.append(
                "📋 Federal compliance implications detected - review NIST/FISMA requirements"
            )
        
        # Historical pattern recommendations
        if insights.get('historical_precedents'):
            recommendations.append(
                "📚 Similar incidents found in historical data - review post-mortems for lessons learned"
            )
        
        # Runbook recommendations
        github_results = search_results.get('github_kb', {})
        if github_results.get('runbooks'):
            recommendations.append(
                "📖 Relevant runbooks available - follow established procedures"
            )
        
        # Pattern-based recommendations
        patterns = insights.get('common_patterns', [])
        if 'timeout' in patterns:
            recommendations.append(
                "⏱️ Timeout pattern detected - check connection pools and service latency"
            )
        if 'memory' in patterns:
            recommendations.append(
                "💾 Memory issues detected - analyze heap dumps and resource usage"
            )
        if 'authentication' in patterns:
            recommendations.append(
                "🔐 Authentication issues detected - verify credentials and token validity"
            )
        
        # Severity-based recommendations
        if incident_data.get('severity') == 'Critical':
            recommendations.insert(0, 
                "🚨 CRITICAL: Engage incident commander and follow escalation procedures"
            )
        
        return recommendations
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        import re
        
        # Convert to lowercase and extract words
        words = re.findall(r'\w+', text.lower())
        
        # Technical keywords to look for
        tech_keywords = {
            'api', 'database', 'connection', 'timeout', 'error', 'failure',
            'authentication', 'authorization', 'ssl', 'certificate', 'memory',
            'cpu', 'performance', 'latency', 'throughput', 'gateway', 'service',
            'cache', 'queue', 'pool', 'leak', 'deadlock', 'race', 'condition'
        }
        
        # Filter for technical keywords
        keywords = [w for w in words if w in tech_keywords]
        
        # Add service names
        service_patterns = [
            'lambda', 'ec2', 's3', 'rds', 'dynamodb', 'sqs', 'sns',
            'kubernetes', 'docker', 'nginx', 'apache', 'redis', 'postgres'
        ]
        
        for pattern in service_patterns:
            if pattern in text.lower():
                keywords.append(pattern)
        
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def _determine_incident_type(self, description: str) -> str:
        """Determine incident type from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['timeout', 'slow', 'latency']):
            return 'performance'
        elif any(word in desc_lower for word in ['auth', 'unauthorized', 'forbidden']):
            return 'security'
        elif any(word in desc_lower for word in ['down', 'unavailable', 'outage']):
            return 'availability'
        elif any(word in desc_lower for word in ['memory', 'heap', 'oom']):
            return 'resource'
        elif any(word in desc_lower for word in ['connection', 'pool', 'socket']):
            return 'connectivity'
        else:
            return 'general'
    
    def _extract_components(self, description: str) -> List[str]:
        """Extract system components from description"""
        components = []
        desc_lower = description.lower()
        
        # Component patterns
        component_map = {
            'api': ['api', 'endpoint', 'rest'],
            'database': ['database', 'db', 'sql', 'query'],
            'cache': ['cache', 'redis', 'memcached'],
            'queue': ['queue', 'sqs', 'rabbitmq', 'kafka'],
            'authentication': ['auth', 'login', 'sso', 'oauth'],
            'gateway': ['gateway', 'proxy', 'loadbalancer', 'lb'],
            'storage': ['s3', 'storage', 'file', 'blob'],
            'compute': ['ec2', 'instance', 'server', 'vm']
        }
        
        for component, patterns in component_map.items():
            if any(pattern in desc_lower for pattern in patterns):
                components.append(component)
        
        return components
    
    def _map_components_to_tags(self, components: List[str]) -> List[str]:
        """Map components to Stack Overflow tags"""
        tag_map = {
            'api': ['rest-api', 'api', 'web-services'],
            'database': ['database', 'sql', 'nosql'],
            'cache': ['caching', 'redis', 'memcached'],
            'queue': ['message-queue', 'rabbitmq', 'kafka'],
            'authentication': ['authentication', 'oauth', 'jwt'],
            'gateway': ['api-gateway', 'reverse-proxy', 'load-balancing'],
            'storage': ['amazon-s3', 'file-storage', 'object-storage'],
            'compute': ['ec2', 'virtual-machine', 'cloud-computing']
        }
        
        tags = []
        for component in components:
            if component in tag_map:
                tags.extend(tag_map[component])
        
        return list(set(tags))[:5]  # Return top 5 unique tags
    
    def _get_relevant_code_snippets(self, config: Dict, params: Dict) -> List[Dict]:
        """Get relevant code snippets from Stack Overflow"""
        try:
            response = requests.post(
                f"{config['base_url']}/so/code-snippets",
                json={
                    'issue': params['query'][:100],
                    'language': 'python'  # Default to Python
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('snippets', [])[:2]  # Return top 2 snippets
            
        except Exception as e:
            logger.error(f"Code snippet retrieval error: {str(e)}")
        
        return []
    
    def _get_runbooks(self, config: Dict, params: Dict) -> List[Dict]:
        """Get relevant runbooks from GitHub KB"""
        try:
            # Use incident type for runbook search
            scenario = params.get('incident_type', 'general')
            
            response = requests.get(
                f"{config['base_url']}/github/runbooks",
                params={'scenario': scenario},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('runbooks', [])[:2]  # Return top 2 runbooks
            
        except Exception as e:
            logger.error(f"Runbook retrieval error: {str(e)}")
        
        return []


def search_all_knowledge_sources(incident_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to search all knowledge sources for an incident
    """
    searcher = MultiSourceKnowledgeSearch()
    return searcher.multi_search_incident(incident_data)