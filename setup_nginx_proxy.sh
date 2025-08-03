#!/bin/bash
# Setup script for Nginx reverse proxy with Streamlit

set -e

echo "=== Setting up Nginx Reverse Proxy for Streamlit ==="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash $0"
    exit 1
fi

# Install Nginx
echo "1. Installing Nginx..."
yum install -y nginx

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   Public IP: $PUBLIC_IP"

# Create Nginx configuration
echo "2. Configuring Nginx..."
cat > /etc/nginx/conf.d/streamlit.conf <<EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    # Increase buffer sizes for Streamlit
    client_max_body_size 200M;
    proxy_buffers 8 16k;
    proxy_buffer_size 32k;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # WebSocket support for Streamlit
    location /_stcore/stream {
        proxy_pass http://localhost:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Test Nginx configuration
echo "3. Testing Nginx configuration..."
nginx -t

# Start and enable Nginx
echo "4. Starting Nginx..."
systemctl start nginx
systemctl enable nginx

# Check if port 80 is allowed in security group
echo "5. Checking Security Group..."
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
SG_ID=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region us-east-1 --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)

echo "   Security Group: $SG_ID"

# Check if port 80 is already open
PORT_80_OPEN=$(aws ec2 describe-security-groups --group-ids $SG_ID --region us-east-1 --query 'SecurityGroups[0].IpPermissions[?FromPort==`80`]' --output text)

if [ -z "$PORT_80_OPEN" ]; then
    echo "6. Opening port 80 in Security Group..."
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region us-east-1 2>/dev/null || echo "   Port 80 might already be open or you need permissions"
else
    echo "6. Port 80 is already open in Security Group"
fi

# Create systemd service for Streamlit (if it doesn't exist)
if [ ! -f /etc/systemd/system/streamlit.service ]; then
    echo "7. Creating Streamlit systemd service..."
    cat > /etc/systemd/system/streamlit.service <<EOF
[Unit]
Description=Streamlit SRE Copilot
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/sre/sre_mcp
ExecStart=/usr/bin/python3 -m streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable streamlit
    echo "   Streamlit service created. Start with: sudo systemctl start streamlit"
else
    echo "7. Streamlit service already exists"
fi

# Display status
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Access your Streamlit app at:"
echo "  http://$PUBLIC_IP"
echo ""
echo "To use a domain name instead:"
echo "  1. Point your domain's A record to: $PUBLIC_IP"
echo "  2. Update /etc/nginx/conf.d/streamlit.conf with your domain"
echo "  3. Restart Nginx: sudo systemctl restart nginx"
echo ""
echo "To add HTTPS with Let's Encrypt:"
echo "  sudo yum install -y certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d yourdomain.com"
echo ""
echo "Service commands:"
echo "  sudo systemctl status nginx"
echo "  sudo systemctl status streamlit"
echo "  sudo systemctl restart nginx"
echo "  sudo systemctl restart streamlit"
echo ""
echo "Logs:"
echo "  sudo journalctl -u nginx -f"
echo "  sudo journalctl -u streamlit -f"
echo ""