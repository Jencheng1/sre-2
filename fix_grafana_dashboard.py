#!/usr/bin/env python3
"""Fix Grafana EC2 CPU dashboard to show data properly"""

import requests
import json
import time
import boto3

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def get_cloudwatch_datasource_uid():
    """Get the UID of the CloudWatch datasource"""
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                return ds['uid']
    return None

def get_prometheus_datasource_uid():
    """Get the UID of the Prometheus datasource"""
    response = requests.get(
        f"{GRAFANA_URL}/api/datasources",
        auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds['type'] == 'prometheus':
                return ds['uid']
    return None

def create_fixed_dashboard():
    """Create a properly configured EC2 CPU dashboard"""
    
    cloudwatch_uid = get_cloudwatch_datasource_uid()
    prometheus_uid = get_prometheus_datasource_uid()
    
    if not cloudwatch_uid:
        print("❌ CloudWatch datasource not found!")
        return False
        
    print(f"✓ Found CloudWatch datasource: {cloudwatch_uid}")
    print(f"✓ Found Prometheus datasource: {prometheus_uid}")
    
    # Get EC2 instances
    ec2 = boto3.client('ec2', region_name='us-east-1')
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            name = next((tag['Value'] for tag in instance.get('Tags', []) 
                        if tag['Key'] == 'Name'), instance['InstanceId'])
            instances.append({
                'id': instance['InstanceId'],
                'name': name
            })
    
    print(f"✓ Found {len(instances)} running instances")
    
    # Create dashboard JSON with proper configuration
    dashboard_json = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [
            {
                "datasource": {
                    "type": "cloudwatch",
                    "uid": cloudwatch_uid
                },
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisCenteredZero": False,
                            "axisColorMode": "text",
                            "axisLabel": "CPU %",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 20,
                            "gradientMode": "none",
                            "hideFrom": {
                                "tooltip": False,
                                "viz": False,
                                "legend": False
                            },
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "pointSize": 5,
                            "scaleDistribution": {
                                "type": "linear"
                            },
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {
                                "group": "A",
                                "mode": "none"
                            },
                            "thresholdsStyle": {
                                "mode": "line"
                            }
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "yellow", 
                                    "value": 60
                                },
                                {
                                    "color": "red",
                                    "value": 80
                                }
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 10,
                    "w": 24,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "legend": {
                        "calcs": ["mean", "max", "lastNotNull"],
                        "displayMode": "table",
                        "placement": "bottom",
                        "showLegend": True
                    },
                    "tooltip": {
                        "mode": "multi",
                        "sort": "none"
                    }
                },
                "pluginVersion": "9.5.2",
                "targets": [
                    {
                        "alias": "",
                        "datasource": {
                            "type": "cloudwatch",
                            "uid": cloudwatch_uid
                        },
                        "dimensions": {},
                        "expression": "",
                        "id": "",
                        "label": "${PROP('Dim.InstanceId')}",
                        "matchExact": False,
                        "metricEditorMode": 0,
                        "metricName": "CPUUtilization",
                        "metricQueryType": 0,
                        "namespace": "AWS/EC2",
                        "period": "300",
                        "queryMode": "Metrics",
                        "refId": "A",
                        "region": "us-east-1",
                        "sqlExpression": "",
                        "statistic": "Average"
                    }
                ],
                "title": "EC2 CPU Utilization - All Instances",
                "type": "timeseries"
            }
        ],
        "refresh": "10s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["ec2", "cpu", "monitoring"],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-30m",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "",
        "title": "EC2 CPU Monitoring - Fixed",
        "uid": "ec2-cpu-monitoring-fixed",
        "version": 1,
        "weekStart": ""
    }
    
    # Add individual instance gauge panels
    row_y = 10
    for i, instance in enumerate(instances):
        panel = {
            "datasource": {
                "type": "cloudwatch",
                "uid": cloudwatch_uid
            },
            "fieldConfig": {
                "defaults": {
                    "color": {
                        "mode": "thresholds"
                    },
                    "mappings": [],
                    "max": 100,
                    "min": 0,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {
                                "color": "green",
                                "value": None
                            },
                            {
                                "color": "yellow",
                                "value": 60
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                        ]
                    },
                    "unit": "percent"
                },
                "overrides": []
            },
            "gridPos": {
                "h": 8,
                "w": 12,
                "x": (i % 2) * 12,
                "y": row_y + (i // 2) * 8
            },
            "id": i + 2,
            "options": {
                "orientation": "auto",
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                },
                "showThresholdLabels": False,
                "showThresholdMarkers": True,
                "text": {}
            },
            "pluginVersion": "9.5.2",
            "targets": [
                {
                    "alias": instance['name'],
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": cloudwatch_uid
                    },
                    "dimensions": {
                        "InstanceId": instance['id']
                    },
                    "expression": "",
                    "id": "",
                    "matchExact": True,
                    "metricEditorMode": 0,
                    "metricName": "CPUUtilization",
                    "metricQueryType": 0,
                    "namespace": "AWS/EC2",
                    "period": "300",
                    "queryMode": "Metrics",
                    "refId": "A",
                    "region": "us-east-1",
                    "sqlExpression": "",
                    "statistic": "Average"
                }
            ],
            "title": f"{instance['name']} CPU",
            "type": "gauge"
        }
        dashboard_json["panels"].append(panel)
    
    # Add Node Exporter panel at the bottom
    if prometheus_uid:
        node_panel = {
            "datasource": {
                "type": "prometheus",
                "uid": prometheus_uid
            },
            "fieldConfig": {
                "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "barAlignment": 0,
                        "drawStyle": "line",
                        "fillOpacity": 10,
                        "gradientMode": "none",
                        "hideFrom": {
                            "tooltip": False,
                            "viz": False,
                            "legend": False
                        },
                        "insertNulls": False,
                        "lineInterpolation": "linear",
                        "lineWidth": 1,
                        "pointSize": 5,
                        "scaleDistribution": {
                            "type": "linear"
                        },
                        "showPoints": "never",
                        "spanNulls": False,
                        "stacking": {
                            "group": "A",
                            "mode": "none"
                        },
                        "thresholdsStyle": {
                            "mode": "off"
                        }
                    },
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {
                                "color": "green",
                                "value": None
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                        ]
                    },
                    "unit": "percent"
                },
                "overrides": []
            },
            "gridPos": {
                "h": 8,
                "w": 24,
                "x": 0,
                "y": row_y + ((len(instances) + 1) // 2) * 8
            },
            "id": len(instances) + 2,
            "options": {
                "legend": {
                    "calcs": [],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                },
                "tooltip": {
                    "mode": "single",
                    "sort": "none"
                }
            },
            "pluginVersion": "9.5.2",
            "targets": [
                {
                    "datasource": {
                        "type": "prometheus",
                        "uid": prometheus_uid
                    },
                    "editorMode": "code",
                    "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) by (instance) * 100)",
                    "legendFormat": "{{instance}}",
                    "range": True,
                    "refId": "A"
                }
            ],
            "title": "Node Exporter CPU Usage (Local)",
            "type": "timeseries"
        }
        dashboard_json["panels"].append(node_panel)
    
    # Delete existing dashboard if it exists
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/ec2-cpu-monitoring-fixed",
            auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        if response.status_code == 200:
            print("✓ Deleting existing dashboard...")
            delete_response = requests.delete(
                f"{GRAFANA_URL}/api/dashboards/uid/ec2-cpu-monitoring-fixed",
                auth=(GRAFANA_USER, GRAFANA_PASS)
            )
    except:
        pass
    
    # Create the dashboard
    create_payload = {
        "dashboard": dashboard_json,
        "overwrite": True,
        "message": "Fixed EC2 CPU monitoring dashboard"
    }
    
    response = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps(create_payload)
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("✅ Dashboard created successfully!")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}/{result['slug']}")
        return True
    else:
        print(f"❌ Failed to create dashboard: {response.text}")
        return False

