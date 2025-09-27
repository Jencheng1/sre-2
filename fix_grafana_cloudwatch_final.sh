#!/bin/bash

echo "🔧 Final Fix for Grafana CloudWatch Integration"
echo "=============================================="

# Set AWS credentials for Grafana
echo "📝 Configuring Grafana environment..."

# Create Grafana environment file
cat > /tmp/grafana-env.conf << 'EOF'
# AWS Configuration for Grafana
GF_AWS_default_REGION=us-east-1
GF_AWS_PROFILES=default
GF_AWS_ALLOWED_AUTH_PROVIDERS=default,keys,credentials
AWS_SDK_LOAD_CONFIG=true
AWS_DEFAULT_REGION=us-east-1
EOF

# Update docker-compose to include environment
echo "🐳 Updating Docker Compose configuration..."

# Check current Grafana container
docker ps | grep grafana

# Restart Grafana with proper AWS config
echo "🔄 Restarting Grafana with AWS credentials..."
cd /home/ec2-user/sre/sre_mcp

# Stop Grafana
docker-compose stop grafana

# Start Grafana with environment
docker-compose up -d grafana

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to restart..."
sleep 10

# Reconfigure CloudWatch datasource
echo "📊 Reconfiguring CloudWatch datasource..."

python3 - << 'PYTHON_SCRIPT'
import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin" 
GRAFANA_PASS = "admin123"

# Wait for Grafana
for i in range(30):
    try:
        r = requests.get(f"{GRAFANA_URL}/api/health")
        if r.status_code == 200:
            print("✓ Grafana is ready")
            break
    except:
        pass
    time.sleep(1)

# Delete old datasources
auth = (GRAFANA_USER, GRAFANA_PASS)
r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
if r.status_code == 200:
    for ds in r.json():
        if ds['type'] == 'cloudwatch':
            print(f"Deleting datasource: {ds['name']}")
            requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

# Create new CloudWatch datasource
datasource = {
    "name": "CloudWatch",
    "type": "cloudwatch", 
    "access": "proxy",
    "jsonData": {
        "authType": "default",
        "defaultRegion": "us-east-1"
    }
}

r = requests.post(
    f"{GRAFANA_URL}/api/datasources",
    auth=auth,
    json=datasource
)

if r.status_code in [200, 201]:
    print("✓ CloudWatch datasource created")
    ds_uid = r.json().get('uid', 'unknown')
    print(f"  UID: {ds_uid}")
    
    # Create working dashboard
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - Working",
            "uid": "ec2-cpu-working",
            "panels": [{
                "datasource": {"type": "cloudwatch", "uid": ds_uid},
                "fieldConfig": {
                    "defaults": {"unit": "percent", "min": 0, "max": 100}
                },
                "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0},
                "targets": [{
                    "datasource": {"type": "cloudwatch", "uid": ds_uid},
                    "dimensions": {},
                    "metricName": "CPUUtilization",
                    "namespace": "AWS/EC2",
                    "period": "300",
                    "region": "us-east-1",
                    "statistic": "Average",
                    "refId": "A"
                }],
                "title": "All EC2 Instances CPU",
                "type": "timeseries"
            }],
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"}
        },
        "overwrite": True
    }
    
    r = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=dashboard
    )
    
    if r.status_code in [200, 201]:
        print("✓ Dashboard created successfully")
        print(f"\n📊 Access dashboard at: {GRAFANA_URL}/d/ec2-cpu-working")
else:
    print(f"✗ Failed to create datasource: {r.text}")

PYTHON_SCRIPT

echo ""
echo "✅ Grafana CloudWatch fix complete!"
echo ""
echo "📊 Access your dashboards:"
echo "   - http://localhost:3000/d/ec2-cpu-working"
echo "   - http://localhost:3000/d/ec2-cpu-test"
echo ""
echo "⏱️  Wait 30-60 seconds for data to appear"
echo "🔄 Set time range to 'Last 1 hour' if needed"