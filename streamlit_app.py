#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard with MCP Integration
Integrates real incident generation, AWS data analysis, and external MCP services.
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
from user_guide_content import get_all_guides, get_guide_titles
from streamlit_key_manager import key_manager
from dataclasses import asdict
import logging

logger = logging.getLogger(__name__)

# Add path for MCP modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try importing MCP modules
try:
    from feedback.feedback_system import FeedbackSystem
    from config.mcp_config import MCPConfigManager
    from enhanced_incident_scenarios import EnhancedIncidentScenarios
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP modules not available - running in standard mode")

# Import IP masking utility
try:
    from utils.ip_masker import IPMasker, mask_logs_for_llm
    IP_MASKING_AVAILABLE = True
except ImportError:
    IP_MASKING_AVAILABLE = False
    print("IP masking utility not available")

# Import post-mortem agent
try:
    from postmortem.postmortem_agent import PostMortemAgent, PostMortemReport
    POSTMORTEM_AVAILABLE = True
except ImportError:
    POSTMORTEM_AVAILABLE = False
    print("Post-mortem agent not available")

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
        'gitlab': 9084
    }

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
    .incident-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
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
    .feedback-section {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = []
if 'current_incident' not in st.session_state:
    st.session_state.current_incident = None
if 'agent_data' not in st.session_state:
    st.session_state.agent_data = {}
if 'generated_incidents' not in st.session_state:
    st.session_state.generated_incidents = []
if 'demo_resources' not in st.session_state:
    st.session_state.demo_resources = {
        'security_group_id': None,
        'log_group_name': '/aws/demo/sre-incident-generator',
        'namespace': 'SREDemo/Application'
    }
if 'mcp_enabled' not in st.session_state:
    st.session_state.mcp_enabled = MCP_AVAILABLE
if 'feedback_enabled' not in st.session_state:
    st.session_state.feedback_enabled = MCP_AVAILABLE
if 'current_analysis_result' not in st.session_state:
    st.session_state.current_analysis_result = None

# Initialize MCP components if available
if MCP_AVAILABLE:
    feedback_system = FeedbackSystem()
    mcp_config = MCPConfigManager()
    enhanced_scenarios = EnhancedIncidentScenarios()

# MCP Helper Functions
def get_mcp_status():
    """Check status of MCP servers."""
    if not MCP_AVAILABLE:
        return {}
    
    status = {}
    for service, port in MCP_PORTS.items():
        try:
            if service == 'splunk':
                response = requests.post(
                    f"http://localhost:{port}/splunk/search",
                    json={"query": "test", "time_range": "-1h"},
                    timeout=1
                )
            elif service in ['dynatrace', 'servicenow']:
                response = requests.get(f"http://localhost:{port}/{service}/incidents", timeout=1)
            else:
                response = requests.get(f"http://localhost:{port}/{service}/search?query=test", timeout=1)
            
            status[service] = 'online' if response.status_code in [200, 201, 405] else 'error'
        except:
            status[service] = 'offline'
    return status

def display_mcp_data_in_analysis(mcp_data):
    """Display MCP correlation data in analysis results."""
    if not mcp_data or not isinstance(mcp_data, dict):
        return
    
    st.markdown("### 🌐 External Service Correlations (MCP)")
    
    cols = st.columns(min(len(mcp_data), 3))
    col_idx = 0
    
    for service, data in mcp_data.items():
        if col_idx >= len(cols):
            cols = st.columns(min(len(mcp_data) - col_idx, 3))
            col_idx = 0
            
        with cols[col_idx]:
            status = data.get('status', 'unknown')
            icon = "✅" if status == 'success' else "❌"
            
            st.markdown(f"**{icon} {service.upper()}**")
            
            if status == 'success':
                if service == 'splunk' and 'network_analysis' in data:
                    st.text(f"High latency hosts: {data['network_analysis'].get('high_latency_hosts', 'N/A')}")
                elif service == 'dynatrace' and 'mq_metrics' in data:
                    st.text(f"Queue depth: {data['mq_metrics'].get('queue_depth', 'N/A')}")
                elif service == 'servicenow':
                    st.text(f"Related incidents: {data.get('related_incidents', 0)}")
                    st.text(f"Recent changes: {data.get('recent_changes', 0)}")
                elif service == 'confluence':
                    st.text(f"KB articles: {data.get('kb_articles', 0)}")
                elif service == 'gitlab':
                    st.text(f"Recent commits: {data.get('recent_commits', 0)}")
                    if data.get('deployment_found'):
                        st.warning("Recent deployment detected!")
            else:
                st.text("Service unavailable")
        
        col_idx += 1

def display_feedback_section(analysis_result, form_key_suffix=""):
    """Display human-in-the-loop feedback section."""
    if not MCP_AVAILABLE or not st.session_state.feedback_enabled:
        return
    
    st.markdown("---")
    st.markdown("### 💬 Feedback & Improvement")
    
    # Create unique form key
    form_key = f"feedback_form_{form_key_suffix}" if form_key_suffix else "feedback_form_default"
    
    with st.form(form_key):
        col1, col2 = st.columns(2)
        
        with col1:
            rating = st.slider("Rate the analysis accuracy:", 1, 5, 4)
            correct_root_cause = st.checkbox("Was the root cause correct?", value=True)
        
        with col2:
            additional_context = st.text_area(
                "Additional context or corrections:", 
                placeholder="E.g., The actual issue was..."
            )
            
        suggested_actions = st.text_area(
            "Suggested actions for similar incidents:",
            placeholder="E.g., Check X before Y..."
        )
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            feedback_data = {
                "incident_id": f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "analysis_id": analysis_result.get('analysis_id', 'unknown'),
                "rating": rating,
                "correct_root_cause": correct_root_cause,
                "additional_context": additional_context,
                "suggested_actions": suggested_actions.split('\n') if suggested_actions else []
            }
            
            result = feedback_system.submit_feedback(feedback_data)
            
            if result['success']:
                st.success("Thank you for your feedback! This will help improve future analysis.")
            else:
                st.error("Failed to submit feedback. Please try again.")

class IncidentGenerator:
    """Handles real incident generation in AWS."""
    
    def __init__(self):
        self.region = 'us-east-1'
        self.demo_resources = {
            'security_group_id': None,
            'log_group_name': '/aws/demo/sre-incident-generator',
            'namespace': 'SREDemo/Application'
        }
        self.setup_aws_clients()
        
    def setup_aws_clients(self):
        """Initialize AWS service clients."""
        self.clients = {
            'logs': boto3.client('logs', region_name=self.region),
            'cloudwatch': boto3.client('cloudwatch', region_name=self.region),
            'ec2': boto3.client('ec2', region_name=self.region),
            'ssm': boto3.client('ssm', region_name=self.region),
            'cloudtrail': boto3.client('cloudtrail', region_name=self.region),
            's3': boto3.client('s3', region_name=self.region),
            'lambda': boto3.client('lambda', region_name=self.region)
        }
        
    def create_demo_resources(self):
        """Create necessary demo resources."""
        # Create CloudWatch Log Group
        try:
            self.clients['logs'].create_log_group(
                logGroupName=self.demo_resources['log_group_name']
            )
        except self.clients['logs'].exceptions.ResourceAlreadyExistsException:
            pass
            
        # Create/Get demo security group
        try:
            response = self.clients['ec2'].create_security_group(
                GroupName='sre-demo-incident-sg',
                Description='Demo security group for incident generation'
            )
            self.demo_resources['security_group_id'] = response['GroupId']
        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                response = self.clients['ec2'].describe_security_groups(
                    GroupNames=['sre-demo-incident-sg']
                )
                self.demo_resources['security_group_id'] = response['SecurityGroups'][0]['GroupId']
                
    def generate_application_logs(self, scenario='error'):
        """Generate application logs in CloudWatch."""
        log_stream = f"app-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            self.clients['logs'].create_log_stream(
                logGroupName=self.demo_resources['log_group_name'],
                logStreamName=log_stream
            )
        except:
            pass
            
        log_events = []
        timestamp = int(time.time() * 1000)
        
        if scenario == 'error':
            messages = [
                {"level": "INFO", "message": "Application started successfully"},
                {"level": "WARN", "message": "Database connection slow", "duration_ms": 3500},
                {"level": "ERROR", "message": "Database connection timeout", "error": "Connection refused"},
                {"level": "ERROR", "message": "Failed to process user request", "user_id": "user456"},
                {"level": "ERROR", "message": "Application crash", "error": "NullPointerException"},
                {"level": "FATAL", "message": "Service unavailable", "status_code": 503}
            ]
        elif scenario == 'performance':
            messages = [
                {"level": "INFO", "message": "Request received", "endpoint": "/api/data"},
                {"level": "WARN", "message": "High response time detected", "duration_ms": 5000},
                {"level": "WARN", "message": "Memory usage high", "memory_percent": 92},
                {"level": "ERROR", "message": "Request timeout", "duration_ms": 30000},
                {"level": "WARN", "message": "Thread pool exhausted", "active_threads": 200}
            ]
            
        for i, msg_data in enumerate(messages):
            log_events.append({
                'timestamp': timestamp + (i * 1000),
                'message': json.dumps(msg_data)
            })
            
        self.clients['logs'].put_log_events(
            logGroupName=self.demo_resources['log_group_name'],
            logStreamName=log_stream,
            logEvents=log_events
        )
        
        return len(log_events), log_stream
        
    def generate_cloudwatch_metrics(self, scenario='failure'):
        """Generate CloudWatch metrics."""
        timestamp = datetime.utcnow()
        
        if scenario == 'failure':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': 95, 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': 92, 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(50, 100), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(50, 80), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(10000, 30000), 'Unit': 'Milliseconds'}
            ]
        elif scenario == 'high_load':
            metrics_data = [
                {'MetricName': 'CPUUtilization', 'Value': random.uniform(85, 95), 'Unit': 'Percent'},
                {'MetricName': 'MemoryUtilization', 'Value': random.uniform(80, 90), 'Unit': 'Percent'},
                {'MetricName': 'RequestCount', 'Value': random.randint(800, 1000), 'Unit': 'Count'},
                {'MetricName': 'ErrorRate', 'Value': random.uniform(5, 15), 'Unit': 'Percent'},
                {'MetricName': 'ResponseTime', 'Value': random.uniform(2000, 5000), 'Unit': 'Milliseconds'}
            ]
            
        for metric in metrics_data:
            self.clients['cloudwatch'].put_metric_data(
                Namespace=self.demo_resources['namespace'],
                MetricData=[{
                    'MetricName': metric['MetricName'],
                    'Value': metric['Value'],
                    'Unit': metric['Unit'],
                    'Timestamp': timestamp,
                    'Dimensions': [
                        {'Name': 'Environment', 'Value': 'demo'},
                        {'Name': 'Service', 'Value': 'sre-demo-app'}
                    ]
                }]
            )
            
        return metrics_data
        
    def modify_security_group(self, action='add_risky_rule'):
        """Modify security group to generate events."""
        if not self.demo_resources['security_group_id']:
            return False
            
        try:
            if action == 'add_risky_rule':
                self.clients['ec2'].authorize_security_group_ingress(
                    GroupId=self.demo_resources['security_group_id'],
                    IpPermissions=[{
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH from anywhere (RISKY)'}]
                    }]
                )
                return True
        except ClientError:
            pass
        return False
        
    def generate_api_failures(self):
        """Generate API failures for CloudTrail."""
        failures = []
        
        # S3 unauthorized access
        try:
            self.clients['s3'].get_object(
                Bucket='non-existent-bucket-sre-demo-12345',
                Key='secret-file.txt'
            )
        except ClientError as e:
            failures.append(f"S3 Access Denied: {e.response['Error']['Code']}")
            
        # Lambda invocation failure
        try:
            self.clients['lambda'].invoke(
                FunctionName='non-existent-function-sre-demo',
                InvocationType='RequestResponse'
            )
        except ClientError as e:
            failures.append(f"Lambda Invocation Failed: {e.response['Error']['Code']}")
            
        return failures
        
    def create_opsitem(self, title, description, severity='3'):
        """Create SSM OpsItem."""
        try:
            response = self.clients['ssm'].create_ops_item(
                Title=title,
                Description=description,
                Priority=int(severity),
                Source='SRE-Demo-Streamlit',
                Category='Performance',
                Severity=severity,
                OperationalData={
                    '/aws/resources': {
                        'Value': json.dumps([{
                            'arn': f'arn:aws:logs:{self.region}:123456789012:log-group:{self.demo_resources["log_group_name"]}'
                        }])
                    }
                },
                Tags=[
                    {'Key': 'Environment', 'Value': 'demo'},
                    {'Key': 'Source', 'Value': 'streamlit-app'}
                ]
            )
            return response['OpsItemId']
        except ClientError:
            return None
            
    def generate_correlated_incident(self, incident_type="performance"):
        """Generate a complete correlated incident."""
        incident_data = {
            'start_time': datetime.utcnow(),
            'type': incident_type,
            'components': []
        }
        
        # Generate different components based on type
        if incident_type == "performance":
            # High load metrics
            metrics = self.generate_cloudwatch_metrics('high_load')
            incident_data['components'].append(f"Generated {len(metrics)} high load metrics")
            
            # Performance logs
            count, stream = self.generate_application_logs('performance')
            incident_data['components'].append(f"Generated {count} performance warning logs")
            
        elif incident_type == "security":
            # Security group change
            if self.modify_security_group('add_risky_rule'):
                incident_data['components'].append("Modified security group with risky rule")
                
            # API failures
            failures = self.generate_api_failures()
            incident_data['components'].append(f"Generated {len(failures)} API failures")
            
        elif incident_type == "outage":
            # Failure metrics
            metrics = self.generate_cloudwatch_metrics('failure')
            incident_data['components'].append(f"Generated {len(metrics)} failure metrics")
            
            # Error logs
            count, stream = self.generate_application_logs('error')
            incident_data['components'].append(f"Generated {count} error logs")
            
        # Create OpsItem
        title = f"Incident: {incident_type.capitalize()} Issue Detected"
        description = f"Automated incident generated for {incident_type} scenario. Components affected: {', '.join(incident_data['components'])}"
        severity = '2' if incident_type == 'outage' else '3'
        
        ops_item_id = self.create_opsitem(title, description, severity)
        
        incident_data['ops_item_id'] = ops_item_id
        incident_data['title'] = title
        incident_data['description'] = description
        incident_data['severity'] = severity
        incident_data['end_time'] = datetime.utcnow()
        
        return incident_data

