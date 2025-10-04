#!/usr/bin/env python3
"""
SRE Copilot - Complete Integrated Dashboard
Combines original SRE Copilot features with enhanced defect management, change correlation, and problem management.
"""

import streamlit as st
import boto3
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import sys
import random
import requests
from botocore.exceptions import ClientError

# Import original modules  
try:
    from user_guide_content import get_all_guides, get_guide_titles
    from streamlit_key_manager import key_manager
    ORIGINAL_MODULES_AVAILABLE = True
except ImportError:
    ORIGINAL_MODULES_AVAILABLE = False

# Add path for modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MCP and feedback modules (original functionality)
try:
    from feedback.feedback_system import FeedbackSystem
    from config.mcp_config import MCPConfigManager
    from enhanced_incident_scenarios import EnhancedIncidentScenarios
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Import enhanced defect management modules
try:
    from defect_driven_incident_scenarios import DefectDrivenIncidentScenarios
    DEFECT_SCENARIOS_AVAILABLE = True
except ImportError:
    DEFECT_SCENARIOS_AVAILABLE = False

try:
    from change_incident_correlator import ChangeIncidentCorrelator
    CHANGE_CORRELATOR_AVAILABLE = True
except ImportError:
    CHANGE_CORRELATOR_AVAILABLE = False

try:
    from change_driven_incident_scenarios import ChangeDrivenIncidentScenarios
    CHANGE_SCENARIOS_AVAILABLE = True
except ImportError:
    CHANGE_SCENARIOS_AVAILABLE = False

try:
    from servicenow_problem_integration import ServiceNowProblemManager
    SERVICENOW_INTEGRATION_AVAILABLE = True
except ImportError:
    SERVICENOW_INTEGRATION_AVAILABLE = False

# Load MCP ports configuration
try:
    with open('mcp_ports.json', 'r') as f:
        MCP_PORTS = json.load(f)
