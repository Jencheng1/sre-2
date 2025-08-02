#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SRECopilotAnalyzer:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1'):
        """Initialize the SRE Copilot Analyzer."""
        self.region = region
        self.config = self._load_config(config_file)
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.region)
        self.logs_client = boto3.client('logs', region_name=self.region)
        
    def _load_config(self, config_file):
        """Load the SRE Copilot configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            raise
            
    def analyze_incident(self, incident_description, log_data=None, metrics_data=None, dashboard_data=None):
        """Analyze an incident using the SRE Copilot."""
        import time
        try:
            agent_id = self.config['supervisor_agent']['id']
            logger.info(f"Analyzing incident: {incident_description[:100]}...")
            
            # Prepare the input text
            input_text = f"Analyze this incident: {incident_description}\n\n"
            
            if log_data:
                input_text += f"Log data:\n{log_data}\n\n"
                
            if metrics_data:
                input_text += f"Metrics data:\n{metrics_data}\n\n"
                
            if dashboard_data:
                input_text += f"Dashboard data:\n{dashboard_data}\n\n"
            
            # Invoke the Supervisor Agent
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID',  # Use the appropriate alias ID or 'TSTALIASID' for testing
                sessionId='test-session-' + str(int(time.time())),  # Generate unique session ID
                inputText=input_text,
                enableTrace=True
            )
            
            # Process and collect the response
            analysis_result = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode('utf-8')
                        analysis_result += text
                        logger.info(f"Agent response chunk: {text[:100]}...")
            
            logger.info("Analysis completed successfully.")
            return analysis_result
            
        except ClientError as e:
            logger.error(f"Error analyzing incident: {e}")
            raise
            
    def fetch_cloudwatch_logs(self, log_group, start_time, end_time, filter_pattern=None, limit=100):
        """Fetch logs from CloudWatch Logs."""
        try:
            logger.info(f"Fetching logs from {log_group}...")
            
            kwargs = {
                'logGroupName': log_group,
                'startTime': int(start_time * 1000),  # Convert to milliseconds
                'endTime': int(end_time * 1000),      # Convert to milliseconds
                'limit': limit
            }
            
            if filter_pattern:
                kwargs['filterPattern'] = filter_pattern
                
            response = self.logs_client.filter_log_events(**kwargs)
            
            # Extract log messages
            log_messages = []
            for event in response.get('events', []):
                timestamp = event['timestamp'] / 1000  # Convert to seconds
                message = event['message']
                log_messages.append(f"{timestamp}: {message}")
                
            logger.info(f"Fetched {len(log_messages)} log messages.")
            return '\n'.join(log_messages)
            
        except ClientError as e:
            logger.error(f"Error fetching CloudWatch logs: {e}")
            raise
            
    def fetch_cloudwatch_metrics(self, namespace, metric_name, dimensions, start_time, end_time, period=60, statistic='Average'):
        """Fetch metrics from CloudWatch."""
        try:
            logger.info(f"Fetching metric {namespace}:{metric_name}...")
            
            response = self.cloudwatch_client.get_metric_data(
                MetricDataQueries=[
                    {
                        'Id': 'm1',
                        'MetricStat': {
                            'Metric': {
                                'Namespace': namespace,
                                'MetricName': metric_name,
                                'Dimensions': dimensions
                            },
                            'Period': period,
                            'Stat': statistic
                        },
                        'ReturnData': True
                    }
                ],
                StartTime=start_time,
                EndTime=end_time
            )
            
            # Extract metric values
            timestamps = response['MetricDataResults'][0]['Timestamps']
            values = response['MetricDataResults'][0]['Values']
            
            # Format metric data
            metric_data = []
            for i in range(len(timestamps)):
                metric_data.append(f"{timestamps[i].isoformat()}: {values[i]}")
                
            logger.info(f"Fetched {len(metric_data)} metric data points.")
            return '\n'.join(metric_data)
            
        except ClientError as e:
            logger.error(f"Error fetching CloudWatch metrics: {e}")
            raise
            
    def analyze_with_data_sources(self, incident_description, log_groups=None, metrics=None, dashboard_description=None):
        """Analyze an incident with automatically fetched data sources."""
        try:
            # Default time range: last hour
            import time
            end_time = time.time()
            start_time = end_time - 3600  # 1 hour ago
            
            # Fetch logs if log groups are provided
            log_data = None
            if log_groups:
                all_logs = []
                for log_group in log_groups:
                    logs = self.fetch_cloudwatch_logs(log_group, start_time, end_time)
                    all_logs.append(f"=== Logs from {log_group} ===\n{logs}")
                log_data = '\n\n'.join(all_logs)
                
            # Fetch metrics if metrics are provided
            metrics_data = None
            if metrics:
                all_metrics = []
                for metric in metrics:
                    namespace = metric['namespace']
                    metric_name = metric['metric_name']
                    dimensions = metric['dimensions']
                    
                    metric_values = self.fetch_cloudwatch_metrics(namespace, metric_name, dimensions, start_time, end_time)
                    all_metrics.append(f"=== Metric {namespace}:{metric_name} ===\n{metric_values}")
                metrics_data = '\n\n'.join(all_metrics)
                
            # Analyze the incident
            return self.analyze_incident(incident_description, log_data, metrics_data, dashboard_description)
            
        except Exception as e:
            logger.error(f"Error analyzing with data sources: {e}")
            raise

def main():
    """Main function to analyze incidents with the SRE Copilot."""
    parser = argparse.ArgumentParser(description='Analyze incidents with the SRE Copilot.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to the configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze incident command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an incident')
    analyze_parser.add_argument('--description', required=True, help='Incident description')
    analyze_parser.add_argument('--logs', help='Path to log data file')
    analyze_parser.add_argument('--metrics', help='Path to metrics data file')
    analyze_parser.add_argument('--dashboard', help='Path to dashboard description file')
    analyze_parser.add_argument('--output', help='Output file for analysis results')
    
    # Analyze with data sources command
    sources_parser = subparsers.add_parser('analyze-with-sources', help='Analyze an incident with automatically fetched data sources')
    sources_parser.add_argument('--description', required=True, help='Incident description')
    sources_parser.add_argument('--log-groups', nargs='+', help='CloudWatch log groups to fetch')
    sources_parser.add_argument('--metrics-config', help='Path to metrics configuration file')
    sources_parser.add_argument('--dashboard-description', help='Dashboard description')
    sources_parser.add_argument('--output', help='Output file for analysis results')
    
    args = parser.parse_args()
    
    try:
        analyzer = SRECopilotAnalyzer(config_file=args.config, region=args.region)
        
        if args.command == 'analyze':
            # Read data from files if provided
            log_data = None
            if args.logs:
                with open(args.logs, 'r') as f:
                    log_data = f.read()
                    
            metrics_data = None
            if args.metrics:
                with open(args.metrics, 'r') as f:
                    metrics_data = f.read()
                    
            dashboard_data = None
            if args.dashboard:
                with open(args.dashboard, 'r') as f:
                    dashboard_data = f.read()
                    
            # Analyze the incident
            result = analyzer.analyze_incident(
                args.description,
                log_data,
                metrics_data,
                dashboard_data
            )
            
            # Output the result
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(result)
            else:
                print(result)
                
        elif args.command == 'analyze-with-sources':
            # Read metrics configuration if provided
            metrics = None
            if args.metrics_config:
                with open(args.metrics_config, 'r') as f:
                    metrics = json.load(f)
                    
            # Read dashboard description if provided
            dashboard_description = None
            if args.dashboard_description:
                with open(args.dashboard_description, 'r') as f:
                    dashboard_description = f.read()
                    
            # Analyze the incident with data sources
            result = analyzer.analyze_with_data_sources(
                args.description,
                args.log_groups,
                metrics,
                dashboard_description
            )
            
            # Output the result
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(result)
            else:
                print(result)
                
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
