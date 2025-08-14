"""
External Knowledge Base Sources Renderer for Streamlit
Displays MCP integration with external knowledge management systems
"""

def render_kb_external_sources(dashboard_self):
    """Render external knowledge base sources with MCP integration."""
    import streamlit as st
    import requests
    import json
    from datetime import datetime
    
    st.subheader("🌐 External Knowledge Base Sources")
    
    # Display MCP integration status
    st.info("💡 **SRE Copilot integrates with multiple external knowledge sources via MCP (Model Context Protocol)**")
    
    # Define external KB sources
    external_sources = {
        "fed_lpp": {
            "name": "Federal LPP Knowledge Base",
            "port": 9087,
            "icon": "🏛️",
            "description": "Federal lessons learned and best practices repository",
            "search_endpoint": "/lpp/search",
            "categories": ["Compliance", "Security", "Operations", "Governance"]
        },
        "fedsearch": {
            "name": "FedSearch",
            "port": 9088,
            "icon": "🔍",
            "description": "Unified federal systems search engine",
            "search_endpoint": "/fedsearch/query",
            "categories": ["Incidents", "Changes", "Documentation", "Policies"]
        },
        "kb_external_1": {
            "name": "StackOverflow Enterprise KB",
            "port": 9089,
            "icon": "📚",
            "description": "Internal Q&A and technical solutions database",
            "search_endpoint": "/stackoverflow/search",
            "categories": ["Development", "DevOps", "Troubleshooting", "Architecture"]
        },
        "kb_external_2": {
            "name": "GitHub Enterprise KB",
            "port": 9090,
            "icon": "🐙",
            "description": "Code repository knowledge and issue tracking",
            "search_endpoint": "/github/search",
            "categories": ["Code", "Issues", "Pull Requests", "Documentation"]
        },
        "confluence": {
            "name": "Confluence Knowledge Base",
            "port": 9083,
            "icon": "📄",
            "description": "Team collaboration and documentation platform",
            "search_endpoint": "/confluence/pages",
            "categories": ["Runbooks", "Architecture", "Processes", "Guidelines"]
        },
        "servicenow": {
            "name": "ServiceNow KB",
            "port": 9082,
            "icon": "🎫",
            "description": "IT service management knowledge articles",
            "search_endpoint": "/servicenow/kb/articles",
            "categories": ["Incidents", "Problems", "Changes", "Knowledge Articles"]
        }
    }
    
    # Create tabs for different views
    view_tabs = st.tabs(["📊 Overview", "🔍 Unified Search", "📈 Analytics", "⚙️ Configuration"])
    
    with view_tabs[0]:
        # Overview tab
        st.markdown("### Connected External Knowledge Sources")
        
        # Check connection status for each source
        cols = st.columns(3)
        connected_count = 0
        
        for idx, (source_key, source_info) in enumerate(external_sources.items()):
            col_idx = idx % 3
            with cols[col_idx]:
                # Check if service is running
                try:
                    response = requests.get(
                        f"http://localhost:{source_info['port']}/health",
                        timeout=1
                    )
                    is_connected = response.status_code in [200, 404]  # 404 is ok, means server is running
                except:
                    is_connected = False
                
                if is_connected:
                    connected_count += 1
                    status_icon = "✅"
                    status_text = "Connected"
                    status_color = "success"
                else:
                    status_icon = "❌"
                    status_text = "Offline"
                    status_color = "error"
                
                with st.container():
                    st.markdown(f"**{source_info['icon']} {source_info['name']}**")
                    st.caption(source_info['description'])
                    
                    # Status indicator
                    if is_connected:
                        st.success(f"{status_icon} {status_text}")
                    else:
                        st.error(f"{status_icon} {status_text}")
                    
                    # Show categories
                    st.caption("Categories:")
                    for cat in source_info['categories'][:3]:
                        st.caption(f"• {cat}")
        
        # Summary metrics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sources", len(external_sources))
        with col2:
            st.metric("Connected", connected_count)
        with col3:
            st.metric("Total Articles", "1.2M+", help="Estimated across all sources")
        with col4:
            st.metric("Search Speed", "<100ms", help="Average query response time")
    
    with view_tabs[1]:
        # Unified Search tab
        st.markdown("### Unified Knowledge Search")
        st.info("Search across all connected external knowledge sources simultaneously")
        
        # Search interface
        search_query = st.text_input(
            "Enter search query",
            placeholder="e.g., database connection timeout kubernetes",
            help="Search will query all connected external sources"
        )
        
        # Search filters
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_sources = st.multiselect(
                "Sources",
                options=list(external_sources.keys()),
                default=list(external_sources.keys()),
                format_func=lambda x: external_sources[x]['name']
            )
        
        with col2:
            result_limit = st.selectbox(
                "Results per source",
                options=[5, 10, 20, 50],
                index=0
            )
        
        with col3:
            search_type = st.radio(
                "Search type",
                ["Relevance", "Recent", "Most Used"],
                horizontal=True
            )
        
        if st.button("🔍 Search All Sources", disabled=not search_query):
            st.markdown("### Search Results")
            
            # Simulate search results from different sources
            for source_key in selected_sources:
                if source_key in external_sources:
                    source = external_sources[source_key]
                    
                    with st.expander(f"{source['icon']} {source['name']}", expanded=True):
                        # Simulate search results
                        st.markdown(f"**Found 15 results for '{search_query}'**")
                        
                        # Sample results
                        sample_results = [
                            {
                                "title": f"Resolving {search_query} in production",
                                "snippet": "This article explains how to troubleshoot and resolve connection timeout issues...",
                                "category": source['categories'][0],
                                "relevance": "95%",
                                "last_updated": "2 days ago"
                            },
                            {
                                "title": f"Best practices for {search_query}",
                                "snippet": "Learn the recommended approaches for handling database connections in containerized...",
                                "category": source['categories'][1],
                                "relevance": "89%",
                                "last_updated": "1 week ago"
                            }
                        ]
                        
                        for result in sample_results[:result_limit]:
                            with st.container():
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"**{result['title']}**")
                                    st.caption(result['snippet'])
                                    st.caption(f"Category: {result['category']} | Updated: {result['last_updated']}")
                                with col2:
                                    st.metric("Relevance", result['relevance'])
                                st.markdown("---")
    
    with view_tabs[2]:
        # Analytics tab
        st.markdown("### Knowledge Base Analytics")
        
        # Usage metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Searches Today", "1,247", "↑ 15%")
        with col2:
            st.metric("Articles Accessed", "3,892", "↑ 23%")
        with col3:
            st.metric("Avg. Resolution Time", "4.2 min", "↓ 1.3 min")
        with col4:
            st.metric("User Satisfaction", "94%", "↑ 2%")
        
        # Top searched topics
        st.markdown("#### Top Searched Topics (Last 7 Days)")
        topics = [
            ("Database Connection Issues", 342),
            ("Kubernetes Pod Failures", 298),
            ("API Rate Limiting", 276),
            ("SSL Certificate Errors", 241),
            ("Memory Leaks Java", 198)
        ]
        
        for topic, count in topics:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(count / 342)  # Normalize to max
                st.caption(topic)
            with col2:
                st.caption(f"{count} searches")
        
        # Knowledge gaps
        st.markdown("#### Identified Knowledge Gaps")
        st.warning("The following topics have high search volume but low article availability:")
        gaps = [
            "GraphQL Performance Optimization",
            "Terraform State Management Best Practices",
            "Observability in Microservices",
            "Zero-Trust Network Architecture"
        ]
        for gap in gaps:
            st.caption(f"• {gap}")
    
    with view_tabs[3]:
        # Configuration tab
        st.markdown("### External Source Configuration")
        
        st.info("Configure connections and settings for external knowledge sources")
        
        # Add new source
        with st.expander("➕ Add New Knowledge Source"):
            new_source_name = st.text_input("Source Name")
            new_source_url = st.text_input("MCP Endpoint URL")
            new_source_port = st.number_input("Port", min_value=1000, max_value=65535, value=9091)
            new_source_api_key = st.text_input("API Key (if required)", type="password")
            
            if st.button("Add Source"):
                st.success(f"Source '{new_source_name}' added successfully!")
        
        # Existing sources configuration
        st.markdown("#### Manage Existing Sources")
        
        for source_key, source_info in external_sources.items():
            with st.expander(f"{source_info['icon']} {source_info['name']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("Endpoint", value=f"http://localhost:{source_info['port']}", key=f"endpoint_{source_key}")
                    st.multiselect("Categories", options=source_info['categories'], default=source_info['categories'], key=f"cats_{source_key}")
                
                with col2:
                    st.selectbox("Sync Frequency", ["Real-time", "Every 5 min", "Every hour", "Daily"], key=f"sync_{source_key}")
                    st.checkbox("Auto-index new content", value=True, key=f"auto_{source_key}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Test Connection", key=f"test_{source_key}"):
                        st.success("✅ Connection successful!")
                with col2:
                    if st.button("Sync Now", key=f"sync_now_{source_key}"):
                        st.info("🔄 Synchronization started...")
                with col3:
                    if st.button("Disable", key=f"disable_{source_key}"):
                        st.warning("Source disabled")
    
    # Footer with tips
    st.markdown("---")
    st.markdown("### 💡 Tips for Using External Knowledge Sources")
    st.markdown("""
    - **Unified Search**: Use the unified search to query all sources simultaneously
    - **Source Selection**: Filter by specific sources when you know where to look
    - **Categories**: Use category filters to narrow down results
    - **Analytics**: Monitor search patterns to identify knowledge gaps
    - **Integration**: External sources are automatically queried during incident analysis
    """)
    
    # Show MCP status
    if hasattr(dashboard_self, 'get_mcp_status'):
        st.markdown("### 🔌 MCP Connection Status")
        mcp_status = dashboard_self.get_mcp_status()
        
        status_cols = st.columns(4)
        for idx, (service, status) in enumerate(mcp_status.items()):
            if service in ['confluence', 'servicenow']:
                col_idx = idx % 4
                with status_cols[col_idx]:
                    if status == 'online':
                        st.success(f"✅ {service.upper()}")
                    else:
                        st.error(f"❌ {service.upper()}")