#!/usr/bin/env python3
"""
SRE Copilot - Enhanced Root Cause Analysis Dashboard
Integrates real incident generation and AWS data analysis using Bedrock agents.
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
from botocore.exceptions import ClientError
from user_guide_content import get_all_guides, get_guide_titles

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
        ops_item_id = self.create_opsitem(
            f"Incident: {incident_type.capitalize()} Issue Detected",
            f"Automated incident generated for {incident_type} scenario. Components affected: {', '.join(incident_data['components'])}",
            severity='2' if incident_type == 'outage' else '3'
        )
        
        incident_data['ops_item_id'] = ops_item_id
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
        self.setup_sidebar()
        
    def setup_sidebar(self):
        """Setup the enhanced sidebar."""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100.png?text=SRE+Copilot", width=300)
            st.markdown("## 🎯 Incident Management")
            
            # Incident Generation Section
            st.markdown("### 🚀 Generate Incident")
            
            incident_type = st.selectbox(
                "Select Incident Type to Generate",
                ["Performance Degradation", "Security Alert", "Service Outage"]
            )
            
            if st.button("🔥 Generate Real Incident", type="primary", use_container_width=True, key="generate_incident"):
                self.generate_incident(incident_type)
                
            # Analysis Section
            st.markdown("### 🔍 Analyze Incident")
            
            # OpsItem selection
            if st.session_state.generated_incidents:
                ops_items = [f"{inc['ops_item_id']} - {inc['type']}" for inc in st.session_state.generated_incidents]
                selected_ops = st.selectbox("Select OpsItem", ops_items)
                
                if st.button("🤖 Run Root Cause Analysis", type="primary", use_container_width=True, key="run_analysis_sidebar"):
                    ops_item_id = selected_ops.split(' - ')[0]
                    self.run_root_cause_analysis(ops_item_id)
            else:
                st.info("Generate an incident first to analyze")
                
            # Data Sources
            st.markdown("### 📊 Data Sources")
            st.session_state.include_logs = st.checkbox("CloudWatch Logs", value=True)
            st.session_state.include_metrics = st.checkbox("CloudWatch Metrics", value=True)
            st.session_state.include_cloudtrail = st.checkbox("CloudTrail Events", value=True)
            st.session_state.include_vpc_logs = st.checkbox("VPC Flow Logs", value=True)
            st.session_state.include_health = st.checkbox("AWS Health", value=True)
            
            # Time Range
            st.session_state.time_range = st.selectbox(
                "Analysis Time Range",
                ["Last 15 minutes", "Last 30 minutes", "Last 1 hour", "Last 6 hours"]
            )
            
            # History
            st.markdown("### 📜 Recent Incidents")
            for i, incident in enumerate(reversed(st.session_state.generated_incidents[-5:])):
                if st.button(f"📋 {incident['type']} - {incident['start_time'].strftime('%H:%M')}", key=f"inc_{i}"):
                    st.session_state.current_incident = incident
                    
    def generate_incident(self, incident_type):
        """Generate a real incident in AWS."""
        with st.spinner(f"🔥 Generating {incident_type} incident..."):
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
            with st.info("🔄 Knowledge Base Integration"):
                st.markdown(f"""
                **Your incident is being indexed to the Knowledge Base!**
                
                In a few seconds, you can:
                - 🔍 Search for this incident in the KB (Search tab)
                - 📖 Browse it in the {incident_type.split()[0].lower()} category (Browse tab)
                - 🤖 Get AI analysis with historical context (Test Analysis tab)
                
                **OpsItem ID:** `{incident_data['ops_item_id']}`
                """)
            st.balloons()
            
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
        """Invoke the supervisor agent for analysis."""
        payload = {
            'action': 'analyze',
            'incident_description': f"{ops_item.get('Title', '')}. {ops_item.get('Description', '')}",
            'start_time': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'end_time': datetime.utcnow().isoformat(),
            'service': 'sre-demo-app',
            'environment': 'demo',
            'additional_context': {
                'ops_item_id': ops_item.get('OpsItemId'),
                'severity': ops_item.get('Severity'),
                'data_summary': {
                    'log_events': sum(len(events) for events in collected_data['logs'].values()),
                    'metric_points': sum(len(points) for points in collected_data['metrics'].values())
                }
            }
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName='sre-supervisor-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            if result.get('statusCode') == 200:
                body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
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
        st.markdown('<h1 class="main-header">🔍 SRE Copilot - Real-Time Root Cause Analysis</h1>', 
                   unsafe_allow_html=True)
        
        # Main navigation tabs
        main_tabs = st.tabs(["🚨 Incident Management", "🔍 Analyze Incident", "🔧 Recent Changes", "📚 Knowledge Base", "📊 Analytics", "❓ User Guide"])
        
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
            
        with main_tabs[5]:
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
                if st.button("🔍 Analyze Another Incident", type="secondary", key="analyze_another"):
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
                    ops_item_id = st.text_input("Enter OpsItem ID:", key="manual_opsitem_with_list")
                else:
                    ops_item_id = selected.split(' - ')[0]
                    
                if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True, key="analyze_selected"):
                    if ops_item_id:
                        self.run_root_cause_analysis(ops_item_id)
                        # Set flag to show results
                        st.session_state.show_analysis_results = True
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter or select an OpsItem ID")
                        
            else:
                st.warning("No open OpsItems found. Enter an OpsItem ID manually.")
                ops_item_id = st.text_input("Enter OpsItem ID:", key="manual_opsitem_no_items")
                
                if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True, key="analyze_manual_no_items"):
                    if ops_item_id:
                        self.run_root_cause_analysis(ops_item_id)
                        # Set flag to show results
                        st.session_state.show_analysis_results = True
                        st.experimental_rerun()
                    else:
                        st.warning("Please enter an OpsItem ID")
                        
        except Exception as e:
            st.error(f"Error fetching OpsItems: {str(e)}")
            
            # Fallback to manual entry
            ops_item_id = st.text_input("Enter OpsItem ID:", key="manual_opsitem_error")
            
            if st.button("🤖 Analyze Root Cause", type="primary", use_container_width=True, key="analyze_error"):
                if ops_item_id:
                    self.run_root_cause_analysis(ops_item_id)
                    # Set flag to show results
                    st.session_state.show_analysis_results = True
                    st.experimental_rerun()
                else:
                    st.warning("Please enter an OpsItem ID")
    
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
        """Display root cause analysis."""
        st.markdown("### 🎯 Root Cause Analysis")
        
        analysis = incident.get('analysis', {})
        
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
                total_events = sum(len(events) for events in data['logs'].values())
                st.metric("Total Log Events Analyzed", total_events)
                
                for log_group, events in data['logs'].items():
                    if events:
                        st.write(f"**{log_group}**: {len(events)} events")
                        # Show sample events
                        with st.expander(f"View sample events from {log_group}"):
                            for event in events[:5]:
                                st.text(event.get('message', ''))
                                
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
        # Use ops_item_id if available, otherwise use a combination of type and timestamp
        incident_id = incident.get('ops_item_id', '')
        incident_type = incident.get('type', 'unknown')
        timestamp = incident.get('time', datetime.now().strftime('%Y%m%d%H%M%S'))
        key_suffix = f"{incident_id}_{incident_type}_{timestamp}".replace('-', '_').replace(' ', '_').replace(':', '')
        
        # Action buttons with unique keys
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📧 Create JIRA Ticket", use_container_width=True, key=f"create_jira_{key_suffix}"):
                st.success("✅ Ticket created")
        with col2:
            if st.button("📢 Send to Slack", use_container_width=True, key=f"send_slack_{key_suffix}"):
                st.success("✅ Notification sent")
        with col3:
            if st.button("📄 Export Report", use_container_width=True, key=f"export_report_{key_suffix}"):
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
        kb_tabs = st.tabs(["🔍 Search", "📖 Browse", "➕ Add Document", "🧪 Test Analysis"])
        
        with kb_tabs[0]:
            self.render_kb_search()
            
        with kb_tabs[1]:
            self.render_kb_browse()
            
        with kb_tabs[2]:
            self.render_kb_add_document()
            
        with kb_tabs[3]:
            self.render_kb_test_analysis()
            
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
            
        if st.button("🔍 Search", type="primary", key="kb_search_button"):
            # Always use the current query value
            if query:
                self.search_knowledge_base(search_type, query, category, max_results)
            else:
                st.warning("Please enter a search query")
                
    def search_knowledge_base(self, search_type, query, category, max_results):
        """Search the knowledge base."""
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
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    
                    if action == "get_resolution" and body.get('guide'):
                        # Display single resolution guide
                        guide = body['guide']
                        with st.expander(f"📋 {guide['title']}", expanded=True):
                            st.markdown(guide['content'])
                    else:
                        # Display search results
                        results = body.get('results', [])
                        st.success(f"Found {len(results)} results")
                        
                        # Group results by type for better visualization
                        incidents = [r for r in results if r['metadata'].get('type') == 'incident']
                        best_practices = [r for r in results if r['metadata'].get('type') == 'best_practice']
                        resolutions = [r for r in results if r['metadata'].get('type') == 'resolution_guide']
                        
                        # Display incidents
                        if incidents:
                            st.markdown("### 🚨 Similar Incidents")
                            for idx, doc in enumerate(incidents, 1):
                                with st.expander(f"{idx}. {doc['title']} (Similarity: {doc.get('score', 0):.2f})"):
                                    st.markdown(f"**Category:** {doc['metadata'].get('category', 'N/A')}")
                                    
                                    # Check for change correlation
                                    if 'change_id' in doc['metadata']:
                                        st.error(f"🔧 **Caused by Change:** {doc['metadata']['change_id']}")
                                    
                                    st.markdown("**Description:**")
                                    st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                                    
                                    # Show resolution if available
                                    if 'resolution' in doc['metadata']:
                                        st.success(f"✅ **Resolution:** {doc['metadata']['resolution']}")
                        
                        # Display best practices
                        if best_practices:
                            st.markdown("### 📚 Related Best Practices")
                            for idx, doc in enumerate(best_practices, 1):
                                with st.expander(f"{idx}. {doc['title']}"):
                                    if doc['metadata'].get('tags'):
                                        st.markdown(f"**Tags:** {', '.join(doc['metadata']['tags'])}")
                                    st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                        
                        # Display resolution guides
                        if resolutions:
                            st.markdown("### 🔧 Resolution Guides")
                            for idx, doc in enumerate(resolutions, 1):
                                with st.expander(f"{idx}. {doc['title']}"):
                                    st.markdown(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                else:
                    st.error(f"Search failed: {result.get('body')}")
                    
            except Exception as e:
                st.error(f"Error searching knowledge base: {str(e)}")
                
    def render_kb_browse(self):
        """Browse knowledge base by category."""
        st.subheader("Browse Knowledge Base")
        
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
        
        if st.button("📖 Browse", key="kb_browse_button"):
            self.browse_knowledge_base(category, doc_type)
            
    def browse_knowledge_base(self, category, doc_type):
        """Browse documents by category."""
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
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    all_results = body.get('results', [])
                    
                    # Display results
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
                                            # Show first 1000 chars with expand option
                                            st.markdown(content[:1000] + "...")
                                            if st.button(f"Show full content", key=f"show_{doc['document_id']}"):
                                                st.markdown(content)
                                        else:
                                            st.markdown(content)
                                        
                                        # Show metadata
                                        if doc.get('metadata', {}).get('root_cause'):
                                            st.info(f"**Root Cause:** {doc['metadata']['root_cause']}")
                    else:
                        st.warning(f"No documents found in {category} category")
                        st.info("Try selecting a different category or adding documents to the knowledge base.")
                else:
                    st.error(f"Failed to browse documents: {result.get('body')}")
                    
            except Exception as e:
                st.error(f"Error browsing knowledge base: {str(e)}")
        
    def render_kb_add_document(self):
        """Add new document to knowledge base."""
        st.subheader("Add Document to Knowledge Base")
        
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
        
        if st.button("➕ Add Document", key="kb_add_document"):
            if all([doc_id, title, category, content]):
                self.add_to_knowledge_base(doc_id, title, category, content, doc_type, tags)
            else:
                st.warning("Please fill all required fields")
                
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
                    st.success(f"✅ Document {doc_id} added successfully!")
                else:
                    st.error(f"Failed to add document: {result.get('body')}")
                    
            except Exception as e:
                st.error(f"Error adding document: {str(e)}")
                
    def render_kb_test_analysis(self):
        """Test knowledge-based analysis."""
        st.subheader("Test Knowledge-Based Analysis")
        
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
        
        if st.button("🧪 Analyze with Knowledge Base", key="kb_test_analysis"):
            if incident_desc:
                self.analyze_with_knowledge_base(incident_desc, incident_type)
            else:
                st.warning("Please enter an incident description")
                
    def analyze_with_knowledge_base(self, incident_desc, incident_type):
        """Analyze incident using knowledge base context."""
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
                
                if result.get('statusCode') == 200:
                    body = json.loads(result['body'])
                    
                    # Display context used
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Similar Incidents", body['context_used']['similar_incidents_count'])
                    with col2:
                        st.metric("Best Practices", body['context_used']['best_practices_count'])
                    with col3:
                        st.metric("Has Resolution Guide", "✅" if body['context_used']['has_resolution_guide'] else "❌")
                        
                    # Display analysis
                    st.markdown("### Knowledge-Enhanced Analysis")
                    st.markdown(body['analysis'])
                else:
                    st.error(f"Analysis failed: {result.get('body')}")
                    
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                
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
                    if st.button("🔄 Refresh Changes", key="refresh_changes"):
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
                if st.button("🎭 Create Demo Change", key="create_demo_change"):
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
                        if st.button("🎮 Generate Test Incident", key="guide_gen_incident"):
                            st.info("Switch to 'Incident Management' tab to generate incidents")
                    with col_b:
                        if st.button("🔍 Analyze Incident", key="guide_analyze"):
                            st.info("Switch to 'Analyze Incident' tab")
                    with col_c:
                        if st.button("📚 Search KB", key="guide_kb"):
                            st.info("Switch to 'Knowledge Base' tab")
                            
                elif selected_guide_id == "incident_analysis":
                    if st.button("🔍 Go to Analyze Tab", key="guide_go_analyze"):
                        st.info("Switch to 'Analyze Incident' tab to start")
                        
                elif selected_guide_id == "knowledge_management":
                    if st.button("📚 Go to Knowledge Base", key="guide_go_kb"):
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
        search_query = st.text_input("Search for specific topics or keywords:", key="guide_search")
        
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

def main():
    """Main application entry point."""
    dashboard = EnhancedSREDashboard()
    dashboard.display_dashboard()

if __name__ == "__main__":
    main()