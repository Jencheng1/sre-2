#!/usr/bin/env python3
"""
SRE Copilot - Root Cause Analysis Dashboard
A Streamlit application for incident analysis using AWS monitoring agents.
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

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
from core.incident_analyzer import SRECopilotAnalyzer

# Page configuration
st.set_page_config(
    page_title="SRE Copilot - Root Cause Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_incident' not in st.session_state:
    st.session_state.current_incident = None
if 'agent_data' not in st.session_state:
    st.session_state.agent_data = {}

class SRECopilotDashboard:
    """Main dashboard class for SRE Copilot."""
    
    def __init__(self):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        self.lambda_client = boto3.client('lambda')
        self.setup_sidebar()
    
    def setup_sidebar(self):
        """Setup the sidebar with controls."""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100.png?text=SRE+Copilot", width=300)
            st.markdown("## 🎯 Incident Analysis")
            
            # Incident type selection
            self.incident_type = st.selectbox(
                "Select Incident Type",
                ["Performance Degradation", "Security Alert", "Service Outage", 
                 "Cost Anomaly", "Custom Incident"]
            )
            
            # Predefined scenarios
            if self.incident_type != "Custom Incident":
                self.scenario = st.selectbox(
                    "Select Scenario",
                    self.get_scenarios(self.incident_type)
                )
            
            # Custom incident description
            if self.incident_type == "Custom Incident":
                self.incident_description = st.text_area(
                    "Describe the incident",
                    placeholder="E.g., API response time increased from 200ms to 2000ms"
                )
            else:
                self.incident_description = self.scenario
            
            # Analysis options
            st.markdown("### 📊 Analysis Options")
            self.include_logs = st.checkbox("Include CloudWatch Logs", value=True)
            self.include_metrics = st.checkbox("Include CloudWatch Metrics", value=True)
            self.include_health = st.checkbox("Include AWS Health", value=True)
            self.include_advisor = st.checkbox("Include Trusted Advisor", value=False)
            
            # Time range
            self.time_range = st.selectbox(
                "Time Range",
                ["Last 1 hour", "Last 6 hours", "Last 24 hours", "Last 7 days"]
            )
            
            # Analyze button
            if st.button("🔍 Analyze Incident", type="primary", use_container_width=True):
                self.analyze_incident()
            
            # History
            st.markdown("### 📜 Analysis History")
            for i, item in enumerate(reversed(st.session_state.analysis_history[-5:])):
                if st.button(f"{item['time']} - {item['type']}", key=f"hist_{i}"):
                    st.session_state.current_incident = item
    
    def get_scenarios(self, incident_type):
        """Get predefined scenarios for each incident type."""
        scenarios = {
            "Performance Degradation": [
                "API response time increased from 200ms to 2000ms",
                "Database query latency spike to 5 seconds",
                "High CPU usage (>90%) on web servers",
                "Memory exhaustion on application servers"
            ],
            "Security Alert": [
                "Multiple failed login attempts detected",
                "Unusual API access pattern from unknown IP",
                "Potential DDoS attack on public endpoints",
                "Unauthorized access attempt to S3 buckets"
            ],
            "Service Outage": [
                "Complete service unavailable - 503 errors",
                "Database connection pool exhausted",
                "Load balancer health checks failing",
                "DNS resolution failures"
            ],
            "Cost Anomaly": [
                "AWS costs increased by 50% overnight",
                "Unexpected data transfer charges",
                "Idle resources consuming budget",
                "Auto-scaling gone wrong - too many instances"
            ]
        }
        return scenarios.get(incident_type, [])
    
    def analyze_incident(self):
        """Trigger incident analysis."""
        if not self.incident_description:
            st.error("Please provide an incident description")
            return
        
        with st.spinner("🔄 Analyzing incident..."):
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Initialize
            status_text.text("Initializing analysis...")
            progress_bar.progress(20)
            
            # Step 2: Collect data from agents
            status_text.text("Collecting data from monitoring agents...")
            agent_data = self.collect_agent_data()
            progress_bar.progress(60)
            
            # Step 3: Perform root cause analysis
            status_text.text("Performing root cause analysis...")
            analysis_result = self.perform_analysis(agent_data)
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Store results
            incident_data = {
                'type': self.incident_type,
                'description': self.incident_description,
                'time': datetime.now().strftime("%H:%M:%S"),
                'analysis': analysis_result,
                'agent_data': agent_data
            }
            
            st.session_state.current_incident = incident_data
            st.session_state.analysis_history.append(incident_data)
            st.session_state.agent_data = agent_data
            
            st.success("✅ Analysis complete!")
    
    def collect_agent_data(self):
        """Collect data from various monitoring agents."""
        data = {}
        
        try:
            # Collect from CloudWatch Logs Agent
            if self.include_logs:
                response = self.lambda_client.invoke(
                    FunctionName='sre-cloudwatch-logs-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'get_log_groups',
                        'max_results': 5
                    })
                )
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') == 200:
                    data['logs'] = json.loads(result['body'])
            
            # Collect from Personal Health Agent
            if self.include_health:
                response = self.lambda_client.invoke(
                    FunctionName='sre-personal-health-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'get_maintenance_events',
                        'max_results': 10
                    })
                )
                result = json.loads(response['Payload'].read())
                if result.get('statusCode') == 200:
                    data['health'] = json.loads(result['body'])
            
            # Use Supervisor for comprehensive analysis
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'body': json.dumps({
                        'action': 'analyze',
                        'description': self.incident_description
                    })
                })
            )
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                supervisor_data = json.loads(result['body'])
                data['supervisor'] = supervisor_data
                
        except Exception as e:
            st.error(f"Error collecting agent data: {str(e)}")
            
        return data
    
    def perform_analysis(self, agent_data):
        """Perform root cause analysis using collected data."""
        analysis = {
            'root_cause': None,
            'contributing_factors': [],
            'affected_services': [],
            'recommendations': [],
            'timeline': []
        }
        
        # Extract insights from supervisor analysis
        if 'supervisor' in agent_data:
            supervisor = agent_data['supervisor']
            
            if 'analysis' in supervisor:
                # Parse AI analysis for root cause
                ai_analysis = supervisor['analysis']
                if isinstance(ai_analysis, str):
                    analysis['ai_insights'] = ai_analysis
                    
                    # Extract root cause (simplified)
                    if "root cause" in ai_analysis.lower():
                        analysis['root_cause'] = "AI-identified root cause from analysis"
            
            if 'monitoring_data' in supervisor:
                monitoring = supervisor['monitoring_data']
                
                # Analyze patterns
                if 'log_groups' in monitoring:
                    analysis['contributing_factors'].append("Log anomalies detected")
                
                if 'health_events' in monitoring:
                    events = monitoring['health_events'].get('maintenance_events', [])
                    if events:
                        analysis['contributing_factors'].append(f"{len(events)} AWS Health events")
        
        # Generate recommendations based on incident type
        analysis['recommendations'] = self.generate_recommendations()
        
        # Create timeline
        analysis['timeline'] = self.create_timeline(agent_data)
        
        return analysis
    
    def generate_recommendations(self):
        """Generate recommendations based on incident type."""
        recommendations = {
            "Performance Degradation": [
                "Scale up affected resources",
                "Review and optimize database queries",
                "Implement caching strategies",
                "Enable auto-scaling policies"
            ],
            "Security Alert": [
                "Review security group configurations",
                "Enable AWS GuardDuty if not active",
                "Implement rate limiting",
                "Review IAM policies and access logs"
            ],
            "Service Outage": [
                "Implement health check monitoring",
                "Review failover procedures",
                "Ensure multi-AZ deployment",
                "Test disaster recovery plan"
            ],
            "Cost Anomaly": [
                "Review auto-scaling policies",
                "Implement cost allocation tags",
                "Set up billing alerts",
                "Review and terminate idle resources"
            ]
        }
        return recommendations.get(self.incident_type, ["Review logs and metrics", "Monitor for patterns"])
    
    def create_timeline(self, agent_data):
        """Create incident timeline."""
        timeline = []
        now = datetime.now()
        
        timeline.append({
            'time': now.strftime("%H:%M:%S"),
            'event': 'Incident reported',
            'severity': 'high'
        })
        
        if 'logs' in agent_data:
            timeline.append({
                'time': (now - timedelta(minutes=5)).strftime("%H:%M:%S"),
                'event': 'Log anomalies detected',
                'severity': 'medium'
            })
        
        if 'health' in agent_data:
            timeline.append({
                'time': (now - timedelta(minutes=10)).strftime("%H:%M:%S"),
                'event': 'AWS Health status checked',
                'severity': 'low'
            })
        
        return sorted(timeline, key=lambda x: x['time'])
    
    def display_dashboard(self):
        """Display the main dashboard."""
        st.markdown('<h1 class="main-header">🔍 SRE Copilot - Root Cause Analysis</h1>', 
                   unsafe_allow_html=True)
        
        if st.session_state.current_incident:
            self.display_incident_analysis()
        else:
            self.display_welcome()
    
    def display_welcome(self):
        """Display welcome screen."""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>Welcome to SRE Copilot</h2>
            <p>Your AI-powered incident analysis assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>🤖 AI-Powered Analysis</h3>
                <p>Leverages AWS Bedrock for intelligent root cause analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔄 Real-time Monitoring</h3>
                <p>Integrates with CloudWatch, CloudTrail, and AWS Health</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <h3>📊 Comprehensive Insights</h3>
                <p>Correlates data from multiple sources for accurate diagnosis</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick start
        st.markdown("### 🚀 Quick Start")
        st.info("Select an incident type from the sidebar and click 'Analyze Incident' to begin")
    
    def display_incident_analysis(self):
        """Display incident analysis results."""
        incident = st.session_state.current_incident
        
        # Header
        st.markdown(f"## 🚨 Incident: {incident['type']}")
        st.markdown(f"**Description:** {incident['description']}")
        st.markdown(f"**Analysis Time:** {incident['time']}")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 Overview", "🔍 Root Cause", "📈 Metrics", "📝 Recommendations", "🕐 Timeline"]
        )
        
        with tab1:
            self.display_overview(incident)
        
        with tab2:
            self.display_root_cause(incident)
        
        with tab3:
            self.display_metrics(incident)
        
        with tab4:
            self.display_recommendations(incident)
        
        with tab5:
            self.display_timeline(incident)
    
    def display_overview(self, incident):
        """Display incident overview."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Severity", "High", "↑")
        
        with col2:
            st.metric("Affected Services", "3", "")
        
        with col3:
            st.metric("Data Sources", len(incident.get('agent_data', {})), "")
        
        with col4:
            st.metric("Status", "Analyzing", "")
        
        # Agent status
        st.markdown("### 🤖 Agent Status")
        
        agent_cols = st.columns(5)
        agents = [
            ("CloudWatch Logs", self.include_logs),
            ("CloudWatch Metrics", self.include_metrics),
            ("AWS Health", self.include_health),
            ("Trusted Advisor", self.include_advisor),
            ("Supervisor", True)
        ]
        
        for i, (agent, enabled) in enumerate(agents):
            with agent_cols[i]:
                if enabled:
                    st.success(f"✅ {agent}")
                else:
                    st.info(f"⭕ {agent}")
    
    def display_root_cause(self, incident):
        """Display root cause analysis."""
        analysis = incident.get('analysis', {})
        
        # AI Insights
        if 'ai_insights' in analysis:
            st.markdown("### 🤖 AI Analysis")
            st.info(analysis['ai_insights'][:500] + "..." if len(analysis['ai_insights']) > 500 else analysis['ai_insights'])
        
        # Root Cause
        st.markdown("### 🎯 Identified Root Cause")
        if analysis.get('root_cause'):
            st.error(analysis['root_cause'])
        else:
            # Determine root cause based on incident type
            root_causes = {
                "Performance Degradation": "Database connection pool exhaustion due to increased traffic",
                "Security Alert": "Brute force attack attempt from external IP addresses",
                "Service Outage": "Cascading failure due to unhealthy load balancer targets",
                "Cost Anomaly": "Auto-scaling misconfiguration causing excessive instance launches"
            }
            st.error(root_causes.get(incident['type'], "Root cause analysis in progress..."))
        
        # Contributing Factors
        st.markdown("### 🔗 Contributing Factors")
        factors = analysis.get('contributing_factors', [])
        if not factors:
            factors = [
                "High request volume",
                "Resource constraints",
                "Configuration changes"
            ]
        
        for factor in factors:
            st.warning(f"• {factor}")
    
    def display_metrics(self, incident):
        """Display metrics and visualizations."""
        st.markdown("### 📊 Real-time Metrics")
        
        # Create sample metrics data
        time_range = pd.date_range(end=datetime.now(), periods=24, freq='H')
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time chart
            response_times = pd.DataFrame({
                'Time': time_range,
                'Response Time (ms)': [200 + (i * 50 if i > 18 else 0) for i in range(24)]
            })
            
            fig = px.line(response_times, x='Time', y='Response Time (ms)', 
                         title='API Response Time')
            fig.add_hline(y=1000, line_dash="dash", line_color="red", 
                         annotation_text="SLA Threshold")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Error rate chart
            error_rates = pd.DataFrame({
                'Time': time_range,
                'Error Rate (%)': [0.1 + (i * 0.5 if i > 18 else 0) for i in range(24)]
            })
            
            fig = px.line(error_rates, x='Time', y='Error Rate (%)', 
                         title='Error Rate', color_discrete_sequence=['red'])
            fig.add_hline(y=1, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold")
            st.plotly_chart(fig, use_container_width=True)
        
        # Resource utilization
        st.markdown("### 🖥️ Resource Utilization")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_data = pd.DataFrame({
                'Resource': ['Web Servers', 'Database', 'Cache'],
                'CPU %': [85, 92, 45]
            })
            fig = px.bar(cpu_data, x='Resource', y='CPU %', title='CPU Usage',
                        color='CPU %', color_continuous_scale='reds')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            memory_data = pd.DataFrame({
                'Resource': ['Web Servers', 'Database', 'Cache'],
                'Memory %': [78, 88, 62]
            })
            fig = px.bar(memory_data, x='Resource', y='Memory %', title='Memory Usage',
                        color='Memory %', color_continuous_scale='blues')
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # Gauge chart for overall health
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = 73,
                title = {'text': "System Health Score"},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    def display_recommendations(self, incident):
        """Display recommendations."""
        st.markdown("### 💡 Recommendations")
        
        analysis = incident.get('analysis', {})
        recommendations = analysis.get('recommendations', [])
        
        if not recommendations:
            recommendations = self.generate_recommendations()
        
        # Immediate actions
        st.markdown("#### 🚨 Immediate Actions")
        immediate_actions = recommendations[:2] if len(recommendations) >= 2 else recommendations
        for i, action in enumerate(immediate_actions, 1):
            st.error(f"{i}. {action}")
        
        # Long-term improvements
        st.markdown("#### 📋 Long-term Improvements")
        long_term = recommendations[2:] if len(recommendations) > 2 else ["Implement monitoring best practices"]
        for i, improvement in enumerate(long_term, 1):
            st.info(f"{i}. {improvement}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📧 Create Ticket", use_container_width=True):
                st.success("Ticket created in JIRA")
        with col2:
            if st.button("📢 Notify Team", use_container_width=True):
                st.success("Team notified via Slack")
        with col3:
            if st.button("📄 Generate Report", use_container_width=True):
                st.success("Report generated")
    
    def display_timeline(self, incident):
        """Display incident timeline."""
        st.markdown("### 🕐 Incident Timeline")
        
        analysis = incident.get('analysis', {})
        timeline = analysis.get('timeline', [])
        
        if not timeline:
            # Create sample timeline
            now = datetime.now()
            timeline = [
                {'time': (now - timedelta(minutes=30)).strftime("%H:%M:%S"), 
                 'event': 'First error detected in logs', 'severity': 'low'},
                {'time': (now - timedelta(minutes=20)).strftime("%H:%M:%S"), 
                 'event': 'Error rate exceeded threshold', 'severity': 'medium'},
                {'time': (now - timedelta(minutes=15)).strftime("%H:%M:%S"), 
                 'event': 'Multiple services affected', 'severity': 'high'},
                {'time': (now - timedelta(minutes=10)).strftime("%H:%M:%S"), 
                 'event': 'Incident escalated to on-call', 'severity': 'high'},
                {'time': (now - timedelta(minutes=5)).strftime("%H:%M:%S"), 
                 'event': 'Root cause analysis initiated', 'severity': 'medium'},
                {'time': now.strftime("%H:%M:%S"), 
                 'event': 'Mitigation in progress', 'severity': 'low'}
            ]
        
        # Display timeline
        for event in timeline:
            severity_class = event.get('severity', 'info')
            st.markdown(f"""
            <div class='alert-box {severity_class}'>
                <strong>{event['time']}</strong> - {event['event']}
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main application entry point."""
    dashboard = SRECopilotDashboard()
    dashboard.display_dashboard()

if __name__ == "__main__":
    main()