def test_cloudwatch_connection():
    """Test if CloudWatch datasource is working"""
    print("\n🔍 Testing CloudWatch datasource...")
    
    cloudwatch_uid = get_cloudwatch_datasource_uid()
    if not cloudwatch_uid:
        print("❌ CloudWatch datasource not found!")
        return False
    
    # Test the datasource
    response = requests.post(
        f"{GRAFANA_URL}/api/datasources/proxy/{cloudwatch_uid}/",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "queries": [{
                "refId": "A",
                "region": "us-east-1",
                "namespace": "AWS/EC2",
                "metricName": "CPUUtilization",
                "dimensions": {},
                "statistics": ["Average"],
                "period": "300"
            }]
        })
    )
    
    print(f"   Datasource test response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Response: {response.text}")
    
    return response.status_code == 200

def main():
    print("🔧 Fixing Grafana EC2 CPU Dashboard")
    print("=" * 50)
    
    # Test CloudWatch connection
    test_cloudwatch_connection()
    
    # Create fixed dashboard
    if create_fixed_dashboard():
        print("\n✅ Dashboard fix complete!")
        print("\nNext steps:")
        print("1. Go to Grafana: http://localhost:3000")
        print("2. Navigate to 'EC2 CPU Monitoring - Fixed' dashboard")
        print("3. Verify CPU metrics are displaying for all EC2 instances")
    else:
        print("\n❌ Dashboard fix failed!")

if __name__ == "__main__":
    main()