"""
Configuration management for AWS Strands Agents
Replaces MCP configuration with Strands-specific settings
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

@dataclass
class StrandsAgentConfig:
    """Configuration for a single Strands agent"""
    name: str
    model: str
    region: str
    enabled: bool = True
    test_mode: bool = True
    timeout: int = 30
    retry_count: int = 3
    custom_parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_parameters is None:
            self.custom_parameters = {}

class StrandsAgentsConfigManager:
    """Configuration manager for AWS Strands Agents"""
    
    def __init__(self, config_file: str = None, region: str = "us-east-1"):
        self.region = region
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), 'strands_agents_config.json'
        )
        self.ssm = boto3.client('ssm', region_name=region)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default Strands agents configuration"""
        default_config = {
            "strands_agents": {
                "splunk": {
                    "name": "splunk",
                    "model": "claude-4-sonnet",
                    "region": self.region,
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "custom_parameters": {
                        "default_time_range": "-1h",
                        "max_search_results": 100,
                        "enable_real_time": False
                    }
                },
                "dynatrace": {
                    "name": "dynatrace", 
                    "model": "claude-4-sonnet",
                    "region": self.region,
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3,
                    "custom_parameters": {
                        "default_time_range": "-30m",
                        "include_traces": True,
                        "trace_duration_threshold": 1000
                    }
                }
            },
            "orchestrator": {
                "enabled": True,
                "max_parallel_agents": 5,
                "session_timeout": 3600,
                "enable_correlation": True,
                "confidence_threshold": 70.0
            },
            "aws_settings": {
                "region": self.region,
                "bedrock_model": "claude-4-sonnet",
                "enable_xray": True,
                "enable_cloudwatch_logs": True,
                "parameter_store_prefix": "/sre-copilot/strands-agents"
            },
            "security": {
                "enable_iam_roles": True,
                "enable_vpc_endpoints": True,
                "encrypt_parameters": True,
                "log_level": "INFO"
            }
        }
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
            
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_agent_config(self, agent_name: str) -> Optional[StrandsAgentConfig]:
        """Get configuration for a specific agent"""
        agent_data = self.config.get("strands_agents", {}).get(agent_name)
        if agent_data:
            return StrandsAgentConfig(**agent_data)
        return None
    
    def add_agent_config(self, agent_config: StrandsAgentConfig) -> Dict[str, Any]:
        """Add or update an agent configuration"""
        try:
            if "strands_agents" not in self.config:
                self.config["strands_agents"] = {}
            
            self.config["strands_agents"][agent_config.name] = asdict(agent_config)
            self.save_config()
            
            return {
                "success": True,
                "message": f"Agent '{agent_config.name}' configuration saved"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def remove_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Remove an agent configuration"""
        if agent_name in self.config.get("strands_agents", {}):
            del self.config["strands_agents"][agent_name]
            self.save_config()
            
            return {
                "success": True,
                "message": f"Agent '{agent_name}' configuration removed"
            }
        else:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found"
            }
    
    def enable_agent(self, agent_name: str, enabled: bool = True) -> Dict[str, Any]:
        """Enable or disable an agent"""
        if agent_name in self.config.get("strands_agents", {}):
            self.config["strands_agents"][agent_name]["enabled"] = enabled
            self.save_config()
            
            status = "enabled" if enabled else "disabled"
            return {
                "success": True,
                "message": f"Agent '{agent_name}' {status}"
            }
        else:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found"
            }
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agents"""
        enabled = []
        for name, config in self.config.get("strands_agents", {}).items():
            if config.get("enabled", True):
                enabled.append(name)
        return enabled
    
    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Get orchestrator configuration"""
        return self.config.get("orchestrator", {})
    
    def update_orchestrator_config(self, orchestrator_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update orchestrator configuration"""
        try:
            self.config["orchestrator"] = {**self.config.get("orchestrator", {}), **orchestrator_config}
            self.save_config()
            
            return {
                "success": True,
                "message": "Orchestrator configuration updated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_aws_settings(self) -> Dict[str, Any]:
        """Get AWS-specific settings"""
        return self.config.get("aws_settings", {})
    
    def store_secret(self, parameter_name: str, value: str, agent_name: str = None) -> bool:
        """Store secret in AWS Systems Manager Parameter Store"""
        try:
            if not parameter_name.startswith('/'):
                prefix = self.config.get("aws_settings", {}).get("parameter_store_prefix", "/sre-copilot/strands-agents")
                if agent_name:
                    parameter_name = f"{prefix}/{agent_name}/{parameter_name}"
                else:
                    parameter_name = f"{prefix}/{parameter_name}"
            
            self.ssm.put_parameter(
                Name=parameter_name,
                Value=value,
                Type='SecureString',
                Overwrite=True
            )
            return True
            
        except Exception as e:
            print(f"Error storing secret: {e}")
            return False
    
    def get_secret(self, parameter_name: str, agent_name: str = None) -> Optional[str]:
        """Retrieve secret from AWS Systems Manager Parameter Store"""
        try:
            if not parameter_name.startswith('/'):
                prefix = self.config.get("aws_settings", {}).get("parameter_store_prefix", "/sre-copilot/strands-agents")
                if agent_name:
                    parameter_name = f"{prefix}/{agent_name}/{parameter_name}"
                else:
                    parameter_name = f"{prefix}/{parameter_name}"
            
            response = self.ssm.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            return response['Parameter']['Value']
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'ParameterNotFound':
                print(f"Error retrieving secret: {e}")
            return None
        except Exception as e:
            print(f"Error retrieving secret: {e}")
            return None
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the entire configuration"""
        issues = []
        
        # Check AWS settings
        aws_settings = self.get_aws_settings()
        if not aws_settings.get("region"):
            issues.append("AWS region not specified")
        
        if not aws_settings.get("bedrock_model"):
            issues.append("Bedrock model not specified")
        
        # Check agent configurations
        for name, config in self.config.get("strands_agents", {}).items():
            if not config.get("model"):
                issues.append(f"Agent '{name}': Model not specified")
            
            if not config.get("region"):
                issues.append(f"Agent '{name}': Region not specified")
        
        # Check orchestrator configuration
        orchestrator = self.get_orchestrator_config()
        if orchestrator.get("max_parallel_agents", 0) > 10:
            issues.append("Orchestrator: Max parallel agents too high (>10)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration for backup or migration"""
        export = json.loads(json.dumps(self.config))  # Deep copy
        
        if not include_secrets:
            # Remove any sensitive data markers
            for agent_name, agent_config in export.get("strands_agents", {}).items():
                custom_params = agent_config.get("custom_parameters", {})
                for key, value in custom_params.items():
                    if "token" in key.lower() or "secret" in key.lower():
                        custom_params[key] = "***REDACTED***"
        
        return export
    
    def import_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import configuration from external source"""
        try:
            # Validate before importing
            if "strands_agents" not in config_data:
                return {
                    "success": False,
                    "error": "Invalid configuration format"
                }
            
            self.config = config_data
            self.save_config()
            
            return {
                "success": True,
                "message": "Configuration imported successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }