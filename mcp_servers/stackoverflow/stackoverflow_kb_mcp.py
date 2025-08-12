#!/usr/bin/env python3
"""
Stack Overflow Enterprise Knowledge Base MCP Server
Provides access to Stack Overflow Enterprise for technical Q&A and solutions
"""

from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime, timedelta
import logging
import hashlib
from typing import Dict, List, Any, Optional
import re

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stack Overflow Enterprise configuration
SO_CONFIG = {
    "api_version": "2.3",
    "site": "stackoverflow.enterprise.com",
    "tags": ["aws", "python", "devops", "sre", "monitoring", "kubernetes", "docker"],
    "min_score": 5,
    "accepted_only": False
}

# Simulated Stack Overflow knowledge base
SO_KNOWLEDGE_BASE = [
    {
        "question_id": 1001,
        "title": "How to handle AWS Lambda timeout errors in production?",
        "tags": ["aws", "lambda", "timeout", "error-handling"],
        "score": 42,
        "accepted_answer": {
            "answer_id": 2001,
            "body": "To handle Lambda timeout errors: 1) Increase timeout to max 15 min, 2) Implement async processing with SQS, 3) Use Step Functions for long-running tasks, 4) Add CloudWatch alarms for timeout monitoring",
            "score": 35,
            "is_accepted": True
        },
        "view_count": 15234,
        "creation_date": "2024-01-15T10:30:00Z"
    },
    {
        "question_id": 1002,
        "title": "Best practices for database connection pooling in microservices",
        "tags": ["database", "connection-pooling", "microservices", "best-practices"],
        "score": 89,
        "accepted_answer": {
            "answer_id": 2002,
            "body": "Connection pooling best practices: 1) Use PgBouncer or ProxySQL, 2) Set pool size = (core_count * 2) + disk_count, 3) Implement connection retry logic, 4) Monitor pool metrics, 5) Use connection pooling libraries",
            "score": 76,
            "is_accepted": True
        },
        "view_count": 28456,
        "creation_date": "2023-11-20T14:15:00Z"
    },
    {
        "question_id": 1003,
        "title": "Debugging memory leaks in Python applications",
        "tags": ["python", "memory-leak", "debugging", "performance"],
        "score": 156,
        "accepted_answer": {
            "answer_id": 2003,
            "body": "Debug memory leaks: 1) Use memory_profiler and tracemalloc, 2) Check for circular references, 3) Profile with objgraph, 4) Monitor with psutil, 5) Use weak references where appropriate",
            "score": 142,
            "is_accepted": True
        },
        "view_count": 45678,
        "creation_date": "2023-08-10T09:45:00Z"
    }
]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Stack Overflow Enterprise KB MCP Server",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/so/search', methods=['POST'])
def search_stackoverflow():
    """Search Stack Overflow Enterprise knowledge base"""
    try:
        data = request.json
        query = data.get('query', '')
        tags = data.get('tags', [])
        min_score = data.get('min_score', SO_CONFIG['min_score'])
        
        # Search through knowledge base
        results = search_questions(query, tags, min_score)
        
        # Enhance with related questions
        enhanced_results = enhance_with_related(results, query)
        
        return jsonify({
            "query": query,
            "total_results": len(enhanced_results),
            "results": enhanced_results,
            "search_metadata": {
                "tags_used": tags,
                "min_score": min_score,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/so/solutions', methods=['POST'])
def get_solutions_for_incident():
    """Get Stack Overflow solutions for an incident"""
    try:
        data = request.json
        incident_description = data.get('description', '')
        incident_type = data.get('type', '')
        
        # Extract keywords from incident
        keywords = extract_technical_keywords(incident_description)
        
        # Find relevant solutions
        solutions = find_relevant_solutions(keywords, incident_type)
        
        # Rank by relevance
        ranked_solutions = rank_solutions(solutions, incident_description)
        
        return jsonify({
            "incident_keywords": keywords,
            "solutions": ranked_solutions[:5],  # Top 5 solutions
            "total_found": len(solutions),
            "confidence_score": calculate_solution_confidence(ranked_solutions)
        })
        
    except Exception as e:
        logger.error(f"Solution lookup error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/so/code-snippets', methods=['POST'])
def get_code_snippets():
    """Get relevant code snippets for a technical issue"""
    try:
        data = request.json
        issue = data.get('issue', '')
        language = data.get('language', 'python')
        
        # Find code snippets
        snippets = find_code_snippets(issue, language)
        
        return jsonify({
            "issue": issue,
            "language": language,
            "snippets": snippets,
            "total_snippets": len(snippets)
        })
        
    except Exception as e:
        logger.error(f"Code snippet error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/so/best-practices', methods=['GET'])
def get_best_practices():
    """Get best practices for a specific technology"""
    try:
        technology = request.args.get('technology', 'sre')
        
        # Get best practices
        best_practices = get_technology_best_practices(technology)
        
        return jsonify({
            "technology": technology,
            "best_practices": best_practices,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Best practices error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def search_questions(query: str, tags: List[str], min_score: int) -> List[Dict]:
    """Search Stack Overflow questions"""
    results = []
    query_lower = query.lower()
    
    for question in SO_KNOWLEDGE_BASE:
        # Check query match
        if query_lower in question['title'].lower():
            score_boost = 2.0
        elif any(query_lower in tag for tag in question['tags']):
            score_boost = 1.5
        else:
            score_boost = 1.0
            
        # Check tag match
        tag_match = any(tag in question['tags'] for tag in tags) if tags else True
        
        # Check score threshold
        if question['score'] >= min_score and (query_lower in question['title'].lower() or tag_match):
            result = question.copy()
            result['relevance_score'] = question['score'] * score_boost
            results.append(result)
    
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)

def enhance_with_related(results: List[Dict], query: str) -> List[Dict]:
    """Enhance results with related questions"""
    enhanced = []
    
    for result in results:
        enhanced_result = result.copy()
        
        # Add related questions (simulated)
        enhanced_result['related_questions'] = [
            {
                "title": f"Common pitfalls when {result['title'].lower()}",
                "url": f"https://so.enterprise.com/q/{result['question_id'] + 1000}",
                "score": result['score'] // 2
            }
        ]
        
        # Add community insights
        enhanced_result['community_insights'] = {
            "common_issues": extract_common_issues(result),
            "recommended_approach": "See accepted answer for best approach"
        }
        
        enhanced.append(enhanced_result)
    
    return enhanced

def extract_technical_keywords(description: str) -> List[str]:
    """Extract technical keywords from incident description"""
    # Common technical terms
    tech_terms = ['api', 'database', 'timeout', 'error', 'connection', 'memory', 
                  'cpu', 'performance', 'authentication', 'authorization', 'ssl',
                  'certificate', 'network', 'latency', 'throughput', 'scaling']
    
    keywords = []
    desc_lower = description.lower()
    
    # Extract matching technical terms
    for term in tech_terms:
        if term in desc_lower:
            keywords.append(term)
    
    # Extract service names (AWS, etc.)
    service_patterns = [
        r'(lambda|ec2|s3|rds|dynamodb|sqs|sns|cloudwatch)',
        r'(kubernetes|k8s|docker|container)',
        r'(nginx|apache|haproxy|redis|postgres|mysql)'
    ]
    
    for pattern in service_patterns:
        matches = re.findall(pattern, desc_lower)
        keywords.extend(matches)
    
    return list(set(keywords))

def find_relevant_solutions(keywords: List[str], incident_type: str) -> List[Dict]:
    """Find relevant Stack Overflow solutions"""
    solutions = []
    
    for question in SO_KNOWLEDGE_BASE:
        relevance_score = 0
        
        # Check keyword matches
        for keyword in keywords:
            if keyword in question['title'].lower():
                relevance_score += 2
            if any(keyword in tag for tag in question['tags']):
                relevance_score += 1
        
        # Check incident type relevance
        if incident_type == 'timeout' and 'timeout' in question['tags']:
            relevance_score += 3
        elif incident_type == 'memory' and 'memory' in question['tags']:
            relevance_score += 3
        
        if relevance_score > 0:
            solution = {
                "question": question['title'],
                "solution": question['accepted_answer']['body'],
                "score": question['score'],
                "relevance_score": relevance_score,
                "tags": question['tags'],
                "url": f"https://so.enterprise.com/questions/{question['question_id']}"
            }
            solutions.append(solution)
    
    return solutions

def rank_solutions(solutions: List[Dict], incident_description: str) -> List[Dict]:
    """Rank solutions by relevance to incident"""
    for solution in solutions:
        # Boost score based on description match
        desc_lower = incident_description.lower()
        solution_lower = solution['solution'].lower()
        
        match_count = sum(1 for word in desc_lower.split() if word in solution_lower)
        solution['final_score'] = solution['relevance_score'] + (match_count * 0.5)
    
    return sorted(solutions, key=lambda x: x['final_score'], reverse=True)

def calculate_solution_confidence(solutions: List[Dict]) -> float:
    """Calculate confidence in found solutions"""
    if not solutions:
        return 0.0
    
    # Base confidence on top solution score
    top_score = solutions[0].get('final_score', 0) if solutions else 0
    
    # Normalize to 0-1 range
    confidence = min(top_score / 10, 1.0)
    
    # Boost if multiple high-quality solutions
    high_quality_count = sum(1 for s in solutions if s.get('score', 0) > 50)
    if high_quality_count > 2:
        confidence = min(confidence + 0.2, 1.0)
    
    return round(confidence, 2)

def find_code_snippets(issue: str, language: str) -> List[Dict]:
    """Find relevant code snippets"""
    snippets = []
    
    # Simulated code snippets based on issue
    if 'timeout' in issue.lower():
        snippets.append({
            "title": "Handling timeouts with retry logic",
            "language": language,
            "code": """import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def requests_retry_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session""",
            "explanation": "Implements exponential backoff retry for timeout handling",
            "votes": 127
        })
    
    if 'connection pool' in issue.lower():
        snippets.append({
            "title": "Database connection pool implementation",
            "language": language,
            "code": """from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Create engine with connection pooling
engine = create_engine(
    'postgresql://user:password@localhost/db',
    poolclass=QueuePool,
    pool_size=20,          # Number of connections to maintain
    max_overflow=0,        # Max overflow connections
    pool_pre_ping=True,    # Test connections before using
    pool_recycle=3600      # Recycle connections after 1 hour
)""",
            "explanation": "SQLAlchemy connection pool configuration for production",
            "votes": 89
        })
    
    return snippets

def get_technology_best_practices(technology: str) -> List[Dict]:
    """Get best practices for a technology"""
    best_practices = {
        "sre": [
            {
                "practice": "Implement SLIs and SLOs",
                "description": "Define Service Level Indicators and Objectives for all critical services",
                "so_references": ["https://so.enterprise.com/q/sli-slo-implementation"]
            },
            {
                "practice": "Error Budget Management",
                "description": "Use error budgets to balance reliability and feature velocity",
                "so_references": ["https://so.enterprise.com/q/error-budget-calculation"]
            }
        ],
        "aws": [
            {
                "practice": "Use IAM roles instead of keys",
                "description": "Always use IAM roles for EC2 instances and Lambda functions",
                "so_references": ["https://so.enterprise.com/q/iam-roles-best-practices"]
            },
            {
                "practice": "Enable CloudTrail logging",
                "description": "Enable CloudTrail for audit logging across all regions",
                "so_references": ["https://so.enterprise.com/q/cloudtrail-setup"]
            }
        ],
        "python": [
            {
                "practice": "Use virtual environments",
                "description": "Always use venv or virtualenv for dependency isolation",
                "so_references": ["https://so.enterprise.com/q/python-virtual-environments"]
            },
            {
                "practice": "Type hints and mypy",
                "description": "Use type hints and run mypy for static type checking",
                "so_references": ["https://so.enterprise.com/q/python-type-hints"]
            }
        ]
    }
    
    return best_practices.get(technology.lower(), [])

def extract_common_issues(question: Dict) -> List[str]:
    """Extract common issues from question data"""
    common_issues = []
    
    # Based on tags
    if 'timeout' in question['tags']:
        common_issues.append("Insufficient timeout configuration")
    if 'memory-leak' in question['tags']:
        common_issues.append("Memory not being properly released")
    if 'connection-pooling' in question['tags']:
        common_issues.append("Connection pool exhaustion")
    
    return common_issues

if __name__ == '__main__':
    logger.info("Starting Stack Overflow Enterprise KB MCP Server on port 9089")
    app.run(host='0.0.0.0', port=9089, debug=False)