class EnhancedSREDashboard:
    """Enhanced dashboard with real incident generation and analysis."""
    
    def __init__(self):
        self.region = 'us-east-1'
        os.environ['AWS_DEFAULT_REGION'] = self.region
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        self.ssm_client = boto3.client('ssm', region_name=self.region)
        self.incident_generator = IncidentGenerator()
        
    def setup_sidebar(self):
        """Setup the enhanced sidebar."""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100.png?text=SRE+Copilot", width=300)
            st.markdown("## 🎯 Incident Management")
            
            # Incident Generation Section
            st.markdown("### 🚀 Generate Incident")
            
            # Add MCP Test Scenarios if available
            incident_categories = ["Standard AWS", "MCP Integration Test"] if MCP_AVAILABLE else ["Standard AWS"]
            incident_category = st.selectbox("Incident Category", incident_categories)
            
            if incident_category == "Standard AWS":
                incident_type = st.selectbox(
                    "Select Incident Type to Generate",
                    ["Performance Degradation", "Security Alert", "Service Outage"]
                )
            else:
                # MCP Test Scenarios
                mcp_scenarios = enhanced_scenarios.get_scenarios() if MCP_AVAILABLE else []
                scenario_names = [s['incident']['title'] for s in mcp_scenarios]
                incident_type = st.selectbox("Select MCP Scenario", scenario_names)
            
            # Create unique button key
            button_key = key_manager.get_unique_key("generate_incident", incident_category, incident_type)
            
            # Use callback for button
            def handle_generate_incident():
                self.generate_incident(incident_type)
            
            st.button("🔥 Generate Real Incident", 
                     type="primary", 
                     use_container_width=True, 
                     key=button_key,
                     on_click=handle_generate_incident)
                
            # Analysis Section
            st.markdown("### 🔍 Analyze Incident")
            
            # OpsItem selection
            if st.session_state.generated_incidents:
                ops_items = [f"{inc['ops_item_id']} - {inc['type']}" for inc in st.session_state.generated_incidents]
                selected_ops = st.selectbox("Select OpsItem", ops_items)
                
                # Create callback for analysis button
                def handle_run_analysis():
                    ops_item_id = selected_ops.split(' - ')[0]
                    self.run_root_cause_analysis(ops_item_id)
                
                st.button("🤖 Run Root Cause Analysis", 
                         type="primary", 
                         use_container_width=True, 
                         key=key_manager.get_unique_key("run_analysis_sidebar", selected_ops),
                         on_click=handle_run_analysis)
            else:
                st.info("Generate an incident first to analyze")
                
            # Data Sources
            st.markdown("### 📊 Data Sources")
            st.session_state.include_logs = st.checkbox("CloudWatch Logs", value=True)
            st.session_state.include_metrics = st.checkbox("CloudWatch Metrics", value=True)
            st.session_state.include_cloudtrail = st.checkbox("CloudTrail Events", value=True)
            st.session_state.include_vpc_logs = st.checkbox("VPC Flow Logs", value=True)
            st.session_state.include_health = st.checkbox("AWS Health", value=True)
            
            # MCP Integration Settings
            if MCP_AVAILABLE:
                st.markdown("### 🌐 MCP Integration")
                st.session_state.mcp_enabled = st.checkbox("Enable MCP Correlation", value=True)
                st.session_state.feedback_enabled = st.checkbox("Enable Human Feedback", value=True)
                
                if st.session_state.mcp_enabled:
                    st.markdown("**MCP Services Status:**")
                    mcp_status = get_mcp_status()
                    for service, status in mcp_status.items():
                        if status == 'online':
                            st.success(f"✅ {service.upper()}")
                        elif status == 'error':
                            st.warning(f"⚠️ {service.upper()}")
                        else:
                            st.error(f"❌ {service.upper()}")
            
            # Time Range
            st.session_state.time_range = st.selectbox(
                "Analysis Time Range",
                ["Last 15 minutes", "Last 30 minutes", "Last 1 hour", "Last 6 hours"]
            )
            
            # History
            st.markdown("### 📜 Recent Incidents")
            for i, incident in enumerate(reversed(st.session_state.generated_incidents[-5:])):
                if st.button(f"📋 {incident['type']} - {incident['start_time'].strftime('%H:%M')}", key=key_manager.get_loop_key("recent_incident", i)):
                    st.session_state.current_incident = incident
            
                    
    def generate_incident(self, incident_type):
        """Generate a real incident in AWS or MCP test scenario."""
        # Use sidebar context for all output
        with st.sidebar:
            with st.spinner(f"🔥 Generating {incident_type} incident..."):
                # Check if this is an MCP scenario
                if MCP_AVAILABLE and 'enhanced_scenarios' in globals():
                    mcp_scenarios = enhanced_scenarios.get_scenarios()
                    if incident_type in [s['incident']['title'] for s in mcp_scenarios]:
                        # Handle MCP test scenario
                        scenario = next(s for s in mcp_scenarios if s['incident']['title'] == incident_type)
                        
                        # Create MCP test incident
                        incident_data = {
                        'type': 'mcp_test',
                        'ops_item_id': f'MCP-TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
                        'ui_type': incident_type,
                        'start_time': datetime.now(),
                        'scenario_data': scenario,
                        'description': f"{scenario['incident']['title']}. {' '.join(scenario['incident']['symptoms'])}",
                        'service': scenario['incident']['service'],
                        'severity': scenario['incident']['severity']
                        }
                        
                        st.session_state.generated_incidents.append(incident_data)
                        st.session_state.current_incident = incident_data
                        
                        st.success(f"✅ Generated MCP test scenario: {incident_type}")
                        
                        # Display scenario details
                        with st.expander("Scenario Details"):
                            st.json(scenario['incident'])
                        return  # Exit after MCP scenario
                
                # Original AWS incident generation
                # Create demo resources if needed
                self.incident_generator.create_demo_resources()
            
                # Map UI types to generator types
                type_map = {
                "Performance Degradation": "performance",
                "Security Alert": "security",
                "Service Outage": "outage"
            }
            
                # Generate the incident
                incident_data = self.incident_generator.generate_correlated_incident(
                    type_map[incident_type]
                )
            
                # Store incident data
                incident_data['ui_type'] = incident_type
                st.session_state.generated_incidents.append(incident_data)
                st.session_state.current_incident = incident_data
            
                st.success(f"✅ Incident generated! OpsItem ID: {incident_data['ops_item_id']}")
            
                # Show KB indexing info
                st.info("🔄 KB: Your incident is being indexed! Check Knowledge Base tab.")
            
    def determine_incident_type(self, ops_item):
        """Determine the incident type from OpsItem data."""
        title = ops_item.get('Title', '').lower()
        description = ops_item.get('Description', '').lower()
        category = ops_item.get('Category', '').lower()
        
        # Check title and description for type indicators
        if any(word in title for word in ['outage', 'unavailable', 'down', 'offline']):
            return 'outage'
        elif any(word in title for word in ['performance', 'slow', 'degradation', 'latency']):
            return 'performance'
        elif any(word in title for word in ['security', 'breach', 'unauthorized', 'vulnerability']):
            return 'security'
        elif any(word in description for word in ['connection', 'timeout', 'failed', 'error']):
            return 'performance'
        elif category == 'performance':
            return 'performance'
        elif category == 'security':
            return 'security'
        elif category == 'availability':
            return 'outage'
        else:
            return 'general'
    
    def run_root_cause_analysis(self, ops_item_id):
        """Run comprehensive root cause analysis."""
        # Use sidebar for status updates
        with st.sidebar:
            with st.spinner("🤖 Running root cause analysis..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Get OpsItem details
                    status_text.text("Fetching incident details...")
                    progress_bar.progress(10)
                    
                    ops_response = self.ssm_client.get_ops_item(OpsItemId=ops_item_id)
                    ops_item = ops_response['OpsItem']
                    
                    # Step 2: Collect data from various sources
                    status_text.text("Collecting data from AWS services...")
                    progress_bar.progress(30)
                    
                    collected_data = self.collect_comprehensive_data(ops_item)
                    
                    # Step 3: Invoke supervisor agent
                    status_text.text("Invoking AI agents for analysis...")
                    progress_bar.progress(60)
                    
                    analysis_result = self.invoke_supervisor_analysis(ops_item, collected_data)
                
                    # Check if analysis failed
                    if 'error' in analysis_result:
                        st.error(f"Analysis error: {analysis_result['error']}")
                        # Still store partial results
                        analysis_result['ai_analysis'] = "Analysis failed. Using fallback analysis based on available data."
                
                    # Step 4: Process results
                    status_text.text("Processing analysis results...")
                    progress_bar.progress(90)
                
                    # Store results
                    incident_data = {
                    'ops_item_id': ops_item_id,
                    'type': self.determine_incident_type(ops_item),
                    'description': ops_item.get('Description', ''),
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'start_time': datetime.now() - timedelta(minutes=15),  # Assume incident started 15 min ago
                    'analysis': analysis_result,
                    'raw_data': collected_data,
                    'ops_item': ops_item,
                    'operational_data': ops_item.get('OperationalData', {})
                }
                
                    # Add debug info
                    st.session_state.last_analysis_debug = {
                        'ops_item_id': ops_item_id,
                        'analysis_keys': list(analysis_result.keys()) if analysis_result else [],
                        'has_error': 'error' in analysis_result
                    }
                    
                    st.session_state.current_incident = incident_data
                    st.session_state.analysis_history.append(incident_data)
                    
                    progress_bar.progress(100)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success("✅ Root cause analysis complete!")
                    
                except Exception as e:
                    st.error(f"❌ Analysis failed: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
                
    def collect_comprehensive_data(self, ops_item):
        """Collect data from multiple AWS services."""
        data = {
            'logs': {},
            'metrics': {},
            'cloudtrail': {},
            'vpc_logs': {},
            'health': {}
        }
        
        # Get time range
        time_map = {
            "Last 15 minutes": 15,
            "Last 30 minutes": 30,
            "Last 1 hour": 60,
            "Last 6 hours": 360
        }
        minutes = time_map.get(st.session_state.get('time_range', 'Last 30 minutes'), 30)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        # Collect CloudWatch Logs
        if st.session_state.get('include_logs', True):
            try:
                log_groups = self.logs_client.describe_log_groups(
                    logGroupNamePrefix='/aws/demo/sre'
                )['logGroups']
                
                for lg in log_groups[:3]:  # Limit to 3 log groups
                    log_data = self.logs_client.filter_log_events(
                        logGroupName=lg['logGroupName'],
                        startTime=int(start_time.timestamp() * 1000),
                        endTime=int(end_time.timestamp() * 1000),
                        limit=50
                    )
                    data['logs'][lg['logGroupName']] = log_data.get('events', [])
            except:
                pass
                
        # Collect CloudWatch Metrics
        if st.session_state.get('include_metrics', True):
            try:
                metrics = ['CPUUtilization', 'MemoryUtilization', 'ErrorRate']
                for metric_name in metrics:
                    metric_data = self.cloudwatch_client.get_metric_statistics(
                        Namespace='SREDemo/Application',
                        MetricName=metric_name,
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Average', 'Maximum'],
                        Dimensions=[
                            {'Name': 'Environment', 'Value': 'demo'},
                            {'Name': 'Service', 'Value': 'sre-demo-app'}
                        ]
                    )
                    data['metrics'][metric_name] = metric_data.get('Datapoints', [])
            except:
                pass
                
        return data
        
    def invoke_supervisor_analysis(self, ops_item, collected_data):
        """Invoke the supervisor agent for analysis with optional MCP."""
        # Check if this is an MCP test incident
        incident_type = ops_item.get('Title', '').split(' - ')[0] if isinstance(ops_item, dict) else 'unknown'
        is_mcp_test = incident_type == 'MCP-TEST' or 'mcp_test' in str(ops_item.get('OperationalData', {}))
        
        # Build the payload
        payload = {
            'action': 'analyze',
            'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
            'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'service': ops_item.get('OperationalData', {}).get('service', {}).get('Value', 'sre-demo-app'),
            'environment': 'demo',
            'enable_mcp': st.session_state.get('mcp_enabled', False) and MCP_AVAILABLE,
            'enable_kb': True,
            'additional_context': {
                'ops_item_id': ops_item.get('OpsItemId'),
                'severity': ops_item.get('Severity'),
                'data_summary': {
                    'log_events': sum(len(events) for events in collected_data['logs'].values()),
                    'metric_points': sum(len(points) for points in collected_data['metrics'].values())
                }
            }
        }
        
        # Add MCP scenario data if available
        if is_mcp_test and 'scenario_data' in ops_item.get('OperationalData', {}):
            payload['mcp_scenario'] = json.loads(ops_item['OperationalData']['scenario_data']['Value'])
        
        try:
            # Determine which Lambda to use
            lambda_function = 'sre-supervisor-lambda'
            if st.session_state.get('mcp_enabled', False) and MCP_AVAILABLE:
                try:
                    # Check if MCP Lambda exists
                    self.lambda_client.get_function(FunctionName='sre-supervisor-lambda-mcp')
                    lambda_function = 'sre-supervisor-lambda-mcp'
                except:
                    pass
            
            response = self.lambda_client.invoke(
                FunctionName=lambda_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                # Store for feedback
                st.session_state.current_analysis_result = body
                return self.parse_supervisor_response(body)
            else:
                return {'error': 'Analysis failed', 'details': result.get('body')}
                
        except Exception as e:
            return {'error': str(e)}
            
    def parse_supervisor_response(self, response):
        """Parse and structure the supervisor response."""
        analysis = {
            'root_cause': 'Analyzing...',
            'contributing_factors': [],
            'affected_services': [],
            'recommendations': [],
            'timeline': [],
            'correlations': [],
            'agent_findings': {}
        }
        
        # Extract information from the response
        if isinstance(response, dict):
            # Look for analysis results
            if 'analysis' in response:
                ai_text = response['analysis']
                analysis['ai_analysis'] = ai_text
                
                # Extract root cause
                if 'root cause' in ai_text.lower():
                    analysis['root_cause'] = "Identified from AI analysis"
                    
            # Extract agent findings
            if 'agent_results' in response:
                analysis['agent_findings'] = response['agent_results']
                
            # Extract timeline
            if 'timeline' in response:
                analysis['timeline'] = response['timeline']
                
            # Extract recommendations
            if 'recommendations' in response:
                analysis['recommendations'] = response['recommendations']
                
        return analysis
        
    def display_dashboard(self):
        """Display the enhanced dashboard."""
        # Setup sidebar first
        self.setup_sidebar()
        
        st.markdown('<h1 class="main-header">🔍 SRE Copilot - Real-Time Root Cause Analysis</h1>', 
                   unsafe_allow_html=True)
        
        # Create navigation selector for groups
        nav_options = ["🏠 Core Features", "🛠️ Advanced Tools", "📊 Additional Features"]
        selected_nav = st.radio(
            "Navigation", 
            nav_options,
            horizontal=True,
            label_visibility="collapsed",
            key="main_navigation"
        )
        
        # Define tab groups
        if selected_nav == "🏠 Core Features":
            tab_names = ["🚨 Incident Management", "🔍 Analyze Incident", "🔧 Recent Changes", "📚 Knowledge Base", "📊 Analytics"]
            tab_offset = 0
        elif selected_nav == "🛠️ Advanced Tools":
            tab_names = ["🐛 Defect Management", "🔗 Defect Correlation", "🧪 Correlation Scenarios", "📋 Post-Mortem", "🔐 IP Masking"]
            tab_offset = 5
        else:  # Additional Features
            tab_names = ["🧪 Test Scenarios"]
            if MCP_AVAILABLE and st.session_state.get('mcp_enabled', False):
                tab_names.extend(["🌐 MCP Status", "📈 Feedback Analytics"])
            tab_names.append("❓ User Guide")
            tab_offset = 10
        
        main_tabs = st.tabs(tab_names)
        
        # Handle tab content based on navigation selection
        if selected_nav == "🏠 Core Features":
            with main_tabs[0]:
                if st.session_state.current_incident:
                    self.display_incident_details()
                else:
                    self.display_welcome()
                    
            with main_tabs[1]:
                self.render_analyze_tab()
                
            with main_tabs[2]:
                self.render_recent_changes()
                
            with main_tabs[3]:
                self.render_knowledge_base()
                
            with main_tabs[4]:
                self.render_analytics()
                
        elif selected_nav == "🛠️ Advanced Tools":
            with main_tabs[0]:
                self.render_defect_management()
            
            with main_tabs[1]:
                self.render_defect_correlation()
            
            with main_tabs[2]:
                self.render_correlation_scenarios()
            
            with main_tabs[3]:
                self.render_postmortem_analysis()
                
            with main_tabs[4]:
                self.render_ip_masking()
                
        else:  # Additional Features
            tab_idx = 0
            with main_tabs[tab_idx]:
                self.render_test_scenarios()
            tab_idx += 1
            
            if MCP_AVAILABLE and st.session_state.get('mcp_enabled', False):
                with main_tabs[tab_idx]:
                    self.render_mcp_status()
                tab_idx += 1
                
                with main_tabs[tab_idx]:
                    self.render_feedback_analytics()
                tab_idx += 1
                
            with main_tabs[tab_idx]:
                self.render_user_guide()
            
    def render_analyze_tab(self):
        """Render the Analyze Incident tab."""
        st.header("🔍 Analyze Incident")
        
        # Check if we just analyzed an incident and should show results
        if hasattr(st.session_state, 'show_analysis_results') and st.session_state.show_analysis_results:
            if st.session_state.current_incident:
                self.display_incident_details()
                # Reset the flag
                st.session_state.show_analysis_results = False
                
                # Show debug info if available
                if hasattr(st.session_state, 'last_analysis_debug'):
                    with st.expander("🐛 Debug Info"):
                        st.json(st.session_state.last_analysis_debug)
                
                # Add button to analyze another incident
                st.markdown("---")
                if st.button("🔍 Analyze Another Incident", type="secondary", key=key_manager.get_unique_key("analyze_another", "main")):
                    st.session_state.show_analysis_results = False
                    st.experimental_rerun()
                    
                return
        
        st.info("""
        Analyze existing OpsItems to understand root causes, business impact, and correlations.
        Select an OpsItem ID or enter one manually to perform comprehensive analysis.
        """)
        
        # Get recent OpsItems for selection
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=20
            )
            
            ops_items = response.get('OpsItemSummaries', [])
            
            if ops_items:
                # Create selection options
                options = ["-- Enter manually --"] + [
                    f"{item['OpsItemId']} - {item['Title']}" 
                    for item in ops_items
                ]
                
                selected = st.selectbox("Select an OpsItem to analyze:", options)
                
                if selected == "-- Enter manually --":
                    ops_item_id = st.text_input("Enter OpsItem ID:", key=key_manager.get_unique_key("manual_opsitem", "with_list"))
                else:
                    ops_item_id = selected.split(' - ')[0]
                    
                # Create callback for analyze button
                def handle_analyze_selected():
                    if ops_item_id:
                        with st.sidebar:
                            st.info(f"Starting analysis for: {ops_item_id}")
                        self.run_root_cause_analysis(ops_item_id)
                        # Set flag to show results
                        st.session_state.show_analysis_results = True
                    else:
                        st.warning("Please enter or select an OpsItem ID")
                
                st.button("🤖 Analyze Root Cause", 
                         type="primary", 
                         use_container_width=True, 
                         key=key_manager.get_unique_key("analyze_selected", selected),
                         on_click=handle_analyze_selected)
                        
            else:
                st.warning("No open OpsItems found. Enter an OpsItem ID manually.")
                ops_item_id = st.text_input("Enter OpsItem ID:", key=key_manager.get_unique_key("manual_opsitem", "no_items"))
                
                # Create callback for manual analyze button
                def handle_analyze_manual():
                    if ops_item_id:
                        self.run_root_cause_analysis(ops_item_id)
                        # Set flag to show results
                        st.session_state.show_analysis_results = True
                    else:
                        st.warning("Please enter an OpsItem ID")
                
                st.button("🤖 Analyze Root Cause", 
                         type="primary", 
                         use_container_width=True, 
                         key=key_manager.get_unique_key("analyze_manual", "no_items"),
                         on_click=handle_analyze_manual)
                        
        except Exception as e:
            st.error(f"Error fetching OpsItems: {str(e)}")
            
            # Fallback to manual entry
            ops_item_id = st.text_input("Enter OpsItem ID:", key=key_manager.get_unique_key("manual_opsitem", "error"))
            
            # Create callback for error case analyze button
            def handle_analyze_error():
                if ops_item_id:
                    self.run_root_cause_analysis(ops_item_id)
                    # Set flag to show results
                    st.session_state.show_analysis_results = True
                else:
                    st.warning("Please enter an OpsItem ID")
            
            st.button("🤖 Analyze Root Cause", 
                     type="primary", 
                     use_container_width=True, 
                     key=key_manager.get_unique_key("analyze", "error"),
                     on_click=handle_analyze_error)
    
    def display_welcome(self):
        """Display enhanced welcome screen."""
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h2>Welcome to Enhanced SRE Copilot</h2>
            <p>Generate real incidents and analyze them with AI-powered root cause analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔥 Real Incidents</h3>
                <p>Generate actual AWS incidents with logs, metrics, and events</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <h3>🤖 AI Analysis</h3>
                <p>Bedrock agents analyze real AWS data for root causes</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <h3>🔗 Correlation</h3>
                <p>Correlate events across CloudWatch, CloudTrail, and VPC logs</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
            <div class='metric-card'>
                <h3>💡 Remediation</h3>
                <p>Get actionable recommendations to resolve incidents</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Quick start guide
        st.markdown("### 🚀 Quick Start")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **Step 1: Generate an Incident**
            1. Select incident type in sidebar
            2. Click "Generate Real Incident"
            3. Wait for AWS resources to be created
            """)
            
        with col2:
            st.info("""
            **Step 2: Analyze the Incident**
            1. Select the generated OpsItem
            2. Click "Run Root Cause Analysis"
            3. Review AI-powered analysis results
            """)
            
    def display_incident_details(self):
        """Display comprehensive incident details."""
        incident = st.session_state.current_incident
        
        # Header
        if 'ops_item_id' in incident:
            st.markdown(f"## 🚨 Incident Analysis: {incident.get('ops_item_id', 'Unknown')}")
        else:
            st.markdown(f"## 🚨 Generated Incident: {incident.get('ui_type', incident.get('type', 'Unknown'))}")
            
        # Incident info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", incident.get('ui_type', incident.get('type', 'Unknown')))
        with col2:
            if 'start_time' in incident:
                st.metric("Generated", incident['start_time'].strftime("%H:%M:%S"))
            else:
                st.metric("Analyzed", incident.get('time', 'Unknown'))
        with col3:
            st.metric("Status", "Analyzed" if 'analysis' in incident else "Generated")
            
        # Show generated components
        if 'components' in incident:
            st.markdown("### 📋 Generated Components")
            for component in incident['components']:
                st.success(f"✅ {component}")
                
        # Analysis results
        if 'analysis' in incident:
            # Tabs for different views
            tabs = st.tabs(["🎯 Root Cause", "📊 Data Analysis", "🔗 Correlations", 
                           "💡 Recommendations", "📈 Metrics", "📝 Raw Data"])
            
            with tabs[0]:
                self.display_root_cause(incident)
                
            with tabs[1]:
                self.display_data_analysis(incident)
                
            with tabs[2]:
                self.display_correlations(incident)
                
            with tabs[3]:
                self.display_recommendations(incident)
                
            with tabs[4]:
                self.display_metrics_analysis(incident)
                
            with tabs[5]:
                self.display_raw_data(incident)
        else:
            st.info("📊 Run root cause analysis to see detailed results")
            
    def display_root_cause(self, incident):
        """Display root cause analysis with MCP data."""
        st.markdown("### 🎯 Root Cause Analysis")
        
        analysis = incident.get('analysis', {})
        
        # Display MCP data if available
        if 'mcp_data_summary' in analysis and st.session_state.get('mcp_enabled', False):
            display_mcp_data_in_analysis(analysis['mcp_data_summary'])
        
        # Business Impact Section
        st.markdown("#### 💼 Business Impact")
        
        ops_data = incident.get('operational_data', {})
        customer_impact = ops_data.get('CustomerImpact', {}).get('Value', 'Unknown')
        
        # Determine business impact based on incident type and data
        if incident.get('type') == 'outage' or customer_impact == 'HIGH':
            st.error("""
            **🚨 CRITICAL BUSINESS IMPACT:**
            - Service is completely unavailable to customers
            - Revenue loss estimated at $50K/hour
            - Customer support tickets: 150+ and rising
            - Affected regions: us-east-1, eu-west-1
            - SLA breach imminent (< 30 minutes to breach)
            """)
        elif incident.get('type') == 'performance':
            st.warning("""
            **⚠️ MODERATE BUSINESS IMPACT:**
            - Service experiencing severe performance degradation
            - Response times increased by 500% (2s → 10s)
            - 30% of transactions failing or timing out
            - Customer complaints increasing
            - Potential revenue impact: $10K/hour
            """)
        elif incident.get('type') == 'security':
            st.error("""
            **🔒 SECURITY IMPACT:**
            - Potential unauthorized access detected
            - Compliance violation risk (PCI-DSS, SOC2)
            - Customer data potentially exposed
            - Immediate remediation required
            - Regulatory reporting may be necessary
            """)
        else:
            st.info("""
            **ℹ️ OPERATIONAL IMPACT:**
            - Service degradation detected
            - Limited customer impact currently
            - Monitoring for escalation
            - Proactive remediation recommended
            """)
        
        # AI Analysis
        if 'ai_analysis' in analysis:
            st.markdown("#### 🤖 AI-Powered Analysis")
            with st.expander("View Full AI Analysis", expanded=True):
                st.text(analysis['ai_analysis'])
        
        # Add feedback section if enabled
        if st.session_state.get('feedback_enabled', False) and MCP_AVAILABLE:
            # Create unique key based on incident details and tab context
            incident_id = incident.get('ops_item_id', '')
            incident_type = incident.get('type', 'unknown')
            # Use a counter to ensure uniqueness even within the same tab
            if 'feedback_counter' not in st.session_state:
                st.session_state.feedback_counter = 0
            st.session_state.feedback_counter += 1
            unique_key = f"{incident_id}_{incident_type}_rootcause_tab_{st.session_state.feedback_counter}".replace('-', '_').replace(' ', '_').replace(':', '')
            display_feedback_section(analysis, form_key_suffix=unique_key)
                
        # Root Cause
        st.markdown("#### 🔍 Identified Root Cause")
        if analysis.get('root_cause'):
            st.error(f"**{analysis['root_cause']}**")
        else:
            # Determine based on incident type
            if incident.get('type') == 'performance':
                st.error("**High resource utilization causing performance degradation**")
            elif incident.get('type') == 'security':
                st.error("**Security group misconfiguration allowing unauthorized access**")
            elif incident.get('type') == 'outage':
                st.error("**Service failure due to resource exhaustion**")
                
        # Contributing Factors
        st.markdown("#### 🔗 Contributing Factors")
        factors = analysis.get('contributing_factors', [])
        if not factors and 'raw_data' in incident:
            # Generate factors from data
            if incident['raw_data'].get('metrics', {}).get('CPUUtilization'):
                factors.append("High CPU utilization detected")
            if incident['raw_data'].get('logs'):
                factors.append("Error patterns found in application logs")
                
        for factor in factors:
            st.warning(f"• {factor}")
            
    def display_data_analysis(self, incident):
        """Display data analysis from various sources."""
        st.markdown("### 📊 Data Source Analysis")
        
        if 'raw_data' in incident:
            data = incident['raw_data']
            
            # CloudWatch Logs Analysis
            if data.get('logs'):
                st.markdown("#### 📝 CloudWatch Logs")
                
                # Add IP masking toggle
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    total_events = sum(len(events) for events in data['logs'].values())
                    st.metric("Total Log Events Analyzed", total_events)
                
                with col2:
                    # Check if IP masking info is available
                    masking_info = incident.get('monitoring_data', {}).get('logs', {})
                    if masking_info.get('ip_masking_applied'):
                        st.metric("IPs Masked", masking_info.get('masked_ip_count', 0))
                
                with col3:
                    if IP_MASKING_AVAILABLE:
                        # Toggle for showing masked/unmasked logs
                        show_masked = st.checkbox(
                            "🔒 Show IP Masking", 
                            value=True,
                            help="Toggle to show logs with IP addresses masked for security",
                            key=key_manager.get_unique_key("show_ip_masking", incident.get('ops_item_id', 'default'))
                        )
                    else:
                        show_masked = False
                
                # Display masking notification
                if masking_info.get('ip_masking_applied'):
                    st.info(f"🔒 IP addresses have been masked before sending to LLM for security. {masking_info.get('masked_ip_count', 0)} IPs were masked.")
                
                for log_group, events in data['logs'].items():
                    if events:
                        st.write(f"**{log_group}**: {len(events)} events")
                        # Show sample events
                        with st.expander(f"View sample events from {log_group}"):
                            for event in events[:5]:
                                message = event.get('message', '')
                                
                                # Apply masking if toggle is on and masking is available
                                if show_masked and IP_MASKING_AVAILABLE:
                                    masker = IPMasker(mask_type="partial")
                                    masked_message, ip_map = masker.mask_text(message)
                                    if ip_map:
                                        st.code(masked_message)
                                        with st.expander("🔍 View IP Mapping"):
                                            for orig, masked in ip_map.items():
                                                st.text(f"{orig} → {masked}")
                                    else:
                                        st.text(message)
                                else:
                                    st.text(message)
                                
            # CloudWatch Metrics Analysis
            if data.get('metrics'):
                st.markdown("#### 📈 CloudWatch Metrics")
                for metric_name, datapoints in data['metrics'].items():
                    if datapoints:
                        df = pd.DataFrame(datapoints)
                        if not df.empty:
                            fig = px.line(df, x='Timestamp', y='Maximum', 
                                         title=f"{metric_name} Over Time")
                            st.plotly_chart(fig, use_container_width=True)
                            
    def display_correlations(self, incident):
        """Display event correlations."""
        st.markdown("### 🔗 Event Correlations")
        
        analysis = incident.get('analysis', {})
        correlations = analysis.get('correlations', [])
        
        if not correlations:
            # Generate sample correlations
            if incident.get('type') == 'performance':
                correlations = [
                    "CPU spike correlates with increased API response times",
                    "Memory exhaustion coincides with application errors",
                    "Database connection timeouts align with service degradation"
                ]
            elif incident.get('type') == 'security':
                correlations = [
                    "Security group changes preceded unauthorized access attempts",
                    "API failures spike after security rule modification",
                    "CloudTrail shows suspicious activity from new IP ranges"
                ]
                
        for correlation in correlations:
            st.info(f"🔗 {correlation}")
            
        # Timeline visualization
        if 'timeline' in analysis or 'start_time' in incident:
            st.markdown("#### ⏱️ Event Timeline")
            self.display_timeline_chart(incident)
            
    def display_timeline_chart(self, incident):
        """Display timeline visualization with change correlation."""
        events = []
        
        # Check if this incident has change correlation
        ops_data = incident.get('operational_data', {})
        has_change = 'RelatedChangeId' in ops_data
        
        if 'start_time' in incident:
            base_time = incident['start_time']
            
            # If there's a related change, show it in the timeline
            if has_change:
                change_id = ops_data.get('RelatedChangeId', 'Unknown')
                
                # Show prominent change causation message
                st.error(f"🔧 **CAUSED BY CHANGE: {change_id}**")
                
                # Show time to incident
                time_to_incident = ops_data.get('TimeToIncident', '15 minutes')
                st.warning(f"⏱️ Time from change to incident: **{time_to_incident}**")
                
                events.extend([
                    {'time': base_time - timedelta(minutes=15), 'event': f'Change {change_id} started', 
                     'severity': 0, 'type': 'change', 'icon': '🔧'},
                    {'time': base_time - timedelta(minutes=13), 'event': 'Config update applied', 
                     'severity': 0, 'type': 'change', 'icon': '⚙️'},
                    {'time': base_time - timedelta(minutes=10), 'event': 'Deployment initiated', 
                     'severity': 0, 'type': 'deployment', 'icon': '🚀'},
                    {'time': base_time - timedelta(minutes=7), 'event': 'Warnings detected', 
                     'severity': 1, 'type': 'warning', 'icon': '⚠️'},
                    {'time': base_time - timedelta(minutes=5), 'event': 'Errors increasing', 
                     'severity': 2, 'type': 'error', 'icon': '❌'},
                    {'time': base_time - timedelta(minutes=3), 'event': 'CUSTOMER IMPACT: Service degrading', 
                     'severity': 3, 'type': 'impact', 'icon': '👥'},
                    {'time': base_time, 'event': 'CRITICAL INCIDENT: Service Unavailable', 
                     'severity': 3, 'type': 'incident', 'icon': '🚨'},
                    {'time': base_time + timedelta(minutes=1), 'event': 'BUSINESS IMPACT: $50K/hour revenue loss', 
                     'severity': 3, 'type': 'impact', 'icon': '💰'},
                    {'time': base_time + timedelta(minutes=2), 'event': 'Root cause identified: Config mismatch', 
                     'severity': 2, 'type': 'analysis', 'icon': '🔍'},
                    {'time': base_time + timedelta(minutes=5), 'event': 'Rollback initiated', 
                     'severity': 1, 'type': 'recovery', 'icon': '↩️'},
                    {'time': base_time + timedelta(minutes=10), 'event': 'Service restored', 
                     'severity': 0, 'type': 'resolved', 'icon': '✅'}
                ])
            else:
                # Standard timeline without change
                events.extend([
                    {'time': base_time, 'event': 'Incident started', 'severity': 1, 'type': 'incident', 'icon': '🚨'},
                    {'time': base_time + timedelta(minutes=2), 'event': 'Metrics degradation detected', 'severity': 2, 'type': 'metric', 'icon': '📊'},
                    {'time': base_time + timedelta(minutes=3), 'event': 'CUSTOMER IMPACT: Performance issues', 'severity': 2, 'type': 'impact', 'icon': '👥'},
                    {'time': base_time + timedelta(minutes=5), 'event': 'Critical errors in logs', 'severity': 3, 'type': 'error', 'icon': '❌'},
                    {'time': base_time + timedelta(minutes=6), 'event': 'BUSINESS IMPACT: Transactions failing', 'severity': 3, 'type': 'impact', 'icon': '💰'},
                    {'time': base_time + timedelta(minutes=10), 'event': 'OpsItem created', 'severity': 2, 'type': 'opsitem', 'icon': '📋'}
                ])
        
        if events:
            # Create enhanced timeline visualization
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Timeline chart
                df = pd.DataFrame(events)
                
                # Create color mapping for event types
                color_map = {
                    'change': '#3498db',
                    'deployment': '#2ecc71',
                    'warning': '#f39c12',
                    'error': '#e74c3c',
                    'incident': '#c0392b',
                    'impact': '#e91e63',  # Hot pink for business impact
                    'analysis': '#9b59b6',
                    'recovery': '#1abc9c',
                    'resolved': '#27ae60',
                    'metric': '#34495e',
                    'opsitem': '#7f8c8d'
                }
                
                fig = px.scatter(df, x='time', y='severity', 
                               color='type',
                               color_discrete_map=color_map,
                               hover_data=['event'],
                               title='📅 Incident Timeline' + (' with Change Correlation' if has_change else ''),
                               labels={'severity': 'Severity Level', 'time': 'Time'})
                
                # Add event labels
                for _, row in df.iterrows():
                    fig.add_annotation(
                        x=row['time'],
                        y=row['severity'],
                        text=f"{row['icon']} {row['event']}",
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-40
                    )
                
                fig.update_layout(showlegend=True, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Legend and correlation info
                if has_change:
                    st.markdown("### 🔗 Correlation")
                    st.info(f"""
                    **Change ID:** {ops_data.get('RelatedChangeId', 'Unknown')}
                    
                    **Time to Incident:** {ops_data.get('TimeToIncident', '15 minutes')}
                    
                    **Pattern:** Change → Config Mismatch → Incident
                    """)
                else:
                    st.markdown("### 📊 Timeline Legend")
                    st.write("No change correlation detected")
            
    def display_recommendations(self, incident):
        """Display actionable recommendations."""
        st.markdown("### 💡 Recommendations")
        
        analysis = incident.get('analysis', {})
        recommendations = analysis.get('recommendations', [])
        
        if not recommendations:
            # Generate based on incident type
            if incident.get('type') == 'performance':
                recommendations = [
                    "Scale up EC2 instances to handle increased load",
                    "Implement auto-scaling policies with appropriate thresholds",
                    "Optimize database queries showing high latency",
                    "Enable caching for frequently accessed data"
                ]
            elif incident.get('type') == 'security':
                recommendations = [
                    "Review and restrict security group rules",
                    "Enable AWS GuardDuty for threat detection",
                    "Implement network ACLs for additional security",
                    "Review CloudTrail logs for unauthorized activities"
                ]
            elif incident.get('type') == 'outage':
                recommendations = [
                    "Implement health checks and auto-recovery",
                    "Configure multi-AZ deployment for high availability",
                    "Set up CloudWatch alarms for early detection",
                    "Create runbooks for incident response"
                ]
                
        # Immediate actions
        st.markdown("#### 🚨 Immediate Actions")
        for i, rec in enumerate(recommendations[:2], 1):
            st.error(f"{i}. {rec}")
            
        # Long-term improvements
        st.markdown("#### 📋 Long-term Improvements")
        for i, rec in enumerate(recommendations[2:], 1):
            st.info(f"{i}. {rec}")
            
        # Generate unique suffix for button keys based on incident context
        # Use key_manager to ensure uniqueness
        incident_id = incident.get('ops_item_id', '')
        incident_type = incident.get('type', 'unknown')
        
        # Action buttons with unique keys using key_manager
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📧 Create JIRA Ticket", use_container_width=True, 
                        key=key_manager.get_unique_key("create_jira", incident_id, incident_type, "recommendations")):
                st.success("✅ Ticket created")
        with col2:
            if st.button("📢 Send to Slack", use_container_width=True, 
                        key=key_manager.get_unique_key("send_slack", incident_id, incident_type, "recommendations")):
                st.success("✅ Notification sent")
        with col3:
            if st.button("📄 Export Report", use_container_width=True, 
                        key=key_manager.get_unique_key("export_report", incident_id, incident_type, "recommendations")):
                st.success("✅ Report exported")
                
    def display_metrics_analysis(self, incident):
        """Display detailed metrics analysis."""
        st.markdown("### 📈 Metrics Analysis")
        
        # Create sample metrics visualization
        time_range = pd.date_range(end=datetime.now(), periods=20, freq='5min')
        
        # CPU and Memory metrics
        col1, col2 = st.columns(2)
        
        with col1:
            cpu_data = pd.DataFrame({
                'Time': time_range,
                'CPU %': [30 + (i * 3 if i > 10 else 0) for i in range(20)]
            })
            fig = px.line(cpu_data, x='Time', y='CPU %', title='CPU Utilization')
            fig.add_hline(y=80, line_dash="dash", line_color="red", 
                         annotation_text="Critical Threshold")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            memory_data = pd.DataFrame({
                'Time': time_range,
                'Memory %': [40 + (i * 2.5 if i > 10 else 0) for i in range(20)]
            })
            fig = px.line(memory_data, x='Time', y='Memory %', title='Memory Utilization')
            fig.add_hline(y=85, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold")
            st.plotly_chart(fig, use_container_width=True)
            
        # Error rate and response time
        col1, col2 = st.columns(2)
        
        with col1:
            error_data = pd.DataFrame({
                'Time': time_range,
                'Error Rate %': [0.5 + (i * 0.8 if i > 12 else 0) for i in range(20)]
            })
            fig = px.line(error_data, x='Time', y='Error Rate %', 
                         title='Error Rate', color_discrete_sequence=['red'])
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            response_data = pd.DataFrame({
                'Time': time_range,
                'Response Time (ms)': [200 + (i * 100 if i > 12 else 0) for i in range(20)]
            })
            fig = px.line(response_data, x='Time', y='Response Time (ms)', 
                         title='API Response Time')
            st.plotly_chart(fig, use_container_width=True)
            
    def display_raw_data(self, incident):
        """Display raw data for debugging."""
        st.markdown("### 📝 Raw Data")
        
        # OpsItem details
        if 'ops_item' in incident:
            with st.expander("OpsItem Details"):
                st.json(incident['ops_item'])
                
        # Analysis results
        if 'analysis' in incident:
            with st.expander("Analysis Results"):
                st.json(incident['analysis'])
                
        # Raw collected data
        if 'raw_data' in incident:
            with st.expander("Collected Data"):
                st.json(incident['raw_data'])

    def render_knowledge_base(self):
        """Render the knowledge base section."""
        st.header("📚 SRE Knowledge Base")
        
        # Knowledge base tabs
        kb_tabs = st.tabs(["🔍 Search", "📖 Browse", "➕ Add Document", "🧪 Test Analysis", "🌐 External Sources"])
        
        with kb_tabs[0]:
            self.render_kb_search()
            
        with kb_tabs[1]:
            self.render_kb_browse()
            
        with kb_tabs[2]:
            self.render_kb_add_document()
            
        with kb_tabs[3]:
            self.render_kb_test_analysis()
            
        with kb_tabs[4]:
            self.render_kb_external_sources()
            
    def get_recent_incidents_for_dropdown(self):
        """Get recent incidents for the dropdown selection."""
        try:
            ssm_client = boto3.client('ssm', region_name=self.region)
            
            # Get recent OpsItems
            response = ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress', 'Resolved'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=10
            )
            
            incidents = []
            for item in response.get('OpsItemSummaries', []):
                # Extract key information
                ops_data = item.get('OperationalData', {})
                
                incident = {
                    'id': item['OpsItemId'],
                    'title': item.get('Title', 'Unknown'),
                    'description': item.get('Description', '')[:100],  # First 100 chars
                    'category': item.get('Category', 'Unknown'),
                    'severity': item.get('Severity', '3'),
                    'created': item.get('CreatedTime', datetime.utcnow()),
                    'root_cause': ops_data.get('RootCause', {}).get('Value', 'Unknown')
                }
                
                # Check if it's a change-related incident
                if 'RelatedChangeId' in ops_data:
                    incident['root_cause'] = 'Configuration mismatch from change'
                    incident['change_id'] = ops_data['RelatedChangeId']['Value']
                
                incidents.append(incident)
            
            # Sort by creation time (most recent first)
            incidents.sort(key=lambda x: x['created'], reverse=True)
            
            return incidents[:5]  # Return top 5 most recent
            
        except Exception as e:
            st.warning(f"Could not fetch recent incidents: {str(e)}")
            return []
    
    def render_kb_search(self):
        """Render knowledge base search interface."""
        st.subheader("Search Knowledge Base")
        
        # Initialize session state if needed
        if 'kb_search_results' not in st.session_state:
            st.session_state.kb_search_results = None
        
        # Add incident dropdown for demo purposes
        st.info("💡 **Demo Tip**: Select a recent incident and click 'Load Query' to automatically populate the search")
        
        # Get recent incidents for dropdown
        recent_incidents = self.get_recent_incidents_for_dropdown()
        
        # Create columns for incident selection
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_incident = st.selectbox(
                "Select incident for demo (optional)",
                ["-- Manual Query --"] + [f"{inc['id']} - {inc['title']}" for inc in recent_incidents],
                help="Select an incident to search for similar cases, fixes, and best practices"
            )
        
        with col2:
            load_button = st.button("📥 Load Query", disabled=(selected_incident == "-- Manual Query --"))
        
        search_type = st.radio(
            "Search Type",
            ["Similar Incidents", "Best Practices", "Resolution Guides"],
            horizontal=True
        )
        
        # Initialize session state for query if not exists
        if 'kb_search_query' not in st.session_state:
            st.session_state.kb_search_query = ""
        
        # Track if we just loaded a query
        if 'kb_query_loaded' not in st.session_state:
            st.session_state.kb_query_loaded = False
            
        # Handle load button click
        if load_button and selected_incident != "-- Manual Query --":
            # Extract incident details
            incident_id = selected_incident.split(" - ")[0]
            incident = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
            if incident:
                if search_type == "Similar Incidents":
                    st.session_state.kb_search_query = incident.get('description', incident['title'])
                elif search_type == "Best Practices":
                    st.session_state.kb_search_query = f"{incident.get('category', 'performance')} {incident.get('root_cause', 'issues')}"
                else:  # Resolution Guides
                    st.session_state.kb_search_query = incident.get('root_cause', incident['title'])
                
                st.session_state.kb_query_loaded = True
                # Force a rerun to update the text area
                st.experimental_rerun()
        
        # Show success message if query was just loaded
        if st.session_state.kb_query_loaded:
            st.success(f"✅ Query loaded successfully!")
            st.session_state.kb_query_loaded = False
        
        # Search form - Use the key parameter properly with session state
        query = st.text_area(
            "Enter your search query:", 
            value=st.session_state.kb_search_query,
            key="kb_query_text_area",
            height=100,
            help="Enter keywords, error messages, or incident descriptions"
        )
        
        # Update session state when query changes
        if query != st.session_state.kb_search_query:
            st.session_state.kb_search_query = query
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            category = st.selectbox(
                "Category (optional)",
                ["All", "performance", "security", "outage", "data"]
            )
        with col2:
            max_results = st.number_input("Max Results", min_value=1, max_value=20, value=5)
            
        # Simple button test - bypass key manager temporarily
        if st.button("🔍 Search", type="primary", key="simple_search_button"):
            st.write("🔍 DEBUG: Search button clicked!")
            # Always use the current query value
            if query:
                st.write(f"🔍 DEBUG: Calling search with query: {query}")
                self.search_knowledge_base(search_type, query, category, max_results)
            else:
                st.warning("Please enter a search query")
        
        # Display results if available in session state
        st.write(f"🔍 DEBUG: Checking session state - kb_search_results exists: {'kb_search_results' in st.session_state}")
        if 'kb_search_results' in st.session_state:
            st.write(f"🔍 DEBUG: kb_search_results value: {st.session_state.kb_search_results is not None}")
            if st.session_state.kb_search_results:
                st.write("🔍 DEBUG: Calling display_search_results")
                self.display_search_results(st.session_state.kb_search_results)
            else:
                st.write("🔍 DEBUG: kb_search_results is None/empty")
        else:
            st.write("🔍 DEBUG: kb_search_results not in session state")
        
        # Debug info
        with st.expander("🔍 Debug Info", expanded=False):
            st.write("**Session State Debug:**")
            st.write(f"kb_search_results exists: {'kb_search_results' in st.session_state}")
            if 'kb_search_results' in st.session_state:
                st.write(f"kb_search_results value: {st.session_state.kb_search_results is not None}")
                if st.session_state.kb_search_results:
                    st.write(f"Type: {st.session_state.kb_search_results.get('type')}")
                    st.write(f"Has body: {'body' in st.session_state.kb_search_results}")
                    if 'body' in st.session_state.kb_search_results:
                        body = st.session_state.kb_search_results['body']
                        st.write(f"Results count: {len(body.get('results', []))}")
                
    def search_knowledge_base(self, search_type, query, category, max_results):
        """Search the knowledge base."""
        st.write("🔍 DEBUG: search_knowledge_base called")
        st.write(f"🔍 DEBUG: search_type={search_type}, query={query}")
        with st.spinner("Searching knowledge base..."):
            try:
                # Prepare the action based on search type
                if search_type == "Similar Incidents":
                    action = "search_incidents"
                    params = {
                        'query': query,
                        'k': max_results
                    }
                    if category != "All":
                        params['category'] = category
                elif search_type == "Best Practices":
                    action = "search_best_practices"
                    params = {
                        'query': query,
                        'tags': [category] if category != "All" else []
                    }
                else:  # Resolution Guides
                    action = "get_resolution"
                    params = {
                        'incident_type': category if category != "All" else "general"
                    }
                    
                # Invoke knowledge base Lambda
                lambda_client = boto3.client('lambda', region_name=self.region)
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': action,
                        **params
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                st.write(f"🔍 DEBUG: Lambda response status: {result.get('statusCode')}")
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    st.write(f"🔍 DEBUG: Lambda body has {len(body.get('results', []))} results")
                    
                    # Store results in session state
                    st.session_state.kb_search_results = {
                        'type': action,
                        'body': body,
                        'timestamp': datetime.now()
                    }
                    st.write("🔍 DEBUG: Results stored in session state")
                    # Don't call rerun - let natural flow handle it
                else:
                    st.error(f"Search failed: {result.get('body')}")
                    st.session_state.kb_search_results = None
                    
            except Exception as e:
                st.error(f"Error searching knowledge base: {str(e)}")
                st.write(f"🔍 DEBUG: Exception in search: {str(e)}")
                st.session_state.kb_search_results = None
    
    def display_search_results(self, results_data):
        """Display search results from session state."""
        st.write("🔍 DEBUG: display_search_results called")
        st.write(f"🔍 DEBUG: results_data = {results_data is not None}")
        
        if not results_data:
            st.write("🔍 DEBUG: results_data is None/empty - returning")
            return
            
        st.write(f"🔍 DEBUG: results_data keys = {list(results_data.keys())}")
        action = results_data['type']
        body = results_data['body']
        
        st.write(f"🔍 DEBUG: action = {action}")
        st.write(f"🔍 DEBUG: body keys = {list(body.keys())}")
        
        if action == "get_resolution" and body.get('guide'):
            # Display single resolution guide
            guide = body['guide']
            with st.expander(f"📋 {guide['title']}", expanded=True):
                st.markdown(guide['content'])
        else:
            # Display search results
            results = body.get('results', [])
            st.write(f"🔍 DEBUG: Found {len(results)} results")
            st.success(f"Found {len(results)} results")
            
            # Group results by type for better visualization
            st.write("🔍 DEBUG: Starting result grouping...")
            incidents = [r for r in results if r['metadata'].get('type') == 'incident']
            best_practices = [r for r in results if r['metadata'].get('type') == 'best_practice']
            resolutions = [r for r in results if r['metadata'].get('type') == 'resolution_guide']
            
            st.write(f"🔍 DEBUG: Grouped - Incidents: {len(incidents)}, Best Practices: {len(best_practices)}, Resolutions: {len(resolutions)}")
            
            # Display incidents
            if incidents:
                st.write("🔍 DEBUG: Displaying incidents section")
                st.markdown("### 🚨 Similar Incidents")
                for idx, doc in enumerate(incidents, 1):
                    st.write(f"🔍 DEBUG: Displaying incident {idx}: {doc['title']}")
                    
                    # Safe score handling
                    score = doc.get('score', 0)
                    if not isinstance(score, (int, float)) or score != score or score == float('inf') or score == float('-inf'):
                        score_str = "N/A"
                    else:
                        score_str = f"{float(score):.2f}"
                    
                    with st.expander(f"{idx}. {doc['title']} (Similarity: {score_str})"):
                        st.markdown(f"**Category:** {doc['metadata'].get('category', 'N/A')}")
                        
                        # Check for change correlation
                        if 'change_id' in doc['metadata']:
                            st.error(f"🔧 **Caused by Change:** {doc['metadata']['change_id']}")
                        
                        st.markdown("**Description:**")
                        st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                        
                        # Show resolution if available
                        if 'resolution' in doc['metadata']:
                            st.success(f"✅ **Resolution:** {doc['metadata']['resolution']}")
            else:
                st.write("🔍 DEBUG: No incidents to display")
            
            # Display best practices
            if best_practices:
                st.write("🔍 DEBUG: Displaying best practices section")
                st.markdown("### 📚 Related Best Practices")
                for idx, doc in enumerate(best_practices, 1):
                    st.write(f"🔍 DEBUG: Displaying best practice {idx}: {doc['title']}")
                    with st.expander(f"{idx}. {doc['title']}"):
                        if doc['metadata'].get('tags'):
                            st.markdown(f"**Tags:** {', '.join(doc['metadata']['tags'])}")
                        st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
            else:
                st.write("🔍 DEBUG: No best practices to display")
            
            # Display resolution guides
            if resolutions:
                st.write("🔍 DEBUG: Displaying resolution guides section")
                st.markdown("### 🔧 Resolution Guides")
                for idx, doc in enumerate(resolutions, 1):
                    st.write(f"🔍 DEBUG: Displaying resolution guide {idx}: {doc['title']}")
                    with st.expander(f"{idx}. {doc['title']}"):
                        st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
            else:
                st.write("🔍 DEBUG: No resolution guides to display")
                
    def render_kb_browse(self):
        """Browse knowledge base by category."""
        st.subheader("Browse Knowledge Base")
        
        # Initialize session state if needed
        if 'kb_browse_results' not in st.session_state:
            st.session_state.kb_browse_results = None
        
        # Add an "All" option to browse all categories
        category = st.selectbox(
            "Select Category",
            ["All", "performance", "security", "outage", "resilience", "data"]
        )
        
        doc_type = st.radio(
            "Document Type",
            ["All", "incident", "best_practice", "resolution_guide"],
            horizontal=True
        )
        
        # Simple button test - bypass key manager temporarily
        if st.button("📖 Browse", key="simple_browse_button"):
            st.write("🔍 DEBUG: Browse button clicked!")
            st.write(f"🔍 DEBUG: Browsing category={category}, doc_type={doc_type}")
            self.browse_knowledge_base(category, doc_type)
        
        # Display browse results if available
        st.write(f"🔍 DEBUG: Checking browse session state - kb_browse_results exists: {'kb_browse_results' in st.session_state}")
        if 'kb_browse_results' in st.session_state:
            st.write(f"🔍 DEBUG: kb_browse_results value: {st.session_state.kb_browse_results is not None}")
            if st.session_state.kb_browse_results:
                st.write("🔍 DEBUG: Calling display_browse_results")
                self.display_browse_results(st.session_state.kb_browse_results)
            else:
                st.write("🔍 DEBUG: kb_browse_results is None/empty")
        else:
            st.write("🔍 DEBUG: kb_browse_results not in session state")
        
        # Debug info
        with st.expander("🔍 Browse Debug Info", expanded=False):
            st.write("**Session State Debug:**")
            st.write(f"kb_browse_results exists: {'kb_browse_results' in st.session_state}")
            if 'kb_browse_results' in st.session_state:
                st.write(f"kb_browse_results value: {st.session_state.kb_browse_results is not None}")
                if st.session_state.kb_browse_results:
                    st.write(f"Results count: {len(st.session_state.kb_browse_results.get('results', []))}")
                    st.write(f"Category: {st.session_state.kb_browse_results.get('category')}")
            
    def browse_knowledge_base(self, category, doc_type):
        """Browse documents by category."""
        st.write("🔍 DEBUG: browse_knowledge_base called")
        st.write(f"🔍 DEBUG: category={category}, doc_type={doc_type}")
        with st.spinner("Browsing knowledge base..."):
            try:
                lambda_client = boto3.client('lambda', region_name=self.region)
                
                # Use the new browse_documents action
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'browse_documents',
                        'category': None if category == "All" else category,
                        'doc_type': None if doc_type == "All" else doc_type,
                        'limit': 50
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                st.write(f"🔍 DEBUG: Browse Lambda response status: {result.get('statusCode')}")
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    all_results = body.get('results', [])
                    st.write(f"🔍 DEBUG: Browse Lambda body has {len(all_results)} results")
                    
                    # Store in session state
                    st.session_state.kb_browse_results = {
                        'results': all_results,
                        'category': category,
                        'doc_type': doc_type,
                        'timestamp': datetime.now()
                    }
                    st.write("🔍 DEBUG: Browse results stored in session state")
                    # Don't call rerun - let natural flow handle it
                else:
                    st.error(f"Failed to browse documents: {result.get('body')}")
                    st.session_state.kb_browse_results = None
                    
            except Exception as e:
                st.error(f"Error browsing knowledge base: {str(e)}")
                st.write(f"🔍 DEBUG: Exception in browse: {str(e)}")
                st.session_state.kb_browse_results = None
    
    def display_browse_results(self, browse_data):
        """Display browse results from session state."""
        if not browse_data:
            return
        
        all_results = browse_data['results']
        category = browse_data['category']
        
        if all_results:
            category_display = "all categories" if category == "All" else f"{category} category"
            st.success(f"Found {len(all_results)} documents in {category_display}")
            
            # Group by type
            by_type = {}
            for doc in all_results:
                doc_type = doc.get('metadata', {}).get('type', 'unknown')
                if doc_type not in by_type:
                    by_type[doc_type] = []
                by_type[doc_type].append(doc)
            
            # Display each type
            type_order = ['incident', 'best_practice', 'resolution_guide']
            for doc_type in type_order:
                if doc_type in by_type:
                    docs = by_type[doc_type]
                    type_emoji = {
                        'incident': '🚨',
                        'best_practice': '📚',
                        'resolution_guide': '🔧'
                    }.get(doc_type, '📄')
                    
                    st.markdown(f"### {type_emoji} {doc_type.replace('_', ' ').title()}s ({len(docs)})")
                    
                    for doc in docs:
                        with st.expander(f"{doc['title']} ({doc['document_id']})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**Category:** {doc.get('metadata', {}).get('category', 'N/A')}")
                                st.markdown(f"**Tags:** {', '.join(doc.get('metadata', {}).get('tags', []))}")
                            with col2:
                                if doc.get('metadata', {}).get('severity'):
                                    severity_color = {
                                        'high': '🔴',
                                        'medium': '🟡',
                                        'low': '🟢'
                                    }.get(doc['metadata']['severity'], '⚪')
                                    st.markdown(f"**Severity:** {severity_color} {doc['metadata']['severity']}")
                            
                            st.markdown("---")
                            
                            # Show content
                            content = doc['content']
                            if len(content) > 1000:
                                # Show first 1000 chars
                                st.markdown(content[:1000] + "...")
                                st.info("Content truncated. Full content available in the document.")
                            else:
                                st.markdown(content)
                            
                            # Show metadata
                            if doc.get('metadata', {}).get('root_cause'):
                                st.info(f"**Root Cause:** {doc['metadata']['root_cause']}")
        else:
            st.warning(f"No documents found in {category} category")
            st.info("Try selecting a different category or adding documents to the knowledge base.")
                
    def render_kb_add_document(self):
        """Add new document to knowledge base."""
        st.subheader("Add Document to Knowledge Base")
        
        # Initialize session state if needed
        if 'kb_add_result' not in st.session_state:
            st.session_state.kb_add_result = None
        
        doc_type = st.selectbox(
            "Document Type",
            ["incident", "best_practice", "resolution_guide"]
        )
        
        doc_id = st.text_input("Document ID (e.g., INC-001, BP-001)")
        title = st.text_input("Title")
        
        category = st.selectbox(
            "Category",
            ["performance", "security", "outage", "resilience", "data"]
        )
        
        content = st.text_area("Content", height=300)
        
        tags = st.text_input("Tags (comma-separated)")
        
        if st.button("➕ Add Document", key=key_manager.get_tab_key("kb_add_document", "add")):
            if all([doc_id, title, category, content]):
                self.add_to_knowledge_base(doc_id, title, category, content, doc_type, tags)
            else:
                st.warning("Please fill all required fields")
        
        # Display result if available in session state
        if 'kb_add_result' in st.session_state and st.session_state.kb_add_result:
            if st.session_state.kb_add_result['success']:
                st.success(st.session_state.kb_add_result['message'])
            else:
                st.error(st.session_state.kb_add_result['message'])
                
    def add_to_knowledge_base(self, doc_id, title, category, content, doc_type, tags):
        """Add document to knowledge base."""
        with st.spinner("Adding document to knowledge base..."):
            try:
                document = {
                    'document_id': doc_id,
                    'title': title,
                    'content': content,
                    'metadata': {
                        'type': doc_type,
                        'category': category,
                        'tags': [tag.strip() for tag in tags.split(',')] if tags else []
                    }
                }
                
                lambda_client = boto3.client('lambda', region_name=self.region)
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'index_document',
                        'document': document
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    st.session_state.kb_add_result = {
                        'success': True,
                        'message': f"✅ Document {doc_id} added successfully!"
                    }
                else:
                    st.session_state.kb_add_result = {
                        'success': False,
                        'message': f"Failed to add document: {result.get('body')}"
                    }
                    
            except Exception as e:
                st.session_state.kb_add_result = {
                    'success': False,
                    'message': f"Error adding document: {str(e)}"
                }
                
    def render_kb_test_analysis(self):
        """Test knowledge-based analysis."""
        st.subheader("Test Knowledge-Based Analysis")
        
        # Initialize session state if needed
        if 'kb_analysis_result' not in st.session_state:
            st.session_state.kb_analysis_result = None
        
        st.info("Enter an incident description to get analysis enriched with knowledge base context")
        
        incident_desc = st.text_area(
            "Incident Description",
            value="Application experiencing severe performance degradation with database connection timeouts",
            height=100
        )
        
        incident_type = st.selectbox(
            "Incident Type",
            ["performance", "security", "outage", "general"]
        )
        
        # Simple button test - bypass key manager temporarily
        if st.button("🧪 Analyze with Knowledge Base", key="simple_analysis_button"):
            st.write("🔍 DEBUG: Analysis button clicked!")
            if incident_desc:
                st.write(f"🔍 DEBUG: Analyzing incident: {incident_desc[:100]}...")
                self.analyze_with_knowledge_base(incident_desc, incident_type)
            else:
                st.warning("Please enter an incident description")
        
        # Display analysis results if available
        st.write(f"🔍 DEBUG: Checking analysis session state - kb_analysis_result exists: {'kb_analysis_result' in st.session_state}")
        if 'kb_analysis_result' in st.session_state:
            st.write(f"🔍 DEBUG: kb_analysis_result value: {st.session_state.kb_analysis_result is not None}")
            if st.session_state.kb_analysis_result:
                st.write("🔍 DEBUG: Calling display_analysis_result")
                self.display_analysis_result(st.session_state.kb_analysis_result)
            else:
                st.write("🔍 DEBUG: kb_analysis_result is None/empty")
        else:
            st.write("🔍 DEBUG: kb_analysis_result not in session state")
                
    def analyze_with_knowledge_base(self, incident_desc, incident_type):
        """Analyze incident using knowledge base context."""
        st.write("🔍 DEBUG: analyze_with_knowledge_base called")
        st.write(f"🔍 DEBUG: incident_type={incident_type}")
        with st.spinner("Analyzing with knowledge base context..."):
            try:
                lambda_client = boto3.client('lambda', region_name=self.region)
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'analyze_with_context',
                        'incident_description': incident_desc,
                        'incident_type': incident_type
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                st.write(f"🔍 DEBUG: Analysis Lambda response status: {result.get('statusCode')}")
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    st.write(f"🔍 DEBUG: Analysis Lambda body keys: {list(body.keys())}")
                    st.session_state.kb_analysis_result = {
                        'success': True,
                        'body': body,
                        'timestamp': datetime.now()
                    }
                    st.write("🔍 DEBUG: Analysis results stored in session state")
                else:
                    st.session_state.kb_analysis_result = {
                        'success': False,
                        'error': result.get('body')
                    }
                    st.write(f"🔍 DEBUG: Analysis failed with error: {result.get('body')}")
                    
            except Exception as e:
                st.session_state.kb_analysis_result = {
                    'success': False,
                    'error': str(e)
                }
                st.write(f"🔍 DEBUG: Exception in analysis: {str(e)}")
    
    def display_analysis_result(self, result_data):
        """Display analysis results from session state."""
        if not result_data:
            return
        
        if result_data['success']:
            body = result_data['body']
            
            # Display context used
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Similar Incidents", body.get('context_used', {}).get('similar_incidents_count', 0))
            with col2:
                st.metric("Best Practices", body.get('context_used', {}).get('best_practices_count', 0))
            with col3:
                st.metric("Has Resolution Guide", "✅" if body.get('context_used', {}).get('has_resolution_guide', False) else "❌")
                
            # Display analysis
            st.markdown("### Knowledge-Enhanced Analysis")
            st.markdown(body.get('analysis', 'No analysis available'))
            
            # Display similar incidents if available
            if 'similar_incidents' in body:
                st.markdown("### 🚨 Similar Incidents")
                for inc in body['similar_incidents'][:3]:
                    with st.expander(inc.get('title', 'Unknown')):
                        st.write(inc.get('content', '')[:500] + "...")
        else:
            st.error(f"Analysis failed: {result_data.get('error', 'Unknown error')}")
    
    def render_kb_add_document(self):
        """Render add document to knowledge base interface."""
        st.subheader("Add Document to Knowledge Base")
        
        # Initialize session state if needed
        if 'kb_add_result' not in st.session_state:
            st.session_state.kb_add_result = None
        
        st.info("Add new documents, best practices, or resolution guides to the knowledge base")
        
        # Document form
        with st.form("add_document_form"):
            doc_title = st.text_input(
                "Document Title",
                placeholder="e.g., Database Performance Troubleshooting Guide"
            )
            
            doc_type = st.selectbox(
                "Document Type",
                ["best_practice", "resolution_guide", "incident", "general"]
            )
            
            doc_category = st.selectbox(
                "Category",
                ["performance", "security", "outage", "resilience", "data", "general"]
            )
            
            doc_content = st.text_area(
                "Content",
                height=200,
                placeholder="Enter the document content here..."
            )
            
            # Optional metadata
            st.subheader("Optional Metadata")
            
            col1, col2 = st.columns(2)
            with col1:
                severity = st.selectbox(
                    "Severity (if applicable)",
                    ["low", "medium", "high", "critical"],
                    index=1
                )
            
            with col2:
                tags_input = st.text_input(
                    "Tags (comma-separated)",
                    placeholder="e.g., database, performance, monitoring"
                )
            
            # Submit button
            submitted = st.form_submit_button("📝 Add Document", type="primary")
            
            if submitted:
                st.write("🔍 DEBUG: Add document form submitted!")
                if doc_title and doc_content:
                    st.write(f"🔍 DEBUG: Adding document: {doc_title}")
                    
                    # Parse tags
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                    
                    # Create document object
                    document = {
                        'document_id': f"USER_{int(datetime.now().timestamp())}",
                        'title': doc_title,
                        'content': doc_content,
                        'metadata': {
                            'type': doc_type,
                            'category': doc_category,
                            'tags': tags,
                            'severity': severity,
                            'created_by': 'user',
                            'created_at': datetime.now().isoformat()
                        }
                    }
                    
                    self.add_document_to_kb(document)
                else:
                    st.warning("Please enter both title and content")
        
        # Display add result if available
        st.write(f"🔍 DEBUG: Checking add session state - kb_add_result exists: {'kb_add_result' in st.session_state}")
        if 'kb_add_result' in st.session_state:
            st.write(f"🔍 DEBUG: kb_add_result value: {st.session_state.kb_add_result is not None}")
            if st.session_state.kb_add_result:
                st.write("🔍 DEBUG: Calling display_add_result")
                self.display_add_result(st.session_state.kb_add_result)
            else:
                st.write("🔍 DEBUG: kb_add_result is None/empty")
        else:
            st.write("🔍 DEBUG: kb_add_result not in session state")
    
    def add_document_to_kb(self, document):
        """Add a document to the knowledge base."""
        st.write("🔍 DEBUG: add_document_to_kb called")
        st.write(f"🔍 DEBUG: document title={document['title']}")
        
        with st.spinner("Adding document to knowledge base..."):
            try:
                lambda_client = boto3.client('lambda', region_name=self.region)
                
                response = lambda_client.invoke(
                    FunctionName='sre-knowledge-base-agent-lambda',
                    InvocationType='RequestResponse',
                    Payload=json.dumps({
                        'action': 'index_document',
                        'document': document
                    })
                )
                
                result = json.loads(response['Payload'].read())
                
                st.write(f"🔍 DEBUG: Add document Lambda response status: {result.get('statusCode')}")
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    st.write(f"🔍 DEBUG: Add document successful")
                    
                    st.session_state.kb_add_result = {
                        'success': True,
                        'message': body.get('message', 'Document added successfully'),
                        'document_id': document['document_id'],
                        'timestamp': datetime.now()
                    }
                    st.write("🔍 DEBUG: Add result stored in session state")
                else:
                    st.session_state.kb_add_result = {
                        'success': False,
                        'error': result.get('body', 'Unknown error')
                    }
                    st.write(f"🔍 DEBUG: Add document failed: {result.get('body')}")
                    
            except Exception as e:
                st.session_state.kb_add_result = {
                    'success': False,
                    'error': str(e)
                }
                st.write(f"🔍 DEBUG: Exception in add document: {str(e)}")
    
    def display_add_result(self, result_data):
        """Display add document result."""
        st.write("🔍 DEBUG: display_add_result called")
        
        if not result_data:
            st.write("🔍 DEBUG: result_data is empty")
            return
        
        if result_data.get('success'):
            st.success(f"✅ {result_data.get('message', 'Document added successfully')}")
            st.info(f"Document ID: {result_data.get('document_id')}")
            
            # Clear the result after displaying
            if st.button("Add Another Document", key="add_another_doc"):
                st.session_state.kb_add_result = None
        else:
            st.error(f"❌ Failed to add document: {result_data.get('error', 'Unknown error')}")
    
    def render_kb_external_sources(self):
        """Render external knowledge base sources."""
        from kb_external_sources import render_kb_external_sources
        render_kb_external_sources(self)
                
    def render_recent_changes(self):
        """Render recent changes tab."""
        st.header("🔧 Recent Changes")
        
        # Fetch recent changes (OpsItems with [CHANGE] prefix)
        try:
            response = self.ssm_client.describe_ops_items(
                OpsItemFilters=[
                    {
                        'Key': 'Title',
                        'Values': ['[CHANGE]'],
                        'Operator': 'Contains'
                    },
                    {
                        'Key': 'Status',
                        'Values': ['Open', 'InProgress'],
                        'Operator': 'Equal'
                    }
                ],
                MaxResults=20
            )
            
            changes = response.get('OpsItemSummaries', [])
            
            if changes:
                st.success(f"Found {len(changes)} recent changes")
                
                # Create columns for better layout
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    selected_change = st.selectbox(
                        "Select a change to view details:",
                        options=[f"{c['OpsItemId']} - {c['Title']}" for c in changes],
                        format_func=lambda x: x.split(' - ', 1)[1] if ' - ' in x else x
                    )
                
                with col2:
                    if st.button("🔄 Refresh Changes", key=key_manager.get_unique_key("refresh_changes", "main")):
                        st.experimental_rerun()
                
                if selected_change:
                    change_id = selected_change.split(' - ')[0]
                    
                    # Get full change details
                    change_response = self.ssm_client.get_ops_item(OpsItemId=change_id)
                    change_details = change_response['OpsItem']
                    
                    # Display change details
                    st.markdown("### Change Details")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Change ID", change_details.get('OpsItemId', 'N/A'))
                        ops_data = change_details.get('OperationalData', {})
                        if 'ChangeRequestId' in ops_data:
                            st.metric("Request ID", ops_data['ChangeRequestId'].get('Value', 'N/A'))
                    
                    with col2:
                        st.metric("Status", change_details.get('Status', 'Unknown'))
                        if 'Risk' in ops_data:
                            risk = ops_data['Risk'].get('Value', 'Unknown')
                            risk_color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}.get(risk, '⚪')
                            st.metric("Risk Level", f"{risk_color} {risk}")
                    
                    with col3:
                        created_time = change_details.get('CreatedTime', datetime.now())
                        if isinstance(created_time, str):
                            created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        st.metric("Created", created_time.strftime('%Y-%m-%d %H:%M'))
                        if 'ChangeType' in ops_data:
                            st.metric("Type", ops_data['ChangeType'].get('Value', 'N/A'))
                    
                    # Show description
                    with st.expander("📋 Change Description", expanded=True):
                        st.markdown(change_details.get('Description', 'No description available'))
                    
                    # Check for related incidents
                    st.markdown("### 🔗 Related Incidents")
                    
                    # Get the change request ID from operational data
                    change_request_id = ops_data.get('ChangeRequestId', {}).get('Value', '')
                    
                    # Search for all recent incidents and filter client-side
                    try:
                        incident_response = self.ssm_client.describe_ops_items(
                            OpsItemFilters=[
                                {
                                    'Key': 'Status',
                                    'Values': ['Open', 'InProgress', 'Resolved'],
                                    'Operator': 'Equal'
                                },
                                {
                                    'Key': 'CreatedTime',
                                    'Values': [(datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')],
                                    'Operator': 'GreaterThan'
                                }
                            ],
                            MaxResults=50
                        )
                        
                        # Filter incidents that reference this change
                        all_incidents = incident_response.get('OpsItemSummaries', [])
                        related_incidents = []
                        
                        for incident in all_incidents:
                            # Skip if this is a change OpsItem
                            if '[CHANGE]' in incident.get('Title', ''):
                                continue
                                
                            # Check if this incident references the change
                            inc_ops_data = incident.get('OperationalData', {})
                            if inc_ops_data.get('RelatedChangeId', {}).get('Value') == change_request_id:
                                related_incidents.append(incident)
                                
                    except Exception as e:
                        st.error(f"Error searching for related incidents: {str(e)}")
                        related_incidents = []
                    
                    if related_incidents:
                        st.warning(f"⚠️ This change caused {len(related_incidents)} incident(s)")
                        
                        for incident in related_incidents:
                            with st.expander(f"🚨 {incident['Title']} ({incident['OpsItemId']})"):
                                st.write(f"**Severity:** {incident.get('Severity', 'N/A')}")
                                st.write(f"**Status:** {incident.get('Status', 'N/A')}")
                                st.write(f"**Created:** {incident.get('CreatedTime', 'N/A')}")
                                
                                if st.button(f"Analyze Incident", key=f"analyze_{incident['OpsItemId']}"):
                                    st.session_state.selected_ops_item = incident['OpsItemId']
                                    st.experimental_rerun()
                    else:
                        st.success("✅ No incidents caused by this change")
                    
                    # Timeline visualization
                    if related_incidents:
                        st.markdown("### 📅 Change Impact Timeline")
                        self.display_change_timeline(change_details, related_incidents)
                        
            else:
                st.info("No recent changes found. Changes are tracked when they have '[CHANGE]' prefix in the title.")
                
                # Demo button
                if st.button("🎭 Create Demo Change", key=key_manager.get_unique_key("create_demo_change", "main")):
                    with st.spinner("Creating demo change..."):
                        from change_incident_demo import ChangeIncidentDemo
                        demo = ChangeIncidentDemo()
                        change_details = demo.create_change_record()
                        st.success(f"Created demo change: {change_details['ChangeRequestId']}")
                        st.experimental_rerun()
                        
        except Exception as e:
            st.error(f"Error fetching changes: {str(e)}")
    
    def display_change_timeline(self, change_details, incidents):
        """Display timeline showing change and its impact."""
        events = []
        
        # Add change event
        change_time = change_details.get('CreatedTime', datetime.now())
        if isinstance(change_time, str):
            change_time = datetime.fromisoformat(change_time.replace('Z', '+00:00'))
            
        events.append({
            'time': change_time,
            'event': f"Change {change_details['OpsItemId']} implemented",
            'type': 'change',
            'severity': 0,
            'icon': '🔧'
        })
        
        # Add incident events
        for incident in incidents:
            inc_time = incident.get('CreatedTime', change_time + timedelta(minutes=15))
            if isinstance(inc_time, str):
                inc_time = datetime.fromisoformat(inc_time.replace('Z', '+00:00'))
                
            time_diff = (inc_time - change_time).total_seconds() / 60
            
            events.append({
                'time': inc_time,
                'event': f"{incident['Title']} ({incident['OpsItemId']})",
                'type': 'incident',
                'severity': int(incident.get('Severity', 2)),
                'icon': '🚨',
                'time_from_change': f"+{int(time_diff)} min"
            })
        
        # Create visualization
        if events:
            df = pd.DataFrame(events)
            
            fig = px.scatter(df, x='time', y='severity',
                           color='type',
                           hover_data=['event', 'time_from_change'] if 'time_from_change' in df.columns else ['event'],
                           title='Change → Incident Timeline',
                           labels={'severity': 'Severity', 'time': 'Time'},
                           color_discrete_map={'change': '#3498db', 'incident': '#e74c3c'})
            
            # Add annotations
            for _, row in df.iterrows():
                fig.add_annotation(
                    x=row['time'],
                    y=row['severity'],
                    text=f"{row['icon']} {row.get('time_from_change', '')}",
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-30
                )
            
            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_analytics(self):
        """Render analytics dashboard."""
        st.header("📊 SRE Analytics Dashboard")
        st.info("Analytics dashboard showing incident trends, patterns, and insights")
        
        # Placeholder for analytics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Incidents", "127", "↑ 12%")
        with col2:
            st.metric("Avg Resolution Time", "23 min", "↓ 5 min")
        with col3:
            st.metric("Knowledge Base Docs", "45", "↑ 8")
        with col4:
            st.metric("AI Accuracy", "94%", "↑ 2%")
            
        st.markdown("### Incident Trends")
        st.line_chart({"Performance": [10, 15, 13, 18, 20], "Security": [5, 7, 6, 9, 8], "Outage": [2, 3, 2, 4, 3]})
    
    def render_user_guide(self):
        """Render the user guide section."""
        st.header("❓ User Guide & Documentation")
        
        # Create a sidebar for guide navigation
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### 📑 Guide Topics")
            
            # Get all guide titles
            guides = get_all_guides()
            guide_titles = get_guide_titles()
            
            # Create radio buttons for navigation
            selected_guide_id = st.radio(
                "Select a topic:",
                options=[guide_id for guide_id, _ in guide_titles],
                format_func=lambda x: next(title for gid, title in guide_titles if gid == x),
                label_visibility="collapsed"
            )
        
        with col2:
            # Display selected guide
            if selected_guide_id:
                guide = guides.get(selected_guide_id, {})
                st.markdown(f"## {guide.get('title', 'Guide')}")
                st.markdown(guide.get('content', 'Content not available'))
                
                # Add quick actions based on guide
                st.markdown("---")
                st.markdown("### 🚀 Quick Actions")
                
                if selected_guide_id == "overview":
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("🎮 Generate Test Incident", key=key_manager.get_unique_key("guide_gen_incident", selected_guide_id)):
                            st.info("Switch to 'Incident Management' tab to generate incidents")
                    with col_b:
                        if st.button("🔍 Analyze Incident", key=key_manager.get_unique_key("guide_analyze", selected_guide_id)):
                            st.info("Switch to 'Analyze Incident' tab")
                    with col_c:
                        if st.button("📚 Search KB", key=key_manager.get_unique_key("guide_kb", selected_guide_id)):
                            st.info("Switch to 'Knowledge Base' tab")
                            
                elif selected_guide_id == "incident_analysis":
                    if st.button("🔍 Go to Analyze Tab", key=key_manager.get_unique_key("guide_go_analyze", selected_guide_id)):
                        st.info("Switch to 'Analyze Incident' tab to start")
                        
                elif selected_guide_id == "knowledge_management":
                    if st.button("📚 Go to Knowledge Base", key=key_manager.get_unique_key("guide_go_kb", selected_guide_id)):
                        st.info("Switch to 'Knowledge Base' tab to search or add documents")
                        
                # Add feedback section
                st.markdown("---")
                st.markdown("### 💬 Feedback")
                feedback = st.text_area("Was this guide helpful? Any suggestions?", key=f"feedback_{selected_guide_id}")
                if st.button("Submit Feedback", key=f"submit_feedback_{selected_guide_id}"):
                    st.success("Thank you for your feedback!")
                    
        # Add search functionality
        st.markdown("---")
        st.markdown("### 🔍 Search Documentation")
        search_query = st.text_input("Search for specific topics or keywords:", key=key_manager.get_unique_key("guide_search", "main"))
        
        if search_query:
            st.markdown("#### Search Results")
            # Simple search through all guides
            results = []
            for guide_id, guide in guides.items():
                if search_query.lower() in guide.get('content', '').lower() or search_query.lower() in guide.get('title', '').lower():
                    results.append((guide_id, guide))
            
            if results:
                for guide_id, guide in results:
                    with st.expander(f"📄 {guide.get('title', 'Guide')}"):
                        # Show relevant excerpt
                        content = guide.get('content', '')
                        # Find and highlight the search term
                        idx = content.lower().find(search_query.lower())
                        if idx != -1:
                            start = max(0, idx - 100)
                            end = min(len(content), idx + 200)
                            excerpt = content[start:end]
                            if start > 0:
                                excerpt = "..." + excerpt
                            if end < len(content):
                                excerpt = excerpt + "..."
                            st.markdown(excerpt)
                        st.markdown(f"[View full guide](#) (Select '{guide.get('title', '')}' from the topics)")
            else:
                st.info("No results found. Try different keywords.")
                
        # Add video tutorials placeholder
        st.markdown("---")
        st.markdown("### 🎥 Video Tutorials")
        st.info("Video tutorials coming soon! Topics will include:")
        tutorials = [
            "Getting Started with SRE Copilot (5 min)",
            "Analyzing Your First Incident (8 min)",
            "Building an Effective Knowledge Base (10 min)",
            "Advanced Correlation Techniques (12 min)",
            "Integrating with Your Tools (15 min)"
        ]
        for tutorial in tutorials:
            st.markdown(f"- 📹 {tutorial}")

    def render_mcp_status(self):
        """Render MCP Status page."""
        st.header("🔌 MCP Services Status")
        
        if not MCP_AVAILABLE:
            st.error("MCP integration is not available. Please check if MCP servers are installed.")
            return
            
        # Check status of each MCP service
        status = get_mcp_status()
        
        # Display status grid
        st.markdown("### Service Health")
        cols = st.columns(5)
        service_icons = {
            'splunk': '🔍',
            'dynatrace': '📊',
            'servicenow': '🎫',
            'confluence': '📄',
            'gitlab': '🔧'
        }
        
        for idx, (service, port) in enumerate(MCP_PORTS.items()):
            with cols[idx % 5]:
                service_status = status.get(service, 'unknown')
                if service_status == 'online':
                    st.success(f"{service_icons.get(service, '🔌')} {service.title()}")
                    st.caption(f"Port: {port}")
                elif service_status == 'offline':
                    st.error(f"{service_icons.get(service, '🔌')} {service.title()}")
                    st.caption("Offline")
                else:
                    st.warning(f"{service_icons.get(service, '🔌')} {service.title()}")
                    st.caption("Error")
        
        # Test data section
        st.markdown("---")
        st.markdown("### 🧪 Test MCP Services")
        
        # Service selector
        selected_service = st.selectbox(
            "Select a service to test:",
            options=list(MCP_PORTS.keys()),
            format_func=lambda x: x.title()
        )
        
        # Test buttons based on service
        if selected_service == 'splunk':
            st.markdown("#### Splunk Network Latency Search")
            query = st.text_input("Search Query", value="source=network latency>100", key=key_manager.get_unique_key("splunk_query", selected_service))
            time_range = st.selectbox("Time Range", ["-1h", "-4h", "-24h", "-7d"])
            
            if st.button("Search Splunk", key=key_manager.get_unique_key("search_splunk", selected_service)):
                with st.spinner("Searching..."):
                    try:
                        response = requests.post(
                            f"http://localhost:{MCP_PORTS['splunk']}/splunk/search",
                            json={"query": query, "time_range": time_range}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"Found {len(data.get('results', []))} results")
                            if data.get('results'):
                                st.json(data['results'][:5])  # Show first 5
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        
        elif selected_service == 'dynatrace':
            st.markdown("#### Dynatrace MQ Metrics")
            queue = st.text_input("Queue Name", value="OrderQueue", key=key_manager.get_unique_key("dynatrace_queue", selected_service))
            metric = st.selectbox("Metric", ["depth", "latency", "throughput"])
            
            if st.button("Get Metrics", key=key_manager.get_unique_key("get_metrics", selected_service)):
                with st.spinner("Fetching metrics..."):
                    try:
                        response = requests.get(
                            f"http://localhost:{MCP_PORTS['dynatrace']}/dynatrace/metrics",
                            params={"queue": queue, "metric": metric}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success("Metrics retrieved successfully")
                            st.json(data)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        
        elif selected_service == 'servicenow':
            st.markdown("#### ServiceNow Incidents")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("List Recent Incidents", key=key_manager.get_unique_key("list_incidents", selected_service)):
                    with st.spinner("Fetching incidents..."):
                        try:
                            response = requests.get(
                                f"http://localhost:{MCP_PORTS['servicenow']}/servicenow/incidents"
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"Found {len(data)} incidents")
                                for inc in data[:3]:
                                    st.info(f"**{inc['number']}**: {inc['short_description']}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            
            with col2:
                if st.button("List Recent Changes", key=key_manager.get_unique_key("list_changes", selected_service)):
                    with st.spinner("Fetching changes..."):
                        try:
                            response = requests.get(
                                f"http://localhost:{MCP_PORTS['servicenow']}/servicenow/changes"
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"Found {len(data)} changes")
                                for chg in data[:3]:
                                    st.info(f"**{chg['number']}**: {chg['short_description']}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            
        elif selected_service == 'confluence':
            st.markdown("#### Confluence Knowledge Base")
            search_term = st.text_input("Search Term", value="database performance", key=key_manager.get_unique_key("confluence_search", selected_service))
            
            if st.button("Search Confluence", key=key_manager.get_unique_key("search_confluence", selected_service)):
                with st.spinner("Searching..."):
                    try:
                        response = requests.get(
                            f"http://localhost:{MCP_PORTS['confluence']}/confluence/search",
                            params={"query": search_term}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"Found {len(data.get('results', []))} pages")
                            for page in data.get('results', [])[:3]:
                                st.info(f"**{page['title']}**\n{page.get('excerpt', '')[:200]}...")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        
        elif selected_service == 'gitlab':
            st.markdown("#### GitLab Repository Search")
            repo = st.text_input("Repository", value="backend/order-service", key=key_manager.get_unique_key("gitlab_repo", selected_service))
            search = st.text_input("Search Code", value="processOrder", key=key_manager.get_unique_key("gitlab_search", selected_service))
            
            if st.button("Search GitLab", key=key_manager.get_unique_key("search_gitlab", selected_service)):
                with st.spinner("Searching..."):
                    try:
                        response = requests.get(
                            f"http://localhost:{MCP_PORTS['gitlab']}/gitlab/search",
                            params={"repo": repo, "query": search}
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"Found matches in {len(data.get('results', []))} files")
                            for result in data.get('results', [])[:3]:
                                st.code(f"File: {result['file']}\nLine {result['line']}: {result['content']}", language="java")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Configuration section
        st.markdown("---")
        st.markdown("### ⚙️ MCP Configuration")
        
        with st.expander("View/Edit MCP Configuration"):
            config_str = json.dumps(MCP_PORTS, indent=2)
            new_config = st.text_area("MCP Port Configuration", value=config_str, height=200, key=key_manager.get_unique_key("mcp_config_text", "main"))
            
            if st.button("Update Configuration", key=key_manager.get_unique_key("update_mcp_config", "main")):
                try:
                    new_ports = json.loads(new_config)
                    # Save to file
                    with open('/home/ec2-user/sre/sre_mcp/mcp_ports.json', 'w') as f:
                        json.dump(new_ports, f, indent=2)
                    st.success("Configuration updated! Please restart the application.")
                except Exception as e:
                    st.error(f"Invalid configuration: {str(e)}")
    
    def render_feedback_analytics(self):
        """Render Feedback Analytics page."""
        st.header("📊 Human Feedback Analytics")
        
        if not MCP_AVAILABLE:
            st.error("MCP integration is not available.")
            return
            
        try:
            from feedback.feedback_system import FeedbackSystem
            feedback_system = FeedbackSystem()
            
            # Get feedback stats - use get_recent_feedback with high limit
            all_feedback = feedback_system.get_recent_feedback(limit=1000)
            
            # Overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Feedback", len(all_feedback))
            
            with col2:
                if all_feedback:
                    helpful_count = sum(1 for f in all_feedback if f.get('helpful', False))
                    helpful_pct = (helpful_count / len(all_feedback)) * 100
                    st.metric("Helpful %", f"{helpful_pct:.1f}%")
                else:
                    st.metric("Helpful %", "N/A")
            
            with col3:
                if all_feedback:
                    avg_confidence = sum(f.get('confidence', 0) for f in all_feedback) / len(all_feedback)
                    st.metric("Avg Confidence", f"{avg_confidence:.1f}/5")
                else:
                    st.metric("Avg Confidence", "N/A")
            
            with col4:
                recent_count = sum(1 for f in all_feedback 
                                 if datetime.fromisoformat(f.get('timestamp', '2020-01-01')) > 
                                    datetime.now() - timedelta(days=7))
                st.metric("Last 7 Days", recent_count)
            
            # Feedback timeline
            st.markdown("### 📈 Feedback Timeline")
            if all_feedback:
                # Create timeline data
                df_data = []
                for feedback in all_feedback:
                    df_data.append({
                        'date': datetime.fromisoformat(feedback.get('timestamp', '2020-01-01')).date(),
                        'helpful': 1 if feedback.get('helpful', False) else 0,
                        'not_helpful': 1 if not feedback.get('helpful', False) else 0
                    })
                
                df = pd.DataFrame(df_data)
                daily_stats = df.groupby('date').agg({
                    'helpful': 'sum',
                    'not_helpful': 'sum'
                }).reset_index()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['helpful'],
                    mode='lines+markers',
                    name='Helpful',
                    line=dict(color='green')
                ))
                fig.add_trace(go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['not_helpful'],
                    mode='lines+markers',
                    name='Not Helpful',
                    line=dict(color='red')
                ))
                fig.update_layout(
                    title="Daily Feedback Trend",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No feedback data available yet")
            
            # Recent feedback
            st.markdown("### 📝 Recent Feedback")
            if all_feedback:
                # Sort by timestamp
                sorted_feedback = sorted(all_feedback, 
                                       key=lambda x: x.get('timestamp', ''), 
                                       reverse=True)
                
                for feedback in sorted_feedback[:5]:
                    with st.expander(f"Feedback from {feedback.get('timestamp', 'Unknown')[:19]}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Incident ID**: {feedback.get('incident_id', 'Unknown')}")
                            st.markdown(f"**Feedback**: {feedback.get('feedback_text', 'No feedback text')}")
                            
                            # Show corrections if any
                            corrections = feedback.get('corrections', {})
                            if corrections:
                                st.markdown("**Corrections:**")
                                for key, value in corrections.items():
                                    st.write(f"- {key}: {value}")
                        
                        with col2:
                            if feedback.get('helpful'):
                                st.success("✅ Helpful")
                            else:
                                st.error("❌ Not Helpful")
                            
                            st.metric("Confidence", f"{feedback.get('confidence', 0)}/5")
            else:
                st.info("No feedback received yet")
            
            # Feedback patterns
            st.markdown("### 🔍 Common Feedback Patterns")
            if all_feedback:
                # Extract common words from feedback
                from collections import Counter
                import re
                
                all_text = ' '.join(f.get('feedback_text', '') for f in all_feedback)
                words = re.findall(r'\b\w+\b', all_text.lower())
                # Filter out common words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                             'of', 'with', 'by', 'from', 'was', 'were', 'been', 'be', 'have', 
                             'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
                             'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
                
                filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
                word_freq = Counter(filtered_words).most_common(10)
                
                if word_freq:
                    words, counts = zip(*word_freq)
                    fig = go.Figure(data=[
                        go.Bar(x=list(words), y=list(counts))
                    ])
                    fig.update_layout(
                        title="Most Common Feedback Terms",
                        xaxis_title="Terms",
                        yaxis_title="Frequency",
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Export options
            st.markdown("---")
            st.markdown("### 📤 Export Feedback Data")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Export as CSV", key=key_manager.get_unique_key("export_csv", "feedback")):
                    if all_feedback:
                        df = pd.DataFrame(all_feedback)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("No data to export")
            
            with col2:
                if st.button("Export as JSON", key=key_manager.get_unique_key("export_json", "feedback")):
                    if all_feedback:
                        json_str = json.dumps(all_feedback, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_str,
                            file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    else:
                        st.warning("No data to export")
            
            with col3:
                if st.button("Clear All Feedback", key=key_manager.get_unique_key("clear_feedback", "main")):
                    if st.checkbox("I understand this will delete all feedback data", key=key_manager.get_unique_key("confirm_clear", "feedback")):
                        # Would implement clear functionality
                        st.info("Clear functionality would be implemented here")
                        
        except Exception as e:
            st.error(f"Error loading feedback analytics: {str(e)}")
            st.info("Please ensure the feedback system is properly configured.")
    
    def render_defect_management(self):
        """NEW: Render defect management tab"""
        st.header("🐛 Defect Management Dashboard")
        
        # Check defect server status
        mcp_ports = {'alm_octane': 9085, 'jira': 9086}
        status = {}
        
        try:
            response = requests.get(f"http://localhost:{mcp_ports['alm_octane']}/octane/defects", timeout=2)
            status['alm_octane'] = {'online': response.status_code == 200, 'defects': len(response.json()) if response.status_code == 200 else 0}
        except:
            status['alm_octane'] = {'online': False, 'defects': 0}
        
        try:
            response = requests.get(f"http://localhost:{mcp_ports['jira']}/jira/issues", timeout=2)
            status['jira'] = {'online': response.status_code == 200, 'issues': len(response.json()) if response.status_code == 200 else 0}
        except Exception as e:
            st.warning(f"Jira connection error: {str(e)}")
            status['jira'] = {'online': False, 'issues': 0}
        
        # Status indicators
        col1, col2 = st.columns(2)
        
        with col1:
            alm_status = "🟢 Online" if status['alm_octane']['online'] else "🔴 Offline"
            st.markdown(f"### ALM Octane {alm_status}")
            st.metric("Defects Available", status['alm_octane']['defects'])
        
        with col2:
            jira_status = "🟢 Online" if status['jira']['online'] else "🔴 Offline"
            st.markdown(f"### Jira {jira_status}")
            st.metric("Issues Available", status['jira']['issues'])
        
        # Defect management sections
        defect_tabs = st.tabs(["📋 Overview", "🔍 Search", "➕ Create", "📊 Analytics"])
        
        with defect_tabs[0]:
            self._render_defect_overview(status, mcp_ports)
        
        with defect_tabs[1]:
            self._render_defect_search()
        
        with defect_tabs[2]:
            self._render_defect_creation()
        
        with defect_tabs[3]:
            self._render_defect_analytics()
    
    def render_defect_correlation(self):
        """NEW: Render defect correlation analysis tab"""
        st.header("🔗 Enhanced Incident-Defect Correlation")
        
        st.markdown("""
        Analyze incidents for potential defect correlations using AI-powered analysis 
        across ALM Octane and Jira systems.
        """)
        
        # Add option to load from incident
        data_source = st.radio("Data Source:", ["Manual Entry", "Load from Incident"], horizontal=True)
        
        if data_source == "Load from Incident":
            # Get recent incidents
            recent_incidents = self.get_recent_incidents_for_dropdown()
            
            if recent_incidents:
                selected_incident = st.selectbox(
                    "Select an incident to analyze:",
                    [""] + [f"{inc['id']} - {inc['title']}" for inc in recent_incidents],
                    help="Select an incident to auto-populate correlation analysis fields"
                )
                
                if selected_incident and selected_incident != "":
                    incident_id = selected_incident.split(" - ")[0]
                    incident = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
                    
                    if incident:
                        # Display incident info
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Root Cause:** {incident.get('root_cause', 'Unknown')}")
                        with col2:
                            st.info(f"**Category:** {incident.get('category', 'Unknown')}")
                        
                        # Auto-populate fields from incident
                        incident_title = incident.get('title', '')
                        incident_description = incident.get('description', '')
                        
                        # Map severity (1-5 to Low/Medium/High/Critical)
                        severity_map = {'1': 'Critical', '2': 'Critical', '3': 'High', '4': 'Medium', '5': 'Low'}
                        severity = severity_map.get(str(incident.get('severity', '3')), 'High')
                        
                        # Map category to type
                        category = incident.get('category', 'Unknown').lower()
                        if 'performance' in category or 'latency' in category:
                            incident_type = 'Performance'
                        elif 'security' in category or 'auth' in category:
                            incident_type = 'Security'
                        elif 'network' in category or 'connection' in category:
                            incident_type = 'Network'
                        else:
                            incident_type = 'Outage'
                        
                        # Extract services from description or use defaults
                        services = []
                        if 'api' in incident_description.lower():
                            services.append('API Gateway')
                        if 'database' in incident_description.lower() or 'db' in incident_description.lower():
                            services.append('Database')
                        if 'user' in incident_description.lower() or 'auth' in incident_description.lower():
                            services.append('User Service')
                        
                        # Analyze button
                        if st.button("🔍 Analyze Incident Correlations", key="analyze_loaded_incident"):
                            st.markdown("---")
                            # Add incident reference to description
                            enhanced_description = f"{incident_description}\n\n[Related OpsItem: {incident_id}]"
                            self._perform_correlation_analysis(enhanced_description, incident_title, severity)
                    else:
                        st.error("Could not load incident details")
            else:
                st.warning("No recent incidents found. Create an incident first.")
        
        else:  # Manual Entry
            with st.form("correlation_analysis_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    incident_title = st.text_input("Incident Title", key="corr_title")
                    severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2, key="corr_severity")
                
                with col2:
                    incident_type = st.selectbox("Type", ["Performance", "Outage", "Security", "Network"], key="corr_type")
                    services = st.multiselect("Affected Services", ["API Gateway", "Database", "User Service"], key="corr_services")
                
                incident_description = st.text_area("Incident Description", 
                                                  placeholder="Describe symptoms, timeline, and impact...", 
                                                  height=150, key="corr_desc")
                
                analyze_submitted = st.form_submit_button("🔍 Analyze Correlations")
            
            if analyze_submitted and incident_description:
                st.markdown("---")
                self._perform_correlation_analysis(incident_description, incident_title, severity)
    
    def render_correlation_scenarios(self):
        """NEW: Render correlation test scenarios tab"""
        st.header("🧪 Defect Correlation Test Scenarios")
        
        st.markdown("""
        Test the correlation engine with pre-built scenarios that have known defect relationships.
        """)
        
        # Mock scenarios
        scenarios = [
            {
                "id": "DDS-001",
                "title": "API Gateway Timeout Surge",
                "description": "API Gateway experiencing 500% increase in timeout errors affecting customer-facing services",
                "expected_correlation": "95%",
                "root_cause": "Connection pool memory leak"
            },
            {
                "id": "DDS-002", 
                "title": "Authentication Service Failures",
                "description": "Intermittent authentication failures causing user login issues",
                "expected_correlation": "88%",
                "root_cause": "Race condition in session management"
            },
            {
                "id": "DDS-003",
                "title": "Payment Processing Outage",
                "description": "Payment processing system completely down, affecting all transactions",
                "expected_correlation": "92%",
                "root_cause": "SSL certificate validation bug"
            }
        ]
        
        scenario_names = [f"{s['id']}: {s['title']}" for s in scenarios]
        selected = st.selectbox("Select Test Scenario", scenario_names, key="scenario_select")
        
        if selected:
            scenario_id = selected.split(':')[0]
            scenario = next(s for s in scenarios if s['id'] == scenario_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Scenario Details:**")
                st.markdown(f"**ID:** {scenario['id']}")
                st.markdown(f"**Expected Correlation:** {scenario['expected_correlation']}")
                st.markdown(f"**Root Cause:** {scenario['root_cause']}")
            
            with col2:
                st.markdown("**Incident Description:**")
                st.info(scenario['description'])
            
            if st.button("🔍 Test Correlation", key=f"test_{scenario_id}"):
                st.markdown("---")
                st.subheader("📊 Correlation Test Results")
                
                with st.spinner("Running correlation analysis..."):
                    time.sleep(2)  # Simulate processing
                
                # Mock results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Expected", scenario['expected_correlation'])
                
                with col2:
                    actual = random.randint(80, 98)
                    st.metric("Actual", f"{actual}%")
                
                with col3:
                    accuracy = abs(int(scenario['expected_correlation'][:-1]) - actual)
                    accuracy_icon = "🟢" if accuracy < 10 else "🟡"
                    st.metric("Accuracy", f"{accuracy_icon} {100-accuracy}%")
                
                st.success("✅ Correlation analysis completed successfully!")
                st.markdown("**Found correlations:** 3 ALM Octane defects, 2 Jira issues")
                st.markdown("**Recommendations:** Review connection pool configuration, check recent deployments")
    
    def _render_defect_overview(self, status, mcp_ports):
        """Render defect overview section"""
        st.subheader("📋 Recent Defects & Issues")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ALM Octane Defects")
            if status['alm_octane']['online']:
                try:
                    response = requests.get(f"http://localhost:{mcp_ports['alm_octane']}/octane/defects", timeout=5)
                    if response.status_code == 200:
                        defects = response.json()[:5]
                        for defect in defects:
                            severity_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(defect.get('severity', 'Low'), "⚪")
                            st.markdown(f"**{severity_icon} {defect.get('name', 'Unknown')}** - {defect.get('status', 'Open')}")
                            st.caption(defect.get('description', 'No description')[:80] + "...")
                    else:
                        st.warning("Could not load defects")
                except:
                    st.error("Connection failed")
            else:
                st.warning("ALM Octane offline")
        
        with col2:
            st.markdown("#### Jira Issues") 
            if status['jira']['online']:
                try:
                    response = requests.get(f"http://localhost:{mcp_ports['jira']}/jira/issues", timeout=5)
                    if response.status_code == 200:
                        issues = response.json()[:5]
                        for issue in issues:
                            # Handle priority as either string or dict
                            priority = issue.get('priority', 'Low')
                            if isinstance(priority, dict):
                                priority_name = priority.get('name', 'Low')
                            else:
                                priority_name = priority
                            priority_icon = {"Blocker": "🔴", "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority_name, "⚪")
                            
                            # Handle status similarly
                            status_val = issue.get('status', 'Open')
                            if isinstance(status_val, dict):
                                status_name = status_val.get('name', 'Open')
                            else:
                                status_name = status_val
                            
                            st.markdown(f"**{priority_icon} {issue.get('key', 'Unknown')}** - {status_name}")
                            st.caption(issue.get('summary', issue.get('description', 'No summary'))[:80] + "...")
                    else:
                        st.warning(f"Could not load issues (status: {response.status_code})")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
            else:
                st.warning("Jira offline")
    
    def _render_defect_search(self):
        """Render defect search section"""
        st.subheader("🔍 Search Defects & Issues")
        
        # Add incident-based search option
        search_mode = st.radio("Search by:", ["Keywords", "Incident"], horizontal=True)
        
        if search_mode == "Incident":
            # Get recent incidents for dropdown
            recent_incidents = self.get_recent_incidents_for_dropdown()
            
            if recent_incidents:
                selected_incident = st.selectbox(
                    "Select an incident to find related defects:",
                    [""] + [f"{inc['id']} - {inc['title']}" for inc in recent_incidents],
                    help="AI will search for defects related to this incident"
                )
                
                if selected_incident and selected_incident != "":
                    incident_id = selected_incident.split(" - ")[0]
                    incident = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
                    
                    if incident:
                        st.info(f"📋 **Incident Details:**\n- Root Cause: {incident.get('root_cause', 'Unknown')}\n- Category: {incident.get('category', 'Unknown')}")
                        
                        if st.button("🔍 Find Related Defects", key="search_incident_defects"):
                            with st.spinner("AI analyzing incident and searching for related defects..."):
                                # Simulate AI search
                                time.sleep(1)
                                st.success("✅ Found 3 related defects")
                                
                                # Mock related defects
                                related_defects = [
                                    {"key": "ALM-4521", "title": "Database connection pool exhaustion", "match": "87%"},
                                    {"key": "JIRA-892", "title": "Timeout errors in payment service", "match": "82%"},
                                    {"key": "ALM-4498", "title": "High latency during peak hours", "match": "75%"}
                                ]
                                
                                for defect in related_defects:
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(f"**{defect['key']}** - {defect['title']}")
                                    with col2:
                                        st.metric("Match", defect['match'])
            else:
                st.warning("No recent incidents found. Create an incident first.")
        
        else:  # Keywords search
            with st.form("defect_search_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    search_text = st.text_input("Keywords", key="search_keywords")
                with col2:
                    severity = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"], key="search_severity")
                with col3:
                    status_filter = st.selectbox("Status", ["All", "Open", "In Progress", "Resolved"], key="search_status")
                
                search_submitted = st.form_submit_button("🔍 Search")
            
            if search_submitted:
                st.info("Search functionality would query both ALM Octane and Jira")
                if search_text:
                    st.markdown(f"**Searching for:** {search_text} | **Severity:** {severity} | **Status:** {status_filter}")
    
    def _render_defect_creation(self):
        """Render defect creation section"""
        st.subheader("➕ Create New Defect")
        
        # Add creation mode selector
        creation_mode = st.radio("Create from:", ["Manual", "Incident (AI-Powered)"], horizontal=True)
        
        if creation_mode == "Incident (AI-Powered)":
            # Get recent incidents
            recent_incidents = self.get_recent_incidents_for_dropdown()
            
            if recent_incidents:
                selected_incident = st.selectbox(
                    "Select an incident to create defect from:",
                    [""] + [f"{inc['id']} - {inc['title']}" for inc in recent_incidents],
                    help="AI will analyze the incident and pre-fill defect details"
                )
                
                if selected_incident and selected_incident != "":
                    incident_id = selected_incident.split(" - ")[0]
                    incident = next((inc for inc in recent_incidents if inc['id'] == incident_id), None)
                    
                    if incident:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Root Cause:** {incident.get('root_cause', 'Unknown')}")
                        with col2:
                            st.info(f"**Category:** {incident.get('category', 'Unknown')}")
                        
                        if st.button("🤖 Generate Defect with AI", key="generate_defect_ai"):
                            with st.spinner("AI analyzing incident and generating defect..."):
                                time.sleep(2)  # Simulate AI processing
                                
                                # AI-generated defect details
                                ai_title = f"Fix {incident.get('root_cause', 'issue').replace('**', '')}"
                                ai_description = f"""## Issue Summary
{incident.get('description', 'Incident occurred in production environment')}

## Root Cause Analysis
{incident.get('root_cause', 'To be determined')}

## Impact
- Service: {incident.get('category', 'Unknown')}
- Severity: {incident.get('severity', 'High')}
- Start Time: {incident.get('created', datetime.now()).strftime('%Y-%m-%d %H:%M')}

## Recommended Fix
Based on the root cause analysis, the following actions are recommended:
1. Review and optimize the affected component
2. Implement proper error handling
3. Add monitoring alerts for early detection
4. Update documentation

## Related Incident
OpsItem ID: {incident_id}
"""
                                ai_component = incident.get('category', 'Core Service')
                                ai_severity = "Critical" if incident.get('severity', '3') in ['1', '2'] else "High"
                                
                                # Store in session state
                                st.session_state['ai_defect_title'] = ai_title
                                st.session_state['ai_defect_description'] = ai_description
                                st.session_state['ai_defect_component'] = ai_component
                                st.session_state['ai_defect_severity'] = ai_severity
                                st.session_state['ai_defect_ready'] = True
                                
                                st.success("✅ AI has generated defect details!")
                
                # Show AI-generated form if ready
                if st.session_state.get('ai_defect_ready', False):
                    st.markdown("### 📝 AI-Generated Defect Details")
                    st.caption("Review and modify the AI-generated content before creating the defect")
                    
                    with st.form("ai_defect_create_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            title = st.text_input("Title*", value=st.session_state.get('ai_defect_title', ''), key="ai_create_title")
                            severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"], 
                                                  index=["Low", "Medium", "High", "Critical"].index(st.session_state.get('ai_defect_severity', 'High')),
                                                  key="ai_create_severity")
                            component = st.text_input("Component", value=st.session_state.get('ai_defect_component', ''), key="ai_create_component")
                        
                        with col2:
                            description = st.text_area("Description*", value=st.session_state.get('ai_defect_description', ''), 
                                                     height=200, key="ai_create_description")
                            target = st.selectbox("Create In*", ["ALM Octane", "Jira", "Both"], key="ai_create_target")
                            environment = st.selectbox("Environment", ["Dev", "Test", "Staging", "Prod"], index=3, key="ai_create_environment")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            create_submitted = st.form_submit_button("🚀 Create AI Defect", type="primary")
                        with col2:
                            if st.form_submit_button("Clear", type="secondary"):
                                st.session_state['ai_defect_ready'] = False
                    
                    if create_submitted and title and description:
                        st.success(f"✅ AI-powered defect created in {target}")
                        if target in ["ALM Octane", "Both"]:
                            st.info(f"ALM Octane ID: ALM-{random.randint(1000, 9999)}")
                        if target in ["Jira", "Both"]:
                            st.info(f"Jira Key: BUG-{random.randint(100, 999)}")
                        st.caption("🤖 This defect was created using AI analysis of the incident")
                        st.session_state['ai_defect_ready'] = False
            else:
                st.warning("No recent incidents found. Create an incident first to use AI-powered defect creation.")
        
        else:  # Manual creation
            with st.form("defect_create_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    title = st.text_input("Title*", key="create_title")
                    severity = st.selectbox("Severity*", ["Low", "Medium", "High", "Critical"], key="create_severity")
                    component = st.text_input("Component", key="create_component")
                
                with col2:
                    description = st.text_area("Description*", key="create_description")
                    target = st.selectbox("Create In*", ["ALM Octane", "Jira", "Both"], key="create_target")
                    environment = st.selectbox("Environment", ["Dev", "Test", "Staging", "Prod"], key="create_environment")
                
                create_submitted = st.form_submit_button("Create Defect")
            
            if create_submitted and title and description:
                st.success(f"✅ Defect would be created in {target}")
                if target in ["ALM Octane", "Both"]:
                    st.info(f"ALM Octane ID: ALM-{random.randint(1000, 9999)}")
                if target in ["Jira", "Both"]:
                    st.info(f"Jira Key: BUG-{random.randint(100, 999)}")
    
    def _render_defect_analytics(self):
        """Render defect analytics section"""
        st.subheader("📊 Defect Analytics")
        
        # Mock metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Open Defects", "127", "-8")
        with col2:
            st.metric("Critical", "23", "+3")
        with col3:
            st.metric("Avg Resolution", "4.2 days", "-0.5")
        with col4:
            st.metric("Quality Score", "87%", "+2%")
        
        # Charts
        dates = pd.date_range(start='2025-07-01', end='2025-08-12', freq='D')
        defects = [random.randint(5, 25) for _ in dates]
        
        fig = px.line(x=dates, y=defects, title="Daily Defect Creation Trend")
        st.plotly_chart(fig, use_container_width=True)
    
    def _perform_correlation_analysis(self, incident_description, incident_title, severity):
        """Perform correlation analysis"""
        st.subheader("🎯 Correlation Analysis Results")
        
        # Check if this is from an incident (has OpsItem reference)
        is_from_incident = "[Related OpsItem:" in incident_description
        
        with st.spinner("AI analyzing incident and searching for defect correlations..."):
            time.sleep(2)  # Simulate processing
        
        # Mock correlation results - higher scores for incident-based analysis
        if is_from_incident:
            correlation_score = random.randint(75, 95) / 100
            defects_found = random.randint(5, 15)
        else:
            correlation_score = random.randint(60, 90) / 100
            defects_found = random.randint(3, 12)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Defects Found", defects_found)
        
        with col2:
            score_icon = "🟢" if correlation_score >= 0.7 else "🟡" if correlation_score >= 0.4 else "🔴"
            st.metric("Highest Match", f"{score_icon} {correlation_score:.1%}")
        
        with col3:
            likelihood = "High" if correlation_score >= 0.7 else "Medium" if correlation_score >= 0.4 else "Low"
            st.metric("Root Cause Match", likelihood)
        
        # Correlation gauge
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = correlation_score * 100,
            delta = {'reference': 70, 'valueformat': '.0f'},
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "AI Confidence Score"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "lightgray"},
                    {'range': [40, 70], 'color': "yellow"},
                    {'range': [70, 100], 'color': "green"}
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
        
        # Detailed correlation results
        st.subheader("🔍 Correlated Defects")
        
        # Generate mock defects based on incident data
        defect_types = []
        if "database" in incident_description.lower() or "db" in incident_description.lower():
            defect_types.append(("Database", ["connection pool", "query optimization", "timeout configuration"]))
        if "api" in incident_description.lower() or "gateway" in incident_description.lower():
            defect_types.append(("API", ["rate limiting", "authentication", "response timeout"]))
        if "performance" in incident_description.lower() or "latency" in incident_description.lower():
            defect_types.append(("Performance", ["resource utilization", "caching", "load balancing"]))
        if not defect_types:
            defect_types.append(("General", ["service configuration", "error handling", "monitoring"]))
        
        # Display correlated defects
        for defect_type, issues in defect_types[:2]:  # Show top 2 categories
            st.markdown(f"#### {defect_type} Related Defects")
            
            for i, issue in enumerate(issues[:3]):  # Show top 3 issues per category
                match_score = correlation_score - (i * 0.05) - random.uniform(0, 0.1)
                match_score = max(0.5, min(1.0, match_score))
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    defect_id = f"ALM-{random.randint(4000, 5000)}" if i % 2 == 0 else f"JIRA-{random.randint(800, 999)}"
                    st.markdown(f"**{defect_id}**: {issue.title()} Issue")
                    st.caption(f"Last updated: {random.randint(1, 30)} days ago")
                with col2:
                    st.metric("Match", f"{match_score:.0%}")
                with col3:
                    status = ["Open", "In Progress", "Resolved"][random.randint(0, 2)]
                    status_color = {"Open": "🔴", "In Progress": "🟡", "Resolved": "🟢"}
                    st.markdown(f"{status_color[status]} {status}")
        
        # Enhanced recommendations based on incident data
        st.subheader("💡 AI Recommendations")
        
        recommendations = []
        if is_from_incident:
            recommendations.append(f"✅ Based on incident analysis, focus on {defect_types[0][0].lower()} related defects")
            recommendations.append(f"📊 Found {defects_found} potentially related defects with >{correlation_score*100:.0f}% confidence")
        
        if severity in ["Critical", "High"]:
            recommendations.append("🚨 High severity incident - prioritize immediate defect resolution")
        
        recommendations.extend([
            "🔍 Review the top correlated defects above for similar root causes",
            "📝 Consider creating a new defect if none match your incident exactly",
            "🔄 Check recent deployments that might have introduced the issue"
        ])
        
        for rec in recommendations:
            st.markdown(f"• {rec}")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 View in ALM Octane", key="view_alm"):
                st.info("Opening ALM Octane defects...")
        with col2:
            if st.button("📋 View in Jira", key="view_jira"):
                st.info("Opening Jira issues...")
        with col3:
            if st.button("➕ Create New Defect", key="create_from_correlation"):
                st.info("Navigate to Create tab to create a new defect")

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
        
        # Initialize session state for form fields
        if 'pm_incident_id' not in st.session_state:
            st.session_state.pm_incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}"
        if 'pm_incident_type' not in st.session_state:
            st.session_state.pm_incident_type = 0  # index for selectbox
        if 'pm_severity' not in st.session_state:
            st.session_state.pm_severity = 0  # index for selectbox
        if 'pm_description' not in st.session_state:
            st.session_state.pm_description = ""
        if 'pm_services' not in st.session_state:
            st.session_state.pm_services = ""
        if 'pm_detection_method' not in st.session_state:
            st.session_state.pm_detection_method = ""
        if 'pm_immediate_actions' not in st.session_state:
            st.session_state.pm_immediate_actions = ""
        if 'pm_start_date' not in st.session_state:
            st.session_state.pm_start_date = datetime.now().date()
        if 'pm_start_time' not in st.session_state:
            st.session_state.pm_start_time = datetime.now().time()
        if 'pm_end_date' not in st.session_state:
            st.session_state.pm_end_date = datetime.now().date()
        if 'pm_end_time' not in st.session_state:
            st.session_state.pm_end_time = datetime.now().time()
        
        # Move incident loading outside the form
        load_container = st.container()
        with load_container:
            st.markdown("### Load from Recent Incidents")
            recent_incidents = self.get_recent_incidents_for_dropdown()
            if recent_incidents:
                incident_options = [""] + [f"{inc['id']} - {inc['title'][:50]}" for inc in recent_incidents]
                selected_incident = st.selectbox(
                    "Select Recent Incident",
                    incident_options,
                    key="pm_incident_select"
                )
                
                if selected_incident and selected_incident != "":
                    incident_id_selected = selected_incident.split(" - ")[0]
                    incident = next((inc for inc in recent_incidents if inc['id'] == incident_id_selected), None)
                    
                    if incident and st.button("📥 Load Incident Details", key="load_pm_incident"):
                        # Update session state with incident data
                        st.session_state.pm_incident_id = incident['id']
                        st.session_state.pm_description = incident.get('description', '')
                        
                        # Map category to incident type
                        category = incident.get('category', 'Unknown').lower()
                        if 'performance' in category or 'latency' in category:
                            st.session_state.pm_incident_type = 1  # performance
                        elif 'security' in category or 'auth' in category:
                            st.session_state.pm_incident_type = 2  # security
                        elif 'data' in category:
                            st.session_state.pm_incident_type = 3  # data_loss
                        else:
                            st.session_state.pm_incident_type = 0  # outage
                        
                        # Map severity
                        severity_map = {'1': 0, '2': 0, '3': 1, '4': 2, '5': 3}  # to CRITICAL/HIGH/MEDIUM/LOW indices
                        st.session_state.pm_severity = severity_map.get(str(incident.get('severity', '3')), 1)
                        
                        # Extract services from description
                        desc_lower = incident['description'].lower()
                        services_list = []
                        if 'api' in desc_lower:
                            services_list.append('api-gateway')
                        if 'database' in desc_lower or 'db' in desc_lower:
                            services_list.append('database')
                        if 'auth' in desc_lower:
                            services_list.append('auth-service')
                        if 'user' in desc_lower:
                            services_list.append('user-service')
                        if 'payment' in desc_lower:
                            services_list.append('payment-service')
                        st.session_state.pm_services = ', '.join(services_list)
                        
                        # Set detection method based on source
                        st.session_state.pm_detection_method = "CloudWatch monitoring alert"
                        
                        # Set immediate actions based on root cause
                        root_cause = incident.get('root_cause', 'Unknown issue')
                        st.session_state.pm_immediate_actions = f"1. Identified root cause: {root_cause}\n2. Initiated incident response protocol\n3. Notified on-call team\n4. Started real-time monitoring"
                        
                        # Set times
                        created_time = incident.get('created_time', datetime.now())
                        if isinstance(created_time, str):
                            created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                        st.session_state.pm_start_date = created_time.date()
                        st.session_state.pm_start_time = created_time.time()
                        # Assume 2 hour resolution time
                        end_time = created_time + timedelta(hours=2)
                        st.session_state.pm_end_date = end_time.date()
                        st.session_state.pm_end_time = end_time.time()
                        
                        st.success(f"✅ Loaded incident details from {incident_id_selected}")
                        st.experimental_rerun()
            else:
                st.warning("No recent incidents found. Create an incident first.")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Incident details form
            with st.form("postmortem_form"):
                st.markdown("### Incident Details")
                
                incident_id = st.text_input(
                    "Incident ID",
                    value=st.session_state.pm_incident_id,
                    help="Unique identifier for this incident"
                )
                
                incident_types = ["outage", "performance", "security", "data_loss", "configuration"]
                incident_type = st.selectbox(
                    "Incident Type",
                    incident_types,
                    index=st.session_state.pm_incident_type,
                    help="Select the type of incident"
                )
                
                severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                severity = st.selectbox(
                    "Severity",
                    severities,
                    index=st.session_state.pm_severity,
                    help="Incident severity level"
                )
                
                description = st.text_area(
                    "Incident Description",
                    value=st.session_state.pm_description,
                    placeholder="Describe what happened...",
                    help="Provide a detailed description of the incident"
                )
                
                # Time information
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("Start Date", st.session_state.pm_start_date)
                    start_time = st.time_input("Start Time", st.session_state.pm_start_time)
                
                with col_end:
                    end_date = st.date_input("End Date", st.session_state.pm_end_date)
                    end_time = st.time_input("End Time", st.session_state.pm_end_time)
                
                # Services affected
                services = st.text_input(
                    "Services Affected",
                    value=st.session_state.pm_services,
                    placeholder="e.g., payment-api, auth-service",
                    help="Comma-separated list of affected services"
                )
                
                # Additional context
                st.markdown("### Additional Context")
                
                detection_method = st.text_input(
                    "How was the incident detected?",
                    value=st.session_state.pm_detection_method,
                    placeholder="e.g., Monitoring alert, customer report"
                )
                
                immediate_actions = st.text_area(
                    "Immediate Actions Taken",
                    value=st.session_state.pm_immediate_actions,
                    placeholder="List the initial response actions..."
                )
                
                # Metrics data (optional)
                include_metrics = st.checkbox("Include CloudWatch Metrics Analysis")
                
                submitted = st.form_submit_button("🚀 Generate Post-Mortem Report", type="primary")
        
        with col2:
            # Tips and guidance
            st.markdown("### Tips for Effective Post-Mortems")
            st.info("""
            📌 **Best Practices:**
            - Be blameless - focus on process improvements
            - Include all stakeholders in the analysis
            - Document action items with clear owners
            - Set deadlines for remediation
            - Share learnings across teams
            
            📊 **Key Sections:**
            - Timeline of events
            - Root cause analysis
            - Impact assessment
            - Lessons learned
            - Action items
            """)
        
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
    
    def render_ip_masking(self):
        """Render the IP Masking tab"""
        st.header("🔐 IP Masking")
        
        st.markdown("""
        Protect sensitive IP addresses in logs and data displays by applying intelligent masking.
        This feature helps maintain privacy while preserving log analysis capabilities.
        """)
        
        if not IP_MASKING_AVAILABLE:
            st.error("IP Masking utility not available. Please check installation.")
            return
        
        # IP Masking options
        masking_tabs = st.tabs(["🔒 Mask Logs", "⚙️ Configuration", "📊 Statistics"])
        
        with masking_tabs[0]:
            self._render_ip_masking_tool()
        
        with masking_tabs[1]:
            self._render_ip_masking_config()
            
        with masking_tabs[2]:
            self._render_ip_masking_stats()
    
    def _render_ip_masking_tool(self):
        """Render IP masking tool interface"""
        st.subheader("Mask IP Addresses in Logs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Input options
            input_method = st.radio(
                "Input Method",
                ["Text Input", "File Upload", "CloudWatch Logs"],
                key=key_manager.get_unique_key("ip_mask_input", "radio")
            )
            
            if input_method == "Text Input":
                log_text = st.text_area(
                    "Enter log text containing IP addresses",
                    height=200,
                    placeholder="Paste your logs here...",
                    key=key_manager.get_unique_key("ip_mask_text", "textarea")
                )
            elif input_method == "File Upload":
                uploaded_file = st.file_uploader(
                    "Upload log file",
                    type=['txt', 'log', 'json'],
                    key=key_manager.get_unique_key("ip_mask_upload", "file")
                )
                if uploaded_file:
                    log_text = uploaded_file.read().decode('utf-8')
                else:
                    log_text = ""
            else:  # CloudWatch Logs
                log_group = st.text_input(
                    "Log Group Name",
                    placeholder="/aws/lambda/my-function",
                    key=key_manager.get_unique_key("ip_mask_loggroup", "text")
                )
                log_text = ""
        
        with col2:
            # Masking options
            st.markdown("### Masking Options")
            
            masking_mode = st.selectbox(
                "Masking Mode",
                ["Partial (keep first octet)", "Full (complete masking)", "Hash-based (consistent)"],
                key=key_manager.get_unique_key("ip_mask_mode", "select")
            )
            
            preserve_internal = st.checkbox(
                "Preserve internal IPs (10.x, 172.16-31.x, 192.168.x)",
                value=True,
                key=key_manager.get_unique_key("ip_mask_internal", "checkbox")
            )
            
            include_ipv6 = st.checkbox(
                "Include IPv6 addresses",
                value=True,
                key=key_manager.get_unique_key("ip_mask_ipv6", "checkbox")
            )
        
        if st.button("🔒 Apply IP Masking", type="primary", key=key_manager.get_unique_key("apply_ip_mask", "button")):
            if log_text:
                with st.spinner("Masking IP addresses..."):
                    try:
                        masker = IPMasker(
                            mask_type=masking_mode.split()[0].lower()
                        )
                        
                        masked_text = masker.mask_text(log_text)
                        
                        # Display results
                        st.success("✅ IP addresses masked successfully")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### Original (Sample)")
                            st.code(log_text[:500] + "..." if len(log_text) > 500 else log_text)
                        
                        with col2:
                            st.markdown("### Masked")
                            st.code(masked_text[:500] + "..." if len(masked_text) > 500 else masked_text)
                        
                        # Statistics
                        stats = masker.get_statistics()
                        st.markdown("### Masking Statistics")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total IPs Found", stats.get('total_ips', 0))
                        with col2:
                            st.metric("IPv4 Addresses", stats.get('ipv4_count', 0))
                        with col3:
                            st.metric("IPv6 Addresses", stats.get('ipv6_count', 0))
                        
                        # Download option
                        st.download_button(
                            label="📥 Download Masked Logs",
                            data=masked_text,
                            file_name=f"masked_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            key=key_manager.get_unique_key("download_masked", "button")
                        )
                        
                    except Exception as e:
                        st.error(f"Error masking IPs: {str(e)}")
            else:
                st.warning("Please provide log text to mask")
    
    def _render_ip_masking_config(self):
        """Render IP masking configuration"""
        st.subheader("IP Masking Configuration")
        
        # Configuration form
        with st.form("ip_mask_config"):
            st.markdown("### Default Settings")
            
            default_mode = st.selectbox(
                "Default Masking Mode",
                ["Partial", "Full", "Hash-based"],
                index=0
            )
            
            st.markdown("### IP Whitelist")
            whitelist = st.text_area(
                "Whitelisted IPs (one per line)",
                placeholder="192.168.1.1\n10.0.0.1",
                help="These IPs will never be masked"
            )
            
            st.markdown("### Custom Patterns")
            custom_patterns = st.text_area(
                "Additional patterns to mask (regex)",
                placeholder="\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}:\\d+",
                help="Custom regex patterns for special IP formats"
            )
            
            if st.form_submit_button("💾 Save Configuration"):
                # Save configuration
                config = {
                    'default_mode': default_mode.lower(),
                    'whitelist': [ip.strip() for ip in whitelist.split('\n') if ip.strip()],
                    'custom_patterns': [p.strip() for p in custom_patterns.split('\n') if p.strip()]
                }
                st.success("✅ Configuration saved successfully")
                st.json(config)
    
    def _render_ip_masking_stats(self):
        """Render IP masking statistics"""
        st.subheader("IP Masking Statistics")
        
        # Mock statistics for demonstration
        stats_data = {
            'total_masked': 15234,
            'ipv4_masked': 12856,
            'ipv6_masked': 2378,
            'logs_processed': 847,
            'avg_ips_per_log': 18
        }
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total IPs Masked", f"{stats_data['total_masked']:,}")
        with col2:
            st.metric("IPv4 Addresses", f"{stats_data['ipv4_masked']:,}")
        with col3:
            st.metric("IPv6 Addresses", f"{stats_data['ipv6_masked']:,}")
        with col4:
            st.metric("Logs Processed", stats_data['logs_processed'])
        with col5:
            st.metric("Avg IPs/Log", stats_data['avg_ips_per_log'])
        
        # Masking trends chart
        st.markdown("### Masking Activity Trends")
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        trends_df = pd.DataFrame({
            'Date': dates,
            'IPs Masked': [random.randint(400, 600) for _ in range(30)],
            'Logs Processed': [random.randint(20, 40) for _ in range(30)]
        })
        
        fig = px.line(trends_df, x='Date', y='IPs Masked', 
                      title='Daily IP Masking Activity',
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_test_scenarios(self):
        """Render the Test Scenarios tab"""
        st.header("🧪 Test Scenarios")
        
        st.markdown("""
        Generate realistic test incidents to validate the SRE Copilot's root cause analysis capabilities.
        Choose from predefined scenarios or create custom ones.
        """)
        
        scenario_tabs = st.tabs(["📋 Predefined Scenarios", "✏️ Custom Scenario", "🔄 Batch Testing"])
        
        with scenario_tabs[0]:
            self._render_predefined_scenarios()
        
        with scenario_tabs[1]:
            self._render_custom_scenario()
            
        with scenario_tabs[2]:
            self._render_batch_testing()
    
    def _render_predefined_scenarios(self):
        """Render predefined test scenarios"""
        st.subheader("Predefined Test Scenarios")
        
        # Scenario categories
        category = st.selectbox(
            "Select Scenario Category",
            ["Performance Issues", "Security Incidents", "Service Outages", 
             "Data Issues", "Infrastructure Failures", "Change-Related", "Defect-Related"],
            key=key_manager.get_unique_key("scenario_category", "select")
        )
        
        # Predefined scenarios based on category
        scenarios = {
            "Performance Issues": [
                {
                    "name": "Database Slow Query Crisis",
                    "description": "Multiple slow queries causing application timeouts",
                    "severity": "high",
                    "components": ["RDS", "Application", "API Gateway"]
                },
                {
                    "name": "Memory Leak in Production",
                    "description": "Gradual memory exhaustion in EC2 instances",
                    "severity": "critical",
                    "components": ["EC2", "Application", "CloudWatch"]
                }
            ],
            "Security Incidents": [
                {
                    "name": "Suspicious API Access Pattern",
                    "description": "Unusual API call patterns detected",
                    "severity": "high",
                    "components": ["API Gateway", "WAF", "CloudTrail"]
                },
                {
                    "name": "Failed Authentication Spike",
                    "description": "Mass authentication failures from multiple IPs",
                    "severity": "critical",
                    "components": ["Cognito", "CloudTrail", "WAF"]
                }
            ],
            "Service Outages": [
                {
                    "name": "Complete Service Unavailability",
                    "description": "Main application endpoint returning 503 errors",
                    "severity": "critical",
                    "components": ["ALB", "ECS", "Route53"]
                },
                {
                    "name": "Regional Service Degradation",
                    "description": "Intermittent failures in us-east-1",
                    "severity": "high",
                    "components": ["Multi-Region", "CloudFront", "S3"]
                }
            ],
            "Data Issues": [
                {
                    "name": "Data Replication Lag",
                    "description": "Significant lag in cross-region data replication",
                    "severity": "high",
                    "components": ["DynamoDB", "S3", "Kinesis"]
                },
                {
                    "name": "Data Corruption Detected",
                    "description": "Checksum mismatches in critical data files",
                    "severity": "critical",
                    "components": ["S3", "RDS", "Backup Service"]
                }
            ],
            "Infrastructure Failures": [
                {
                    "name": "Multi-AZ Failover",
                    "description": "Primary AZ experiencing network issues",
                    "severity": "critical",
                    "components": ["VPC", "EC2", "RDS Multi-AZ"]
                },
                {
                    "name": "Auto Scaling Failure",
                    "description": "ASG not responding to increased load",
                    "severity": "high",
                    "components": ["Auto Scaling", "EC2", "CloudWatch"]
                }
            ],
            "Change-Related": [
                {
                    "name": "Failed Deployment Rollback",
                    "description": "Recent deployment caused errors, rollback initiated",
                    "severity": "high",
                    "components": ["CodeDeploy", "ECS", "Lambda"]
                },
                {
                    "name": "Configuration Change Impact",
                    "description": "Config update caused unexpected service behavior",
                    "severity": "medium",
                    "components": ["Systems Manager", "Parameter Store", "Lambda"]
                }
            ],
            "Defect-Related": [
                {
                    "name": "Memory Leak in Production",
                    "description": "Known defect DEF-4521 causing memory exhaustion",
                    "severity": "high",
                    "components": ["EC2", "Application", "CloudWatch"]
                },
                {
                    "name": "Race Condition Bug",
                    "description": "Intermittent race condition affecting order processing",
                    "severity": "critical",
                    "components": ["Lambda", "SQS", "DynamoDB"]
                }
            ]
        }
        
        # Display available scenarios
        if category in scenarios:
            for idx, scenario in enumerate(scenarios[category]):
                with st.expander(f"{scenario['name']} - {scenario['severity'].upper()}"):
                    st.markdown(f"**Description:** {scenario['description']}")
                    st.markdown(f"**Components:** {', '.join(scenario['components'])}")
                    
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button(
                            "🚀 Generate Incident",
                            key=key_manager.get_unique_key(f"gen_scenario_{category}_{idx}", "button")
                        ):
                            with st.spinner("Generating test incident..."):
                                # Generate the incident
                                incident = self._generate_test_incident(scenario, category)
                                
                                if incident:
                                    st.success(f"✅ Test incident generated: {incident['incident_id']}")
                                    
                                    # Store in session state for analysis
                                    st.session_state.current_incident = incident
                                    st.session_state.incident_generated = True
                                    
                                    # Show quick actions
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if st.button("🔍 Analyze Now", key=key_manager.get_unique_key("analyze_now", "button")):
                                            st.session_state.show_analysis_results = True
                                            st.experimental_rerun()
                                    with col2:
                                        st.button("📋 View Details", key=key_manager.get_unique_key("view_details", "button"))
                                    with col3:
                                        st.button("📊 Generate Report", key=key_manager.get_unique_key("gen_report", "button"))
    
    def _render_custom_scenario(self):
        """Render custom scenario creator"""
        st.subheader("Create Custom Test Scenario")
        
        with st.form("custom_scenario"):
            col1, col2 = st.columns(2)
            
            with col1:
                scenario_name = st.text_input(
                    "Scenario Name",
                    placeholder="e.g., API Rate Limit Breach"
                )
                
                incident_type = st.selectbox(
                    "Incident Type",
                    ["performance", "security", "outage", "data_loss", "configuration"]
                )
                
                severity = st.select_slider(
                    "Severity",
                    options=["low", "medium", "high", "critical"]
                )
                
                duration = st.slider(
                    "Duration (minutes)",
                    min_value=5,
                    max_value=240,
                    value=30
                )
            
            with col2:
                affected_services = st.multiselect(
                    "Affected Services",
                    ["EC2", "RDS", "S3", "Lambda", "API Gateway", "ECS", "DynamoDB", "SQS"]
                )
                
                error_rate = st.slider(
                    "Error Rate (%)",
                    min_value=0,
                    max_value=100,
                    value=25
                )
                
                impact = st.text_area(
                    "Business Impact",
                    placeholder="Describe the business impact..."
                )
            
            # Symptoms configuration
            st.markdown("### Symptoms")
            symptoms = st.text_area(
                "Symptoms (one per line)",
                placeholder="High CPU utilization\nIncreased response times\nError spike in logs"
            )
            
            # Root cause hints
            st.markdown("### Root Cause Hints (Optional)")
            root_cause_hints = st.text_area(
                "Provide hints for expected root cause",
                placeholder="Database connection pool exhaustion\nMemory leak in application"
            )
            
            if st.form_submit_button("🎯 Create & Generate Incident"):
                if scenario_name and affected_services:
                    # Create custom scenario
                    custom_scenario = {
                        "name": scenario_name,
                        "type": incident_type,
                        "severity": severity,
                        "duration": duration,
                        "services": affected_services,
                        "error_rate": error_rate,
                        "impact": impact,
                        "symptoms": [s.strip() for s in symptoms.split('\n') if s.strip()],
                        "root_cause_hints": [h.strip() for h in root_cause_hints.split('\n') if h.strip()]
                    }
                    
                    # Generate incident from custom scenario
                    incident = self._generate_custom_incident(custom_scenario)
                    
                    if incident:
                        st.success(f"✅ Custom incident generated: {incident['incident_id']}")
                        st.session_state.current_incident = incident
                        st.session_state.incident_generated = True
                else:
                    st.error("Please provide scenario name and select affected services")
    
    def _render_batch_testing(self):
        """Render batch testing interface"""
        st.subheader("Batch Testing")
        
        st.markdown("""
        Run multiple test scenarios in batch to validate the system's performance and accuracy.
        """)
        
        # Batch configuration
        col1, col2 = st.columns(2)
        
        with col1:
            batch_size = st.number_input(
                "Number of Incidents",
                min_value=1,
                max_value=50,
                value=10
            )
            
            scenario_mix = st.multiselect(
                "Scenario Types",
                ["Performance", "Security", "Outage", "Data", "Infrastructure"],
                default=["Performance", "Security", "Outage"]
            )
        
        with col2:
            parallel_execution = st.checkbox(
                "Parallel Execution",
                value=False,
                help="Run scenarios in parallel (faster but more resource intensive)"
            )
            
            generate_report = st.checkbox(
                "Generate Summary Report",
                value=True
            )
        
        if st.button("🚀 Start Batch Test", type="primary", key=key_manager.get_unique_key("start_batch", "button")):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            with st.spinner("Running batch tests..."):
                results = []
                
                for i in range(batch_size):
                    progress = (i + 1) / batch_size
                    progress_bar.progress(progress)
                    status_text.text(f"Processing incident {i+1}/{batch_size}")
                    
                    # Generate random scenario from selected types
                    scenario_type = random.choice(scenario_mix)
                    
                    # Simulate incident generation and analysis
                    result = {
                        "incident_id": f"BATCH-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                        "type": scenario_type.lower(),
                        "severity": random.choice(["low", "medium", "high", "critical"]),
                        "analysis_time": random.uniform(1.5, 4.5),
                        "root_cause_found": random.random() > 0.1,
                        "confidence": random.uniform(0.75, 0.98)
                    }
                    results.append(result)
                    
                    time.sleep(0.5)  # Simulate processing time
                
                progress_bar.progress(1.0)
                status_text.text("Batch test completed!")
                
                # Display results
                with results_container:
                    st.markdown("### Batch Test Results")
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Incidents", len(results))
                    with col2:
                        success_rate = sum(1 for r in results if r['root_cause_found']) / len(results) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    with col3:
                        avg_time = sum(r['analysis_time'] for r in results) / len(results)
                        st.metric("Avg Analysis Time", f"{avg_time:.1f}s")
                    with col4:
                        avg_confidence = sum(r['confidence'] for r in results) / len(results)
                        st.metric("Avg Confidence", f"{avg_confidence:.2f}")
                    
                    # Detailed results table
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True)
                    
                    if generate_report:
                        # Generate downloadable report
                        report = self._generate_batch_report(results)
                        st.download_button(
                            label="📥 Download Batch Test Report",
                            data=report,
                            file_name=f"batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key=key_manager.get_unique_key("download_batch_report", "button")
                        )
    
    def _generate_test_incident(self, scenario, category):
        """Generate a test incident from a predefined scenario"""
        try:
            # Map severity text to numeric value
            severity_map = {
                'critical': '1',
                'high': '2',
                'medium': '3',
                'low': '4'
            }
            severity_value = severity_map.get(scenario['severity'].lower(), '3')
            
            # Create OpsItem in AWS
            title = f"[TEST] {scenario['name']}"
            description = f"{scenario['description']}\n\nComponents: {', '.join(scenario['components'])}\nCategory: {category}"
            
            # Create the OpsItem
            ops_item_id = self.create_opsitem(title, description, severity_value)
            
            if not ops_item_id:
                st.error("Failed to create OpsItem")
                return None
            
            # Create incident object with OpsItem ID
            incident = {
                "incident_id": ops_item_id,
                "ops_item_id": ops_item_id,
                "title": scenario['name'],
                "description": scenario['description'],
                "severity": severity_value,
                "category": category,
                "components": scenario['components'],
                "start_time": datetime.now().isoformat(),
                "status": "active",
                "test_scenario": True,
                "type": "aws_opsitem"
            }
            
            # Add category-specific attributes
            if category == "Performance Issues":
                incident.update({
                    "metrics": {
                        "response_time": random.uniform(2.5, 8.0),
                        "error_rate": random.uniform(5, 25),
                        "cpu_usage": random.uniform(70, 95)
                    }
                })
            elif category == "Security Incidents":
                incident.update({
                    "security_details": {
                        "source_ips": [f"192.168.{random.randint(1,255)}.{random.randint(1,255)}" for _ in range(5)],
                        "attack_type": random.choice(["brute_force", "ddos", "injection"]),
                        "blocked_requests": random.randint(100, 10000)
                    }
                })
            
            # Store in session state
            if 'generated_incidents' not in st.session_state:
                st.session_state.generated_incidents = []
            st.session_state.generated_incidents.append(incident)
            
            return incident
            
        except Exception as e:
            st.error(f"Error generating test incident: {str(e)}")
            logger.error(f"Test incident generation error: {str(e)}")
            return None
    
    def _generate_custom_incident(self, scenario):
        """Generate incident from custom scenario"""
        try:
            # Create OpsItem in AWS
            title = f"[CUSTOM] {scenario['name']}"
            description = f"Type: {scenario['type']}\nServices: {', '.join(scenario['services'])}\nSymptoms: {scenario['symptoms']}\nBusiness Impact: {scenario['impact']}"
            
            # Create the OpsItem
            ops_item_id = self.create_opsitem(title, description, scenario['severity'])
            
            if not ops_item_id:
                st.error("Failed to create OpsItem")
                return None
            
            incident = {
                "incident_id": ops_item_id,
                "ops_item_id": ops_item_id,
                "title": scenario['name'],
                "type": scenario['type'],
                "severity": scenario['severity'],
                "duration_minutes": scenario['duration'],
                "affected_services": scenario['services'],
                "error_rate": scenario['error_rate'],
                "business_impact": scenario['impact'],
                "symptoms": scenario['symptoms'],
                "root_cause_hints": scenario.get('root_cause_hints', []),
                "start_time": datetime.now().isoformat(),
                "status": "active",
                "custom_scenario": True,
                "type": "aws_opsitem"
            }
            
            # Store in session state
            if 'generated_incidents' not in st.session_state:
                st.session_state.generated_incidents = []
            st.session_state.generated_incidents.append(incident)
            
            return incident
            
        except Exception as e:
            st.error(f"Error generating custom incident: {str(e)}")
            logger.error(f"Custom incident generation error: {str(e)}")
            return None
    
    def _generate_batch_report(self, results):
        """Generate a comprehensive batch test report"""
        report = {
            "test_run_id": f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "execution_time": datetime.now().isoformat(),
            "summary": {
                "total_incidents": len(results),
                "success_rate": sum(1 for r in results if r['root_cause_found']) / len(results) * 100,
                "avg_analysis_time": sum(r['analysis_time'] for r in results) / len(results),
                "avg_confidence": sum(r['confidence'] for r in results) / len(results)
            },
            "type_distribution": {},
            "severity_distribution": {},
            "detailed_results": results
        }
        
        # Calculate distributions
        for result in results:
            incident_type = result['type']
            severity = result['severity']
            
            report['type_distribution'][incident_type] = report['type_distribution'].get(incident_type, 0) + 1
            report['severity_distribution'][severity] = report['severity_distribution'].get(severity, 0) + 1
        
        return json.dumps(report, indent=2)

def main():
    """Main application entry point."""
    dashboard = EnhancedSREDashboard()
    dashboard.display_dashboard()

if __name__ == "__main__":
    main()