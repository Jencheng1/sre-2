#!/usr/bin/env python3
"""
Create Change Records in Systems Manager and Display in Grafana
Demonstrates change management integration with correlation capabilities
"""

import boto3
import json
import requests
from datetime import datetime, timedelta
import uuid

class ChangeManagementDemo:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.instance_id = "i-02bef13982a179478"  # SRE-DEMO
        
        # Grafana configuration
        self.grafana_url = "http://localhost:3000"
        self.grafana_user = "admin"
        self.grafana_pass = "admin123"
        
    def create_change_record(self, change_details):
        """Create a change record in SSM OpsCenter"""
        print(f"\n📋 Creating Change Record: {change_details['title']}")
        
        response = self.ssm_client.create_ops_item(
            Title=f"[CHANGE] {change_details['title']}",
            Description=change_details['description'],
            Source="Change Management System",
            Severity=change_details.get('severity', '3'),
            Category="Availability",
            OperationalData={
                'ChangeRequestId': {'Value': change_details['change_id'], 'Type': 'String'},
                'ChangeType': {'Value': change_details['type'], 'Type': 'String'},
                'Risk': {'Value': change_details['risk'], 'Type': 'String'},
                'Environment': {'Value': change_details['environment'], 'Type': 'String'},
                'DeploymentTime': {'Value': change_details['deployment_time'], 'Type': 'String'},
                'ApprovedBy': {'Value': change_details.get('approved_by', 'CAB'), 'Type': 'String'},
                'ImplementedBy': {'Value': change_details.get('implemented_by', 'DevOps Team'), 'Type': 'String'},
                'RollbackPlan': {'Value': change_details.get('rollback_plan', 'Revert to previous version'), 'Type': 'String'},
                'TestingStatus': {'Value': change_details.get('testing_status', 'Passed'), 'Type': 'String'},
                'AffectedServices': {'Value': json.dumps(change_details.get('affected_services', [])), 'Type': 'String'},
                'GitCommit': {'Value': change_details.get('git_commit', 'N/A'), 'Type': 'String'},
                'JIRA': {'Value': change_details.get('jira', 'N/A'), 'Type': 'String'}
            },
            Tags=[
                {'Key': 'ChangeType', 'Value': change_details['type']},
                {'Key': 'Environment', 'Value': change_details['environment']},
                {'Key': 'Risk', 'Value': change_details['risk']}
            ]
        )
        
        ops_item_id = response['OpsItemId']
        print(f"✅ Created Change Record: {ops_item_id}")
        
        # Push change event to CloudWatch as custom metric
        self.push_change_metrics(change_details, ops_item_id)
        
        return ops_item_id
        
    def push_change_metrics(self, change_details, ops_item_id):
        """Push change events as CloudWatch metrics for Grafana visualization"""
        print("📊 Pushing change metrics to CloudWatch...")
        
        # Create custom metrics for change tracking
        metric_data = [
            {
                'MetricName': 'ChangeEvent',
                'Value': 1,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'ChangeType', 'Value': change_details['type']},
                    {'Name': 'Risk', 'Value': change_details['risk']},
                    {'Name': 'Environment', 'Value': change_details['environment']},
                    {'Name': 'ChangeId', 'Value': change_details['change_id']}
                ]
            },
            {
                'MetricName': 'ChangeRiskScore',
                'Value': {'Low': 1, 'Medium': 5, 'High': 10}.get(change_details['risk'], 1),
                'Unit': 'None',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'ChangeId', 'Value': change_details['change_id']},
                    {'Name': 'Service', 'Value': change_details.get('service', 'payment-service')}
                ]
            }
        ]
        
        # Add deployment duration metric if available
        if 'deployment_duration' in change_details:
            metric_data.append({
                'MetricName': 'DeploymentDuration',
                'Value': change_details['deployment_duration'],
                'Unit': 'Seconds',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': 'ChangeType', 'Value': change_details['type']},
                    {'Name': 'Service', 'Value': change_details.get('service', 'payment-service')}
                ]
            })
            
        self.cloudwatch_client.put_metric_data(
            Namespace='ChangeManagement',
            MetricData=metric_data
        )
        
        print("✅ Change metrics pushed to CloudWatch")
        
    def create_grafana_change_dashboard(self):
        """Create Grafana dashboard for change management visualization"""
        print("\n📊 Creating Change Management Dashboard in Grafana...")
        
        auth = (self.grafana_user, self.grafana_pass)
        
        # Get CloudWatch datasource
        r = requests.get(f"{self.grafana_url}/api/datasources", auth=auth)
        datasource = None
        
        if r.status_code == 200:
            for ds in r.json():
                if ds['type'] == 'cloudwatch':
                    datasource = ds
                    break
                    
        if not datasource:
            print("❌ No CloudWatch datasource found")
            return False
            
        dashboard = {
            "dashboard": {
                "title": "Change Management & Correlation Dashboard",
                "uid": "change-management",
                "tags": ["change", "correlation", "deployment"],
                "timezone": "browser",
                "annotations": {
                    "list": [{
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "enable": True,
                        "hide": False,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Change Events",
                        "target": {
                            "dimensions": {},
                            "metricName": "ChangeEvent",
                            "namespace": "ChangeManagement",
                            "period": "300",
                            "refId": "Anno",
                            "region": "default",
                            "statistic": "Sum"
                        }
                    }]
                },
                "panels": [
                    # Row 1: Change Overview
                    {
                        "id": 1,
                        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                        "type": "stat",
                        "title": "Total Changes (24h)",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "ChangeManagement",
                            "metricName": "ChangeEvent",
                            "dimensions": {},
                            "statistic": "Sum",
                            "period": "86400",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "color": {"mode": "thresholds"},
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 5},
                                        {"color": "red", "value": 10}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                        "type": "piechart",
                        "title": "Changes by Risk Level",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "ChangeManagement",
                                "metricName": "ChangeEvent",
                                "dimensions": {"Risk": "High"},
                                "statistic": "Sum",
                                "period": "86400",
                                "region": "default",
                                "refId": "A",
                                "alias": "High Risk"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "ChangeManagement",
                                "metricName": "ChangeEvent",
                                "dimensions": {"Risk": "Medium"},
                                "statistic": "Sum",
                                "period": "86400",
                                "region": "default",
                                "refId": "B",
                                "alias": "Medium Risk"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "ChangeManagement",
                                "metricName": "ChangeEvent",
                                "dimensions": {"Risk": "Low"},
                                "statistic": "Sum",
                                "period": "86400",
                                "region": "default",
                                "refId": "C",
                                "alias": "Low Risk"
                            }
                        ],
                        "options": {
                            "pieType": "donut",
                            "displayLabels": ["name", "percent"],
                            "legendDisplayMode": "list",
                            "legendPlacement": "right"
                        }
                    },
                    {
                        "id": 3,
                        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                        "type": "bargauge",
                        "title": "Average Deployment Duration",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "ChangeManagement",
                            "metricName": "DeploymentDuration",
                            "dimensions": {},
                            "statistic": "Average",
                            "period": "86400",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "s",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 300},
                                        {"color": "red", "value": 600}
                                    ]
                                }
                            }
                        },
                        "options": {
                            "orientation": "horizontal",
                            "displayMode": "gradient",
                            "showUnfilled": True
                        }
                    },
                    # Row 2: Change Timeline with Correlation
                    {
                        "id": 4,
                        "gridPos": {"h": 10, "w": 24, "x": 0, "y": 8},
                        "type": "timeseries",
                        "title": "Change Events Timeline with Incident Correlation",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "ChangeManagement",
                                "metricName": "ChangeRiskScore",
                                "dimensions": {},
                                "statistic": "Maximum",
                                "period": "300",
                                "region": "default",
                                "refId": "A",
                                "alias": "Change Risk Score"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "AWS/EC2",
                                "metricName": "CPUUtilization",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Maximum",
                                "period": "300",
                                "region": "default",
                                "refId": "B",
                                "alias": "CPU % (Post-Change)"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "JavaApp/SpringBoot",
                                "metricName": "HeapMemoryUsed",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Average",
                                "period": "300",
                                "region": "default",
                                "refId": "C",
                                "alias": "Memory % (Post-Change)"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "lineWidth": 2,
                                    "fillOpacity": 10,
                                    "spanNulls": True,
                                    "showPoints": "auto",
                                    "pointSize": 5
                                }
                            },
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "Change Risk Score"},
                                    "properties": [
                                        {"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}},
                                        {"id": "custom.lineStyle", "value": {"dash": [10, 10], "fill": "dash"}},
                                        {"id": "custom.lineWidth", "value": 3},
                                        {"id": "custom.axisPlacement", "value": "right"}
                                    ]
                                }
                            ]
                        },
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {
                                "showLegend": True,
                                "displayMode": "table",
                                "placement": "bottom",
                                "calcs": ["lastNotNull", "max", "mean"]
                            }
                        }
                    },
                    # Row 3: Change Impact Analysis
                    {
                        "id": 5,
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 18},
                        "type": "table",
                        "title": "Recent Changes with Impact",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "ChangeManagement",
                            "metricName": "ChangeEvent",
                            "dimensions": {},
                            "statistic": "Sum",
                            "period": "3600",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "align": "auto",
                                    "displayMode": "auto"
                                }
                            }
                        }
                    },
                    {
                        "id": 6,
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 18},
                        "type": "heatmap",
                        "title": "Change Frequency Heatmap",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "ChangeManagement",
                            "metricName": "ChangeEvent",
                            "dimensions": {},
                            "statistic": "Sum",
                            "period": "3600",
                            "region": "default",
                            "refId": "A"
                        }],
                        "options": {
                            "calculate": True,
                            "cellGap": 2,
                            "color": {
                                "exponent": 0.5,
                                "fill": "dark-orange",
                                "scheme": "Oranges"
                            },
                            "exemplar": {"color": "rgba(255,0,255,0.7)"},
                            "filterValues": {"le": 1e-9},
                            "rowsFrame": {"layout": "auto"}
                        }
                    }
                ],
                "refresh": "10s",
                "time": {"from": "now-3h", "to": "now"}
            },
            "overwrite": True
        }
        
        # Create the dashboard
        r = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            auth=auth,
            json=dashboard
        )
        
        if r.status_code in [200, 201]:
            result = r.json()
            print(f"✅ Change Management dashboard created")
            print(f"   URL: {self.grafana_url}/d/{result['uid']}")
            return True
        else:
            print(f"❌ Failed to create dashboard: {r.text}")
            return False
            
    def create_demo_changes(self):
        """Create a series of demo change records"""
        print("\n🎭 Creating Demo Change Records...")
        
        demo_changes = [
            {
                'title': 'Deploy payment-service v2.1.0 with cache optimization',
                'description': 'Implementing new caching layer for payment processing to improve performance',
                'type': 'Application Update',
                'risk': 'Medium',
                'environment': 'Production',
                'change_id': f'CHG-{datetime.now().strftime("%Y%m%d")}-001',
                'deployment_time': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'service': 'payment-service',
                'git_commit': 'a7b3c4d5e6f7890abcdef1234567890abcdef123',
                'jira': 'PAY-1234',
                'approved_by': 'jane.smith@company.com',
                'implemented_by': 'john.doe@company.com',
                'affected_services': ['payment-service', 'transaction-processor'],
                'deployment_duration': 300,
                'rollback_plan': 'Revert deployment using blue-green switch'
            },
            {
                'title': 'Update EC2 instance security groups',
                'description': 'Adding new IP ranges for partner integration',
                'type': 'Infrastructure Change',
                'risk': 'Low',
                'environment': 'Production',
                'change_id': f'CHG-{datetime.now().strftime("%Y%m%d")}-002',
                'deployment_time': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'service': 'infrastructure',
                'approved_by': 'security-team@company.com',
                'affected_services': ['all-services'],
                'deployment_duration': 120
            },
            {
                'title': 'Database schema migration for performance',
                'description': 'Adding indexes and partitioning for transaction table',
                'type': 'Database Change',
                'risk': 'High',
                'environment': 'Production',
                'change_id': f'CHG-{datetime.now().strftime("%Y%m%d")}-003',
                'deployment_time': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'service': 'database',
                'jira': 'DB-5678',
                'approved_by': 'dba-team@company.com',
                'affected_services': ['payment-service', 'reporting-service'],
                'deployment_duration': 1800,
                'rollback_plan': 'Restore from backup taken before migration'
            }
        ]
        
        created_changes = []
        for change in demo_changes:
            ops_item_id = self.create_change_record(change)
            created_changes.append({
                'ops_item_id': ops_item_id,
                'change_id': change['change_id'],
                'title': change['title']
            })
            
        return created_changes

