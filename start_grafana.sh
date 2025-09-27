#!/bin/bash

echo "Starting Grafana and monitoring stack..."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Start only Grafana, Prometheus and node-exporter
docker-compose up -d grafana prometheus node-exporter

# Wait for Grafana to start
echo "Waiting for Grafana to start..."
sleep 10

# Check status
docker-compose ps

echo ""
echo "Grafana is available at: http://localhost:3000"
echo "Default credentials: admin/admin123"
echo ""
echo "Prometheus is available at: http://localhost:9090"