#!/bin/bash

echo "Configuring Grafana CloudWatch datasource..."

# Get instance credentials
ROLE_CREDENTIALS=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/intelligentmq-ec2-role)

if [ -z "$ROLE_CREDENTIALS" ]; then
    echo "Error: Unable to get EC2 instance credentials"
    exit 1
fi

# Parse credentials
ACCESS_KEY=$(echo $ROLE_CREDENTIALS | jq -r '.AccessKeyId')
SECRET_KEY=$(echo $ROLE_CREDENTIALS | jq -r '.SecretAccessKey')
SESSION_TOKEN=$(echo $ROLE_CREDENTIALS | jq -r '.Token')

# Wait for Grafana to be ready
echo "Waiting for Grafana to be ready..."
until curl -s http://localhost:3000/api/health > /dev/null; do
    sleep 2
done

# Configure CloudWatch datasource using Grafana API
echo "Configuring CloudWatch datasource..."

# First, delete existing CloudWatch datasource if it exists
curl -s -X GET \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  http://localhost:3000/api/datasources/name/CloudWatch > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "Deleting existing CloudWatch datasource..."
    curl -s -X DELETE \
      -H "Content-Type: application/json" \
      -u admin:admin123 \
      http://localhost:3000/api/datasources/name/CloudWatch
fi

# Create new CloudWatch datasource
DATASOURCE_PAYLOAD=$(cat <<EOF
{
  "name": "CloudWatch",
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
EOF
)

RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d "${DATASOURCE_PAYLOAD}" \
  http://localhost:3000/api/datasources)

echo "CloudWatch datasource response: $RESPONSE"

# Test the datasource
echo "Testing CloudWatch datasource..."
DS_ID=$(echo $RESPONSE | jq -r '.id')

if [ "$DS_ID" != "null" ] && [ ! -z "$DS_ID" ]; then
    TEST_RESPONSE=$(curl -s -X POST \
      -H "Content-Type: application/json" \
      -u admin:admin123 \
      http://localhost:3000/api/datasources/${DS_ID}/health)
    
    echo "Test response: $TEST_RESPONSE"
fi

# Import the dashboard
echo "Importing EC2 CPU monitoring dashboard..."

# Read the dashboard JSON
DASHBOARD_JSON=$(cat /home/ec2-user/sre/sre_mcp/grafana/dashboards/ec2-cpu-monitoring.json)

# Create import payload
IMPORT_PAYLOAD=$(cat <<EOF
{
  "dashboard": ${DASHBOARD_JSON},
  "overwrite": true,
  "inputs": [
    {
      "name": "DS_CLOUDWATCH",
      "type": "datasource",
      "pluginId": "cloudwatch",
      "value": "CloudWatch"
    },
    {
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    }
  ]
}
EOF
)

IMPORT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d "${IMPORT_PAYLOAD}" \
  http://localhost:3000/api/dashboards/import)

echo "Dashboard import response: $IMPORT_RESPONSE"

echo ""
echo "Configuration complete!"
echo "Access Grafana at: http://localhost:3000"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "EC2 CPU Monitoring dashboard should now be available"