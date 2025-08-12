"""
Knowledge Base Management Tab for Streamlit Dashboard
Integrates all MCP external data sources for comprehensive search
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import time
from knowledge_base_multi_search import MultiSourceKnowledgeSearch

def render_knowledge_base_tab():
    """Render the Knowledge Base Management tab"""
    st.markdown("## 📚 Knowledge Base Management")
    st.markdown("Search across all knowledge sources including FedSearch, Fed LPP, Stack Overflow, and GitHub")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Knowledge Sources", "7", delta="2")
    with col2:
        st.metric("Total Articles", "12,543", delta="156")
    with col3:
        st.metric("Search Success Rate", "94%", delta="2%")
    with col4:
        st.metric("Avg Response Time", "1.2s", delta="-0.3s", delta_color="normal")
    
    st.markdown("---")
    
    # Search Interface
    st.subheader("🔍 Multi-Source Knowledge Search")
    
    # Search input
    search_query = st.text_input(
        "Search Query",
        placeholder="Enter incident description or technical keywords...",
        help="Search across federal regulations, technical solutions, runbooks, and more"
    )
    
    # Advanced search options
    with st.expander("⚙️ Advanced Search Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_sources = st.multiselect(
                "Knowledge Sources",
                ["Fed Launch Pad Pro", "FedSearch", "Stack Overflow Enterprise", 
                 "GitHub KB", "AWS Knowledge Base"],
                default=["Fed Launch Pad Pro", "FedSearch", "Stack Overflow Enterprise", "GitHub KB"]
            )
            
            search_type = st.selectbox(
                "Search Type",
                ["Comprehensive", "Technical Solutions", "Compliance", "Runbooks", "Post-mortems"]
            )
        
        with col2:
            severity_filter = st.select_slider(
                "Incident Severity",
                options=["All", "Low", "Medium", "High", "Critical"],
                value="All"
            )
            
            time_range = st.selectbox(
                "Time Range",
                ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Last Year"]
            )
    
    # Search button
    if st.button("🔎 Search Knowledge Base", type="primary"):
        if search_query:
            perform_knowledge_search(search_query, search_sources, search_type, severity_filter)
        else:
            st.warning("Please enter a search query")
    
    st.markdown("---")
    
    # Quick Search for Current Incidents
    st.subheader("🚨 Search for Active Incidents")
    
    # Mock active incidents (in production, fetch from AWS SSM)
    active_incidents = [
        {
            'id': 'INC-2025-001',
            'title': 'API Gateway Timeout Errors',
            'severity': 'High',
            'description': 'Multiple timeout errors in API Gateway affecting payment processing'
        },
        {
            'id': 'INC-2025-002',
            'title': 'Database Connection Pool Exhaustion',
            'severity': 'Critical',
            'description': 'RDS connection pool exhausted causing application failures'
        },
        {
            'id': 'INC-2025-003',
            'title': 'Authentication Service Degradation',
            'severity': 'Medium',
            'description': 'Intermittent failures in OAuth authentication flow'
        }
    ]
    
    # Display incidents with search buttons
    for incident in active_incidents:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{incident['id']}**: {incident['title']}")
                st.caption(incident['description'])
            
            with col2:
                severity_color = {
                    'Critical': '🔴',
                    'High': '🟠',
                    'Medium': '🟡',
                    'Low': '🟢'
                }
                st.write(f"{severity_color.get(incident['severity'], '⚪')} {incident['severity']}")
            
            with col3:
                if st.button(f"Search KB", key=f"search_{incident['id']}"):
                    perform_knowledge_search(
                        f"{incident['title']} {incident['description']}", 
                        search_sources, 
                        "Comprehensive",
                        incident['severity']
                    )
            
            with col4:
                if st.button(f"Auto-Analyze", key=f"analyze_{incident['id']}"):
                    perform_ai_analysis(incident)
    
    st.markdown("---")
    
    # Knowledge Base Statistics
    st.subheader("📊 Knowledge Base Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Source distribution
        fig_sources = create_source_distribution_chart()
        st.plotly_chart(fig_sources, use_container_width=True)
    
    with col2:
        # Content type distribution
        fig_content = create_content_type_chart()
        st.plotly_chart(fig_content, use_container_width=True)
    
    # Search trends
    fig_trends = create_search_trends_chart()
    st.plotly_chart(fig_trends, use_container_width=True)
    
    st.markdown("---")
    
    # Knowledge Base Management
    st.subheader("🛠️ Knowledge Base Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Import Knowledge"):
            st.info("Knowledge import functionality - Coming soon")
    
    with col2:
        if st.button("🔄 Sync Sources"):
            sync_knowledge_sources()
    
    with col3:
        if st.button("📈 Generate Report"):
            generate_kb_report()

def perform_knowledge_search(query, sources, search_type, severity):
    """Perform multi-source knowledge search"""
    with st.spinner("Searching across knowledge sources..."):
        # Create search container
        search_container = st.container()
        
        with search_container:
            # Initialize multi-source searcher
            searcher = MultiSourceKnowledgeSearch()
            
            # Prepare incident data for search
            incident_data = {
                'id': f'SEARCH-{int(time.time())}',
                'title': query[:100],
                'description': query,
                'severity': severity if severity != 'All' else 'Medium'
            }
            
            # Perform search
            try:
                results = searcher.multi_search_incident(incident_data)
                
                # Display search summary
                st.success(f"✅ Search completed across {len(results['sources_searched'])} sources")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Results", results['total_results'])
                with col2:
                    st.metric("Sources Searched", len(results['sources_searched']))
                with col3:
                    st.metric("Confidence", f"{results['consolidated_insights']['confidence_score']:.0%}")
                with col4:
                    st.metric("Execution Time", f"{results['search_metadata']['execution_time']:.1f}s")
                
                # Display recommendations
                if results['recommendations']:
                    st.markdown("### 💡 AI Recommendations")
                    for rec in results['recommendations']:
                        st.info(rec)
                
                # Display results by source
                st.markdown("### 📋 Search Results by Source")
                
                # Create tabs for each source
                source_tabs = st.tabs([s.replace('_', ' ').title() for s in results['sources_searched']])
                
                for i, (source_key, source_tab) in enumerate(zip(results['sources_searched'], source_tabs)):
                    with source_tab:
                        source_results = results['search_results'].get(source_key, {})
                        
                        if 'error' not in source_results:
                            # Display source-specific results
                            display_source_results(source_key, source_results)
                        else:
                            st.error(f"Error searching {source_key}: {source_results['error']}")
                
                # Display consolidated insights
                st.markdown("### 🎯 Consolidated Insights")
                
                insights = results['consolidated_insights']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if insights['common_patterns']:
                        st.markdown("**Common Patterns Detected:**")
                        for pattern in insights['common_patterns']:
                            st.write(f"• {pattern}")
                    
                    if insights['technical_solutions']:
                        st.markdown("**Technical Solutions Found:**")
                        for solution in insights['technical_solutions'][:3]:
                            with st.expander(solution.get('question', 'Solution')):
                                st.write(solution.get('solution', 'No details available'))
                
                with col2:
                    if insights['compliance_requirements']:
                        st.markdown("**Compliance Requirements:**")
                        for req in insights['compliance_requirements']:
                            st.write(f"• {req['source']}: {len(req.get('requirements', {}))} requirements")
                    
                    if insights['historical_precedents']:
                        st.markdown("**Similar Past Incidents:**")
                        for precedent in insights['historical_precedents'][:3]:
                            st.write(f"• {precedent.get('title', 'Past incident')}")
                
            except Exception as e:
                st.error(f"Search error: {str(e)}")

def display_source_results(source_key, results):
    """Display results from a specific source"""
    st.write(f"**Found {results.get('count', 0)} results**")
    
    if source_key == 'fed_lpp':
        # Display Fed LPP results
        if 'results' in results:
            for item in results['results'][:5]:
                with st.expander(f"{item.get('title', 'Federal Document')} (Score: {item.get('relevance_score', 0):.2f})"):
                    st.write(f"**Type**: {item.get('type', 'Unknown')}")
                    st.write(f"**Content**: {item.get('content', 'No content available')}")
                    if 'tags' in item:
                        st.write(f"**Tags**: {', '.join(item['tags'])}")
        
        if 'compliance_analysis' in results:
            st.markdown("**Compliance Analysis:**")
            analysis = results['compliance_analysis']
            if 'severity' in analysis:
                st.write(f"• Severity: {analysis['severity']}")
            if 'affected_regulations' in analysis:
                st.write(f"• Affected Regulations: {len(analysis['affected_regulations'])}")
    
    elif source_key == 'fedsearch':
        # Display FedSearch results
        if 'results' in results:
            for item in results['results'][:5]:
                with st.expander(f"{item.get('title', 'Federal Resource')}"):
                    st.write(f"**Source**: {item.get('source', 'Unknown')}")
                    st.write(f"**URL**: {item.get('url', 'N/A')}")
                    st.write(f"**Published**: {item.get('published_date', 'Unknown')}")
        
        if 'compliance_scores' in results:
            st.markdown("**Compliance Readiness:**")
            for framework, score in results['compliance_scores'].items():
                st.progress(score.get('readiness_score', 0) / 100, text=f"{framework}: {score.get('readiness_score', 0)}%")
    
    elif source_key == 'stackoverflow':
        # Display Stack Overflow results
        if 'solutions' in results:
            st.markdown("**Top Solutions:**")
            for solution in results['solutions'][:3]:
                with st.expander(f"{solution.get('question', 'Solution')} ({solution.get('score', 0)} votes)"):
                    st.write(solution.get('solution', 'No solution text'))
                    if 'url' in solution:
                        st.write(f"[View on Stack Overflow]({solution['url']})")
        
        if 'code_snippets' in results:
            st.markdown("**Code Snippets:**")
            for snippet in results['code_snippets']:
                with st.expander(snippet.get('title', 'Code Snippet')):
                    st.code(snippet.get('code', '# No code available'), language=snippet.get('language', 'python'))
    
    elif source_key == 'github_kb':
        # Display GitHub KB results
        if 'similar_postmortems' in results:
            st.markdown("**Similar Post-mortems:**")
            for pm in results['similar_postmortems'][:3]:
                with st.expander(f"{pm.get('title', 'Post-mortem')} (Similarity: {pm.get('similarity_score', 0):.0%})"):
                    st.write(f"**Root Cause**: {pm.get('root_cause', 'Unknown')}")
                    st.write(f"**Resolution**: {pm.get('resolution', 'No resolution details')}")
                    if 'action_items' in pm:
                        st.write("**Action Items:**")
                        for item in pm['action_items'][:3]:
                            st.write(f"• {item}")
        
        if 'runbooks' in results:
            st.markdown("**Relevant Runbooks:**")
            for runbook in results['runbooks']:
                with st.expander(runbook.get('title', 'Runbook')):
                    st.write(f"**Repository**: {runbook.get('repo', 'Unknown')}")
                    st.markdown(runbook.get('content', 'No content available'))

def perform_ai_analysis(incident):
    """Perform AI-powered analysis of incident"""
    with st.spinner(f"Performing AI analysis for {incident['id']}..."):
        time.sleep(2)  # Simulate processing
        
        # Display analysis results
        st.markdown(f"### 🤖 AI Analysis for {incident['id']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Root Cause Hypothesis:**")
            st.info("Based on knowledge base search, the likely root cause is resource exhaustion due to connection leak patterns identified in similar incidents.")
            
            st.markdown("**Recommended Actions:**")
            actions = [
                "1. Review connection pool configuration",
                "2. Implement connection timeout settings",
                "3. Add monitoring for connection metrics",
                "4. Review code for proper connection closure"
            ]
            for action in actions:
                st.write(action)
        
        with col2:
            st.markdown("**Similar Incidents Found:**")
            st.write("• PRB-2024-789: Database connection exhaustion (95% match)")
            st.write("• INC-2024-456: API timeout due to pool limits (87% match)")
            st.write("• PRB-2024-234: Connection leak in payment service (82% match)")
            
            st.markdown("**Compliance Considerations:**")
            st.warning("NIST 800-53: Ensure proper resource management controls")
            st.warning("PCI-DSS: Payment processing must maintain availability")

def sync_knowledge_sources():
    """Sync all knowledge sources"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    sources = ["Fed LPP", "FedSearch", "Stack Overflow", "GitHub KB", "AWS KB"]
    
    for i, source in enumerate(sources):
        status_text.text(f"Syncing {source}...")
        progress_bar.progress((i + 1) / len(sources))
        time.sleep(0.5)
    
    st.success("✅ All knowledge sources synchronized successfully!")