def main():
    """Run the change management demo"""
    print("🚀 Change Management Demo with Grafana Integration")
    print("=" * 60)
    
    demo = ChangeManagementDemo()
    
    # Step 1: Create Grafana dashboard
    if demo.create_grafana_change_dashboard():
        print("\n✅ Change Management dashboard ready!")
        
        # Step 2: Create demo change records
        changes = demo.create_demo_changes()
        
        print("\n📊 Demo Summary:")
        print("=" * 60)
        print(f"Created {len(changes)} change records:")
        for change in changes:
            print(f"  - {change['change_id']}: {change['title']}")
            print(f"    OpsItem: {change['ops_item_id']}")
            
        print("\n🔗 Integration Points:")
        print("1. Change records created in AWS Systems Manager OpsCenter")
        print("2. Change metrics pushed to CloudWatch")
        print("3. Grafana dashboard shows change timeline")
        print("4. Correlation with CPU/Memory metrics enabled")
        
        print("\n📊 View in Grafana:")
        print(f"   Change Dashboard: {demo.grafana_url}/d/change-management")
        print(f"   Java Monitoring: {demo.grafana_url}/d/java-app-monitoring")
        
        print("\n🎯 Next Steps:")
        print("1. Run the memory leak test:")
        print("   python3 java_memory_leak_test_case.py")
        print("2. View correlation in Streamlit CPU Spike Demo")
        print("3. Check Grafana to see change events aligned with incidents")
        
        print("\n💡 The dashboard shows:")
        print("   - Change events as annotations on the timeline")
        print("   - Risk score correlation with system metrics")
        print("   - Change frequency heatmap")
        print("   - Impact analysis table")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())