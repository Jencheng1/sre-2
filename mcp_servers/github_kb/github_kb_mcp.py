#!/usr/bin/env python3
"""
GitHub Knowledge Base MCP Server
Provides access to GitHub Issues, Discussions, and Wiki content for knowledge base
"""

from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, List, Any, Optional
import hashlib

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub KB configuration
GITHUB_CONFIG = {
    "org": "enterprise-org",
    "repos": ["sre-handbook", "incident-playbooks", "infrastructure", "monitoring"],
    "labels": ["incident", "runbook", "postmortem", "best-practice", "documentation"],
    "issue_states": ["open", "closed"],
    "min_reactions": 5
}

# Simulated GitHub knowledge base
GITHUB_KB = [
    {
        "id": "issue-1",
        "type": "issue",
        "repo": "sre-handbook",
        "title": "Runbook: Handling Database Connection Pool Exhaustion",
        "body": "## Problem\nDatabase connection pool exhaustion causing application errors.\n\n## Detection\n- Error: 'Too many connections'\n- Metric: connection_pool_usage > 90%\n\n## Resolution\n1. Increase pool size temporarily\n2. Identify connection leaks\n3. Restart affected services\n4. Implement connection pooling best practices",
        "labels": ["runbook", "database", "incident"],
        "state": "closed",
        "reactions": 23,
        "created_at": "2024-02-15T10:30:00Z",
        "resolution": "Implemented connection pool monitoring and auto-scaling"
    },
    {
        "id": "discussion-1",
        "type": "discussion",
        "repo": "infrastructure",
        "title": "Best Practices for API Rate Limiting",
        "body": "Discussion on implementing effective API rate limiting strategies:\n\n1. Token bucket algorithm\n2. Sliding window counters\n3. Distributed rate limiting with Redis\n4. Client-specific limits\n5. Graceful degradation",
        "category": "Best Practices",
        "upvotes": 45,
        "answers": 12,
        "created_at": "2024-01-20T14:00:00Z"
    },
    {
        "id": "wiki-1",
        "type": "wiki",
        "repo": "incident-playbooks",
        "title": "Incident Response Playbook - Service Outages",
        "content": "# Service Outage Response\n\n## Severity Levels\n- P1: Complete outage\n- P2: Partial outage\n- P3: Degraded performance\n\n## Response Steps\n1. Acknowledge incident\n2. Assess impact\n3. Engage on-call team\n4. Communicate status\n5. Implement fix\n6. Post-mortem",
        "last_updated": "2024-03-01T09:00:00Z",
        "contributors": ["sre-team", "ops-team"]
    },
    {
        "id": "issue-2",
        "type": "issue",
        "repo": "monitoring",
        "title": "Post-mortem: API Gateway Timeout Incident 2024-02-10",
        "body": "## Summary\nAPI Gateway experienced widespread timeouts affecting 30% of requests.\n\n## Timeline\n- 14:00 - First timeout alerts\n- 14:15 - Incident declared\n- 14:30 - Root cause identified\n- 15:00 - Fix deployed\n- 15:30 - Service restored\n\n## Root Cause\nMemory leak in request processing causing gradual performance degradation.\n\n## Action Items\n1. ✅ Fix memory leak\n2. ✅ Add memory monitoring\n3. ✅ Implement circuit breaker\n4. 🔄 Update runbook",
        "labels": ["postmortem", "incident", "api-gateway"],
        "state": "closed",
        "reactions": 34,
        "created_at": "2024-02-11T10:00:00Z"
    }
]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "GitHub Knowledge Base MCP Server",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/github/search', methods=['POST'])
def search_github_kb():
    """Search GitHub knowledge base"""
    try:
        data = request.json
        query = data.get('query', '')
        content_types = data.get('types', ['issue', 'discussion', 'wiki'])
        labels = data.get('labels', [])
        
        # Search across content types
        results = search_github_content(query, content_types, labels)
        
        # Enhance with context
        enhanced_results = enhance_github_results(results)
        
        return jsonify({
            "query": query,
            "total_results": len(enhanced_results),
            "results": enhanced_results,
            "content_types": content_types,
            "search_metadata": {
                "repos_searched": GITHUB_CONFIG['repos'],
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/github/runbooks', methods=['GET'])
def get_runbooks():
    """Get runbooks for specific scenarios"""
    try:
        scenario = request.args.get('scenario', '')
        
        # Find relevant runbooks
        runbooks = find_runbooks(scenario)
        
        return jsonify({
            "scenario": scenario,
            "runbooks": runbooks,
            "total_runbooks": len(runbooks)
        })
        
    except Exception as e:
        logger.error(f"Runbook error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/github/postmortems', methods=['POST'])
def search_postmortems():
    """Search post-mortems for similar incidents"""
    try:
        data = request.json
        incident_description = data.get('description', '')
        incident_type = data.get('type', '')
        
        # Find similar post-mortems
        postmortems = find_similar_postmortems(incident_description, incident_type)
        
        # Extract learnings
        learnings = extract_postmortem_learnings(postmortems)
        
        return jsonify({
            "incident_type": incident_type,
            "similar_postmortems": postmortems,
            "key_learnings": learnings,
            "prevention_measures": generate_prevention_measures(learnings)
        })
        
    except Exception as e:
        logger.error(f"Post-mortem search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/github/best-practices', methods=['GET'])
def get_github_best_practices():
    """Get best practices from GitHub discussions and wikis"""
    try:
        topic = request.args.get('topic', 'sre')
        
        # Find best practices
        best_practices = find_best_practices(topic)
        
        return jsonify({
            "topic": topic,
            "best_practices": best_practices,
            "sources": ["discussions", "wikis", "issues"]
        })
        
    except Exception as e:
        logger.error(f"Best practices error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/github/incident-patterns', methods=['POST'])
def analyze_incident_patterns():
    """Analyze patterns from historical incidents"""
    try:
        data = request.json
        time_range = data.get('time_range', 'last_month')
        
        # Analyze incident patterns
        patterns = analyze_patterns(time_range)
        
        # Generate insights
        insights = generate_pattern_insights(patterns)
        
        return jsonify({
            "time_range": time_range,
            "patterns": patterns,
            "insights": insights,
            "recommendations": generate_pattern_recommendations(patterns)
        })
        
    except Exception as e:
        logger.error(f"Pattern analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def search_github_content(query: str, content_types: List[str], labels: List[str]) -> List[Dict]:
    """Search GitHub content"""
    results = []
    query_lower = query.lower()
    
    for item in GITHUB_KB:
        # Check content type
        if item['type'] not in content_types:
            continue
        
        # Check query match
        title_match = query_lower in item.get('title', '').lower()
        body_match = query_lower in item.get('body', item.get('content', '')).lower()
        
        # Check label match
        label_match = True
        if labels and 'labels' in item:
            label_match = any(label in item['labels'] for label in labels)
        
        if (title_match or body_match) and label_match:
            result = item.copy()
            result['relevance_score'] = calculate_relevance(query, item)
            results.append(result)
    
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)

def enhance_github_results(results: List[Dict]) -> List[Dict]:
    """Enhance search results with additional context"""
    enhanced = []
    
    for result in results:
        enhanced_result = result.copy()
        
        # Add contextual information
        if result['type'] == 'issue':
            enhanced_result['resolution_time'] = calculate_resolution_time(result)
            enhanced_result['impact_level'] = determine_impact_level(result)
        elif result['type'] == 'discussion':
            enhanced_result['consensus'] = determine_consensus(result)
            enhanced_result['key_takeaways'] = extract_key_takeaways(result)
        elif result['type'] == 'wiki':
            enhanced_result['freshness'] = calculate_freshness(result)
            enhanced_result['completeness'] = assess_completeness(result)
        
        enhanced.append(enhanced_result)
    
    return enhanced

def find_runbooks(scenario: str) -> List[Dict]:
    """Find runbooks for a scenario"""
    runbooks = []
    scenario_lower = scenario.lower()
    
    for item in GITHUB_KB:
        if item['type'] in ['issue', 'wiki'] and 'runbook' in item.get('labels', []):
            if scenario_lower in item.get('title', '').lower() or \
               scenario_lower in item.get('body', item.get('content', '')).lower():
                runbook = {
                    "id": item['id'],
                    "title": item['title'],
                    "repo": item['repo'],
                    "content": item.get('body', item.get('content', '')),
                    "last_updated": item.get('created_at', item.get('last_updated')),
                    "effectiveness_score": calculate_runbook_effectiveness(item)
                }
                runbooks.append(runbook)
    
    return sorted(runbooks, key=lambda x: x['effectiveness_score'], reverse=True)

def find_similar_postmortems(description: str, incident_type: str) -> List[Dict]:
    """Find similar post-mortems"""
    postmortems = []
    desc_lower = description.lower()
    
    for item in GITHUB_KB:
        if 'postmortem' in item.get('labels', []):
            similarity_score = calculate_similarity(desc_lower, item)
            
            if similarity_score > 0.3:  # Threshold
                postmortem = {
                    "id": item['id'],
                    "title": item['title'],
                    "incident_date": extract_incident_date(item),
                    "root_cause": extract_root_cause(item),
                    "resolution": item.get('resolution', 'See full post-mortem'),
                    "similarity_score": similarity_score,
                    "action_items": extract_action_items(item)
                }
                postmortems.append(postmortem)
    
    return sorted(postmortems, key=lambda x: x['similarity_score'], reverse=True)

def extract_postmortem_learnings(postmortems: List[Dict]) -> List[Dict]:
    """Extract key learnings from post-mortems"""
    learnings = []
    
    for pm in postmortems[:5]:  # Top 5 similar incidents
        learning = {
            "incident": pm['title'],
            "root_cause": pm['root_cause'],
            "key_learning": f"Similar incident caused by {pm['root_cause']}",
            "prevention": extract_prevention_measures(pm)
        }
        learnings.append(learning)
    
    return learnings

def find_best_practices(topic: str) -> List[Dict]:
    """Find best practices for a topic"""
    practices = []
    topic_lower = topic.lower()
    
    for item in GITHUB_KB:
        if item['type'] in ['discussion', 'wiki']:
            if 'best' in item.get('title', '').lower() and \
               topic_lower in item.get('body', item.get('content', '')).lower():
                practice = {
                    "title": item['title'],
                    "type": item['type'],
                    "content": summarize_content(item),
                    "source": f"{item['repo']}/{item['type']}/{item['id']}",
                    "last_updated": item.get('last_updated', item.get('created_at')),
                    "community_score": item.get('upvotes', item.get('reactions', 0))
                }
                practices.append(practice)
    
    return sorted(practices, key=lambda x: x['community_score'], reverse=True)

def analyze_patterns(time_range: str) -> Dict[str, Any]:
    """Analyze incident patterns"""
    patterns = {
        "common_root_causes": {},
        "frequent_services": {},
        "time_patterns": {},
        "resolution_times": []
    }
    
    # Analyze post-mortems
    for item in GITHUB_KB:
        if 'postmortem' in item.get('labels', []):
            # Root causes
            root_cause = extract_root_cause(item)
            if root_cause:
                patterns['common_root_causes'][root_cause] = \
                    patterns['common_root_causes'].get(root_cause, 0) + 1
            
            # Affected services
            services = extract_affected_services(item)
            for service in services:
                patterns['frequent_services'][service] = \
                    patterns['frequent_services'].get(service, 0) + 1
    
    return patterns

def generate_pattern_insights(patterns: Dict[str, Any]) -> List[str]:
    """Generate insights from patterns"""
    insights = []
    
    # Most common root cause
    if patterns['common_root_causes']:
        top_cause = max(patterns['common_root_causes'], 
                       key=patterns['common_root_causes'].get)
        insights.append(f"Most common root cause: {top_cause}")
    
    # Most affected service
    if patterns['frequent_services']:
        top_service = max(patterns['frequent_services'], 
                         key=patterns['frequent_services'].get)
        insights.append(f"Most frequently affected service: {top_service}")
    
    return insights

def calculate_relevance(query: str, item: Dict) -> float:
    """Calculate relevance score"""
    score = 0.0
    query_lower = query.lower()
    
    # Title match (highest weight)
    if query_lower in item.get('title', '').lower():
        score += 3.0
    
    # Content match
    content = item.get('body', item.get('content', ''))
    if query_lower in content.lower():
        score += 2.0
    
    # Label match
    for label in item.get('labels', []):
        if query_lower in label:
            score += 1.0
    
    # Boost for reactions/upvotes
    reactions = item.get('reactions', item.get('upvotes', 0))
    if reactions > 20:
        score += 1.0
    elif reactions > 10:
        score += 0.5
    
    return score

def calculate_resolution_time(issue: Dict) -> str:
    """Calculate issue resolution time"""
    if issue.get('state') == 'closed' and 'created_at' in issue:
        # Simulated resolution time
        return "4 hours"
    return "Ongoing"

def determine_impact_level(issue: Dict) -> str:
    """Determine impact level from issue"""
    labels = issue.get('labels', [])
    
    if 'critical' in labels or 'p1' in labels:
        return "Critical"
    elif 'high' in labels or 'p2' in labels:
        return "High"
    elif 'medium' in labels or 'p3' in labels:
        return "Medium"
    else:
        return "Low"

def determine_consensus(discussion: Dict) -> str:
    """Determine consensus level in discussion"""
    upvotes = discussion.get('upvotes', 0)
    answers = discussion.get('answers', 0)
    
    if upvotes > 30 and answers > 10:
        return "Strong consensus"
    elif upvotes > 15 and answers > 5:
        return "Moderate consensus"
    else:
        return "Limited consensus"

def extract_key_takeaways(discussion: Dict) -> List[str]:
    """Extract key takeaways from discussion"""
    # Simulated extraction
    content = discussion.get('body', '')
    takeaways = []
    
    # Look for numbered lists
    lines = content.split('\n')
    for line in lines:
        if re.match(r'^\d+\.', line.strip()):
            takeaways.append(line.strip())
    
    return takeaways[:3]  # Top 3

def calculate_freshness(wiki: Dict) -> str:
    """Calculate wiki freshness"""
    last_updated = wiki.get('last_updated', '')
    if last_updated:
        update_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        days_old = (datetime.now(update_date.tzinfo) - update_date).days
        
        if days_old < 30:
            return "Fresh"
        elif days_old < 90:
            return "Recent"
        elif days_old < 180:
            return "Aging"
        else:
            return "Stale"
    
    return "Unknown"

def assess_completeness(wiki: Dict) -> float:
    """Assess wiki completeness"""
    content = wiki.get('content', '')
    
    # Check for key sections
    required_sections = ['overview', 'steps', 'troubleshooting', 'references']
    found_sections = sum(1 for section in required_sections if section in content.lower())
    
    completeness = found_sections / len(required_sections)
    return round(completeness, 2)

def calculate_runbook_effectiveness(item: Dict) -> float:
    """Calculate runbook effectiveness score"""
    score = 0.5  # Base score
    
    # Has resolution steps
    if 'resolution' in item.get('body', item.get('content', '')).lower():
        score += 0.2
    
    # Has detection criteria
    if 'detection' in item.get('body', item.get('content', '')).lower():
        score += 0.2
    
    # Community validation
    reactions = item.get('reactions', 0)
    if reactions > 20:
        score += 0.1
    
    return min(score, 1.0)

def calculate_similarity(description: str, item: Dict) -> float:
    """Calculate similarity between description and item"""
    item_text = f"{item.get('title', '')} {item.get('body', item.get('content', ''))}".lower()
    
    # Simple word overlap similarity
    desc_words = set(description.split())
    item_words = set(item_text.split())
    
    if not desc_words or not item_words:
        return 0.0
    
    overlap = len(desc_words & item_words)
    similarity = overlap / min(len(desc_words), len(item_words))
    
    return min(similarity, 1.0)

def extract_incident_date(item: Dict) -> str:
    """Extract incident date from post-mortem"""
    title = item.get('title', '')
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', title)
    
    if date_match:
        return date_match.group()
    
    return item.get('created_at', 'Unknown')

def extract_root_cause(item: Dict) -> str:
    """Extract root cause from post-mortem"""
    content = item.get('body', item.get('content', ''))
    
    # Look for root cause section
    root_cause_match = re.search(r'root cause[:\s]+([^\n]+)', content, re.IGNORECASE)
    
    if root_cause_match:
        return root_cause_match.group(1).strip()
    
    return "Unknown"

def extract_action_items(item: Dict) -> List[str]:
    """Extract action items from post-mortem"""
    content = item.get('body', item.get('content', ''))
    action_items = []
    
    # Look for action items section
    lines = content.split('\n')
    in_action_section = False
    
    for line in lines:
        if 'action items' in line.lower():
            in_action_section = True
            continue
        
        if in_action_section:
            # Look for checkbox items or numbered items
            if re.match(r'^[\-\*\d]+[\.\)]\s', line.strip()):
                action_items.append(line.strip())
    
    return action_items[:5]  # Top 5

def extract_prevention_measures(postmortem: Dict) -> str:
    """Extract prevention measures from post-mortem"""
    action_items = postmortem.get('action_items', [])
    
    if action_items:
        return f"Implement {len(action_items)} action items including monitoring improvements"
    
    return "Review and implement recommended action items"

def summarize_content(item: Dict) -> str:
    """Summarize content to key points"""
    content = item.get('body', item.get('content', ''))
    
    # Simple summarization - take first paragraph
    paragraphs = content.split('\n\n')
    if paragraphs:
        return paragraphs[0][:200] + "..."
    
    return content[:200] + "..."

def extract_affected_services(item: Dict) -> List[str]:
    """Extract affected services from incident"""
    content = item.get('body', item.get('content', '')).lower()
    services = []
    
    # Common service patterns
    service_patterns = [
        'api gateway', 'database', 'cache', 'queue', 'storage',
        'authentication', 'payment', 'notification', 'monitoring'
    ]
    
    for service in service_patterns:
        if service in content:
            services.append(service)
    
    return services

def generate_prevention_measures(learnings: List[Dict]) -> List[str]:
    """Generate prevention measures from learnings"""
    measures = []
    
    for learning in learnings:
        if 'timeout' in learning.get('root_cause', '').lower():
            measures.append("Implement timeout monitoring and alerts")
        elif 'memory' in learning.get('root_cause', '').lower():
            measures.append("Add memory usage monitoring and limits")
        elif 'connection' in learning.get('root_cause', '').lower():
            measures.append("Implement connection pool monitoring")
    
    # Add general measures
    measures.extend([
        "Regular review of post-mortems for pattern identification",
        "Update runbooks based on incident learnings",
        "Implement preventive monitoring for identified patterns"
    ])
    
    return list(set(measures))[:5]  # Top 5 unique measures

def generate_pattern_recommendations(patterns: Dict[str, Any]) -> List[str]:
    """Generate recommendations from patterns"""
    recommendations = []
    
    # Based on common root causes
    if patterns['common_root_causes']:
        top_cause = max(patterns['common_root_causes'], 
                       key=patterns['common_root_causes'].get)
        recommendations.append(f"Focus on preventing {top_cause} incidents")
    
    # Based on frequent services
    if patterns['frequent_services']:
        top_service = max(patterns['frequent_services'], 
                         key=patterns['frequent_services'].get)
        recommendations.append(f"Increase monitoring for {top_service}")
    
    recommendations.extend([
        "Implement pattern-based alerting",
        "Create targeted runbooks for common scenarios",
        "Schedule regular incident pattern reviews"
    ])
    
    return recommendations

if __name__ == '__main__':
    logger.info("Starting GitHub Knowledge Base MCP Server on port 9090")
    app.run(host='0.0.0.0', port=9090, debug=False)