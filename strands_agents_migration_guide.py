#!/usr/bin/env python3
"""
Migration Guide and Utility for moving from MCP to AWS Strands Agents
This script helps migrate existing MCP configurations and provides migration utilities
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

def load_mcp_config() -> Optional[Dict[str, Any]]:
    """Load existing MCP configuration"""
    mcp_config_paths = [
        "config/mcp_config.json",
        "mcp_config.json",
        "src/mcp_config.json"
    ]
    
    for path in mcp_config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading MCP config from {path}: {e}")
                continue
    
    return None

def migrate_mcp_to_strands_config(mcp_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MCP configuration to Strands Agents configuration"""
    strands_config = {
        "strands_agents": {},
        "orchestrator": {
            "enabled": True,
            "max_parallel_agents": 5,
            "session_timeout": 3600,
            "enable_correlation": True,
            "confidence_threshold": 70.0
        },
        "aws_settings": {
            "region": "us-east-1",
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
    
    # Map MCP servers to Strands agents
    mcp_to_strands_mapping = {
        "splunk": "splunk",
        "dynatrace": "dynatrace",
        "servicenow": "servicenow", 
        "confluence": "confluence",
        "gitlab": "gitlab"
    }
    
    mcp_servers = mcp_config.get("mcp_servers", {})
    
    for mcp_name, mcp_server_config in mcp_servers.items():
        if mcp_name in mcp_to_strands_mapping:
            strands_name = mcp_to_strands_mapping[mcp_name]
            
            # Convert MCP server config to Strands agent config
            strands_agent_config = {
                "name": strands_name,
                "model": "claude-4-sonnet",
                "region": "us-east-1",
                "enabled": mcp_server_config.get("enabled", True),
                "test_mode": mcp_server_config.get("test_mode", True),
                "timeout": mcp_server_config.get("timeout", 30),
                "retry_count": mcp_server_config.get("retry_count", 3),
                "custom_parameters": {}
            }
            
            # Map specific parameters
            if strands_name == "splunk":
                strands_agent_config["custom_parameters"] = {
                    "default_time_range": "-1h",
                    "max_search_results": 100,
                    "enable_real_time": False
                }
            elif strands_name == "dynatrace":
                strands_agent_config["custom_parameters"] = {
                    "default_time_range": "-30m",
                    "include_traces": True,
                    "trace_duration_threshold": 1000
                }
            
            strands_config["strands_agents"][strands_name] = strands_agent_config
    
    return strands_config

def generate_migration_report(mcp_config: Dict[str, Any], strands_config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a migration report comparing MCP and Strands configurations"""
    report = {
        "migration_timestamp": datetime.now().isoformat(),
        "source": "MCP Servers",
        "target": "AWS Strands Agents",
        "summary": {
            "mcp_servers_found": len(mcp_config.get("mcp_servers", {})),
            "strands_agents_created": len(strands_config.get("strands_agents", {})),
            "migration_success": True
        },
        "mappings": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Document server mappings
    mcp_servers = mcp_config.get("mcp_servers", {})
    strands_agents = strands_config.get("strands_agents", {})
    
    for mcp_name, mcp_server in mcp_servers.items():
        if mcp_name in strands_agents:
            report["mappings"].append({
                "mcp_server": mcp_name,
                "strands_agent": mcp_name,
                "endpoint_before": mcp_server.get("endpoint", "N/A"),
                "model_after": strands_agents[mcp_name].get("model", "N/A"),
                "status": "migrated"
            })
        else:
            report["mappings"].append({
                "mcp_server": mcp_name,
                "strands_agent": None,
                "status": "not_migrated"
            })
            report["warnings"].append(f"MCP server '{mcp_name}' could not be migrated - no Strands agent equivalent")
    
    # Add recommendations
    recommendations = [
        "Test all agents after migration to ensure functionality",
        "Update client code to use Strands Agents orchestrator instead of direct MCP calls",
        "Configure AWS Bedrock model access for production use",
        "Set up proper IAM roles and policies for security",
        "Enable CloudWatch logging and X-Ray tracing for observability",
        "Store sensitive credentials in AWS Systems Manager Parameter Store"
    ]
    
    report["recommendations"] = recommendations
    
    return report

def create_migration_checklist() -> List[str]:
    """Create a migration checklist for manual verification"""
    return [
        "☐ Backup existing MCP configuration files",
        "☐ Stop all running MCP servers",
        "☐ Install AWS Strands Agents framework",
        "☐ Configure AWS credentials and region",
        "☐ Enable Claude 4 Sonnet access in AWS Bedrock",
        "☐ Run migration script to convert configuration",
        "☐ Validate new Strands configuration",
        "☐ Test individual agents functionality",
        "☐ Test multi-agent orchestration",
        "☐ Update application code to use new agents",
        "☐ Deploy to staging environment first",
        "☐ Run comprehensive tests",
        "☐ Monitor performance and errors",
        "☐ Deploy to production environment",
        "☐ Update documentation and runbooks",
        "☐ Train team on new Strands Agents system"
    ]

def main():
    parser = argparse.ArgumentParser(description="Migrate from MCP to AWS Strands Agents")
    parser.add_argument("--mcp-config", help="Path to MCP configuration file")
    parser.add_argument("--output", default="strands_agents_migrated_config.json", 
                       help="Output file for Strands configuration")
    parser.add_argument("--report", default="migration_report.json",
                       help="Migration report output file")
    parser.add_argument("--checklist", action="store_true",
                       help="Display migration checklist")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MCP TO AWS STRANDS AGENTS MIGRATION UTILITY")
    print("=" * 60)
    
    if args.checklist:
        print("\nMIGRATION CHECKLIST:")
        print("-" * 30)
        for item in create_migration_checklist():
            print(item)
        return
    
    # Load MCP configuration
    print("Loading MCP configuration...")
    if args.mcp_config:
        try:
            with open(args.mcp_config, 'r') as f:
                mcp_config = json.load(f)
            print(f"✓ Loaded MCP config from: {args.mcp_config}")
        except Exception as e:
            print(f"✗ Failed to load MCP config: {e}")
            return
    else:
        mcp_config = load_mcp_config()
        if not mcp_config:
            print("✗ No MCP configuration found")
            print("Please specify --mcp-config path or ensure config file exists")
            return
        print("✓ Found and loaded MCP configuration")
    
    # Convert to Strands configuration
    print("\nConverting to Strands Agents configuration...")
    strands_config = migrate_mcp_to_strands_config(mcp_config)
    
    # Save Strands configuration
    try:
        with open(args.output, 'w') as f:
            json.dump(strands_config, f, indent=2)
        print(f"✓ Strands configuration saved to: {args.output}")
    except Exception as e:
        print(f"✗ Failed to save Strands config: {e}")
        return
    
    # Generate migration report
    print("\nGenerating migration report...")
    report = generate_migration_report(mcp_config, strands_config)
    
    try:
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Migration report saved to: {args.report}")
    except Exception as e:
        print(f"✗ Failed to save report: {e}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"MCP Servers Found: {report['summary']['mcp_servers_found']}")
    print(f"Strands Agents Created: {report['summary']['strands_agents_created']}")
    
    if report['warnings']:
        print("\nWarnings:")
        for warning in report['warnings']:
            print(f"  ⚠ {warning}")
    
    print("\nNext Steps:")
    print("1. Review the generated Strands configuration file")
    print("2. Run deployment script: ./deploy_strands_agents.sh") 
    print("3. Test the new agents: python test_strands_agents_simple.py")
    print("4. Update your application code to use the new orchestrator")
    
    print(f"\nFor detailed information, check: {args.report}")

if __name__ == "__main__":
    main()