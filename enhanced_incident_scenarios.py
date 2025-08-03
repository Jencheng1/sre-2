"""
Enhanced incident scenarios incorporating MCP service data
These scenarios demonstrate how external data from Splunk, Dynatrace, ServiceNow, 
Confluence, and GitLab enhance root cause analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

class EnhancedIncidentScenarios:
    """Incident scenarios that leverage MCP integrations"""
    
    @staticmethod
    def get_scenarios() -> List[Dict[str, Any]]:
        """Get all enhanced incident scenarios"""
        return [
            EnhancedIncidentScenarios.network_latency_dns_issue(),
            EnhancedIncidentScenarios.mq_backlog_deployment_issue(),
            EnhancedIncidentScenarios.database_connection_pool_exhaustion(),
            EnhancedIncidentScenarios.api_gateway_rate_limiting(),
            EnhancedIncidentScenarios.cross_region_replication_lag(),
            EnhancedIncidentScenarios.container_orchestration_failure(),
            EnhancedIncidentScenarios.cache_invalidation_storm(),
            EnhancedIncidentScenarios.security_group_misconfiguration()
        ]
    
    @staticmethod
    def network_latency_dns_issue() -> Dict[str, Any]:
        """Network latency caused by DNS misconfiguration"""
        return {
            "incident": {
                "id": "INC-2024-001",
                "title": "High Network Latency Affecting Payment Service",
                "type": "network_latency",
                "severity": "high",
                "service": "payment-service",
                "start_time": (datetime.now() - timedelta(hours=2)).isoformat(),
                "symptoms": [
                    "API response times > 5 seconds",
                    "Intermittent timeout errors",
                    "Customer complaints about slow checkout"
                ],
                "aws_data": {
                    "cloudwatch": {
                        "network_latency_p99": "5200ms",
                        "error_rate": "12%",
                        "request_count": "declining"
                    },
                    "route53": {
                        "health_check_failures": 3,
                        "dns_query_time": "2000ms"
                    }
                }
            },
            "mcp_correlations": {
                "splunk": {
                    "finding": "DNS resolution timeouts detected",
                    "evidence": [
                        "Multiple hosts showing DNS lookup times > 2s",
                        "Pattern started after Route53 configuration change",
                        "Affecting multiple availability zones"
                    ],
                    "query": "index=network dns_lookup_time>2000 | stats count by host"
                },
                "dynatrace": {
                    "finding": "Application traces show external service delays",
                    "evidence": [
                        "Payment service waiting on DNS resolution",
                        "Database connection attempts timing out",
                        "No application code changes detected"
                    ]
                },
                "servicenow": {
                    "finding": "Recent DNS configuration change",
                    "evidence": [
                        "CHG0012345: Update Route53 resolver rules",
                        "Implemented 2 hours before incident",
                        "Changed by Network Team"
                    ]
                },
                "confluence": {
                    "kb_article": "DNS Troubleshooting Guide",
                    "relevant_sections": [
                        "Common DNS misconfigurations",
                        "Route53 resolver troubleshooting",
                        "DNS cache poisoning symptoms"
                    ]
                },
                "gitlab": {
                    "finding": "No recent code changes to payment service",
                    "last_deployment": "3 days ago",
                    "relevant_commits": []
                }
            },
            "root_cause": "DNS resolver rules misconfigured during Route53 update, causing recursive lookup loops",
            "resolution": [
                "Revert Route53 resolver rules to previous configuration",
                "Clear DNS caches on affected instances",
                "Implement DNS query monitoring alerts"
            ],
            "prevention": [
                "Add DNS resolution time to standard health checks",
                "Require peer review for Route53 changes",
                "Implement gradual rollout for DNS changes"
            ]
        }
    
    @staticmethod
    def mq_backlog_deployment_issue() -> Dict[str, Any]:
        """Message queue backlog caused by deployment bug"""
        return {
            "incident": {
                "id": "INC-2024-002",
                "title": "Order Processing Queue Backlog Growing",
                "type": "performance_degradation",
                "severity": "high",
                "service": "order-service",
                "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "symptoms": [
                    "Order processing delays > 10 minutes",
                    "MQ depth increasing continuously",
                    "DLQ message count rising"
                ],
                "aws_data": {
                    "sqs": {
                        "queue_depth": 15000,
                        "message_age_max": "45 minutes",
                        "dlq_messages": 250
                    },
                    "ecs": {
                        "task_cpu": "95%",
                        "task_memory": "80%",
                        "task_count": 10
                    }
                }
            },
            "mcp_correlations": {
                "dynatrace": {
                    "finding": "Message processing rate dropped 80%",
                    "evidence": [
                        "Queue consumption rate: 10 msg/sec (was 50 msg/sec)",
                        "Message processing time increased 5x",
                        "Error: 'Invalid message format' appearing in logs"
                    ],
                    "mq_metrics": {
                        "queue_depth_trend": "exponential_growth",
                        "consumer_lag": "increasing",
                        "error_pattern": "schema_validation_failure"
                    }
                },
                "gitlab": {
                    "finding": "Recent commit changed message schema",
                    "evidence": [
                        "Commit: 'Add new required field to order messages'",
                        "Deployed 1 hour ago",
                        "Changed OrderMessage.java schema"
                    ],
                    "problematic_commit": {
                        "sha": "a3f4d5e",
                        "author": "developer@example.com",
                        "message": "Add customer_segment field to orders",
                        "files_changed": ["OrderMessage.java", "OrderProcessor.java"]
                    }
                },
                "servicenow": {
                    "finding": "Emergency change deployed without full testing",
                    "evidence": [
                        "CHG0012346: Add customer segmentation to orders",
                        "Type: Emergency",
                        "Testing: Partial (dev environment only)"
                    ]
                },
                "splunk": {
                    "finding": "Schema validation errors in application logs",
                    "evidence": [
                        "Error rate spike coincides with deployment",
                        "Pattern: 'Required field customer_segment missing'",
                        "Affecting 95% of incoming messages"
                    ]
                },
                "confluence": {
                    "kb_article": "Message Queue Troubleshooting Playbook",
                    "relevant_sections": [
                        "Schema compatibility testing",
                        "Rolling back message processor deployments",
                        "DLQ message recovery procedures"
                    ]
                }
            },
            "root_cause": "Backward-incompatible schema change deployed without updating message producers",
            "resolution": [
                "Rollback order service to previous version",
                "Implement backward-compatible schema change",
                "Reprocess DLQ messages after fix"
            ],
            "prevention": [
                "Enforce backward compatibility for message schemas",
                "Add integration tests for all message consumers",
                "Implement canary deployments for message processors"
            ]
        }
    
    @staticmethod
    def database_connection_pool_exhaustion() -> Dict[str, Any]:
        """Database connection pool exhaustion during peak load"""
        return {
            "incident": {
                "id": "INC-2024-003",
                "title": "Database Connection Pool Exhausted",
                "type": "service_degradation",
                "severity": "critical",
                "service": "user-service",
                "start_time": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "symptoms": [
                    "Connection timeout errors",
                    "Response times > 30 seconds",
                    "Cascading failures in dependent services"
                ],
                "aws_data": {
                    "rds": {
                        "connection_count": 500,
                        "cpu_utilization": "45%",
                        "database_load": "moderate"
                    },
                    "cloudwatch": {
                        "application_errors": "ConnectionPoolExhaustedException",
                        "error_rate": "65%"
                    }
                }
            },
            "mcp_correlations": {
                "dynatrace": {
                    "finding": "Connection leak in user service",
                    "evidence": [
                        "Connections not being released after use",
                        "Thread dump shows 450 waiting threads",
                        "Memory leak pattern detected"
                    ],
                    "code_insights": {
                        "problematic_method": "UserRepository.findUserWithDetails()",
                        "issue": "Transaction not closed in error path",
                        "impact": "Connections leaked on exceptions"
                    }
                },
                "gitlab": {
                    "finding": "Recent refactoring introduced connection leak",
                    "evidence": [
                        "Commit: 'Refactor user repository for performance'",
                        "Changed transaction handling",
                        "Missing finally block for connection cleanup"
                    ],
                    "code_analysis": {
                        "file": "UserRepository.java",
                        "line": 234,
                        "issue": "try-catch without finally for connection.close()"
                    }
                },
                "splunk": {
                    "finding": "Connection pool metrics show steady leak",
                    "evidence": [
                        "Active connections growing without release",
                        "Pattern started after 14:30 deployment",
                        "Idle connections: 0 (unusual)"
                    ]
                },
                "servicenow": {
                    "finding": "Previous incident with similar symptoms",
                    "evidence": [
                        "INC0011234: Connection pool exhaustion (3 months ago)",
                        "Root cause: Missing connection cleanup",
                        "Resolution: Added connection interceptor"
                    ],
                    "historical_context": "Team has seen this pattern before"
                },
                "confluence": {
                    "kb_article": "Database Connection Pool Best Practices",
                    "relevant_sections": [
                        "Common connection leak patterns",
                        "Implementing connection interceptors",
                        "Monitoring pool health metrics"
                    ]
                }
            },
            "root_cause": "Connection leak introduced by refactoring - database connections not released in error scenarios",
            "resolution": [
                "Hot patch to add finally blocks for connection cleanup",
                "Restart affected service instances to clear leaked connections",
                "Increase connection pool size temporarily"
            ],
            "prevention": [
                "Add connection leak detection to CI/CD pipeline",
                "Implement connection pool monitoring alerts",
                "Use try-with-resources for automatic cleanup"
            ]
        }
    
    @staticmethod
    def api_gateway_rate_limiting() -> Dict[str, Any]:
        """API Gateway rate limiting misconfiguration"""
        return {
            "incident": {
                "id": "INC-2024-004",
                "title": "API Gateway Rejecting Valid Requests",
                "type": "availability_issue",
                "severity": "high",
                "service": "api-gateway",
                "start_time": (datetime.now() - timedelta(hours=3)).isoformat(),
                "symptoms": [
                    "429 errors for authenticated users",
                    "Customer complaints about API access",
                    "Partner integrations failing"
                ],
                "aws_data": {
                    "api_gateway": {
                        "throttled_requests": 45000,
                        "4xx_errors": "85%",
                        "request_count": 50000
                    },
                    "waf": {
                        "blocked_requests": 0,
                        "rate_rules_triggered": ["api-burst-limit"]
                    }
                }
            },
            "mcp_correlations": {
                "splunk": {
                    "finding": "Legitimate traffic being rate limited",
                    "evidence": [
                        "Known partner IPs receiving 429 errors",
                        "Rate limit: 10 req/sec (was 1000 req/sec)",
                        "Configuration change at 09:00"
                    ],
                    "affected_clients": [
                        "Partner API Key: pk_live_abc123",
                        "Mobile App Client ID: mobile_prod_v2",
                        "Web Dashboard: admin_console"
                    ]
                },
                "servicenow": {
                    "finding": "Rate limit change part of security update",
                    "evidence": [
                        "CHG0012347: Implement stricter rate limiting",
                        "Reason: Recent DDoS attempt",
                        "Approval: Security team only"
                    ],
                    "change_details": {
                        "implementer": "security-team",
                        "testing": "Security scenarios only",
                        "stakeholder_notification": "None"
                    }
                },
                "dynatrace": {
                    "finding": "API consumers experiencing failures",
                    "evidence": [
                        "Partner service circuit breakers opening",
                        "Mobile app fallback to cached data",
                        "Revenue impact: $10K/hour"
                    ]
                },
                "confluence": {
                    "kb_article": "API Rate Limiting Guidelines",
                    "relevant_sections": [
                        "Rate limit sizing for different client types",
                        "Gradual rate limit rollout process",
                        "Emergency rate limit rollback procedure"
                    ],
                    "missing_step": "Stakeholder notification before changes"
                },
                "gitlab": {
                    "finding": "Rate limit configuration in IaC",
                    "evidence": [
                        "terraform/api-gateway/rate-limits.tf changed",
                        "Previous value: 1000, New value: 10",
                        "No load testing in PR"
                    ]
                }
            },
            "root_cause": "API rate limits reduced by 100x without considering legitimate traffic patterns",
            "resolution": [
                "Immediately increase rate limits to 500 req/sec",
                "Whitelist known partner API keys",
                "Implement graduated rate limits by client type"
            ],
            "prevention": [
                "Require traffic analysis before rate limit changes",
                "Implement rate limit changes gradually",
                "Add integration tests for partner APIs"
            ]
        }
    
    @staticmethod
    def cross_region_replication_lag() -> Dict[str, Any]:
        """Cross-region replication lag causing data inconsistency"""
        return {
            "incident": {
                "id": "INC-2024-005",
                "title": "Cross-Region Data Inconsistency",
                "type": "data_consistency",
                "severity": "high",
                "service": "inventory-service",
                "start_time": (datetime.now() - timedelta(hours=4)).isoformat(),
                "symptoms": [
                    "Inventory counts differ between regions",
                    "Orders failing due to stock availability",
                    "Replication lag > 5 minutes"
                ],
                "aws_data": {
                    "dynamodb": {
                        "replication_lag": "5-10 minutes",
                        "pending_writes": 50000,
                        "throttled_requests": 1200
                    },
                    "cloudwatch": {
                        "cross_region_latency": "250ms",
                        "packet_loss": "0.5%"
                    }
                }
            },
            "mcp_correlations": {
                "splunk": {
                    "finding": "Network latency spike between regions",
                    "evidence": [
                        "us-east-1 to eu-west-1 latency: 250ms (normally 80ms)",
                        "Started after network maintenance window",
                        "Affecting multiple AWS services"
                    ],
                    "network_analysis": {
                        "affected_path": "us-east-1 -> eu-west-1",
                        "latency_increase": "3x normal",
                        "bandwidth_utilization": "85%"
                    }
                },
                "dynatrace": {
                    "finding": "Database write throughput exceeding capacity",
                    "evidence": [
                        "Write capacity consumed: 95%",
                        "Burst capacity exhausted",
                        "Auto-scaling not keeping up with demand"
                    ]
                },
                "servicenow": {
                    "finding": "Network maintenance in progress",
                    "evidence": [
                        "CHG0012348: Transatlantic cable maintenance",
                        "Expected impact: Minor latency increase",
                        "Actual impact: Major latency spike"
                    ]
                },
                "gitlab": {
                    "finding": "Recent code change increased write volume",
                    "evidence": [
                        "Commit: 'Add detailed audit logging'",
                        "Each transaction now generates 5x more writes",
                        "Deployed yesterday to all regions"
                    ],
                    "code_impact": {
                        "write_amplification": "5x",
                        "affected_tables": ["inventory", "audit_log"],
                        "batch_writing": "disabled"
                    }
                },
                "confluence": {
                    "kb_article": "DynamoDB Global Tables Best Practices",
                    "relevant_sections": [
                        "Capacity planning for global tables",
                        "Handling replication lag",
                        "Write shaping strategies"
                    ]
                }
            },
            "root_cause": "Combination of network maintenance latency and increased write volume overwhelming replication capacity",
            "resolution": [
                "Increase DynamoDB write capacity in all regions",
                "Enable batch writing for audit logs",
                "Implement write throttling for non-critical updates"
            ],
            "prevention": [
                "Model write capacity needs before deploying write-heavy features",
                "Implement write batching by default",
                "Monitor replication lag metrics with tighter thresholds"
            ]
        }
    
    @staticmethod
    def container_orchestration_failure() -> Dict[str, Any]:
        """Container orchestration failure causing service disruption"""
        return {
            "incident": {
                "id": "INC-2024-006",
                "title": "ECS Tasks Failing to Start",
                "type": "service_outage",
                "severity": "critical",
                "service": "recommendation-engine",
                "start_time": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "symptoms": [
                    "New deployments failing",
                    "Auto-scaling not working",
                    "Service operating at 40% capacity"
                ],
                "aws_data": {
                    "ecs": {
                        "failed_task_launches": 150,
                        "running_tasks": 4,
                        "desired_tasks": 10,
                        "error": "ResourceInitializationError"
                    },
                    "ecr": {
                        "image_pulls_failed": 150,
                        "error": "403 Forbidden"
                    }
                }
            },
            "mcp_correlations": {
                "splunk": {
                    "finding": "ECR authentication failures",
                    "evidence": [
                        "Error: 'ECR GetAuthorizationToken failed'",
                        "IAM role authentication failing",
                        "Started after IAM policy update"
                    ]
                },
                "servicenow": {
                    "finding": "IAM policy change this morning",
                    "evidence": [
                        "CHG0012349: Tighten IAM policies for compliance",
                        "Modified ECS task execution role",
                        "Removed ecr:GetAuthorizationToken permission"
                    ],
                    "change_impact": {
                        "intended": "Remove unused permissions",
                        "actual": "Broke ECR authentication"
                    }
                },
                "gitlab": {
                    "finding": "Terraform shows IAM policy changes",
                    "evidence": [
                        "iam/policies/ecs-task-execution.tf modified",
                        "Removed ECR permissions deemed 'unused'",
                        "PR approved by security team only"
                    ]
                },
                "dynatrace": {
                    "finding": "Service degradation cascade",
                    "evidence": [
                        "Recommendation API response time: 5s",
                        "Fallback to default recommendations",
                        "User engagement dropped 30%"
                    ]
                },
                "confluence": {
                    "kb_article": "ECS Task Launch Failures",
                    "relevant_sections": [
                        "Common IAM permission issues",
                        "ECR authentication requirements",
                        "Testing IAM changes before production"
                    ]
                }
            },
            "root_cause": "IAM policy change removed required ECR permissions from ECS task execution role",
            "resolution": [
                "Add ecr:GetAuthorizationToken back to task execution role",
                "Add ecr:BatchCheckLayerAvailability and ecr:GetDownloadUrlForLayer",
                "Force new deployment to refresh tasks"
            ],
            "prevention": [
                "Test IAM changes in staging environment",
                "Use AWS IAM Policy Simulator before applying changes",
                "Require ops team review for IAM changes affecting ECS"
            ]
        }
    
    @staticmethod
    def cache_invalidation_storm() -> Dict[str, Any]:
        """Cache invalidation storm causing database overload"""
        return {
            "incident": {
                "id": "INC-2024-007",
                "title": "Cache Invalidation Storm Overloading Database",
                "type": "performance_degradation",
                "severity": "high",
                "service": "product-catalog",
                "start_time": (datetime.now() - timedelta(hours=1)).isoformat(),
                "symptoms": [
                    "Database CPU at 100%",
                    "Cache hit rate dropped to 5%",
                    "Page load times > 10 seconds"
                ],
                "aws_data": {
                    "elasticache": {
                        "evicted_keys": 2000000,
                        "hit_rate": "5%",
                        "memory_usage": "95%"
                    },
                    "rds": {
                        "cpu_utilization": "100%",
                        "read_iops": 50000,
                        "connection_count": 450
                    }
                }
            },
            "mcp_correlations": {
                "dynatrace": {
                    "finding": "Cascading cache invalidations",
                    "evidence": [
                        "Single product update triggering full category flush",
                        "Category flush triggering homepage flush",
                        "2M cache keys invalidated in 5 minutes"
                    ],
                    "cache_analysis": {
                        "invalidation_pattern": "cascading",
                        "trigger": "product.price.update",
                        "affected_keys": ["product:*", "category:*", "homepage:*"]
                    }
                },
                "gitlab": {
                    "finding": "Cache invalidation logic changed",
                    "evidence": [
                        "Commit: 'Ensure cache consistency on updates'",
                        "Added aggressive invalidation strategy",
                        "Invalidates entire hierarchy on any change"
                    ],
                    "code_change": {
                        "file": "CacheInvalidationService.java",
                        "method": "invalidateRelatedKeys()",
                        "issue": "Recursive invalidation without limits"
                    }
                },
                "splunk": {
                    "finding": "Bulk product import triggered storm",
                    "evidence": [
                        "10,000 product updates in 2 minutes",
                        "Each update invalidating 200 cache keys",
                        "Total invalidations: 2M keys"
                    ]
                },
                "servicenow": {
                    "finding": "Bulk import not flagged as high risk",
                    "evidence": [
                        "REQ0012350: Bulk update product prices",
                        "No performance impact assessment",
                        "Executed during peak hours"
                    ]
                },
                "confluence": {
                    "kb_article": "Cache Invalidation Strategies",
                    "relevant_sections": [
                        "Avoiding invalidation storms",
                        "Lazy invalidation patterns",
                        "Cache warming strategies"
                    ]
                }
            },
            "root_cause": "Overly aggressive cache invalidation logic combined with bulk update caused invalidation storm",
            "resolution": [
                "Implement cache invalidation rate limiting",
                "Switch to lazy invalidation for non-critical updates",
                "Warm critical caches after storm subsides"
            ],
            "prevention": [
                "Implement cache invalidation queuing",
                "Add circuit breaker for cascade prevention",
                "Schedule bulk updates during maintenance windows"
            ]
        }
    
    @staticmethod
    def security_group_misconfiguration() -> Dict[str, Any]:
        """Security group misconfiguration blocking legitimate traffic"""
        return {
            "incident": {
                "id": "INC-2024-008",
                "title": "Security Group Blocking Internal Service Communication",
                "type": "connectivity_issue",
                "severity": "critical",
                "service": "authentication-service",
                "start_time": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "symptoms": [
                    "Internal services cannot reach auth service",
                    "Health checks failing",
                    "Complete authentication outage"
                ],
                "aws_data": {
                    "vpc_flow_logs": {
                        "rejected_connections": 50000,
                        "source_ips": ["10.0.1.0/24", "10.0.2.0/24"],
                        "destination_port": 8443
                    },
                    "alb": {
                        "unhealthy_targets": 10,
                        "health_check_failures": "connection refused"
                    }
                }
            },
            "mcp_correlations": {
                "splunk": {
                    "finding": "Security group rule removed",
                    "evidence": [
                        "VPC Flow Logs show REJECT for port 8443",
                        "Source: Internal subnets",
                        "Started at 14:15 UTC"
                    ],
                    "flow_analysis": {
                        "rejected_flows": 50000,
                        "pattern": "Internal->AuthService:8443",
                        "action": "REJECT"
                    }
                },
                "servicenow": {
                    "finding": "Security group cleanup change",
                    "evidence": [
                        "CHG0012351: Remove unused security group rules",
                        "Automated cleanup script run",
                        "Marked port 8443 as 'unused'"
                    ],
                    "automation_issue": {
                        "script": "sg_cleanup.py",
                        "logic_flaw": "Only checked external traffic",
                        "missed": "Internal service mesh traffic"
                    }
                },
                "gitlab": {
                    "finding": "Automated SG cleanup script flawed",
                    "evidence": [
                        "scripts/security/sg_cleanup.py",
                        "Only analyzes CloudTrail for usage",
                        "Misses VPC-internal traffic"
                    ],
                    "script_analysis": {
                        "detection_method": "CloudTrail API calls only",
                        "missing": "VPC Flow Logs analysis",
                        "false_positive": "Internal-only services"
                    }
                },
                "dynatrace": {
                    "finding": "Complete service mesh failure",
                    "evidence": [
                        "All services reporting auth failures",
                        "Circuit breakers open across fleet",
                        "Business impact: Complete outage"
                    ]
                },
                "confluence": {
                    "kb_article": "Security Group Management Best Practices",
                    "relevant_sections": [
                        "Analyzing rule usage before removal",
                        "Testing SG changes in staging",
                        "Emergency SG rollback procedures"
                    ],
                    "key_point": "Always analyze VPC Flow Logs for internal traffic"
                }
            },
            "root_cause": "Automated security group cleanup script incorrectly identified internal service port as unused",
            "resolution": [
                "Immediately restore security group rule for port 8443",
                "Allow 10.0.0.0/16 -> auth-service-sg:8443",
                "Restart ALB health checks"
            ],
            "prevention": [
                "Include VPC Flow Logs in usage analysis",
                "Require manual approval for SG changes affecting production",
                "Test security group changes in staging first"
            ]
        }
    
    @staticmethod
    def generate_test_scenario(scenario_type: str = None) -> Dict[str, Any]:
        """Generate a test scenario with MCP data"""
        scenarios = EnhancedIncidentScenarios.get_scenarios()
        
        if scenario_type:
            # Find specific scenario type
            for scenario in scenarios:
                if scenario["incident"]["type"] == scenario_type:
                    return scenario
        
        # Return first scenario as default
        return scenarios[0]