except:
    MCP_PORTS = {
        'splunk': 9080,
        'dynatrace': 9081,
        'servicenow': 9082,
        'confluence': 9083,
        'gitlab': 9084,
        'alm_octane': 9085,
        'jira': 9086
    }

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Complete Integrated Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS combining original and new styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .critical { background-color: #ffebee; border-left: 4px solid #f44336; }
    .warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
    .info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
    .success { background-color: #e8f5e9; border-left: 4px solid #4caf50; }
    .incident-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .defect-correlation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .defect-card {
        background-color: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .change-card {
        background-color: #f0fff4;
        border: 1px solid #c6f6d5;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .problem-card {
        background-color: #f7fafc;
        border: 1px solid #cbd5e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .mcp-status {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .mcp-online { background-color: #4caf50; }
    .mcp-offline { background-color: #f44336; }
    .mcp-warning { background-color: #ff9800; }
</style>
""", unsafe_allow_html=True)


class SRECopilotComplete:
    """Complete SRE Copilot with original + enhanced functionality"""
    
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.bedrock_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Initialize enhanced modules if available
        if CHANGE_CORRELATOR_AVAILABLE:
            self.change_correlator = ChangeIncidentCorrelator()
        
        if SERVICENOW_INTEGRATION_AVAILABLE:
            self.problem_manager = ServiceNowProblemManager()
        
        # Initialize session state
        if 'current_incident' not in st.session_state:
            st.session_state.current_incident = None
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'mcp_enabled' not in st.session_state:
            st.session_state.mcp_enabled = MCP_AVAILABLE
    
    def run_root_cause_analysis(self, ops_item_id):
        """Run comprehensive root cause analysis (original functionality)"""
        with st.sidebar:
            with st.spinner("🤖 Running root cause analysis..."):
                progress_bar = st.progress(0)
                
                try:
                    # Step 1: Get OpsItem details
                    st.info("📋 Fetching incident details...")
                    progress_bar.progress(20)
                    
                    response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
                    ops_item = response['OpsItem']
                    
                    # Step 2: Invoke Bedrock agent
                    st.info("🤖 Analyzing with AI agents...")
                    progress_bar.progress(60)
                    
                    # Call supervisor agent
                    bedrock_response = self.bedrock_client.invoke_agent(
                        agentId='PJMZCQ6JAP',
                        agentAliasId='ZXIRZXRTBX',
                        sessionId=f"session-{int(time.time())}",
                        inputText=f"Analyze incident {ops_item_id}: {ops_item.get('Title', '')}. {ops_item.get('Description', '')}"
                    )
                    
                    # Process response
                    analysis_text = ""
                    for event in bedrock_response['completion']:
                        if 'chunk' in event:
                            chunk_data = event['chunk']['bytes'].decode('utf-8')
                            analysis_text += chunk_data
                    
                    progress_bar.progress(100)
                    
                    # Store results
                    st.session_state.current_incident = {
                        'ops_item_id': ops_item_id,
                        'title': ops_item.get('Title', ''),
                        'description': ops_item.get('Description', ''),
                        'status': ops_item.get('Status', ''),
                        'severity': ops_item.get('Severity', ''),
                        'source': ops_item.get('Source', ''),
                        'created_time': ops_item.get('CreatedTime', ''),
                        'last_modified_time': ops_item.get('LastModifiedTime', ''),
                        'analysis': analysis_text,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                    
                    st.success("✅ Analysis complete!")
                    time.sleep(1)
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    progress_bar.progress(0)
                    raise e
    
    def create_ops_item(self, title, description, severity="Medium"):
        """Create a new OpsItem (original functionality)"""
        try:
            response = self.ssm_client.create_ops_item(
                Description=description,
                Title=title,
                Source="SRE-Copilot",
                Severity=severity,
                Tags=[
                    {'Key': 'CreatedBy', 'Value': 'SRE-Copilot'},
                    {'Key': 'Namespace', 'Value': 'SREDemo/Application'},
                    {'Key': 'Environment', 'Value': 'Production'},
                    {'Key': 'Timestamp', 'Value': datetime.now().isoformat()}
                ]
            )
            return response['OpsItemId']
        except Exception as e:
            st.error(f"Failed to create OpsItem: {str(e)}")
            return None
    
    def render_main_dashboard(self):
        """Render the complete integrated dashboard"""
        st.markdown("<h1 class='main-header'>🔍 SRE Copilot - Complete Integrated Analysis</h1>", 
                   unsafe_allow_html=True)
        
        # Sidebar configuration
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # MCP Status
            if MCP_AVAILABLE:
                st.subheader("🌐 MCP Services")
                self.display_mcp_status()
            
            # System metrics
            st.subheader("📊 System Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active Incidents", "12", "↑2")
            with col2:
                st.metric("Resolved Today", "8", "↑3")
        
        # Main navigation tabs - Complete integration
        tab_names = [
            "🚨 Incident Management",      # Original
            "🔍 Analyze Incident",         # Original  
            "🔧 Recent Changes",           # Original
            "📚 Knowledge Base",           # Original
            "📊 Analytics",                # Original
            "🐛 Defect Management",        # Enhanced
            "🔄 Change Management",        # Enhanced
            "🔗 Change Correlation",       # Enhanced
            "🎫 Problem Management",       # Enhanced
            "📈 Correlation Analytics",    # Enhanced
            "🧪 Test Scenarios"            # Enhanced
        ]
        
        if MCP_AVAILABLE:
            tab_names.extend(["🌐 MCP Status", "📈 Feedback Analytics"])
        
        if ORIGINAL_MODULES_AVAILABLE:
            tab_names.append("❓ User Guide")
        
        main_tabs = st.tabs(tab_names)
        
        # Original functionality tabs
        with main_tabs[0]:
            self.render_incident_management()
            
        with main_tabs[1]:
            self.render_analyze_incident()
            
        with main_tabs[2]:
            self.render_recent_changes()
            
        with main_tabs[3]:
            self.render_knowledge_base()
            
        with main_tabs[4]:
            self.render_analytics()
        
        # Enhanced functionality tabs
        with main_tabs[5]:
            self.render_defect_management()
            
        with main_tabs[6]:
            self.render_change_management()
            
        with main_tabs[7]:
            self.render_change_correlation()
            
        with main_tabs[8]:
            self.render_problem_management()
            
        with main_tabs[9]:
            self.render_correlation_analytics()
            
        with main_tabs[10]:
            self.render_test_scenarios()
        
        # Optional tabs
        tab_idx = 11
        if MCP_AVAILABLE:
            with main_tabs[tab_idx]:
                self.render_mcp_status_detailed()
            tab_idx += 1
            
            with main_tabs[tab_idx]:
                self.render_feedback_analytics()
            tab_idx += 1
        
        if ORIGINAL_MODULES_AVAILABLE and tab_idx < len(main_tabs):
            with main_tabs[tab_idx]:
                self.render_user_guide()

    def render_incident_management(self):
        """Render original incident management functionality"""
        st.header("🚨 Incident Management")
        
        if st.session_state.current_incident:
            self.display_incident_details()
        else:
            self.display_welcome()
    
    def display_welcome(self):
        """Display enhanced welcome screen (original)"""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>Welcome to Complete SRE Copilot</h2>
            <p>Generate real incidents, analyze with AI, and manage the full lifecycle with defect/change correlation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced feature cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔥 Real Incidents</h3>
                <p>Generate actual AWS incidents with logs and metrics</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <h3>🤖 AI Analysis</h3>
                <p>Bedrock agents analyze AWS data for root causes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <h3>🐛 Defect Correlation</h3>
                <p>Link incidents to defects with AI-powered analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔄 Change Management</h3>
                <p>Track changes and correlate with incidents</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons for incident creation
        st.markdown("---")
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Generate Test Incident", type="primary", use_container_width=True):
                self.generate_test_incident()
        
        with col2:
            if st.button("🔍 Analyze Existing Incident", type="secondary", use_container_width=True):
                st.session_state.show_analysis_tab = True
                st.experimental_rerun()
        
        with col3:
            if st.button("📚 Browse Knowledge Base", type="secondary", use_container_width=True):
                st.session_state.show_kb_tab = True
                st.experimental_rerun()
    
    def generate_test_incident(self):
        """Generate a test incident (original functionality)"""
        scenarios = [
            {
                "title": "API Gateway Performance Degradation",
                "description": "API Gateway experiencing increased latency and intermittent 500 errors. Response times increased from 200ms to 2000ms average. Affecting customer checkout process.",
                "severity": "High"
            },
            {
                "title": "Database Connection Pool Exhaustion", 
                "description": "RDS database connection pool reaching maximum capacity. Applications unable to establish new database connections. Error rate at 15%.",
                "severity": "High"
            },
            {
                "title": "Lambda Function Cold Start Issues",
                "description": "Lambda functions experiencing excessive cold start delays. Timeout errors increasing. Performance degraded across multiple services.",
                "severity": "Medium"
            }
        ]
        
        selected_scenario = random.choice(scenarios)
        
        ops_item_id = self.create_ops_item(
            title=selected_scenario["title"],
            description=selected_scenario["description"],
            severity=selected_scenario["severity"]
        )
        
        if ops_item_id:
            st.success(f"✅ Generated test incident: {ops_item_id}")
            
            # Auto-analyze the generated incident
            with st.spinner("🤖 Running analysis on generated incident..."):
                self.run_root_cause_analysis(ops_item_id)
                st.success("📋 Analysis complete! View results below.")
                st.experimental_rerun()
        else:
            st.error("❌ Failed to generate test incident")

    def display_incident_details(self):
        """Display comprehensive incident details (original functionality)"""
        incident = st.session_state.current_incident
        
        # Header with incident info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### 🚨 {incident.get('title', 'Unknown Incident')}")
            st.text(f"ID: {incident.get('ops_item_id', 'N/A')}")
        
        with col2:
            status = incident.get('status', 'Unknown')
            status_color = {'Open': '🔴', 'InProgress': '🟡', 'Resolved': '🟢'}.get(status, '⚪')
            st.markdown(f"**Status:** {status_color} {status}")
        
        with col3:
            severity = incident.get('severity', 'Unknown')
            severity_color = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
            st.markdown(f"**Severity:** {severity_color} {severity}")
        
        # Analysis results
        if 'analysis' in incident and incident['analysis']:
            with st.expander("🎯 Root Cause Analysis Results", expanded=True):
                st.markdown(incident['analysis'])
        
        # Incident details
        with st.expander("📋 Incident Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Description:**")
                st.text_area("", incident.get('description', ''), disabled=True, height=100, key="incident_desc")
                
            with col2:
                st.markdown("**Timeline:**")
                st.text(f"Created: {incident.get('created_time', 'N/A')}")
                st.text(f"Modified: {incident.get('last_modified_time', 'N/A')}")
                if 'analysis_timestamp' in incident:
                    st.text(f"Analyzed: {incident['analysis_timestamp']}")
        
        # Enhanced actions - link to defect management
        st.markdown("---")
        st.subheader("🔗 Related Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🐛 Create Defect", type="secondary", use_container_width=True):
                st.session_state.create_defect_from_incident = incident
                st.experimental_rerun()
        
        with col2:
            if st.button("🔄 Check Changes", type="secondary", use_container_width=True):
                st.session_state.check_changes_for_incident = incident
                st.experimental_rerun()
        
        with col3:
            if st.button("🎫 Create Problem", type="secondary", use_container_width=True):
                st.session_state.create_problem_from_incident = incident
                st.experimental_rerun()
        
        with col4:
            if st.button("🔍 Analyze Another", type="primary", use_container_width=True):
                st.session_state.current_incident = None
                st.experimental_rerun()

    def render_analyze_incident(self):
        """Render the analyze incident tab (original functionality)"""
        st.header("🔍 Analyze Incident")
        
        # Check if we should show analysis results
        if hasattr(st.session_state, 'show_analysis_results') and st.session_state.show_analysis_results:
            if st.session_state.current_incident:
                self.display_incident_details()
                st.session_state.show_analysis_results = False
                return
        
        st.info("Analyze existing OpsItems to understand root causes, business impact, and correlations.")
        
        # Get recent OpsItems for selection
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {'Key': 'Status', 'Values': ['Open', 'InProgress'], 'Operator': 'Equal'}
                ],
                MaxResults=20
            )
            
            ops_items = response.get('OpsItemSummaries', [])
            
            if ops_items:
                options = ["-- Enter manually --"] + [
                    f"{item['OpsItemId']} - {item['Title']}" 
                    for item in ops_items
                ]
                
                selected = st.selectbox("Select an OpsItem to analyze:", options)
                
                if selected == "-- Enter manually --":
                    ops_item_id = st.text_input("Enter OpsItem ID:")
                else:
                    ops_item_id = selected.split(' - ')[0]
                
                if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True):
                    if ops_item_id:
                        self.run_root_cause_analysis(ops_item_id)
                        st.session_state.show_analysis_results = True
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter or select an OpsItem ID")
            else:
                st.warning("No open OpsItems found. Enter an OpsItem ID manually.")
                ops_item_id = st.text_input("Enter OpsItem ID:")
                
                if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True):
                    if ops_item_id:
                        self.run_root_cause_analysis(ops_item_id)
                        st.session_state.show_analysis_results = True
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter an OpsItem ID")
        
        except Exception as e:
            st.error(f"Error fetching OpsItems: {str(e)}")
            ops_item_id = st.text_input("Enter OpsItem ID:")
            
            if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True):
                if ops_item_id:
                    self.run_root_cause_analysis(ops_item_id)
                    st.session_state.show_analysis_results = True
                    st.experimental_rerun()
                else:
                    st.warning("Please enter an OpsItem ID")

    def render_recent_changes(self):
        """Render recent changes tab (original functionality)"""
        st.header("🔧 Recent Changes")
        
        st.info("Monitor recent changes that might correlate with incidents")
        
        # Mock change data for demonstration
        changes_data = [
            {
                "Change ID": "CHG0001",
                "Title": "API Gateway Configuration Update",
                "Type": "Configuration",
                "Status": "Completed",
                "Date": datetime.now() - timedelta(hours=2),
                "Risk": "Medium"
            },
            {
                "Change ID": "CHG0002", 
                "Title": "Database Schema Migration",
                "Type": "Database",
                "Status": "In Progress",
                "Date": datetime.now() - timedelta(hours=6),
                "Risk": "High"
            }
        ]
        
        df = pd.DataFrame(changes_data)
        st.dataframe(df, use_container_width=True)
        
        # Add change analysis button
        if st.button("🔗 Analyze Change-Incident Correlations", type="primary"):
            if CHANGE_CORRELATOR_AVAILABLE:
                st.info("Change correlation analysis would be performed here")
            else:
                st.warning("Change correlation module not available")

    def render_knowledge_base(self):
        """Render knowledge base tab (original functionality)"""
        st.header("📚 SRE Knowledge Base")
        
        kb_tabs = st.tabs(["🔍 Search", "📖 Browse", "➕ Add Document", "🧪 Test Analysis"])
        
        with kb_tabs[0]:
            st.subheader("🔍 Search Knowledge Base")
            
            query = st.text_input("Enter search query:", placeholder="e.g., API Gateway errors")
            
            if st.button("Search", type="primary") and query:
                st.info("Searching knowledge base...")
                # Mock search results
                st.success("Found 3 relevant documents")
                
                with st.expander("Best Practices: API Gateway Error Handling"):
                    st.markdown("**Confidence:** 95%")
                    st.markdown("Common causes of API Gateway errors include...")
        
        with kb_tabs[1]:
            st.subheader("📖 Browse Documents")
            st.info("Browse existing knowledge base documents")
            
            categories = ["Incident Response", "AWS Services", "Monitoring", "Troubleshooting"]
            selected_category = st.selectbox("Select category:", categories)
            
            if selected_category:
                st.markdown(f"**Documents in {selected_category}:**")
                st.markdown("- API Gateway Troubleshooting Guide")
                st.markdown("- Database Performance Issues")
                st.markdown("- Lambda Function Optimization")
        
        with kb_tabs[2]:
            st.subheader("➕ Add Document")
            
            title = st.text_input("Document Title:")
            content = st.text_area("Content:", height=200)
            category = st.selectbox("Category:", ["Incident Response", "AWS Services", "Monitoring"])
            
            if st.button("Add Document", type="primary"):
                if title and content:
                    st.success(f"Added document: {title}")
                else:
                    st.warning("Please fill in title and content")
        
        with kb_tabs[3]:
            st.subheader("🧪 Test Analysis")
            st.info("Test the knowledge base analysis capabilities")
            
            test_query = st.text_area("Test Query:", placeholder="Describe an incident scenario")
            
            if st.button("Test Analysis", type="primary") and test_query:
                st.info("Analyzing with knowledge base...")
                st.success("Analysis complete - recommendations would appear here")

    def render_analytics(self):
        """Render analytics tab (original functionality)"""
        st.header("📊 Analytics Dashboard")
        
        # Mock analytics data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Incidents", "127", "↑12%")
        
        with col2:
            st.metric("Mean Resolution Time", "2.3h", "↓15%")
        
        with col3:
            st.metric("Defects Created", "23", "↑8%")
        
        with col4:
            st.metric("Change Correlations", "45", "↑22%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Incident Trends")
            
            # Mock trend data
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
            incidents = [random.randint(10, 30) for _ in dates]
            
            fig = px.line(x=dates, y=incidents, title="Monthly Incident Count")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Resolution Sources")
            
            sources = ['AI Analysis', 'Knowledge Base', 'Manual Investigation', 'Change Correlation']
            values = [45, 25, 20, 10]
            
            fig = px.pie(values=values, names=sources, title="Resolution Method Distribution")
            st.plotly_chart(fig, use_container_width=True)

    def render_defect_management(self):
        """Render enhanced defect management functionality"""
        st.header("🐛 Defect Management")
        
        # Get recent incidents for dropdown
        recent_incidents = self.get_recent_incidents()
        
        defect_tabs = st.tabs(["🆕 Create Defect", "📋 View Defects", "🔗 Defect Analytics"])
        
        with defect_tabs[0]:
            st.subheader("🆕 Create New Defect")
            
            # Incident selection dropdown
            if recent_incidents:
                incident_options = ["-- Select incident --"] + [
                    f"{inc['OpsItemId']} - {inc['Title']}" for inc in recent_incidents
                ]
                
                selected_incident = st.selectbox(
                    "🔍 Link to Incident:",
                    incident_options,
                    help="Select an incident to auto-populate defect fields"
                )
                
                # Auto-populate if incident selected
                if selected_incident != "-- Select incident --":
                    incident_id = selected_incident.split(' - ')[0]
                    incident_title = selected_incident.split(' - ', 1)[1]
                    
                    st.info(f"📋 Auto-populating from incident: {incident_id}")
                    
                    defect_title = st.text_input(
                        "Defect Title:", 
                        value=f"Defect from incident: {incident_title}"
                    )
                    defect_description = st.text_area(
                        "Description:",
                        value=f"Root cause analysis required for incident {incident_id}.\n\nIncident: {incident_title}"
                    )
                else:
                    defect_title = st.text_input("Defect Title:")
                    defect_description = st.text_area("Description:")
            else:
                st.warning("No recent incidents found")
                defect_title = st.text_input("Defect Title:")
                defect_description = st.text_area("Description:")
            
            # Defect details
            col1, col2 = st.columns(2)
            
            with col1:
                severity = st.selectbox("Severity:", ["Low", "Medium", "High", "Critical"])
                component = st.text_input("Component:", value="API Gateway")
                
            with col2:
                environment = st.selectbox("Environment:", ["Development", "Staging", "Production"])
                assigned_to = st.text_input("Assigned To:", value="sre-team@company.com")
            
            # Platform selection
            platform = st.radio("Create defect in:", ["ALM Octane", "Jira", "Both"])
            
            if st.button("🐛 Create Defect", type="primary", use_container_width=True):
                self.create_defect_from_form(
                    defect_title, defect_description, severity, component, 
                    environment, assigned_to, platform, 
                    selected_incident if selected_incident != "-- Select incident --" else None
                )
        
        with defect_tabs[1]:
            st.subheader("📋 View Existing Defects")
            self.display_existing_defects()
        
        with defect_tabs[2]:
            st.subheader("🔗 Defect Analytics")
            self.display_defect_analytics()

    def render_change_management(self):
        """Render change management functionality"""
        st.header("🔄 Change Management")
        
        change_tabs = st.tabs(["📋 Change Requests", "🆕 New Change", "📊 Change Analytics"])
        
        with change_tabs[0]:
            st.subheader("📋 Recent Change Requests")
            self.display_change_requests()
        
        with change_tabs[1]:
            st.subheader("🆕 Create Change Request")
            self.create_change_request_form()
        
        with change_tabs[2]:
            st.subheader("📊 Change Analytics")
            self.display_change_analytics()

    def render_change_correlation(self):
        """Render change-incident correlation analysis"""
        st.header("🔗 Change-Incident Correlation")
        
        if not CHANGE_CORRELATOR_AVAILABLE:
            st.warning("Change correlation module not available")
            return
        
        correlation_tabs = st.tabs(["🔍 Analyze Correlation", "📈 Correlation Results", "⚙️ Configuration"])
        
        with correlation_tabs[0]:
            st.subheader("🔍 Analyze Change-Incident Correlation")
            
            # Get recent incidents
            recent_incidents = self.get_recent_incidents()
            
            if recent_incidents:
                incident_options = [f"{inc['OpsItemId']} - {inc['Title']}" for inc in recent_incidents]
                selected_incident = st.selectbox("Select Incident:", incident_options)
                
                if st.button("🔍 Analyze Correlations", type="primary"):
                    incident_id = selected_incident.split(' - ')[0]
                    incident_description = selected_incident.split(' - ', 1)[1]
                    
                    with st.spinner("Analyzing change-incident correlations..."):
                        results = self.change_correlator.analyze_change_incident_correlation(
                            incident_id, incident_description
                        )
                    
                    st.success("Analysis complete!")
                    self.display_correlation_results(results)
            else:
                st.warning("No incidents found for correlation analysis")
        
        with correlation_tabs[1]:
            st.subheader("📈 Recent Correlation Results")
            st.info("Historical correlation analysis results would be displayed here")
        
        with correlation_tabs[2]:
            st.subheader("⚙️ Correlation Configuration")
            self.display_correlation_config()

    def render_problem_management(self):
        """Render ServiceNow problem management"""
        st.header("🎫 Problem Management")
        
        if not SERVICENOW_INTEGRATION_AVAILABLE:
            st.warning("ServiceNow integration not available")
            return
        
        problem_tabs = st.tabs(["🆕 Create Problem", "📋 View Problems", "🔗 Problem Analytics"])
        
        with problem_tabs[0]:
            st.subheader("🆕 Create Problem from Incident")
            self.create_problem_form()
        
        with problem_tabs[1]:
            st.subheader("📋 Existing Problems")
            self.display_existing_problems()
        
        with problem_tabs[2]:
            st.subheader("🔗 Problem Analytics")
            self.display_problem_analytics()

    def render_correlation_analytics(self):
        """Render comprehensive correlation analytics"""
        st.header("📈 Correlation Analytics")
        
        analytics_tabs = st.tabs(["📊 Overview", "🐛 Defect Correlations", "🔄 Change Correlations", "🎫 Problem Tracking"])
        
        with analytics_tabs[0]:
            st.subheader("📊 Correlation Overview")
            self.display_correlation_overview()
        
        with analytics_tabs[1]:
            st.subheader("🐛 Defect Correlation Analysis")
            self.display_defect_correlation_analytics()
        
        with analytics_tabs[2]:
            st.subheader("🔄 Change Correlation Analysis")
            self.display_change_correlation_analytics()
        
        with analytics_tabs[3]:
            st.subheader("🎫 Problem Tracking Analysis")
            self.display_problem_tracking_analytics()

    def render_test_scenarios(self):
        """Render test scenarios combining defect and change scenarios"""
        st.header("🧪 Test Scenarios")
        
        scenario_tabs = st.tabs(["🐛 Defect Scenarios", "🔄 Change Scenarios", "🔗 Combined Analysis"])
        
        with scenario_tabs[0]:
            st.subheader("🐛 Defect-Driven Incident Scenarios")
            if DEFECT_SCENARIOS_AVAILABLE:
                self.display_defect_scenarios()
            else:
                st.warning("Defect scenarios module not available")
        
        with scenario_tabs[1]:
            st.subheader("🔄 Change-Driven Incident Scenarios")
            if CHANGE_SCENARIOS_AVAILABLE:
                self.display_change_scenarios()
            else:
                st.warning("Change scenarios module not available")
        
        with scenario_tabs[2]:
            st.subheader("🔗 Combined Scenario Analysis")
            self.display_combined_scenario_analysis()

    # Helper methods for enhanced functionality
    
    def get_recent_incidents(self):
        """Get recent incidents from AWS SSM"""
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {'Key': 'Status', 'Values': ['Open', 'InProgress', 'Resolved'], 'Operator': 'Equal'}
                ],
                MaxResults=20
            )
            return response.get('OpsItemSummaries', [])
        except Exception as e:
            st.error(f"Error fetching incidents: {str(e)}")
            return []

    def create_defect_from_form(self, title, description, severity, component, environment, assigned_to, platform, incident):
        """Create defect in specified platform(s)"""
        success_count = 0
        
        defect_data = {
            "name": title,
            "description": description,
            "severity": severity,
            "component": component,
            "environment": environment,
            "assigned_to": assigned_to
        }
        
        if incident:
            defect_data["source_incident_id"] = incident.split(' - ')[0]
        
        if platform in ["ALM Octane", "Both"]:
            try:
                response = requests.post(
                    f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects",
                    json=defect_data,
                    timeout=10
                )
                if response.status_code == 201:
                    st.success(f"✅ Created ALM Octane defect: {response.json().get('id')}")
                    success_count += 1
                else:
                    st.error(f"❌ Failed to create ALM Octane defect: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error creating ALM Octane defect: {str(e)}")
        
        if platform in ["Jira", "Both"]:
            try:
                jira_data = {
                    "project": "SREPROJ",
                    "summary": title,
                    "description": description,
                    "issue_type": "Bug",
                    "priority": severity,
                    "assignee": assigned_to
                }
                
                response = requests.post(
                    f"http://localhost:{MCP_PORTS['jira']}/jira/issues",
                    json=jira_data,
                    timeout=10
                )
                if response.status_code == 201:
                    st.success(f"✅ Created Jira issue: {response.json().get('key')}")
                    success_count += 1
                else:
                    st.error(f"❌ Failed to create Jira issue: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error creating Jira issue: {str(e)}")
        
        if success_count > 0:
            st.success(f"✅ Successfully created {success_count} defect(s)")

    def display_existing_defects(self):
        """Display existing defects from both platforms"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 ALM Octane Defects")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['alm_octane']}/octane/defects", timeout=5)
                if response.status_code == 200:
                    defects = response.json()
                    for defect in defects[:5]:  # Show first 5
                        with st.expander(f"Defect {defect.get('id')}: {defect.get('name', 'Unknown')}"):
                            st.text(f"Severity: {defect.get('severity', 'N/A')}")
                            st.text(f"Status: {defect.get('status', 'N/A')}")
                            st.text(f"Component: {defect.get('component', 'N/A')}")
                else:
                    st.warning("Could not fetch ALM Octane defects")
            except Exception as e:
                st.error(f"Error fetching ALM Octane defects: {str(e)}")
        
        with col2:
            st.subheader("🎫 Jira Issues")
            try:
                response = requests.get(f"http://localhost:{MCP_PORTS['jira']}/jira/issues", timeout=5)
                if response.status_code == 200:
                    issues = response.json()
                    for issue in issues[:5]:  # Show first 5
                        with st.expander(f"Issue {issue.get('key')}: {issue.get('summary', 'Unknown')}"):
                            st.text(f"Type: {issue.get('issue_type', 'N/A')}")
                            st.text(f"Priority: {issue.get('priority', 'N/A')}")
                            st.text(f"Assignee: {issue.get('assignee', 'N/A')}")
                else:
                    st.warning("Could not fetch Jira issues")
            except Exception as e:
                st.error(f"Error fetching Jira issues: {str(e)}")

    def display_defect_analytics(self):
        """Display defect analytics"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Defects", "47", "↑5")
        
        with col2:
            st.metric("Open Defects", "12", "↓2")
        
        with col3:
            st.metric("Avg Resolution Time", "3.2 days", "↓0.5")
        
        # Mock chart
        severity_data = ["High: 8", "Medium: 15", "Low: 24"]
        st.subheader("📊 Defects by Severity")
        for item in severity_data:
            st.text(f"• {item}")

    def display_mcp_status(self):
        """Display MCP service status in sidebar"""
        for service, port in MCP_PORTS.items():
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    st.markdown(f'<span class="mcp-status mcp-online"></span> {service.title()}', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="mcp-status mcp-warning"></span> {service.title()}', 
                              unsafe_allow_html=True)
            except:
                st.markdown(f'<span class="mcp-status mcp-offline"></span> {service.title()}', 
                          unsafe_allow_html=True)

    # Placeholder methods for additional functionality
    def display_change_requests(self): pass
    def create_change_request_form(self): pass
    def display_change_analytics(self): pass
    def display_correlation_results(self, results): pass
    def display_correlation_config(self): pass
    def create_problem_form(self): pass
    def display_existing_problems(self): pass
    def display_problem_analytics(self): pass
    def display_correlation_overview(self): pass
    def display_defect_correlation_analytics(self): pass
    def display_change_correlation_analytics(self): pass
    def display_problem_tracking_analytics(self): pass
    def display_defect_scenarios(self): pass
    def display_change_scenarios(self): pass
    def display_combined_scenario_analysis(self): pass
    def render_mcp_status_detailed(self): pass
    def render_feedback_analytics(self): pass
    def render_user_guide(self): pass


# Main application
def main():
    """Main application entry point"""
    app = SRECopilotComplete()
    app.render_main_dashboard()


if __name__ == "__main__":
    main()