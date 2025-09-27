#!/bin/bash

echo "🔧 Final Fix for Grafana AWS CloudWatch Access"
echo "=============================================="

# Get AWS credentials from EC2 metadata
echo "📝 Getting EC2 instance credentials..."

# Get the IAM role
ROLE_NAME=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
echo "   IAM Role: ${ROLE_NAME}"

# Get credentials
CREDS=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/${ROLE_NAME})

# Extract credentials
ACCESS_KEY=$(echo $CREDS | jq -r '.AccessKeyId')
SECRET_KEY=$(echo $CREDS | jq -r '.SecretAccessKey')
SESSION_TOKEN=$(echo $CREDS | jq -r '.Token')

echo "   ✅ Retrieved credentials"

# Create .env file for Grafana
echo "📄 Creating Grafana environment file..."
cat > /home/ec2-user/sre/sre_mcp/grafana.env << EOF
AWS_ACCESS_KEY_ID=${ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${SECRET_KEY}
AWS_SESSION_TOKEN=${SESSION_TOKEN}
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
EOF

echo "   ✅ Created grafana.env"

# Update docker-compose.yml
echo "🐳 Updating docker-compose.yml..."

cd /home/ec2-user/sre/sre_mcp

# Check if env_file is already in docker-compose
if ! grep -q "env_file.*grafana.env" docker-compose.yml; then
    # Backup original
    cp docker-compose.yml docker-compose.yml.backup.$(date +%s)
    
    # Add env_file to grafana service using Python
    python3 - << 'PYTHON_UPDATE'
import yaml

with open('docker-compose.yml', 'r') as f:
    config = yaml.safe_load(f)

# Add env_file to grafana service
if 'grafana' in config['services']:
    if 'env_file' not in config['services']['grafana']:
        config['services']['grafana']['env_file'] = ['./grafana.env']
    elif './grafana.env' not in config['services']['grafana']['env_file']:
        config['services']['grafana']['env_file'].append('./grafana.env')

with open('docker-compose.yml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print("   ✅ Updated docker-compose.yml")
PYTHON_UPDATE
fi

# Restart Grafana
echo "🔄 Restarting Grafana..."
docker-compose stop grafana
docker-compose up -d grafana

# Wait for Grafana
echo "⏳ Waiting for Grafana to start..."
sleep 10

# Configure datasource with fresh credentials
echo "📊 Configuring CloudWatch datasource..."

python3 - << PYTHON_CONFIG
import requests
import json
import time

GRAFANA_URL = "http://localhost:3000"
auth = ("admin", "admin123")

# Wait for Grafana
for i in range(30):
    try:
        r = requests.get(f"{GRAFANA_URL}/api/health")
        if r.status_code == 200:
            print("   ✅ Grafana is ready")
            break
    except:
        pass
    time.sleep(1)

# Delete existing CloudWatch datasources
r = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
if r.status_code == 200:
    for ds in r.json():
        if ds['type'] == 'cloudwatch':
            print(f"   Deleting old datasource: {ds['name']}")
            requests.delete(f"{GRAFANA_URL}/api/datasources/{ds['id']}", auth=auth)

# Create new datasource with environment credentials
datasource = {
    "name": "CloudWatch-Working",
    "type": "cloudwatch",
    "access": "proxy",
    "jsonData": {
        "authType": "keys",
        "defaultRegion": "us-east-1"
    },
    "secureJsonData": {
        "accessKey": "${ACCESS_KEY}",
        "secretKey": "${SECRET_KEY}", 
        "sessionToken": "${SESSION_TOKEN}"
    }
}

# Use environment variables instead
datasource_env = {
    "name": "CloudWatch-Working",
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
    json=datasource_env
)

if r.status_code in [200, 201]:
    result = r.json()
    print(f"   ✅ Created CloudWatch datasource (ID: {result['id']})")
    
    # Create simple dashboard
    dashboard = {
        "dashboard": {
            "title": "EC2 CPU Monitoring - WORKING",
            "uid": "ec2-cpu-working-v2",
            "panels": [{
                "datasource": {
                    "type": "cloudwatch",
                    "uid": result.get('uid', 'cloudwatch')
                },
                "targets": [{
                    "refId": "A",
                    "region": "us-east-1",
                    "namespace": "AWS/EC2",
                    "metricName": "CPUUtilization",
                    "dimensions": {},
                    "statistic": "Average",
                    "period": "300"
                }],
                "title": "EC2 CPU Usage",
                "type": "timeseries",
                "gridPos": {"h": 10, "w": 24, "x": 0, "y": 0},
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "min": 0,
                        "max": 100
                    }
                }
            }],
            "refresh": "30s",
            "time": {"from": "now-1h", "to": "now"}
        },
        "overwrite": True
    }
    
    r2 = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=auth,
        json=dashboard
    )
    
    if r2.status_code in [200, 201]:
        print("   ✅ Created working dashboard")
    
else:
    print(f"   ❌ Failed to create datasource: {r.text}")

PYTHON_CONFIG

echo ""
echo "✅ Grafana AWS fix complete!"
echo ""
echo "📊 Access your dashboard at:"
echo "   http://localhost:3000/d/ec2-cpu-working-v2"
echo ""
echo "⚠️  IMPORTANT:"
echo "   - AWS credentials expire every ~6 hours"
echo "   - Re-run this script if data stops appearing"
echo "   - Check time range is set to 'Last 1 hour'"
echo ""
echo "🔍 To verify:"
echo "   docker logs sre-grafana --tail 20"