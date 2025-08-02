#!/usr/bin/env python3

import os
import sys
import logging
from dotenv import load_dotenv
from setup_iam_role import setup_iam_role
from setup_opensearch import setup_opensearch
from src.core.configure_agents import SRECopilotAgentConfigurator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main setup function for SRE Copilot."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Step 1: Set up IAM roles
        logger.info("Setting up IAM roles...")
        setup_iam_role()
        
        # Step 2: Set up OpenSearch Serverless
        logger.info("Setting up OpenSearch Serverless...")
        collection_id = setup_opensearch()
        
        # Step 3: Configure Bedrock agents
        logger.info("Configuring Bedrock agents...")
        configurator = SRECopilotAgentConfigurator()
        configurator.configure_agents()
        
        logger.info("SRE Copilot setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 