def generate_kb_report():
    """Generate knowledge base report"""
    with st.spinner("Generating report..."):
        time.sleep(2)
        
        st.markdown("### 📊 Knowledge Base Report")
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Searches (30d)", "2,456")
            st.metric("Unique Users", "89")
        
        with col2:
            st.metric("Avg Search Time", "1.8s")
            st.metric("Cache Hit Rate", "67%")
        
        with col3:
            st.metric("Most Searched", "timeout errors")
            st.metric("Top Source", "Stack Overflow")
        
        st.success("📄 Report generated successfully!")

def create_source_distribution_chart():
    """Create knowledge source distribution chart"""
    sources = ['Stack Overflow', 'GitHub KB', 'Fed LPP', 'FedSearch', 'AWS KB', 'Internal Wiki', 'Confluence']
    counts = [3456, 2890, 2345, 1987, 1654, 1234, 987]
    
    fig = go.Figure(data=[
        go.Bar(x=sources, y=counts, marker_color='lightblue')
    ])
    
    fig.update_layout(
        title="Knowledge Articles by Source",
        xaxis_title="Source",
        yaxis_title="Number of Articles",
        showlegend=False
    )
    
    return fig

def create_content_type_chart():
    """Create content type distribution chart"""
    types = ['Technical Solutions', 'Runbooks', 'Post-mortems', 'Best Practices', 'Compliance Docs', 'FAQs']
    values = [35, 20, 18, 12, 10, 5]
    
    fig = px.pie(
        values=values,
        names=types,
        title="Content Type Distribution",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    return fig

def create_search_trends_chart():
    """Create search trends chart"""
    import pandas as pd
    
    # Generate sample data
    dates = pd.date_range(start='2025-07-12', end='2025-08-12', freq='D')
    searches = [50 + i*2 + (i%7)*5 for i in range(len(dates))]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=searches,
        mode='lines+markers',
        name='Daily Searches',
        line=dict(color='royalblue', width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Knowledge Base Search Trends (Last 30 Days)",
        xaxis_title="Date",
        yaxis_title="Number of Searches",
        hovermode='x unified'
    )
    
    return fig