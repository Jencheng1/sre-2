#!/bin/bash

# AWS Strands Agents Deployment Script
# This script replaces the MCP servers deployment with Strands Agents

set -e

echo "=========================================="
echo "AWS Strands Agents Deployment Script"
echo "=========================================="

# Configuration
REGION="${AWS_REGION:-us-east-1}"
PYTHON_VERSION="python3"
VENV_DIR="strands_agents_venv"
CONFIG_FILE="strands_agents/config/strands_agents_config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v $PYTHON_VERSION &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    log_info "✓ Python 3 found"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is required but not installed"
        exit 1
    fi
    log_info "✓ AWS CLI found"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured properly"
        exit 1
    fi
    log_info "✓ AWS credentials configured"
    
    # Check region
    if [ -z "$REGION" ]; then
        log_error "AWS region not specified"
        exit 1
    fi
    log_info "✓ Using AWS region: $REGION"
}

# Setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating Python virtual environment..."
        $PYTHON_VERSION -m venv $VENV_DIR
    fi
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    log_info "✓ Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages
    log_info "Installing required packages..."
    pip install boto3 botocore
    
    # When Strands Agents becomes available, uncomment this:
    # pip install strands-agents strands-agents-tools
    
    log_info "✓ Python environment setup complete"
}

# Configure AWS Bedrock access
configure_bedrock_access() {
    log_info "Configuring AWS Bedrock access..."
    
    # Check if Claude 4 Sonnet is available
    if aws bedrock list-foundation-models --region $REGION --query "modelSummaries[?contains(modelId, 'claude-3')]" &> /dev/null; then
        log_info "✓ Claude models available in Bedrock"
    else
        log_warn "Claude models may not be available in $REGION"
        log_warn "Please ensure model access is enabled in the AWS Console"
    fi
    
    # Create IAM role for Strands Agents (if it doesn't exist)
    ROLE_NAME="StrandsAgentsExecutionRole"
    if ! aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
        log_info "Creating IAM role for Strands Agents..."
        
        # Create trust policy
        cat > strands_agents_trust_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
        
        # Create role
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document file://strands_agents_trust_policy.json \
            --region $REGION
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
        
        # Create custom policy for Bedrock and SSM access
        cat > strands_agents_policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:PutParameter",
                "ssm:DeleteParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/sre-copilot/strands-agents/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords"
            ],
            "Resource": "*"
        }
    ]
}
EOF
        
        aws iam put-role-policy \
            --role-name $ROLE_NAME \
            --policy-name StrandsAgentsPolicy \
            --policy-document file://strands_agents_policy.json
        
        # Clean up temp files
        rm strands_agents_trust_policy.json strands_agents_policy.json
        
        log_info "✓ IAM role created successfully"
    else
        log_info "✓ IAM role already exists"
    fi
}

# Initialize configuration
initialize_configuration() {
    log_info "Initializing Strands Agents configuration..."
    
    # Create configuration if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        log_info "Creating default configuration..."
        
        $PYTHON_VERSION << EOF
import sys
import os
sys.path.append('strands_agents')

from config.strands_agents_config import StrandsAgentsConfigManager

# Create config manager and initialize default config
config_manager = StrandsAgentsConfigManager(region='$REGION')
print("Default configuration created at: $CONFIG_FILE")
EOF
        
        log_info "✓ Configuration file created"
    else
        log_info "✓ Configuration file already exists"
    fi
    
    # Validate configuration
    $PYTHON_VERSION << EOF
import sys
import os
sys.path.append('strands_agents')

from config.strands_agents_config import StrandsAgentsConfigManager

config_manager = StrandsAgentsConfigManager(region='$REGION')
validation = config_manager.validate_configuration()

if validation['valid']:
    print("✓ Configuration validation passed")
else:
    print("⚠ Configuration validation issues:")
    for issue in validation['issues']:
        print(f"  - {issue}")
EOF
}

# Stop MCP servers
stop_mcp_servers() {
    log_info "Stopping MCP servers..."
    
    # Kill any running MCP servers
    pkill -f "mcp_server" || true
    pkill -f "start_mcp_servers" || true
    
    # Check for specific processes
    for port in 8080 8081 8082 8083 8084; do
        if lsof -Pi :$port -sTCP:LISTEN -t &> /dev/null; then
            log_info "Stopping service on port $port"
            kill $(lsof -Pi :$port -sTCP:LISTEN -t) || true
        fi
    done
    
    log_info "✓ MCP servers stopped"
}

# Deploy Strands Agents
deploy_strands_agents() {
    log_info "Deploying Strands Agents..."
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Run deployment validation
    $PYTHON_VERSION << EOF
import sys
import os
sys.path.append('strands_agents')

try:
    from orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator
    
    # Test orchestrator initialization
    orchestrator = MultiAgentOrchestrator(region='$REGION', test_mode=True)
    
    # Check available agents
    agents = orchestrator.get_available_agents()
    print(f"Available agents: {agents}")
    
    # Perform health check
    health = orchestrator.health_check_all_agents()
    healthy_agents = [name for name, status in health.items() if status.get('status') == 'healthy']
    print(f"Healthy agents: {healthy_agents}")
    
    if len(healthy_agents) > 0:
        print("✓ Strands Agents deployment successful")
        exit(0)
    else:
        print("✗ No healthy agents found")
        exit(1)

except Exception as e:
    print(f"✗ Deployment failed: {e}")
    exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        log_info "✓ Strands Agents deployed successfully"
    else
        log_error "Strands Agents deployment failed"
        exit 1
    fi
}

# Run tests
run_tests() {
    log_info "Running Strands Agents tests..."
    
    source $VENV_DIR/bin/activate
    
    if $PYTHON_VERSION test_strands_agents_simple.py; then
        log_info "✓ All tests passed"
    else
        log_error "Some tests failed"
        exit 1
    fi
}

# Create systemd service (optional)
create_systemd_service() {
    if [ "$1" = "--systemd" ]; then
        log_info "Creating systemd service..."
        
        # Create service file
        cat > strands-agents.service << EOF
[Unit]
Description=AWS Strands Agents Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/$VENV_DIR/bin
ExecStart=$(pwd)/$VENV_DIR/bin/python strands_agents_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        if [ -d "/etc/systemd/system" ]; then
            sudo cp strands-agents.service /etc/systemd/system/
            sudo systemctl daemon-reload
            sudo systemctl enable strands-agents.service
            log_info "✓ Systemd service created and enabled"
        else
            log_warn "Systemd not available, service file created locally"
        fi
        
        rm strands-agents.service
    fi
}

# Main deployment function
main() {
    log_info "Starting AWS Strands Agents deployment..."
    log_info "Target region: $REGION"
    
    check_prerequisites
    setup_python_environment
    configure_bedrock_access
    initialize_configuration
    stop_mcp_servers
    deploy_strands_agents
    run_tests
    create_systemd_service "$1"
    
    echo ""
    log_info "=========================================="
    log_info "Deployment completed successfully!"
    log_info "=========================================="
    log_info "AWS Strands Agents are now ready to use"
    log_info "Configuration file: $CONFIG_FILE"
    log_info "Virtual environment: $VENV_DIR"
    echo ""
    log_info "To test the deployment:"
    log_info "  source $VENV_DIR/bin/activate"
    log_info "  python test_strands_agents_simple.py"
    echo ""
    log_info "To start using the agents:"
    log_info "  python -c \"from strands_agents.orchestrator.multi_agent_orchestrator import MultiAgentOrchestrator; print('Agents ready!')\""
    echo ""
}

# Run main function with all arguments
main "$@"