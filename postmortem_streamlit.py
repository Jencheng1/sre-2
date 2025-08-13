"""
Post-Mortem Analysis UI Component for Streamlit
This file contains the render_postmortem_analysis method to be added to streamlit_app.py
"""

def render_postmortem_analysis(self):
    """Render the Post-Mortem Analysis tab"""
    st.header("📋 Post-Mortem Analysis")
    
    st.markdown("""
    Generate comprehensive post-mortem reports for resolved incidents with AI-powered insights,
    root cause analysis, and actionable recommendations.
    """)
    
    if not POSTMORTEM_AVAILABLE:
        st.error("Post-mortem agent not available. Please check installation.")
        return
    
    # Initialize session state
    if 'postmortem_report' not in st.session_state:
        st.session_state.postmortem_report = None
    if 'postmortem_markdown' not in st.session_state:
        st.session_state.postmortem_markdown = None
    
    # Post-mortem generation options
    postmortem_tabs = st.tabs(["📝 Generate Report", "📊 View Reports", "🔍 Analyze OpsItem"])
    
    with postmortem_tabs[0]:
        self._render_postmortem_generator()
    
    with postmortem_tabs[1]:
        self._render_postmortem_viewer()
        
    with postmortem_tabs[2]:
        self._render_opsitem_postmortem()

def _render_postmortem_generator(self):
    """Render post-mortem report generator"""
    st.subheader("Generate Post-Mortem Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Incident details form
        with st.form("postmortem_form"):
            st.markdown("### Incident Details")
            
            incident_id = st.text_input(
                "Incident ID",
                value=f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}",
                help="Unique identifier for this incident"
            )
            
            incident_type = st.selectbox(
                "Incident Type",
                ["outage", "performance", "security", "data_loss", "configuration"],
                help="Select the type of incident"
            )
            
            severity = st.selectbox(
                "Severity",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                help="Incident severity level"
            )
            
            description = st.text_area(
                "Incident Description",
                placeholder="Describe what happened...",
                help="Provide a detailed description of the incident"
            )
            
            # Time information
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input("Start Date", datetime.now().date())
                start_time = st.time_input("Start Time", datetime.now().time())
            
            with col_end:
                end_date = st.date_input("End Date", datetime.now().date())
                end_time = st.time_input("End Time", datetime.now().time())
            
            # Services affected
            services = st.text_input(
                "Services Affected",
                placeholder="e.g., payment-api, auth-service",
                help="Comma-separated list of affected services"
            )
            
            # Additional context
            st.markdown("### Additional Context")
            
            detection_method = st.text_input(
                "How was the incident detected?",
                placeholder="e.g., Monitoring alert, customer report"
            )
            
            immediate_actions = st.text_area(
                "Immediate Actions Taken",
                placeholder="List the initial response actions..."
            )
            
            # Metrics data (optional)
            include_metrics = st.checkbox("Include CloudWatch Metrics Analysis")
            
            submitted = st.form_submit_button("🚀 Generate Post-Mortem Report", type="primary")
    
    with col2:
        # Recent incidents for reference
        st.markdown("### Recent Incidents")
        st.info("Select a recent incident to use as a template or reference")
        
        # Mock recent incidents
        recent_incidents = [
            {"id": "INC-20240115-001", "type": "outage", "title": "Database Connection Pool Exhaustion"},
            {"id": "INC-20240114-003", "type": "performance", "title": "API Response Time Degradation"},
            {"id": "INC-20240113-002", "type": "security", "title": "Unauthorized Access Attempt"}
        ]
        
        for incident in recent_incidents:
            if st.button(f"📄 {incident['id']}: {incident['title']}", key=f"recent_{incident['id']}"):
                st.info(f"Loading template from {incident['id']}...")
    
    # Process form submission
    if submitted:
        if not description:
            st.error("Please provide an incident description")
            return
            
        with st.spinner("🤖 Generating AI-powered post-mortem report..."):
            try:
                # Prepare incident data
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)
                
                incident_data = {
                    'incident_id': incident_id,
                    'type': incident_type,
                    'severity': severity,
                    'description': description,
                    'start_time': start_datetime,
                    'resolution_time': end_datetime.isoformat(),
                    'service': services,
                    'detection_method': detection_method,
                    'immediate_actions': immediate_actions,
                    'raw_data': {}
                }
                
                # Include metrics if requested
                if include_metrics:
                    incident_data['raw_data']['metrics'] = {
                        'CPUUtilization': [{'Maximum': 85, 'Timestamp': start_datetime.isoformat()}],
                        'ErrorRate': [{'Maximum': 45, 'Timestamp': start_datetime.isoformat()}]
                    }
                
                # Generate post-mortem
                agent = PostMortemAgent()
                report = agent.analyze_incident(incident_data)
                markdown_report = agent.generate_markdown_report(report)
                
                # Store in session state
                st.session_state.postmortem_report = report
                st.session_state.postmortem_markdown = markdown_report
                
                st.success("✅ Post-mortem report generated successfully!")
                
                # Show preview
                with st.expander("📄 Report Preview", expanded=True):
                    st.markdown(markdown_report)
                    
                # Download options
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="📥 Download Markdown",
                        data=markdown_report,
                        file_name=f"postmortem_{incident_id}.md",
                        mime="text/markdown"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download JSON",
                        data=json.dumps(asdict(report), indent=2),
                        file_name=f"postmortem_{incident_id}.json",
                        mime="application/json"
                    )
                with col3:
                    if st.button("📧 Email Report"):
                        st.info("Email functionality coming soon!")
                        
            except Exception as e:
                st.error(f"Error generating post-mortem: {str(e)}")
                logger.error(f"Post-mortem generation error: {str(e)}")

