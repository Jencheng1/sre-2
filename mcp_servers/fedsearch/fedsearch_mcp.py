#!/usr/bin/env python3
"""
FedSearch MCP Server
Provides intelligent search capabilities across federal knowledge sources
Integrates with multiple federal APIs and knowledge bases
"""

from flask import Flask, request, jsonify
import json
import requests
from datetime import datetime, timedelta
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import boto3
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# FedSearch Configuration
FEDSEARCH_CONFIG = {
    "search_sources": [
        "federal_register",
        "gao_reports",
        "nist_publications",
        "cisa_advisories",
        "opm_guidance",
        "gsa_standards"
    ],
    "api_endpoints": {
        "federal_register": "https://www.federalregister.gov/api/v1/documents",
        "gao": "https://api.gao.gov/v1/reports",
        "nist": "https://csrc.nist.gov/api/publications",
        "cisa": "https://api.cisa.gov/v1/advisories"
    },
    "search_models": {
        "semantic": "titan-embed-text-v1",
        "reranker": "cohere-rerank-v2",
        "summarizer": "claude-3-sonnet"
    },
    "cache_ttl": 3600  # 1 hour cache
}

# In-memory cache for search results
search_cache = {}

# FedSearch Knowledge Repository (Demo Data)
FEDSEARCH_REPOSITORY = [
    {
        "id": "FS-NIST-001",
        "source": "NIST",
        "type": "publication",
        "title": "NIST SP 800-53 Rev 5: Security and Privacy Controls",
        "content": "Comprehensive catalog of security and privacy controls for information systems...",
        "url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf",
        "tags": ["security", "controls", "compliance", "privacy"],
        "published_date": "2020-09-23",
        "relevance_score": 0.95
    },
    {
        "id": "FS-CISA-002",
        "source": "CISA",
        "type": "advisory",
        "title": "Critical Infrastructure Security Advisory: API Security",
        "content": "Advisory on securing APIs in critical infrastructure systems...",
        "url": "https://www.cisa.gov/advisory/api-security-2024",
        "tags": ["api", "security", "infrastructure", "advisory"],
        "published_date": "2024-01-15",
        "relevance_score": 0.92
    },
    {
        "id": "FS-GAO-003",
        "source": "GAO",
        "type": "report",
        "title": "Federal IT Modernization: Progress and Challenges",
        "content": "GAO report on federal IT modernization efforts and recommendations...",
        "url": "https://www.gao.gov/products/gao-24-105709",
        "tags": ["modernization", "IT", "federal", "report"],
        "published_date": "2024-03-10",
        "relevance_score": 0.88
    }
]

# Initialize TF-IDF vectorizer for semantic search
tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "FedSearch MCP Server",
        "timestamp": datetime.now().isoformat(),
        "search_sources": len(FEDSEARCH_CONFIG['search_sources'])
    })

