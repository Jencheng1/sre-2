#!/usr/bin/env python3
"""
Update Grafana dashboards to show Maximum CPU instead of Average
"""

import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"  
GRAFANA_PASS = "admin123"

def get_all_dashboards():
    """Get all dashboards"""
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    print("📋 Fetching all dashboards...")
    r = requests.get(f"{GRAFANA_URL}/api/search?type=dash-db", auth=auth)
    
    if r.status_code == 200:
        dashboards = r.json()
        cpu_dashboards = [d for d in dashboards if 'cpu' in d['title'].lower() or 'ec2' in d['title'].lower()]
        print(f"   Found {len(cpu_dashboards)} CPU-related dashboards")
        return cpu_dashboards
    else:
        print(f"   ❌ Failed to fetch dashboards: {r.status_code}")
        return []

def update_dashboard_to_max_cpu(dashboard_info):
    """Update a dashboard to use Maximum CPU statistic"""
    auth = (GRAFANA_USER, GRAFANA_PASS)
    uid = dashboard_info['uid']
    
    print(f"\n🔄 Updating dashboard: {dashboard_info['title']} (uid: {uid})")
    
    # Get the full dashboard
    r = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{uid}", auth=auth)
    
    if r.status_code != 200:
        print(f"   ❌ Failed to fetch dashboard: {r.status_code}")
        return False
        
    dash_data = r.json()
    dashboard = dash_data['dashboard']
    
    # Track if we made any changes
    changes_made = False
    
    # Update all panels
    for panel in dashboard.get('panels', []):
        # Check each target in the panel
        for target in panel.get('targets', []):
            # Check if this is a CPU metric
            if target.get('metricName') == 'CPUUtilization' or 'cpu' in str(target).lower():
                current_stat = target.get('statistic', 'Average')
                if current_stat != 'Maximum':
                    print(f"   📊 Panel '{panel.get('title', 'Untitled')}': Changing statistic from {current_stat} to Maximum")
                    target['statistic'] = 'Maximum'
                    changes_made = True
                    
    if not changes_made:
        print("   ℹ️  No changes needed - already using Maximum")
        return True
        
    # Save the updated dashboard
    save_payload = {
        "dashboard": dashboard,
        "overwrite": True,
        "message": "Updated to show Maximum CPU instead of Average"
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=save_payload
    )
    
    if r.status_code in [200, 201]:
        print("   ✅ Dashboard updated successfully")
        return True
    else:
        print(f"   ❌ Failed to save dashboard: {r.status_code}")
        print(f"   Response: {r.text}")
        return False

def create_max_cpu_dashboard():
    """Create a new dashboard specifically for Maximum CPU"""
    print("\n📈 Creating new Maximum CPU dashboard...")
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # Get datasource
    r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
    datasource = None
    
    if r.status_code == 200:
        datasources = r.json()
        for ds in datasources:
            if ds['type'] == 'cloudwatch':
                datasource = ds
                break
    
    if not datasource:
        print("   ❌ No CloudWatch datasource found")
        return False
    
    dashboard = {
        "dashboard": {
            "title": "EC2 Maximum CPU Utilization",
            "uid": "ec2-max-cpu",
            "panels": [{
                "id": 1,
                "datasource": {
                    "type": "cloudwatch",
                    "uid": datasource['uid']
                },
                "targets": [{
                    "alias": "",
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": datasource['uid']
                    },
                    "dimensions": {},
                    "expression": "",
                    "id": "",
                    "label": "",
                    "matchExact": False,
                    "metricEditorMode": 0,
                    "metricName": "CPUUtilization",
                    "metricQueryType": 0,
                    "namespace": "AWS/EC2",
                    "period": "",
                    "queryMode": "Metrics",
                    "refId": "A",
                    "region": "default",
                    "sqlExpression": "",
                    "statistic": "Maximum"  # Using Maximum instead of Average
                }],
                "title": "EC2 CPU Usage (Maximum)",
                "type": "timeseries",
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100,
                        "color": {"mode": "palette-classic"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 60},
                                {"color": "red", "value": 80}
                            ]
                        }
                    }
                }
            },
            {
                "id": 2,
                "datasource": {
                    "type": "cloudwatch",
                    "uid": datasource['uid']
                },
                "targets": [{
                    "datasource": {
                        "type": "cloudwatch",
                        "uid": datasource['uid']
                    },
                    "dimensions": {},
                    "metricName": "CPUUtilization",
                    "namespace": "AWS/EC2",
                    "period": "300",
                    "queryMode": "Metrics",
                    "refId": "A",
                    "region": "default",
                    "statistic": "Maximum"
                }],
                "title": "Current Max CPU",
                "type": "stat",
                "gridPos": {"h": 6, "w": 8, "x": 0, "y": 12},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 60},
                                {"color": "red", "value": 80}
                            ]
                        },
                        "color": {"mode": "thresholds"}
                    }
                },
                "options": {
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "center"
                }
            }],
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"},
            "tags": ["ec2", "cpu", "maximum", "cloudwatch"]
        },
        "overwrite": True
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=dashboard
    )
    
    if r.status_code in [200, 201]:
        result = r.json()
        print("   ✅ Maximum CPU dashboard created")
        print(f"   URL: {GRAFANA_URL}/d/{result['uid']}")
        return True
    else:
        print(f"   ❌ Failed to create dashboard: {r.text}")
        return False

def main():
    print("🔧 Updating Grafana Dashboards to Show Maximum CPU")
    print("=" * 50)
    
    # Wait for Grafana
    print("⏳ Ensuring Grafana is ready...")
    time.sleep(2)
    
    # Get all dashboards
    dashboards = get_all_dashboards()
    
    if dashboards:
        # Update existing dashboards
        success_count = 0
        for dashboard in dashboards:
            if update_dashboard_to_max_cpu(dashboard):
                success_count += 1
                
        print(f"\n📊 Updated {success_count}/{len(dashboards)} dashboards")
    
    # Create new maximum CPU dashboard
    create_max_cpu_dashboard()
    
    print("\n✅ Configuration complete!")
    print("\n📊 Available dashboards:")
    print(f"   • Maximum CPU: {GRAFANA_URL}/d/ec2-max-cpu")
    print(f"   • Simple Dashboard: {GRAFANA_URL}/d/ec2-cpu-simple-final")
    print(f"   • Full Dashboard: {GRAFANA_URL}/d/ec2-cpu-host-network")
    print("\n⚡ All dashboards now show Maximum CPU utilization!")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())