def _render_postmortem_viewer(self):
    """Render post-mortem report viewer"""
    st.subheader("View Post-Mortem Reports")
    
    if st.session_state.postmortem_report:
        report = st.session_state.postmortem_report
        
        # Report metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{report.duration_minutes} min")
        with col2:
            st.metric("Users Impacted", f"{report.users_impacted:,}")
        with col3:
            st.metric("Revenue Impact", report.revenue_impact)
        with col4:
            st.metric("AI Confidence", f"{report.ai_confidence_score:.0%}")
        
        # Main report sections
        report_tabs = st.tabs(["📊 Summary", "⏱️ Timeline", "🔍 Analysis", "✅ Action Items", "📈 Metrics"])
        
        with report_tabs[0]:
            # Executive Summary
            st.markdown("### Executive Summary")
            st.markdown(f"**Title:** {report.title}")
            st.markdown(f"**Severity:** {report.severity}")
            st.markdown(f"**Root Cause:** {report.root_cause}")
            
            # Impact Summary
            st.markdown("### Impact")
            impact_col1, impact_col2 = st.columns(2)
            with impact_col1:
                st.markdown("**Services Affected:**")
                for service in report.services_affected:
                    st.markdown(f"- {service}")
            with impact_col2:
                st.markdown(f"**SLA Breached:** {'Yes 🔴' if report.sla_breached else 'No 🟢'}")
                st.markdown(f"**Detection Method:** {report.detection_method}")
        
        with report_tabs[1]:
            # Timeline
            st.markdown("### Incident Timeline")
            
            timeline_df = pd.DataFrame(report.timeline)
            if not timeline_df.empty:
                # Create timeline visualization
                fig = go.Figure()
                
                for i, event in enumerate(report.timeline):
                    color = 'red' if event.get('severity') == 'critical' else 'orange' if event.get('severity') == 'warning' else 'blue'
                    fig.add_trace(go.Scatter(
                        x=[event['time']],
                        y=[i],
                        mode='markers+text',
                        marker=dict(size=12, color=color),
                        text=event['event'],
                        textposition="top center",
                        name=event['event']
                    ))
                
                fig.update_layout(
                    title="Incident Timeline",
                    xaxis_title="Time",
                    yaxis_title="Events",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Timeline table
                st.dataframe(timeline_df, use_container_width=True)
        
        with report_tabs[2]:
            # Root Cause Analysis
            st.markdown("### Root Cause Analysis")
            st.error(f"🔍 **Root Cause:** {report.root_cause}")
            
            st.markdown("### Contributing Factors")
            for factor in report.contributing_factors:
                st.warning(f"• {factor}")
            
            # What went well/wrong
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ What Went Well")
                for item in report.what_went_well:
                    st.success(f"• {item}")
            
            with col2:
                st.markdown("### ❌ What Went Wrong")
                for item in report.what_went_wrong:
                    st.error(f"• {item}")
            
            # Lessons Learned
            st.markdown("### 💡 Lessons Learned")
            for lesson in report.lessons_learned:
                st.info(f"• {lesson}")
        
        with report_tabs[3]:
            # Action Items
            st.markdown("### Action Items")
            
            action_df = pd.DataFrame(report.action_items)
            if not action_df.empty:
                # Add status indicators
                def style_priority(val):
                    color = 'red' if val == 'HIGH' else 'orange' if val == 'MEDIUM' else 'green'
                    return f'color: {color}'
                
                styled_df = action_df.style.applymap(style_priority, subset=['priority'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Action item details
                st.markdown("### Preventive Measures")
                for measure in report.preventive_measures:
                    st.markdown(f"• 🛡️ {measure}")
                
                st.markdown("### Monitoring Improvements")
                for improvement in report.monitoring_improvements:
                    st.markdown(f"• 📊 {improvement}")
        
        with report_tabs[4]:
            # Metrics and Data
            st.markdown("### Performance Metrics")
            
            # Create sample metrics visualization
            if 'raw_data' in st.session_state.get('incident_data', {}):
                metrics_data = st.session_state.incident_data.get('raw_data', {}).get('metrics', {})
                
                for metric_name, datapoints in metrics_data.items():
                    if datapoints:
                        df = pd.DataFrame(datapoints)
                        fig = px.line(df, x='Timestamp', y='Maximum', title=metric_name)
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No metrics data available for this incident")
    else:
        st.info("No post-mortem report generated yet. Use the 'Generate Report' tab to create one.")

def _render_opsitem_postmortem(self):
    """Render OpsItem-based post-mortem analysis"""
    st.subheader("Analyze OpsItem for Post-Mortem")
    
    st.info("Select an OpsItem to generate a post-mortem report based on actual incident data")
    
    # Get OpsItems
    try:
        ssm = boto3.client('ssm')
        response = ssm.describe_ops_items(
            OpsItemFilters=[
                {
                    'Key': 'Status',
                    'Values': ['Resolved', 'Closed'],
                    'Operator': 'Equal'
                }
            ],
            MaxResults=10
        )
        
        ops_items = response.get('OpsItemSummaries', [])
        
        if ops_items:
            # Display OpsItems
            ops_item_options = [f"{item['OpsItemId']}: {item.get('Title', 'No Title')}" for item in ops_items]
            selected_ops_item = st.selectbox("Select OpsItem", ops_item_options)
            
            if st.button("🔍 Analyze OpsItem", type="primary"):
                ops_item_id = selected_ops_item.split(':')[0]
                
                with st.spinner(f"Analyzing OpsItem {ops_item_id}..."):
                    # Get full OpsItem details
                    ops_item_response = ssm.get_ops_item(OpsItemId=ops_item_id)
                    ops_item = ops_item_response['OpsItem']
                    
                    # Convert OpsItem to incident data format
                    incident_data = {
                        'incident_id': ops_item_id,
                        'type': 'operational',  # Default type
                        'severity': ops_item.get('Severity', 'MEDIUM'),
                        'description': ops_item.get('Description', 'No description available'),
                        'start_time': ops_item.get('CreatedTime', datetime.now()),
                        'resolution_time': ops_item.get('LastModifiedTime', datetime.now()).isoformat(),
                        'service': ops_item.get('Source', 'Unknown'),
                        'operational_data': ops_item.get('OperationalData', {})
                    }
                    
                    # Generate post-mortem
                    agent = PostMortemAgent()
                    report = agent.analyze_incident(incident_data)
                    markdown_report = agent.generate_markdown_report(report)
                    
                    # Store in session state
                    st.session_state.postmortem_report = report
                    st.session_state.postmortem_markdown = markdown_report
                    
                    st.success(f"✅ Post-mortem report generated for {ops_item_id}")
                    
                    # Show report
                    with st.expander("📄 Generated Report", expanded=True):
                        st.markdown(markdown_report)
        else:
            st.warning("No resolved OpsItems found. Resolve some incidents first.")
            
    except Exception as e:
        st.error(f"Error fetching OpsItems: {str(e)}")
        
        # Provide sample OpsItem analysis
        if st.button("🧪 Try Sample OpsItem Analysis"):
            sample_incident = {
                'incident_id': 'OPS-SAMPLE-001',
                'type': 'outage',
                'severity': 'HIGH',
                'description': 'Sample database outage affecting production services',
                'start_time': datetime.now() - timedelta(hours=2),
                'resolution_time': datetime.now().isoformat(),
                'service': 'database-cluster'
            }
            
            agent = PostMortemAgent()
            report = agent.analyze_incident(sample_incident)
            markdown_report = agent.generate_markdown_report(report)
            
            st.session_state.postmortem_report = report
            st.session_state.postmortem_markdown = markdown_report
            
            st.success("✅ Sample post-mortem report generated")
            st.markdown(markdown_report)