"""
Defect-Incident Correlation Engine
Advanced correlation logic between incidents and defects from ALM Octane and Jira
"""

import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
from dataclasses import dataclass
from enum import Enum

class CorrelationStrength(Enum):
    NONE = 0.0
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9

@dataclass
class CorrelationResult:
    """Represents the result of incident-defect correlation"""
    incident_id: str
    defect_id: str
    defect_source: str  # 'alm_octane' or 'jira'
    correlation_score: float
    correlation_factors: Dict[str, float]
    evidence: List[str]
    recommendations: List[str]
    confidence_level: str

class DefectIncidentCorrelator:
    """Advanced correlation engine for incidents and defects"""
    
    def __init__(self, mcp_endpoints: Dict[str, str]):
        self.mcp_endpoints = mcp_endpoints
        self.logger = logging.getLogger(__name__)
        
        # Technical keyword mappings for better correlation
        self.keyword_categories = {
            'database': ['database', 'db', 'sql', 'connection', 'pool', 'transaction', 'deadlock', 'timeout'],
            'api': ['api', 'rest', 'endpoint', 'gateway', 'service', 'microservice', 'http', 'request'],
            'authentication': ['auth', 'login', 'token', 'session', 'oauth', 'sso', 'authentication', 'authorization'],
            'performance': ['performance', 'slow', 'latency', 'response', 'cpu', 'memory', 'disk', 'network'],
            'security': ['security', 'vulnerability', 'ssl', 'certificate', 'encryption', 'breach', 'attack'],
            'infrastructure': ['server', 'infrastructure', 'deployment', 'configuration', 'environment', 'cluster'],
            'integration': ['integration', 'third-party', 'external', 'webhook', 'callback', 'sync'],
            'ui': ['ui', 'frontend', 'user interface', 'browser', 'javascript', 'css', 'rendering'],
            'data': ['data', 'processing', 'etl', 'pipeline', 'batch', 'stream', 'queue', 'message']
        }
        
        # Severity mapping for correlation
        self.severity_weights = {
            'critical': 1.0,
            'blocker': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # Status weights (open/active issues are more relevant)
        self.status_weights = {
            'new': 1.0,
            'open': 1.0,
            'in progress': 0.9,
            'in_progress': 0.9,
            'reopened': 0.8,
            'resolved': 0.3,
            'fixed': 0.3,
            'closed': 0.2,
            'done': 0.2
        }
    
    def correlate_incident_with_defects(self, incident_data: Dict[str, Any]) -> List[CorrelationResult]:
        """Main correlation function that processes an incident against all defects"""
        correlation_results = []
        
        # Extract incident features
        incident_features = self._extract_incident_features(incident_data)
        
        # Get defects from ALM Octane
        octane_defects = self._fetch_octane_defects()
        for defect in octane_defects:
            result = self._correlate_with_single_defect(incident_features, defect, 'alm_octane')
            if result.correlation_score >= CorrelationStrength.WEAK.value:
                correlation_results.append(result)
        
        # Get issues from Jira
        jira_issues = self._fetch_jira_issues()
        for issue in jira_issues:
            result = self._correlate_with_single_issue(incident_features, issue, 'jira')
            if result.correlation_score >= CorrelationStrength.WEAK.value:
                correlation_results.append(result)
        
        # Sort by correlation score
        correlation_results.sort(key=lambda x: x.correlation_score, reverse=True)
        
        return correlation_results
    
    def _extract_incident_features(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from incident data for correlation"""
        title = incident_data.get('title', '').lower()
        description = incident_data.get('description', '').lower()
        severity = incident_data.get('severity', 'medium').lower()
        affected_services = incident_data.get('affected_services', [])
        
        # Extract keywords by category
        categorized_keywords = {}
        full_text = f"{title} {description}".lower()
        
        for category, keywords in self.keyword_categories.items():
            found_keywords = []
            for keyword in keywords:
                if keyword in full_text:
                    found_keywords.append(keyword)
            categorized_keywords[category] = found_keywords
        
        # Extract technical patterns
        patterns = self._extract_technical_patterns(full_text)
        
        # Extract error codes and numbers
        error_codes = re.findall(r'\b[4-5]\d{2}\b', full_text)  # HTTP error codes
        numbers = re.findall(r'\b\d+(?:\.\d+)?\s*(?:ms|sec|min|hour|%|gb|mb|kb)\b', full_text)
        
        return {
            'title': title,
            'description': description,
            'severity': severity,
            'affected_services': [s.lower() for s in affected_services],
            'categorized_keywords': categorized_keywords,
            'technical_patterns': patterns,
            'error_codes': error_codes,
            'numeric_values': numbers,
            'timestamp': incident_data.get('timestamp', datetime.now().isoformat())
        }
    
    def _extract_technical_patterns(self, text: str) -> List[str]:
        """Extract common technical patterns from text"""
        patterns = []
        
        # Common error patterns
        if re.search(r'timeout|timed out', text):
            patterns.append('timeout_pattern')
        if re.search(r'connection.*(?:refused|reset|failed)', text):
            patterns.append('connection_failure')
        if re.search(r'memory.*(?:leak|exhausted|out of)', text):
            patterns.append('memory_issue')
        if re.search(r'cpu.*(?:high|spike|100%)', text):
            patterns.append('cpu_issue')
        if re.search(r'disk.*(?:full|space|io)', text):
            patterns.append('disk_issue')
        if re.search(r'network.*(?:latency|packet|loss)', text):
            patterns.append('network_issue')
        if re.search(r'ssl.*(?:certificate|handshake|expired)', text):
            patterns.append('ssl_issue')
        if re.search(r'authentication.*(?:failed|error|invalid)', text):
            patterns.append('auth_failure')
        if re.search(r'database.*(?:lock|deadlock|slow)', text):
            patterns.append('database_issue')
        
        return patterns
    
    def _fetch_octane_defects(self) -> List[Dict[str, Any]]:
        """Fetch defects from ALM Octane"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['alm_octane']}/octane/defects",
                params={'status': 'all', 'limit': 100},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching ALM Octane defects: {e}")
        return []
    
    def _fetch_jira_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues from Jira"""
        try:
            response = requests.get(
                f"{self.mcp_endpoints['jira']}/jira/issues",
                params={'issue_type': 'Bug', 'status': 'all', 'limit': 100},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching Jira issues: {e}")
        return []
    
    def _correlate_with_single_defect(self, incident_features: Dict[str, Any], 
                                    defect: Dict[str, Any], source: str) -> CorrelationResult:
        """Correlate incident with a single ALM Octane defect"""
        correlation_factors = {}
        evidence = []
        recommendations = []
        
        # Extract defect features
        defect_name = defect.get('name', '').lower()
        defect_desc = defect.get('description', '').lower()
        defect_severity = defect.get('severity', 'medium').lower()
        defect_status = defect.get('status', 'new').lower()
        defect_component = defect.get('component', '').lower()
        defect_created = defect.get('created_date', '')
        
        # 1. Textual similarity correlation
        text_similarity = self._calculate_text_similarity(
            incident_features, defect_name, defect_desc
        )
        correlation_factors['text_similarity'] = text_similarity
        if text_similarity > 0.5:
            evidence.append(f"High textual similarity with defect description")
        
        # 2. Keyword category correlation
        keyword_correlation = self._calculate_keyword_correlation(
            incident_features['categorized_keywords'], f"{defect_name} {defect_desc}"
        )
        correlation_factors['keyword_correlation'] = keyword_correlation
        if keyword_correlation > 0.6:
            evidence.append(f"Strong keyword overlap in technical categories")
        
        # 3. Component/service correlation
        component_correlation = self._calculate_component_correlation(
            incident_features['affected_services'], defect_component
        )
        correlation_factors['component_correlation'] = component_correlation
        if component_correlation > 0.5:
            evidence.append(f"Component overlap with affected services")
        
        # 4. Severity correlation
        severity_correlation = self._calculate_severity_correlation(
            incident_features['severity'], defect_severity
        )
        correlation_factors['severity_correlation'] = severity_correlation
        
        # 5. Temporal correlation
        temporal_correlation = self._calculate_temporal_correlation(
            incident_features['timestamp'], defect_created
        )
        correlation_factors['temporal_correlation'] = temporal_correlation
        if temporal_correlation > 0.7:
            evidence.append(f"Defect created recently before incident")
        
        # 6. Technical pattern correlation
        pattern_correlation = self._calculate_pattern_correlation(
            incident_features['technical_patterns'], f"{defect_name} {defect_desc}"
        )
        correlation_factors['pattern_correlation'] = pattern_correlation
        if pattern_correlation > 0.5:
            evidence.append(f"Similar technical patterns detected")
        
        # 7. Status relevance
        status_weight = self.status_weights.get(defect_status, 0.5)
        correlation_factors['status_relevance'] = status_weight
        if status_weight > 0.8:
            evidence.append(f"Defect is currently {defect_status} - highly relevant")
        
        # Calculate overall correlation score
        weights = {
            'text_similarity': 0.25,
            'keyword_correlation': 0.20,
            'component_correlation': 0.15,
            'severity_correlation': 0.10,
            'temporal_correlation': 0.15,
            'pattern_correlation': 0.10,
            'status_relevance': 0.05
        }
        
        correlation_score = sum(
            correlation_factors[factor] * weight
            for factor, weight in weights.items()
            if factor in correlation_factors
        )
        
        # Generate recommendations
        recommendations = self._generate_defect_recommendations(
            defect, correlation_score, correlation_factors
        )
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(correlation_score)
        
        return CorrelationResult(
            incident_id=incident_features.get('incident_id', 'unknown'),
            defect_id=defect.get('id', 'unknown'),
            defect_source=source,
            correlation_score=correlation_score,
            correlation_factors=correlation_factors,
            evidence=evidence,
            recommendations=recommendations,
            confidence_level=confidence_level
        )
    
    def _correlate_with_single_issue(self, incident_features: Dict[str, Any], 
                                   issue: Dict[str, Any], source: str) -> CorrelationResult:
        """Correlate incident with a single Jira issue"""
        correlation_factors = {}
        evidence = []
        recommendations = []
        
        # Extract issue features
        issue_summary = issue.get('summary', '').lower()
        issue_desc = issue.get('description', '').lower()
        issue_priority = issue.get('priority', {}).get('name', 'medium').lower()
        issue_status = issue.get('status', {}).get('name', 'open').lower()
        issue_project = issue.get('project', {}).get('key', '').lower()
        issue_created = issue.get('created', '')
        
        # Similar correlation logic as defects but adapted for Jira structure
        text_similarity = self._calculate_text_similarity(
            incident_features, issue_summary, issue_desc
        )
        correlation_factors['text_similarity'] = text_similarity
        
        keyword_correlation = self._calculate_keyword_correlation(
            incident_features['categorized_keywords'], f"{issue_summary} {issue_desc}"
        )
        correlation_factors['keyword_correlation'] = keyword_correlation
        
        component_correlation = self._calculate_component_correlation(
            incident_features['affected_services'], issue_project
        )
        correlation_factors['component_correlation'] = component_correlation
        
        severity_correlation = self._calculate_severity_correlation(
            incident_features['severity'], issue_priority
        )
        correlation_factors['severity_correlation'] = severity_correlation
        
        temporal_correlation = self._calculate_temporal_correlation(
            incident_features['timestamp'], issue_created
        )
        correlation_factors['temporal_correlation'] = temporal_correlation
        
        pattern_correlation = self._calculate_pattern_correlation(
            incident_features['technical_patterns'], f"{issue_summary} {issue_desc}"
        )
        correlation_factors['pattern_correlation'] = pattern_correlation
        
        status_weight = self.status_weights.get(issue_status.replace(' ', '_'), 0.5)
        correlation_factors['status_relevance'] = status_weight
        
        # Calculate correlation score (same weights as defects)
        weights = {
            'text_similarity': 0.25,
            'keyword_correlation': 0.20,
            'component_correlation': 0.15,
            'severity_correlation': 0.10,
            'temporal_correlation': 0.15,
            'pattern_correlation': 0.10,
            'status_relevance': 0.05
        }
        
        correlation_score = sum(
            correlation_factors[factor] * weight
            for factor, weight in weights.items()
            if factor in correlation_factors
        )
        
        # Generate evidence
        if text_similarity > 0.5:
            evidence.append(f"High textual similarity with issue summary/description")
        if keyword_correlation > 0.6:
            evidence.append(f"Strong keyword overlap in technical categories")
        if temporal_correlation > 0.7:
            evidence.append(f"Issue created recently before incident")
        if status_weight > 0.8:
            evidence.append(f"Issue is currently {issue_status} - highly relevant")
        
        recommendations = self._generate_jira_recommendations(
            issue, correlation_score, correlation_factors
        )
        
        confidence_level = self._determine_confidence_level(correlation_score)
        
        return CorrelationResult(
            incident_id=incident_features.get('incident_id', 'unknown'),
            defect_id=issue.get('key', 'unknown'),
            defect_source=source,
            correlation_score=correlation_score,
            correlation_factors=correlation_factors,
            evidence=evidence,
            recommendations=recommendations,
            confidence_level=confidence_level
        )
    
    def _calculate_text_similarity(self, incident_features: Dict[str, Any], 
                                 defect_title: str, defect_desc: str) -> float:
        """Calculate text similarity between incident and defect"""
        incident_text = f"{incident_features['title']} {incident_features['description']}"
        defect_text = f"{defect_title} {defect_desc}"
        
        # Simple word overlap similarity
        incident_words = set(incident_text.split())
        defect_words = set(defect_text.split())
        
        if not incident_words or not defect_words:
            return 0.0
        
        intersection = incident_words.intersection(defect_words)
        union = incident_words.union(defect_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_keyword_correlation(self, incident_keywords: Dict[str, List[str]], 
                                     defect_text: str) -> float:
        """Calculate correlation based on categorized keywords"""
        total_score = 0.0
        total_categories = len(incident_keywords)
        
        for category, keywords in incident_keywords.items():
            if keywords:  # If incident has keywords in this category
                category_score = 0.0
                for keyword in keywords:
                    if keyword in defect_text:
                        category_score += 1.0
                
                # Normalize by number of keywords in category
                category_score = category_score / len(keywords)
                total_score += category_score
        
        return total_score / total_categories if total_categories > 0 else 0.0
    
    def _calculate_component_correlation(self, affected_services: List[str], 
                                       defect_component: str) -> float:
        """Calculate correlation based on component/service overlap"""
        if not affected_services or not defect_component:
            return 0.0
        
        defect_component_lower = defect_component.lower()
        
        # Check for direct matches or substring matches
        matches = 0
        for service in affected_services:
            if service in defect_component_lower or defect_component_lower in service:
                matches += 1
        
        return matches / len(affected_services)
    
    def _calculate_severity_correlation(self, incident_severity: str, defect_severity: str) -> float:
        """Calculate correlation based on severity alignment"""
        incident_weight = self.severity_weights.get(incident_severity, 0.5)
        defect_weight = self.severity_weights.get(defect_severity, 0.5)
        
        # Perfect match = 1.0, close match = 0.8, etc.
        diff = abs(incident_weight - defect_weight)
        
        if diff == 0.0:
            return 1.0
        elif diff <= 0.2:
            return 0.8
        elif diff <= 0.4:
            return 0.6
        else:
            return 0.2
    
    def _calculate_temporal_correlation(self, incident_timestamp: str, defect_created: str) -> float:
        """Calculate temporal correlation between incident and defect creation"""
        try:
            # Parse timestamps
            incident_dt = datetime.fromisoformat(incident_timestamp.replace('Z', '+00:00'))
            defect_dt = datetime.fromisoformat(defect_created.replace('Z', '+00:00'))
            
            # Calculate days difference
            days_diff = (incident_dt - defect_dt).days
            
            # Higher correlation for defects created recently before incident
            if days_diff < 0:  # Defect created after incident
                return 0.1
            elif days_diff <= 1:
                return 1.0
            elif days_diff <= 7:
                return 0.8
            elif days_diff <= 30:
                return 0.6
            elif days_diff <= 90:
                return 0.4
            else:
                return 0.2
        except:
            return 0.5  # Default if timestamp parsing fails
    
    def _calculate_pattern_correlation(self, incident_patterns: List[str], defect_text: str) -> float:
        """Calculate correlation based on technical patterns"""
        if not incident_patterns:
            return 0.0
        
        matches = 0
        for pattern in incident_patterns:
            # Check if pattern indicators exist in defect text
            if pattern == 'timeout_pattern' and ('timeout' in defect_text or 'timed out' in defect_text):
                matches += 1
            elif pattern == 'connection_failure' and 'connection' in defect_text:
                matches += 1
            elif pattern == 'memory_issue' and 'memory' in defect_text:
                matches += 1
            elif pattern == 'cpu_issue' and 'cpu' in defect_text:
                matches += 1
            # Add more pattern matching logic as needed
        
        return matches / len(incident_patterns)
    
    def _generate_defect_recommendations(self, defect: Dict[str, Any], 
                                       correlation_score: float, 
                                       correlation_factors: Dict[str, float]) -> List[str]:
        """Generate recommendations based on defect correlation"""
        recommendations = []
        
        if correlation_score >= CorrelationStrength.STRONG.value:
            recommendations.append(f"🚨 HIGH PRIORITY: Review ALM Octane defect {defect.get('id')} immediately")
            recommendations.append(f"🔧 Check if defect {defect.get('id')} has pending fixes or workarounds")
            
            if defect.get('status', '').lower() in ['new', 'in progress']:
                recommendations.append(f"⚡ Expedite resolution of defect {defect.get('id')} - directly related to incident")
        
        elif correlation_score >= CorrelationStrength.MODERATE.value:
            recommendations.append(f"🔍 Investigate potential relationship with ALM Octane defect {defect.get('id')}")
            recommendations.append(f"📊 Compare incident symptoms with defect {defect.get('id')} details")
        
        if correlation_factors.get('temporal_correlation', 0) > 0.7:
            recommendations.append(f"⏰ Recent defect creation suggests possible causal relationship")
        
        if correlation_factors.get('component_correlation', 0) > 0.5:
            recommendations.append(f"🏗️ Component overlap detected - review {defect.get('component')} architecture")
        
        return recommendations
    
    def _generate_jira_recommendations(self, issue: Dict[str, Any], 
                                     correlation_score: float, 
                                     correlation_factors: Dict[str, float]) -> List[str]:
        """Generate recommendations based on Jira issue correlation"""
        recommendations = []
        
        if correlation_score >= CorrelationStrength.STRONG.value:
            recommendations.append(f"🎫 HIGH PRIORITY: Review Jira issue {issue.get('key')} immediately")
            recommendations.append(f"🔗 Link incident to Jira issue {issue.get('key')} for tracking")
            
            if issue.get('status', {}).get('name', '').lower() in ['open', 'in progress']:
                recommendations.append(f"🚀 Escalate Jira issue {issue.get('key')} - directly related to incident")
        
        elif correlation_score >= CorrelationStrength.MODERATE.value:
            recommendations.append(f"🔍 Investigate potential relationship with Jira issue {issue.get('key')}")
            recommendations.append(f"📋 Add incident details to Jira issue {issue.get('key')} comments")
        
        if issue.get('priority', {}).get('name', '').lower() in ['blocker', 'critical']:
            recommendations.append(f"⚠️ Critical/Blocker issue detected - requires immediate attention")
        
        return recommendations
    
    def _determine_confidence_level(self, correlation_score: float) -> str:
        """Determine confidence level based on correlation score"""
        if correlation_score >= CorrelationStrength.VERY_STRONG.value:
            return "Very High"
        elif correlation_score >= CorrelationStrength.STRONG.value:
            return "High"
        elif correlation_score >= CorrelationStrength.MODERATE.value:
            return "Medium"
        elif correlation_score >= CorrelationStrength.WEAK.value:
            return "Low"
        else:
            return "Very Low"
    
    def generate_correlation_summary(self, correlation_results: List[CorrelationResult]) -> Dict[str, Any]:
        """Generate a summary of all correlation results"""
        if not correlation_results:
            return {
                'total_correlations': 0,
                'highest_correlation': 0.0,
                'defect_likelihood': 'Low',
                'recommended_actions': ['🆕 Treat as new issue - no significant defect correlations found'],
                'summary': 'No significant correlations with existing defects detected'
            }
        
        highest_correlation = max(r.correlation_score for r in correlation_results)
        alm_octane_count = sum(1 for r in correlation_results if r.defect_source == 'alm_octane')
        jira_count = sum(1 for r in correlation_results if r.defect_source == 'jira')
        
        # Determine overall defect likelihood
        if highest_correlation >= CorrelationStrength.STRONG.value:
            defect_likelihood = 'High'
        elif highest_correlation >= CorrelationStrength.MODERATE.value:
            defect_likelihood = 'Medium'
        else:
            defect_likelihood = 'Low'
        
        # Compile all recommendations
        all_recommendations = []
        for result in correlation_results[:5]:  # Top 5 results
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        return {
            'total_correlations': len(correlation_results),
            'highest_correlation': highest_correlation,
            'alm_octane_correlations': alm_octane_count,
            'jira_correlations': jira_count,
            'defect_likelihood': defect_likelihood,
            'recommended_actions': unique_recommendations[:10],  # Top 10 recommendations
            'summary': self._generate_summary_text(correlation_results, highest_correlation)
        }
    
    def _generate_summary_text(self, correlation_results: List[CorrelationResult], 
                             highest_correlation: float) -> str:
        """Generate human-readable summary text"""
        alm_octane_count = sum(1 for r in correlation_results if r.defect_source == 'alm_octane')
        jira_count = sum(1 for r in correlation_results if r.defect_source == 'jira')
        
        if highest_correlation >= CorrelationStrength.STRONG.value:
            return f"Strong correlation detected with {len(correlation_results)} defects ({alm_octane_count} ALM Octane, {jira_count} Jira). This incident is likely related to existing known issues that require immediate attention."
        
        elif highest_correlation >= CorrelationStrength.MODERATE.value:
            return f"Moderate correlation found with {len(correlation_results)} defects ({alm_octane_count} ALM Octane, {jira_count} Jira). Further investigation needed to determine relationship."
        
        else:
            return f"Weak correlation with {len(correlation_results)} defects ({alm_octane_count} ALM Octane, {jira_count} Jira). This appears to be a new issue requiring fresh investigation."


# Usage example
if __name__ == "__main__":
    # Example usage
    mcp_endpoints = {
        'alm_octane': 'http://localhost:9085',
        'jira': 'http://localhost:9086'
    }
    
    correlator = DefectIncidentCorrelator(mcp_endpoints)
    
    # Example incident data
    incident_data = {
        'incident_id': 'INC-001',
        'title': 'API Gateway Timeout Issues',
        'description': 'Customers experiencing timeout errors when accessing payment API endpoints. Connection pool appears to be exhausted.',
        'severity': 'Critical',
        'affected_services': ['api-gateway', 'payment-service', 'database'],
        'timestamp': '2024-08-12T14:30:00Z'
    }
    
    # Run correlation
    results = correlator.correlate_incident_with_defects(incident_data)
    summary = correlator.generate_correlation_summary(results)
    
    print("Correlation Summary:")
    print(json.dumps(summary, indent=2))