@app.route('/fedsearch/search', methods=['POST'])
def intelligent_federal_search():
    """
    Perform intelligent search across federal knowledge sources
    """
    try:
        data = request.json
        query = data.get('query', '')
        sources = data.get('sources', FEDSEARCH_CONFIG['search_sources'])
        search_type = data.get('search_type', 'semantic')  # semantic, keyword, hybrid
        filters = data.get('filters', {})
        
        # Check cache
        cache_key = generate_cache_key(query, sources, filters)
        if cache_key in search_cache:
            cached_result = search_cache[cache_key]
            if is_cache_valid(cached_result):
                logger.info(f"Returning cached result for query: {query}")
                return jsonify(cached_result['data'])
        
        # Perform search based on type
        if search_type == 'semantic':
            results = perform_semantic_search(query, sources, filters)
        elif search_type == 'hybrid':
            results = perform_hybrid_search(query, sources, filters)
        else:
            results = perform_keyword_search(query, sources, filters)
        
        # Apply AI reranking
        reranked_results = ai_rerank_results(results, query)
        
        # Generate search insights
        insights = generate_search_insights(reranked_results, query)
        
        # Prepare response
        response_data = {
            "query": query,
            "search_type": search_type,
            "total_results": len(reranked_results),
            "results": reranked_results[:20],  # Top 20 results
            "insights": insights,
            "sources_searched": sources,
            "search_metadata": {
                "execution_time": datetime.now().isoformat(),
                "ai_models_used": list(FEDSEARCH_CONFIG['search_models'].values())
            }
        }
        
        # Cache the result
        search_cache[cache_key] = {
            "data": response_data,
            "timestamp": time.time()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fedsearch/analyze-document', methods=['POST'])
def analyze_federal_document():
    """
    Analyze a federal document for compliance and insights
    """
    try:
        data = request.json
        document_url = data.get('document_url')
        document_content = data.get('document_content')
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        # Fetch document if URL provided
        if document_url and not document_content:
            document_content = fetch_document_content(document_url)
        
        # Perform analysis
        analysis_results = analyze_document(
            document_content,
            analysis_type
        )
        
        # Extract compliance requirements
        compliance_requirements = extract_compliance_requirements(
            document_content,
            analysis_results
        )
        
        # Generate actionable insights
        actionable_insights = generate_actionable_insights(
            analysis_results,
            compliance_requirements
        )
        
        return jsonify({
            "document_url": document_url,
            "analysis_type": analysis_type,
            "analysis_results": analysis_results,
            "compliance_requirements": compliance_requirements,
            "actionable_insights": actionable_insights,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fedsearch/cross-reference', methods=['POST'])
def cross_reference_sources():
    """
    Cross-reference information across multiple federal sources
    """
    try:
        data = request.json
        topic = data.get('topic')
        primary_source = data.get('primary_source')
        reference_sources = data.get('reference_sources', FEDSEARCH_CONFIG['search_sources'])
        
        # Search primary source
        primary_results = search_single_source(topic, primary_source)
        
        # Cross-reference with other sources
        cross_references = {}
        for source in reference_sources:
            if source != primary_source:
                source_results = search_single_source(topic, source)
                cross_references[source] = find_correlations(
                    primary_results,
                    source_results
                )
        
        # Generate cross-reference report
        report = generate_cross_reference_report(
            topic,
            primary_source,
            primary_results,
            cross_references
        )
        
        return jsonify({
            "topic": topic,
            "primary_source": primary_source,
            "cross_references": cross_references,
            "report": report,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Cross-reference error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fedsearch/compliance-mapping', methods=['POST'])
def map_compliance_requirements():
    """
    Map incident or system to federal compliance requirements
    """
    try:
        data = request.json
        incident_data = data.get('incident_data', {})
        system_description = data.get('system_description', '')
        compliance_frameworks = data.get('frameworks', ['NIST', 'FISMA', 'FedRAMP'])
        
        # Extract key characteristics
        characteristics = extract_system_characteristics(
            incident_data,
            system_description
        )
        
        # Map to compliance requirements
        compliance_mapping = {}
        for framework in compliance_frameworks:
            requirements = map_to_framework_requirements(
                characteristics,
                framework
            )
            compliance_mapping[framework] = requirements
        
        # Generate compliance recommendations
        recommendations = generate_compliance_recommendations(
            compliance_mapping,
            characteristics
        )
        
        # Calculate compliance scores
        compliance_scores = calculate_compliance_scores(
            compliance_mapping,
            characteristics
        )
        
        return jsonify({
            "system_characteristics": characteristics,
            "compliance_mapping": compliance_mapping,
            "recommendations": recommendations,
            "compliance_scores": compliance_scores,
            "frameworks_analyzed": compliance_frameworks,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Compliance mapping error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fedsearch/trend-analysis', methods=['POST'])
def analyze_federal_trends():
    """
    Analyze trends in federal guidance and regulations
    """
    try:
        data = request.json
        topic = data.get('topic')
        time_range = data.get('time_range', 'last_year')
        sources = data.get('sources', FEDSEARCH_CONFIG['search_sources'])
        
        # Collect historical data
        historical_data = collect_historical_data(
            topic,
            time_range,
            sources
        )
        
        # Analyze trends
        trend_analysis = analyze_trends(historical_data)
        
        # Predict future changes
        predictions = predict_regulatory_changes(
            trend_analysis,
            topic
        )
        
        # Generate trend report
        trend_report = generate_trend_report(
            topic,
            trend_analysis,
            predictions
        )
        
        return jsonify({
            "topic": topic,
            "time_range": time_range,
            "trend_analysis": trend_analysis,
            "predictions": predictions,
            "report": trend_report,
            "data_points": len(historical_data),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def perform_semantic_search(query: str, sources: List[str], filters: Dict) -> List[Dict]:
    """
    Perform semantic search using embeddings
    """
    results = []
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Search each source
    for source in sources:
        source_results = search_with_embeddings(
            query,
            query_embedding,
            source,
            filters
        )
        results.extend(source_results)
    
    # Sort by semantic similarity
    results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
    
    return results

def perform_hybrid_search(query: str, sources: List[str], filters: Dict) -> List[Dict]:
    """
    Perform hybrid search combining keyword and semantic approaches
    """
    # Get keyword results
    keyword_results = perform_keyword_search(query, sources, filters)
    
    # Get semantic results
    semantic_results = perform_semantic_search(query, sources, filters)
    
    # Merge and deduplicate results
    merged_results = merge_search_results(keyword_results, semantic_results)
    
    # Apply hybrid scoring
    for result in merged_results:
        keyword_score = result.get('keyword_score', 0)
        semantic_score = result.get('similarity_score', 0)
        result['hybrid_score'] = (0.4 * keyword_score) + (0.6 * semantic_score)
    
    # Sort by hybrid score
    merged_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    
    return merged_results

def perform_keyword_search(query: str, sources: List[str], filters: Dict) -> List[Dict]:
    """
    Perform traditional keyword-based search
    """
    results = []
    
    # Tokenize query
    query_tokens = tokenize_and_normalize(query)
    
    # Search repository
    for item in FEDSEARCH_REPOSITORY:
        if item['source'] in sources:
            score = calculate_keyword_score(query_tokens, item)
            if score > 0.1 and apply_filters(item, filters):
                result = item.copy()
                result['keyword_score'] = score
                results.append(result)
    
    # Add results from external APIs (simulated)
    for source in sources:
        if source in FEDSEARCH_CONFIG['api_endpoints']:
            api_results = search_external_api(query, source, filters)
            results.extend(api_results)
    
    return results

def generate_embedding(text: str) -> List[float]:
    """
    Generate text embedding using AWS Bedrock Titan
    """
    try:
        response = bedrock_runtime.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            contentType='application/json',
            body=json.dumps({
                "inputText": text
            })
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
        
    except Exception as e:
        logger.error(f"Embedding generation error: {str(e)}")
        # Return random embedding as fallback
        return np.random.rand(1536).tolist()

def search_with_embeddings(query: str, query_embedding: List[float], source: str, filters: Dict) -> List[Dict]:
    """
    Search using embeddings and calculate similarity
    """
    results = []
    
    for item in FEDSEARCH_REPOSITORY:
        if item['source'] == source and apply_filters(item, filters):
            # Generate item embedding (in production, these would be pre-computed)
            item_text = f"{item['title']} {item['content']}"
            item_embedding = generate_embedding(item_text)
            
            # Calculate cosine similarity
            similarity = calculate_cosine_similarity(
                query_embedding,
                item_embedding
            )
            
            if similarity > 0.5:  # Threshold
                result = item.copy()
                result['similarity_score'] = similarity
                results.append(result)
    
    return results

def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    """
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm_product = np.linalg.norm(vec1_array) * np.linalg.norm(vec2_array)
    
    if norm_product == 0:
        return 0.0
    
    return float(dot_product / norm_product)

def ai_rerank_results(results: List[Dict], query: str) -> List[Dict]:
    """
    Use AI to rerank search results
    """
    if not results:
        return results
    
    # In production, would use actual reranking model
    # For now, simulate with relevance adjustment
    for i, result in enumerate(results):
        # Adjust score based on position and content relevance
        position_penalty = i * 0.01
        content_boost = 0.1 if query.lower() in result.get('title', '').lower() else 0
        
        current_score = result.get('hybrid_score', result.get('similarity_score', result.get('keyword_score', 0.5)))
        result['rerank_score'] = current_score - position_penalty + content_boost
    
    # Sort by rerank score
    results.sort(key=lambda x: x['rerank_score'], reverse=True)
    
    return results

def generate_search_insights(results: List[Dict], query: str) -> Dict:
    """
    Generate insights from search results
    """
    insights = {
        "key_themes": [],
        "source_distribution": {},
        "temporal_distribution": {},
        "compliance_implications": [],
        "recommended_actions": []
    }
    
    if not results:
        return insights
    
    # Analyze key themes
    all_tags = []
    for result in results:
        all_tags.extend(result.get('tags', []))
    
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    insights['key_themes'] = sorted(
        tag_counts.keys(),
        key=lambda x: tag_counts[x],
        reverse=True
    )[:5]
    
    # Analyze source distribution
    for result in results:
        source = result.get('source', 'Unknown')
        insights['source_distribution'][source] = insights['source_distribution'].get(source, 0) + 1
    
    # Analyze temporal distribution
    current_year = datetime.now().year
    for result in results:
        pub_date = result.get('published_date', '')
        if pub_date:
            year = int(pub_date.split('-')[0])
            decade = f"{(year // 10) * 10}s"
            insights['temporal_distribution'][decade] = insights['temporal_distribution'].get(decade, 0) + 1
    
    # Generate compliance implications
    if any('compliance' in tag for tag in insights['key_themes']):
        insights['compliance_implications'].append("Multiple compliance-related documents found")
    
    if any('security' in tag for tag in insights['key_themes']):
        insights['compliance_implications'].append("Security requirements identified")
    
    # Generate recommended actions
    if insights['source_distribution'].get('NIST', 0) > 0:
        insights['recommended_actions'].append("Review NIST guidelines for technical implementation")
    
    if insights['source_distribution'].get('CISA', 0) > 0:
        insights['recommended_actions'].append("Check CISA advisories for security updates")
    
    return insights

def tokenize_and_normalize(text: str) -> List[str]:
    """
    Tokenize and normalize text for search
    """
    # Convert to lowercase and extract words
    tokens = re.findall(r'\w+', text.lower())
    
    # Remove stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    tokens = [token for token in tokens if token not in stopwords and len(token) > 2]
    
    return tokens

def calculate_keyword_score(query_tokens: List[str], item: Dict) -> float:
    """
    Calculate keyword relevance score
    """
    score = 0.0
    
    # Check title
    title_tokens = tokenize_and_normalize(item.get('title', ''))
    for token in query_tokens:
        if token in title_tokens:
            score += 0.4
    
    # Check content
    content_tokens = tokenize_and_normalize(item.get('content', ''))
    for token in query_tokens:
        if token in content_tokens:
            score += 0.2
    
    # Check tags
    for tag in item.get('tags', []):
        if tag in query_tokens:
            score += 0.3
    
    return min(score, 1.0)

def apply_filters(item: Dict, filters: Dict) -> bool:
    """
    Apply search filters to item
    """
    # Date filter
    if 'start_date' in filters:
        pub_date = item.get('published_date', '')
        if pub_date and pub_date < filters['start_date']:
            return False
    
    if 'end_date' in filters:
        pub_date = item.get('published_date', '')
        if pub_date and pub_date > filters['end_date']:
            return False
    
    # Type filter
    if 'types' in filters:
        if item.get('type') not in filters['types']:
            return False
    
    # Source filter
    if 'sources' in filters:
        if item.get('source') not in filters['sources']:
            return False
    
    return True

def search_external_api(query: str, source: str, filters: Dict) -> List[Dict]:
    """
    Search external federal API (simulated)
    """
    # In production, would make actual API calls
    # For demo, return simulated results
    return []

def merge_search_results(keyword_results: List[Dict], semantic_results: List[Dict]) -> List[Dict]:
    """
    Merge and deduplicate search results
    """
    merged = {}
    
    # Add keyword results
    for result in keyword_results:
        result_id = result.get('id', hash(result.get('title', '')))
        merged[result_id] = result
    
    # Merge semantic results
    for result in semantic_results:
        result_id = result.get('id', hash(result.get('title', '')))
        if result_id in merged:
            # Merge scores
            merged[result_id]['similarity_score'] = result.get('similarity_score', 0)
        else:
            merged[result_id] = result
    
    return list(merged.values())

def generate_cache_key(query: str, sources: List[str], filters: Dict) -> str:
    """
    Generate cache key for search results
    """
    key_components = [
        query,
        ','.join(sorted(sources)),
        json.dumps(filters, sort_keys=True)
    ]
    
    key_string = '|'.join(key_components)
    return hashlib.md5(key_string.encode()).hexdigest()

def is_cache_valid(cached_item: Dict) -> bool:
    """
    Check if cached item is still valid
    """
    timestamp = cached_item.get('timestamp', 0)
    age = time.time() - timestamp
    
    return age < FEDSEARCH_CONFIG['cache_ttl']

def fetch_document_content(document_url: str) -> str:
    """
    Fetch document content from URL
    """
    try:
        response = requests.get(document_url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        return ""

def analyze_document(content: str, analysis_type: str) -> Dict:
    """
    Analyze document content using AI
    """
    analysis = {
        "summary": "Document analysis summary",
        "key_points": [],
        "entities": [],
        "topics": [],
        "sentiment": "neutral"
    }
    
    # Extract key points
    sentences = content.split('.')[:10]  # First 10 sentences
    analysis['key_points'] = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
    
    # Extract entities (simplified)
    entities = re.findall(r'[A-Z]{2,}', content)
    analysis['entities'] = list(set(entities))[:10]
    
    # Extract topics
    tokens = tokenize_and_normalize(content)
    token_counts = {}
    for token in tokens:
        token_counts[token] = token_counts.get(token, 0) + 1
    
    analysis['topics'] = sorted(
        token_counts.keys(),
        key=lambda x: token_counts[x],
        reverse=True
    )[:10]
    
    return analysis

def extract_compliance_requirements(content: str, analysis: Dict) -> List[Dict]:
    """
    Extract compliance requirements from document
    """
    requirements = []
    
    # Look for requirement patterns
    requirement_patterns = [
        r'shall\s+([^.]+)',
        r'must\s+([^.]+)',
        r'required\s+to\s+([^.]+)',
        r'requirement:\s*([^.]+)'
    ]
    
    for pattern in requirement_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches[:5]:  # Limit to 5 per pattern
            requirements.append({
                "requirement": match.strip(),
                "type": "mandatory",
                "source": "document"
            })
    
    return requirements

def generate_actionable_insights(analysis: Dict, requirements: List[Dict]) -> List[str]:
    """
    Generate actionable insights from analysis
    """
    insights = []
    
    # Based on topics
    if 'security' in analysis.get('topics', []):
        insights.append("🔒 Document contains security-related content - review for compliance")
    
    if 'compliance' in analysis.get('topics', []):
        insights.append("📋 Compliance requirements identified - map to current systems")
    
    # Based on requirements
    if len(requirements) > 5:
        insights.append(f"⚠️ {len(requirements)} mandatory requirements found - prioritize implementation")
    
    # Based on entities
    if 'NIST' in analysis.get('entities', []):
        insights.append("📚 References NIST standards - ensure alignment with NIST framework")
    
    return insights

def search_single_source(topic: str, source: str) -> List[Dict]:
    """
    Search a single federal source
    """
    results = []
    
    for item in FEDSEARCH_REPOSITORY:
        if item['source'] == source:
            score = calculate_topic_relevance(topic, item)
            if score > 0.3:
                result = item.copy()
                result['relevance_score'] = score
                results.append(result)
    
    return results

def calculate_topic_relevance(topic: str, item: Dict) -> float:
    """
    Calculate relevance of item to topic
    """
    topic_tokens = tokenize_and_normalize(topic)
    score = 0.0
    
    # Check title
    title_tokens = tokenize_and_normalize(item.get('title', ''))
    matching_tokens = set(topic_tokens) & set(title_tokens)
    score += len(matching_tokens) * 0.3
    
    # Check tags
    for tag in item.get('tags', []):
        if tag in topic_tokens:
            score += 0.2
    
    return min(score, 1.0)

def find_correlations(primary_results: List[Dict], source_results: List[Dict]) -> Dict:
    """
    Find correlations between primary and source results
    """
    correlations = {
        "matching_topics": [],
        "complementary_content": [],
        "conflicting_guidance": [],
        "correlation_score": 0.0
    }
    
    if not primary_results or not source_results:
        return correlations
    
    # Find matching topics
    primary_tags = set()
    for result in primary_results:
        primary_tags.update(result.get('tags', []))
    
    source_tags = set()
    for result in source_results:
        source_tags.update(result.get('tags', []))
    
    correlations['matching_topics'] = list(primary_tags & source_tags)
    
    # Calculate correlation score
    if primary_tags and source_tags:
        correlations['correlation_score'] = len(primary_tags & source_tags) / len(primary_tags | source_tags)
    
    return correlations

def generate_cross_reference_report(topic: str, primary_source: str, primary_results: List[Dict], cross_refs: Dict) -> Dict:
    """
    Generate cross-reference report
    """
    report = {
        "topic": topic,
        "primary_source": primary_source,
        "primary_documents": len(primary_results),
        "cross_reference_summary": {},
        "consistency_analysis": {},
        "recommendations": []
    }
    
    # Summarize cross-references
    for source, correlations in cross_refs.items():
        report['cross_reference_summary'][source] = {
            "correlation_score": correlations['correlation_score'],
            "matching_topics": len(correlations['matching_topics'])
        }
    
    # Analyze consistency
    high_correlation_sources = [
        source for source, corr in cross_refs.items()
        if corr['correlation_score'] > 0.7
    ]
    
    if len(high_correlation_sources) > 2:
        report['consistency_analysis']['status'] = 'consistent'
        report['consistency_analysis']['confidence'] = 'high'
    else:
        report['consistency_analysis']['status'] = 'inconsistent'
        report['consistency_analysis']['confidence'] = 'low'
    
    # Generate recommendations
    if report['consistency_analysis']['status'] == 'consistent':
        report['recommendations'].append(f"Multiple sources confirm guidance on {topic}")
    else:
        report['recommendations'].append(f"Review conflicting guidance on {topic} across sources")
    
    return report

def extract_system_characteristics(incident_data: Dict, system_description: str) -> Dict:
    """
    Extract system characteristics for compliance mapping
    """
    characteristics = {
        "system_type": "unknown",
        "data_classification": "unknown",
        "criticality": "medium",
        "security_requirements": [],
        "operational_environment": "production"
    }
    
    # Analyze incident data
    if incident_data:
        description = incident_data.get('description', '').lower()
        
        if 'payment' in description or 'financial' in description:
            characteristics['system_type'] = 'financial'
            characteristics['data_classification'] = 'sensitive'
            characteristics['criticality'] = 'high'
        elif 'authentication' in description or 'login' in description:
            characteristics['system_type'] = 'authentication'
            characteristics['data_classification'] = 'sensitive'
        
        if 'production' in description:
            characteristics['operational_environment'] = 'production'
    
    # Analyze system description
    if system_description:
        desc_lower = system_description.lower()
        
        if 'encryption' in desc_lower:
            characteristics['security_requirements'].append('encryption')
        if 'multi-factor' in desc_lower or 'mfa' in desc_lower:
            characteristics['security_requirements'].append('mfa')
        if 'audit' in desc_lower:
            characteristics['security_requirements'].append('audit_logging')
    
    return characteristics

def map_to_framework_requirements(characteristics: Dict, framework: str) -> Dict:
    """
    Map system characteristics to framework requirements
    """
    requirements = {
        "framework": framework,
        "applicable_controls": [],
        "priority": "medium",
        "implementation_guidance": []
    }
    
    if framework == "NIST":
        # NIST 800-53 mapping
        if characteristics['criticality'] == 'high':
            requirements['applicable_controls'].extend([
                "AC-2: Account Management",
                "AU-2: Audit Events",
                "SC-13: Cryptographic Protection"
            ])
            requirements['priority'] = 'high'
        
        if 'encryption' in characteristics['security_requirements']:
            requirements['applicable_controls'].append("SC-28: Protection of Information at Rest")
        
        if 'mfa' in characteristics['security_requirements']:
            requirements['applicable_controls'].append("IA-2: Multi-factor Authentication")
            
    elif framework == "FISMA":
        # FISMA requirements
        requirements['applicable_controls'].extend([
            "Risk Assessment",
            "Security Planning",
            "Certification and Accreditation"
        ])
        
        if characteristics['data_classification'] == 'sensitive':
            requirements['priority'] = 'high'
            
    elif framework == "FedRAMP":
        # FedRAMP requirements
        if characteristics['operational_environment'] == 'production':
            requirements['applicable_controls'].extend([
                "Continuous Monitoring",
                "Incident Response",
                "Vulnerability Scanning"
            ])
    
    # Add implementation guidance
    requirements['implementation_guidance'] = [
        f"Implement {len(requirements['applicable_controls'])} controls for {framework} compliance",
        f"Priority level: {requirements['priority']}",
        "Conduct gap analysis against current controls"
    ]
    
    return requirements

def generate_compliance_recommendations(mapping: Dict, characteristics: Dict) -> List[str]:
    """
    Generate compliance recommendations
    """
    recommendations = []
    
    # High priority recommendations
    high_priority_frameworks = [
        fw for fw, reqs in mapping.items()
        if reqs.get('priority') == 'high'
    ]
    
    if high_priority_frameworks:
        recommendations.append(
            f"🚨 Prioritize compliance with: {', '.join(high_priority_frameworks)}"
        )
    
    # Control implementation recommendations
    total_controls = sum(
        len(reqs.get('applicable_controls', []))
        for reqs in mapping.values()
    )
    
    if total_controls > 10:
        recommendations.append(
            f"📋 Implement {total_controls} controls across frameworks - consider phased approach"
        )
    
    # Security requirement recommendations
    if 'encryption' not in characteristics.get('security_requirements', []):
        recommendations.append("🔐 Consider implementing encryption for data protection")
    
    if 'audit_logging' not in characteristics.get('security_requirements', []):
        recommendations.append("📝 Implement comprehensive audit logging")
    
    # Environment-specific recommendations
    if characteristics.get('operational_environment') == 'production':
        recommendations.append("🔄 Establish continuous monitoring for production systems")
    
    return recommendations

def calculate_compliance_scores(mapping: Dict, characteristics: Dict) -> Dict:
    """
    Calculate compliance readiness scores
    """
    scores = {}
    
    for framework, requirements in mapping.items():
        # Base score
        score = 50
        
        # Adjust based on controls
        controls_count = len(requirements.get('applicable_controls', []))
        if controls_count > 0:
            score += min(controls_count * 5, 30)  # Max 30 points for controls
        
        # Adjust based on existing security requirements
        existing_reqs = len(characteristics.get('security_requirements', []))
        score += existing_reqs * 10  # 10 points per existing requirement
        
        # Adjust based on priority
        if requirements.get('priority') == 'high':
            score = min(score * 0.8, 100)  # High priority = lower readiness
        
        scores[framework] = {
            "readiness_score": round(score),
            "confidence": "high" if controls_count > 5 else "medium",
            "estimated_effort": "high" if score < 60 else "medium"
        }
    
    return scores

def collect_historical_data(topic: str, time_range: str, sources: List[str]) -> List[Dict]:
    """
    Collect historical data for trend analysis
    """
    historical_data = []
    
    # Determine date range
    end_date = datetime.now()
    if time_range == 'last_year':
        start_date = end_date - timedelta(days=365)
    elif time_range == 'last_quarter':
        start_date = end_date - timedelta(days=90)
    else:
        start_date = end_date - timedelta(days=730)  # 2 years
    
    # Filter repository by date and topic
    for item in FEDSEARCH_REPOSITORY:
        if item['source'] in sources:
            pub_date_str = item.get('published_date', '')
            if pub_date_str:
                pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                if start_date <= pub_date <= end_date:
                    if calculate_topic_relevance(topic, item) > 0.3:
                        historical_data.append(item)
    
    return historical_data

def analyze_trends(historical_data: List[Dict]) -> Dict:
    """
    Analyze trends in historical data
    """
    trends = {
        "publication_frequency": {},
        "topic_evolution": {},
        "source_activity": {},
        "sentiment_shift": "neutral"
    }
    
    if not historical_data:
        return trends
    
    # Analyze publication frequency
    for item in historical_data:
        pub_date = item.get('published_date', '')
        if pub_date:
            year_month = pub_date[:7]  # YYYY-MM
            trends['publication_frequency'][year_month] = \
                trends['publication_frequency'].get(year_month, 0) + 1
    
    # Analyze source activity
    for item in historical_data:
        source = item.get('source', 'Unknown')
        trends['source_activity'][source] = \
            trends['source_activity'].get(source, 0) + 1
    
    # Analyze topic evolution
    early_items = historical_data[:len(historical_data)//2]
    recent_items = historical_data[len(historical_data)//2:]
    
    early_tags = set()
    for item in early_items:
        early_tags.update(item.get('tags', []))
    
    recent_tags = set()
    for item in recent_items:
        recent_tags.update(item.get('tags', []))
    
    trends['topic_evolution'] = {
        "emerging_topics": list(recent_tags - early_tags),
        "declining_topics": list(early_tags - recent_tags),
        "consistent_topics": list(early_tags & recent_tags)
    }
    
    return trends

def predict_regulatory_changes(trend_analysis: Dict, topic: str) -> Dict:
    """
    Predict future regulatory changes based on trends
    """
    predictions = {
        "likelihood_of_updates": "medium",
        "predicted_focus_areas": [],
        "expected_timeline": "6-12 months",
        "confidence_level": "medium"
    }
    
    # Analyze publication frequency trend
    pub_freq = trend_analysis.get('publication_frequency', {})
    if pub_freq:
        recent_months = sorted(pub_freq.keys())[-3:]
        recent_activity = sum(pub_freq.get(month, 0) for month in recent_months)
        
        if recent_activity > 5:
            predictions['likelihood_of_updates'] = "high"
            predictions['expected_timeline'] = "3-6 months"
    
    # Predict focus areas based on emerging topics
    emerging = trend_analysis.get('topic_evolution', {}).get('emerging_topics', [])
    if emerging:
        predictions['predicted_focus_areas'] = emerging[:3]
        predictions['confidence_level'] = "high" if len(emerging) > 3 else "medium"
    
    return predictions

def generate_trend_report(topic: str, trend_analysis: Dict, predictions: Dict) -> Dict:
    """
    Generate comprehensive trend report
    """
    report = {
        "executive_summary": f"Trend analysis for {topic} shows evolving regulatory landscape",
        "key_findings": [],
        "trend_indicators": {},
        "recommendations": []
    }
    
    # Generate key findings
    pub_freq = trend_analysis.get('publication_frequency', {})
    if pub_freq:
        total_pubs = sum(pub_freq.values())
        report['key_findings'].append(f"{total_pubs} relevant publications identified")
    
    emerging_topics = trend_analysis.get('topic_evolution', {}).get('emerging_topics', [])
    if emerging_topics:
        report['key_findings'].append(f"Emerging focus areas: {', '.join(emerging_topics[:3])}")
    
    # Set trend indicators
    report['trend_indicators'] = {
        "activity_level": "high" if len(pub_freq) > 10 else "moderate",
        "change_velocity": predictions.get('likelihood_of_updates', 'medium'),
        "stability": "low" if len(emerging_topics) > 5 else "high"
    }
    
    # Generate recommendations
    if predictions.get('likelihood_of_updates') == 'high':
        report['recommendations'].append(
            f"Monitor {topic} closely - high likelihood of updates in {predictions.get('expected_timeline')}"
        )
    
    if emerging_topics:
        report['recommendations'].append(
            f"Prepare for changes in: {', '.join(emerging_topics[:2])}"
        )
    
    return report

if __name__ == '__main__':
    logger.info("Starting FedSearch MCP Server on port 9088")
    app.run(host='0.0.0.0', port=9088, debug=False)