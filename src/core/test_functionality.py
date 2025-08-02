#!/usr/bin/env python3

import boto3
import json
import time
import logging
import argparse
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SRECopilotTester:
    def __init__(self, config_file='sre_copilot_config.json', region='us-east-1'):
        """Initialize the SRE Copilot tester."""
        self.region = region
        self.config = self._load_config(config_file)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.region)
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
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
            
    def verify_agent_status(self, agent_type):
        """Verify that an agent exists and is in the PREPARED state."""
        try:
            agent_id = self.config[agent_type]['id']
            response = self.bedrock_agent_client.get_agent(
                agentId=agent_id
            )
            
            status = response['agent']['agentStatus']
            logger.info(f"{agent_type} status: {status}")
            
            if status == 'PREPARED':
                logger.info(f"✅ {agent_type} is ready.")
                return True
            else:
                logger.warning(f"⚠️ {agent_type} is not ready. Current status: {status}")
                return False
                
        except ClientError as e:
            logger.error(f"Error verifying {agent_type} status: {e}")
            return False
            
    def verify_knowledge_base(self):
        """Verify that the knowledge base exists and is in the AVAILABLE state."""
        try:
            kb_id = self.config['knowledge_base']['id']
            response = self.bedrock_agent_client.get_knowledge_base(
                knowledgeBaseId=kb_id
            )
            
            status = response['knowledgeBase']['status']
            logger.info(f"Knowledge base status: {status}")
            
            if status == 'AVAILABLE':
                logger.info("✅ Knowledge base is available.")
                return True
            else:
                logger.warning(f"⚠️ Knowledge base is not available. Current status: {status}")
                return False
                
        except ClientError as e:
            logger.error(f"Error verifying knowledge base status: {e}")
            return False
            
    def test_supervisor_agent(self, query="What would cause high CPU usage on an EC2 instance?"):
        """Test the supervisor agent with a sample query."""
        try:
            agent_id = self.config['supervisor_agent']['id']
            logger.info(f"Testing supervisor agent with query: '{query}'")
            
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID', # Use the appropriate alias ID or 'TSTALIASID' for testing
                inputText=query,
                enableTrace=True
            )
            
            # Process and display the response
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode('utf-8')
                        logger.info(f"Agent response: {text}")
            
            logger.info("✅ Supervisor agent test completed successfully.")
            return True
            
        except ClientError as e:
            logger.error(f"Error testing supervisor agent: {e}")
            return False
            
    def test_agent_collaboration(self, query="Analyze the logs and metrics to find the root cause of the high latency issue."):
        """Test collaboration between the supervisor agent and specialized agents."""
        try:
            agent_id = self.config['supervisor_agent']['id']
            logger.info(f"Testing agent collaboration with query: '{query}'")
            
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId='TSTALIASID', # Use the appropriate alias ID or 'TSTALIASID' for testing
                inputText=query,
                enableTrace=True
            )
            
            # Process and display the response
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode('utf-8')
                        logger.info(f"Agent response: {text}")
            
            logger.info("✅ Agent collaboration test completed successfully.")
            return True
            
        except ClientError as e:
            logger.error(f"Error testing agent collaboration: {e}")
            return False
            
    def test_knowledge_base_query(self, query="Find similar incidents to the current database connection timeout."):
        """Test querying the knowledge base."""
        try:
            kb_id = self.config['knowledge_base']['id']
            logger.info(f"Testing knowledge base query: '{query}'")
            
            response = self.bedrock_runtime_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={
                    'text': query
                },
                numberOfResults=3
            )
            
            # Process and display the results
            for result in response['retrievalResults']:
                logger.info(f"Result score: {result['score']}")
                logger.info(f"Content: {result['content']['text']}")
                
            logger.info("✅ Knowledge base query test completed successfully.")
            return True
            
        except ClientError as e:
            logger.error(f"Error testing knowledge base query: {e}")
            return False
            
    def run_all_tests(self):
        """Run all tests to verify SRE Copilot functionality."""
        logger.info("=== Starting SRE Copilot Functionality Tests ===")
        
        # Verify agent statuses
        all_agents_ready = True
        for agent_type in ['supervisor_agent', 'log_analysis_agent', 'metrics_analysis_agent', 
                          'dashboard_analysis_agent', 'knowledge_base_agent']:
            if not self.verify_agent_status(agent_type):
                all_agents_ready = False
                
        # Verify knowledge base
        kb_ready = self.verify_knowledge_base()
        
        # Only proceed with functional tests if all components are ready
        if all_agents_ready and kb_ready:
            logger.info("All components are ready. Proceeding with functional tests.")
            
            # Test supervisor agent
            self.test_supervisor_agent()
            
            # Test agent collaboration
            self.test_agent_collaboration()
            
            # Test knowledge base query
            self.test_knowledge_base_query()
            
            logger.info("=== SRE Copilot Functionality Tests Completed ===")
        else:
            logger.warning("Some components are not ready. Skipping functional tests.")
            
def main():
    """Main function to test SRE Copilot functionality."""
    parser = argparse.ArgumentParser(description='Test SRE Copilot functionality.')
    parser.add_argument('--config', default='sre_copilot_config.json', help='Path to the configuration file')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--test', choices=['all', 'supervisor', 'collaboration', 'knowledge_base'], 
                        default='all', help='Specific test to run')
    args = parser.parse_args()
    
    try:
        tester = SRECopilotTester(config_file=args.config, region=args.region)
        
        if args.test == 'all':
            tester.run_all_tests()
        elif args.test == 'supervisor':
            tester.verify_agent_status('supervisor_agent')
            tester.test_supervisor_agent()
        elif args.test == 'collaboration':
            tester.test_agent_collaboration()
        elif args.test == 'knowledge_base':
            tester.verify_knowledge_base()
            tester.test_knowledge_base_query()
            
    except Exception as e:
        logger.error(f"Error testing SRE Copilot functionality: {e}")
        raise

if __name__ == "__main__":
    main()
