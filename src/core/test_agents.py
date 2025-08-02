#!/usr/bin/env python3

import boto3
import json
import logging
import argparse
import time
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentTester:
    def __init__(self, config_file=None, region='us-east-1'):
        """Initialize the agent tester."""
        self.region = region
        self.config = self._load_config(config_file) if config_file else {}
        self.bedrock_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        
    def _load_config(self, config_file):
        """Load configuration from file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing configuration file {config_file}.")
            return {}

    def _get_agent_id(self, agent_name):
        """Get agent ID by name."""
        try:
            paginator = self.bedrock_agent_client.get_paginator('list_agents')
            for page in paginator.paginate():
                for agent in page.get('agentSummaries', []):
                    if agent.get('agentName') == agent_name:
                        return agent.get('agentId')
            return None
        except Exception as e:
            logger.error(f"Error getting agent ID for {agent_name}: {e}")
            return None

    def _get_agent_alias_id(self, agent_name):
        """Get agent alias ID for the LATEST alias."""
        try:
            agent_id = self._get_agent_id(agent_name)
            if not agent_id:
                return None

            response = self.bedrock_agent_client.list_agent_aliases(agentId=agent_id)
            for alias in response.get('agentAliasSummaries', []):
                if alias.get('agentAliasName') == 'LATEST':
                    return alias.get('agentAliasId')
            return None
        except Exception as e:
            logger.error(f"Error getting alias ID for {agent_name}: {e}")
            return None

    def _run_test_scenarios(self, agent_name, scenarios):
        """Run test scenarios for an agent."""
        results = {
            'success': True,
            'scenarios': {}
        }
        alias_id = self._get_agent_alias_id(agent_name)
        
        if not alias_id:
            logger.error(f"Agent alias not found for {agent_name}")
            results['success'] = False
            return results

        for scenario in scenarios:
            logger.info(f"Running scenario: {scenario['name']}")
            try:
                response = self.bedrock_client.invoke_agent(
                    agentAliasId=alias_id,
                    sessionId=f"test-{int(time.time())}",
                    inputText=json.dumps(scenario['input'])
                )
                
                # Handle streaming response
                response_body = []
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']['bytes'].decode('utf-8')
                        response_body.append(chunk)
                        print(chunk, end='', flush=True)  # Print response in real-time
                
                results['scenarios'][scenario['name']] = {
                    'success': True,
                    'response': ''.join(response_body)
                }
                logger.info(f"✅ Scenario '{scenario['name']}' completed successfully")
                
            except Exception as e:
                logger.error(f"❌ Scenario '{scenario['name']}' failed: {e}")
                results['scenarios'][scenario['name']] = {
                    'success': False,
                    'error': str(e)
                }
                results['success'] = False
                
            time.sleep(2)  # Add delay between requests
            
        return results

    def test_log_analyzer(self):
        """Test the log analysis agent with real scenarios."""
        logger.info("Testing Log Analysis Agent...")
        
        test_scenarios = [
            {
                "name": "Error Pattern Analysis",
                "input": {
                    "prompt": "Analyze the following log patterns in our production API logs. Look for error patterns, their frequency, and potential root causes.",
                    "log_data": """
2024-03-15 10:23:45 ERROR [production-api] Connection timeout to database
2024-03-15 10:23:46 WARN [production-api] Retrying database connection (attempt 1/3)
2024-03-15 10:23:47 ERROR [production-api] Database connection failed: Connection refused
2024-03-15 10:23:48 ERROR [production-api] API request failed due to database unavailability
2024-03-15 10:24:00 INFO [production-api] Database connection restored
2024-03-15 10:24:05 ERROR [production-api] High latency detected in /api/users endpoint
2024-03-15 10:24:10 WARN [production-api] Memory usage at 85% threshold
                    """
                }
            },
            {
                "name": "Performance Analysis",
                "input": {
                    "prompt": "Analyze these logs for performance issues. Identify slow requests, resource constraints, and potential optimizations.",
                    "log_data": """
2024-03-15 11:15:30 INFO [production-api] Request to /api/orders took 2500ms
2024-03-15 11:15:35 WARN [production-api] Slow query detected - execution time: 3200ms
2024-03-15 11:15:40 ERROR [production-api] Request timeout after 5000ms
2024-03-15 11:15:45 WARN [production-api] CPU usage spike detected: 92%
2024-03-15 11:15:50 INFO [production-api] Database connection pool at 80% capacity
                    """
                }
            }
        ]

        return self._run_test_scenarios('SRE-Log-Analyzer', test_scenarios)

    def test_metrics_analyzer(self):
        """Test the metrics analysis agent with real scenarios."""
        logger.info("Testing Metrics Analysis Agent...")
        
        test_scenarios = [
            {
                "name": "Resource Utilization Analysis",
                "input": {
                    "prompt": "Analyze these resource utilization metrics. Identify trends, anomalies, and potential capacity issues.",
                    "metrics_data": {
                        "timestamp_range": "2024-03-15T10:00:00Z to 2024-03-15T11:00:00Z",
                        "metrics": [
                            {"timestamp": "2024-03-15T10:00:00Z", "cpu_usage": 45, "memory_usage": 60, "latency_ms": 100},
                            {"timestamp": "2024-03-15T10:15:00Z", "cpu_usage": 65, "memory_usage": 75, "latency_ms": 150},
                            {"timestamp": "2024-03-15T10:30:00Z", "cpu_usage": 85, "memory_usage": 85, "latency_ms": 250},
                            {"timestamp": "2024-03-15T10:45:00Z", "cpu_usage": 95, "memory_usage": 90, "latency_ms": 500}
                        ]
                    }
                }
            },
            {
                "name": "Error Rate Analysis",
                "input": {
                    "prompt": "Analyze these error rate metrics. Look for patterns and recommend actions.",
                    "metrics_data": {
                        "timestamp_range": "2024-03-15T11:00:00Z to 2024-03-15T12:00:00Z",
                        "metrics": [
                            {"timestamp": "2024-03-15T11:00:00Z", "error_rate": 0.1, "error_count": 5},
                            {"timestamp": "2024-03-15T11:15:00Z", "error_rate": 0.5, "error_count": 25},
                            {"timestamp": "2024-03-15T11:30:00Z", "error_rate": 2.0, "error_count": 100},
                            {"timestamp": "2024-03-15T11:45:00Z", "error_rate": 5.0, "error_count": 250}
                        ]
                    }
                }
            }
        ]

        return self._run_test_scenarios('SRE-Metrics-Analyzer', test_scenarios)

    def test_supervisor(self):
        """Test the supervisor agent with real scenarios."""
        logger.info("Testing Supervisor Agent...")
        
        test_scenarios = [
            {
                "name": "Incident Response Coordination",
                "input": {
                    "prompt": "Coordinate response to this production incident. Analyze the situation and provide action items.",
                    "incident_data": {
                        "title": "Production API Performance Degradation",
                        "severity": "High",
                        "status": "Active",
                        "description": "Users reporting slow response times and occasional timeouts",
                        "metrics": {
                            "error_rate": "5%",
                            "p95_latency": "2500ms",
                            "cpu_usage": "92%"
                        },
                        "affected_services": [
                            "user-api",
                            "order-processing",
                            "payment-service"
                        ]
                    }
                }
            },
            {
                "name": "System Health Assessment",
                "input": {
                    "prompt": "Assess overall system health based on these metrics and logs. Identify risks and recommend preventive actions.",
                    "system_data": {
                        "services_status": {
                            "api_gateway": {"status": "degraded", "uptime": "99.9%"},
                            "user_service": {"status": "healthy", "uptime": "99.99%"},
                            "order_service": {"status": "at_risk", "uptime": "99.5%"}
                        },
                        "recent_incidents": [
                            {
                                "type": "performance_degradation",
                                "duration_minutes": 45,
                                "impact": "moderate"
                            },
                            {
                                "type": "database_slowdown",
                                "duration_minutes": 30,
                                "impact": "minor"
                            }
                        ],
                        "current_metrics": {
                            "total_error_rate": "2.5%",
                            "avg_response_time": "800ms",
                            "cpu_usage": "78%",
                            "memory_usage": "85%"
                        }
                    }
                }
            }
        ]

        return self._run_test_scenarios('SRE-Supervisor', test_scenarios)

    def test_all_agents(self):
        """Test all agents with real-world scenarios."""
        results = {
            'success': True,
            'agents': {},
            'next_steps': []
        }

        # Test Log Analysis Agent
        logger.info("\n=== Testing Log Analysis Agent ===")
        log_results = self.test_log_analyzer()
        results['agents']['SRE-Log-Analyzer'] = log_results
        if not log_results.get('success', False):
            results['success'] = False
            results['next_steps'].append("Fix issues with Log Analysis Agent")

        # Test Metrics Analysis Agent
        logger.info("\n=== Testing Metrics Analysis Agent ===")
        metrics_results = self.test_metrics_analyzer()
        results['agents']['SRE-Metrics-Analyzer'] = metrics_results
        if not metrics_results.get('success', False):
            results['success'] = False
            results['next_steps'].append("Fix issues with Metrics Analysis Agent")

        # Test Supervisor Agent
        logger.info("\n=== Testing Supervisor Agent ===")
        supervisor_results = self.test_supervisor()
        results['agents']['SRE-Supervisor'] = supervisor_results
        if not supervisor_results.get('success', False):
            results['success'] = False
            results['next_steps'].append("Fix issues with Supervisor Agent")

        # Add next steps based on results
        if results['success']:
            results['next_steps'].append("All agents tested successfully")
            results['next_steps'].append("You can now use the agents in production")
        else:
            results['next_steps'].append("Check CloudWatch logs for detailed error messages")
            results['next_steps'].append("Verify agent configurations and permissions")

        return results

    def print_results(self, results):
        """Print the test results in a readable format."""
        print("\n" + "="*80)
        print("SRE COPILOT AGENT TEST RESULTS")
        print("="*80)
        
        if results['success']:
            print("\n✅ All agents tested successfully!")
        else:
            print("\n❌ Some agents failed testing.")
        
        print("\nAGENT STATUS:")
        for agent_name, agent_results in results['agents'].items():
            print(f"\n{agent_name}:")
            for scenario_name, scenario_result in agent_results['scenarios'].items():
                status = "✅ Success" if scenario_result['success'] else "❌ Failed"
                print(f"  - {scenario_name}: {status}")
                if not scenario_result['success']:
                    print(f"    Error: {scenario_result.get('error', 'Unknown error')}")
        
        print("\nNEXT STEPS:")
        for i, step in enumerate(results['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "="*80)

def main():
    """Main function to test agents."""
    parser = argparse.ArgumentParser(description='Test SRE Copilot agents with real-world scenarios.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    args = parser.parse_args()
    
    try:
        tester = AgentTester(config_file=args.config, region=args.region)
        results = tester.test_all_agents()
        tester.print_results(results)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 