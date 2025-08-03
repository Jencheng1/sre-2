"""
Extensible MCP Configuration Management System
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

@dataclass
class MCPServerConfig:
    name: str
    type: str
    endpoint: str
    auth: Dict[str, str]
    enabled: bool = True
    test_mode: bool = True
    timeout: int = 30
    retry_count: int = 3
    custom_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_headers is None:
            self.custom_headers = {}


class MCPConfigManager:
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), 'mcp_config.json'
        )
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default MCP configuration"""
        default_config = {
            "mcp_servers": {
                "splunk": {
                    "name": "splunk",
                    "type": "rest_api",
                    "endpoint": "http://localhost:8080/splunk",
                    "auth": {
                        "type": "bearer",
                        "token": "test_token_splunk"
                    },
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3
                },
                "dynatrace": {
                    "name": "dynatrace",
                    "type": "rest_api",
                    "endpoint": "http://localhost:8081/dynatrace",
                    "auth": {
                        "type": "api_token",
                        "token": "test_token_dynatrace"
                    },
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3
                },
                "servicenow": {
                    "name": "servicenow",
                    "type": "rest_api",
                    "endpoint": "http://localhost:8082/servicenow",
                    "auth": {
                        "type": "basic",
                        "username": "admin",
                        "password": "test_password"
                    },
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3
                },
                "confluence": {
                    "name": "confluence",
                    "type": "rest_api",
                    "endpoint": "http://localhost:8083/confluence",
                    "auth": {
                        "type": "bearer",
                        "token": "test_token_confluence"
                    },
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3
                },
                "gitlab": {
                    "name": "gitlab",
                    "type": "rest_api",
                    "endpoint": "http://localhost:8084/gitlab",
                    "auth": {
                        "type": "private_token",
                        "token": "test_token_gitlab"
                    },
                    "enabled": True,
                    "test_mode": True,
                    "timeout": 30,
                    "retry_count": 3
                }
            },
            "external_data_sources": {},
            "global_settings": {
                "default_timeout": 30,
                "max_retry_count": 5,
                "enable_caching": True,
                "cache_ttl": 300,
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
    
    def get_mcp_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific MCP server"""
        return self.config.get("mcp_servers", {}).get(server_name)
    
    def add_mcp_server(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add or update an MCP server configuration"""
        try:
            # Validate required fields
            required_fields = ["name", "type", "endpoint", "auth"]
            for field in required_fields:
                if field not in server_config:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # Store sensitive data in SSM Parameter Store
            if "token" in server_config["auth"]:
                param_name = f"/sre-copilot/mcp/{server_config['name']}/token"
                self._store_secret(param_name, server_config["auth"]["token"])
                server_config["auth"]["token"] = f"ssm:{param_name}"
            
            # Add to configuration
            if "mcp_servers" not in self.config:
                self.config["mcp_servers"] = {}
                
            self.config["mcp_servers"][server_config["name"]] = server_config
            self.save_config()
            
            return {
                "success": True,
                "message": f"MCP server '{server_config['name']}' added successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def remove_mcp_server(self, server_name: str) -> Dict[str, Any]:
        """Remove an MCP server configuration"""
        if server_name in self.config.get("mcp_servers", {}):
            del self.config["mcp_servers"][server_name]
            self.save_config()
            
            # Clean up SSM parameters
            param_name = f"/sre-copilot/mcp/{server_name}/token"
            self._delete_secret(param_name)
            
            return {
                "success": True,
                "message": f"MCP server '{server_name}' removed"
            }
        else:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not found"
            }
    
    def enable_mcp_server(self, server_name: str, enabled: bool = True) -> Dict[str, Any]:
        """Enable or disable an MCP server"""
        if server_name in self.config.get("mcp_servers", {}):
            self.config["mcp_servers"][server_name]["enabled"] = enabled
            self.save_config()
            
            status = "enabled" if enabled else "disabled"
            return {
                "success": True,
                "message": f"MCP server '{server_name}' {status}"
            }
        else:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not found"
            }
    
    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled MCP servers"""
        enabled = []
        for name, config in self.config.get("mcp_servers", {}).items():
            if config.get("enabled", True):
                enabled.append(name)
        return enabled
    
    def add_external_data_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add an external data source configuration"""
        try:
            name = source_config.get("name")
            if not name:
                return {
                    "success": False,
                    "error": "Data source name is required"
                }
            
            if "external_data_sources" not in self.config:
                self.config["external_data_sources"] = {}
                
            self.config["external_data_sources"][name] = source_config
            self.save_config()
            
            return {
                "success": True,
                "message": f"External data source '{name}' added"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_auth_headers(self, server_name: str) -> Dict[str, str]:
        """Get authentication headers for an MCP server"""
        server_config = self.get_mcp_config(server_name)
        if not server_config:
            return {}
        
        auth = server_config.get("auth", {})
        auth_type = auth.get("type", "")
        headers = {}
        
        if auth_type == "bearer":
            token = self._resolve_secret(auth.get("token", ""))
            headers["Authorization"] = f"Bearer {token}"
            
        elif auth_type == "api_token":
            token = self._resolve_secret(auth.get("token", ""))
            headers["X-API-Token"] = token
            
        elif auth_type == "private_token":
            token = self._resolve_secret(auth.get("token", ""))
            headers["PRIVATE-TOKEN"] = token
            
        elif auth_type == "basic":
            username = auth.get("username", "")
            password = self._resolve_secret(auth.get("password", ""))
            import base64
            creds = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        
        # Add custom headers
        custom_headers = server_config.get("custom_headers", {})
        headers.update(custom_headers)
        
        return headers
    
    def _store_secret(self, param_name: str, value: str):
        """Store secret in SSM Parameter Store"""
        try:
            self.ssm.put_parameter(
                Name=param_name,
                Value=value,
                Type='SecureString',
                Overwrite=True
            )
        except Exception as e:
            print(f"Error storing secret: {e}")
    
    def _delete_secret(self, param_name: str):
        """Delete secret from SSM Parameter Store"""
        try:
            self.ssm.delete_parameter(Name=param_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ParameterNotFound':
                print(f"Error deleting secret: {e}")
    
    def _resolve_secret(self, value: str) -> str:
        """Resolve secret from SSM if needed"""
        if value.startswith("ssm:"):
            param_name = value[4:]
            try:
                response = self.ssm.get_parameter(
                    Name=param_name,
                    WithDecryption=True
                )
                return response['Parameter']['Value']
            except Exception as e:
                print(f"Error resolving secret: {e}")
                return value
        return value
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate the entire configuration"""
        issues = []
        
        # Check MCP servers
        for name, config in self.config.get("mcp_servers", {}).items():
            # Check endpoint format
            endpoint = config.get("endpoint", "")
            if not endpoint.startswith(("http://", "https://")):
                issues.append(f"{name}: Invalid endpoint format")
            
            # Check auth configuration
            auth = config.get("auth", {})
            if not auth.get("type"):
                issues.append(f"{name}: Missing auth type")
        
        # Check global settings
        global_settings = self.config.get("global_settings", {})
        if global_settings.get("default_timeout", 30) > 300:
            issues.append("Global: Timeout too high (>300s)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration (optionally without secrets)"""
        export = json.loads(json.dumps(self.config))  # Deep copy
        
        if not include_secrets:
            # Remove sensitive data
            for server in export.get("mcp_servers", {}).values():
                auth = server.get("auth", {})
                if "token" in auth:
                    auth["token"] = "***REDACTED***"
                if "password" in auth:
                    auth["password"] = "***REDACTED***"
        
        return export
    
    def import_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import configuration from external source"""
        try:
            # Validate before importing
            # Basic validation - you can expand this
            if "mcp_servers" not in config_data:
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