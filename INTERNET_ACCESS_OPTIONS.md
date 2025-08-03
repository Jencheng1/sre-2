# Internet Access Options for Streamlit SRE Copilot

## Current Setup
- **Public IP**: 44.202.201.32
- **Streamlit Port**: 8501
- **Security Group**: sg-066d8a7f3a5ff0c62
- **Region**: us-east-1

## Option 1: Direct Public IP Access (Current - Not Recommended for Production)

### Current Access
```
http://44.202.201.32:8501
```

### Limitations
- IP changes if instance stops/starts
- No HTTPS encryption
- Not user-friendly
- No load balancing

### Security Group Configuration Needed
```bash
# Check current security group rules
aws ec2 describe-security-groups --group-ids sg-066d8a7f3a5ff0c62 --region us-east-1

# Add rule for Streamlit (if not already present)
aws ec2 authorize-security-group-ingress \
    --group-id sg-066d8a7f3a5ff0c62 \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

## Option 2: Elastic IP + Route 53 (Simple DNS)

### Steps
1. **Allocate Elastic IP**
```bash
# Allocate EIP
aws ec2 allocate-address --domain vpc --region us-east-1

# Associate with instance
aws ec2 associate-address \
    --instance-id $(curl -s http://169.254.169.254/latest/meta-data/instance-id) \
    --allocation-id <ALLOCATION_ID> \
    --region us-east-1
```

2. **Configure Route 53**
```bash
# Create hosted zone (if needed)
aws route53 create-hosted-zone \
    --name srecopilot.example.com \
    --caller-reference $(date +%s)

# Create A record
aws route53 change-resource-record-sets \
    --hosted-zone-id <ZONE_ID> \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "srecopilot.example.com",
                "Type": "A",
                "TTL": 300,
                "ResourceRecords": [{"Value": "<ELASTIC_IP>"}]
            }
        }]
    }'
```

### Result
- Access via: `http://srecopilot.example.com:8501`
- IP persists across instance restarts
- Still no HTTPS

## Option 3: Application Load Balancer + Route 53 (Recommended)

### Architecture
```
Internet → Route 53 → ALB (HTTPS) → Target Group → EC2 (HTTP:8501)
```

### Implementation Steps

1. **Create Target Group**
```bash
aws elbv2 create-target-group \
    --name sre-copilot-tg \
    --protocol HTTP \
    --port 8501 \
    --vpc-id <VPC_ID> \
    --health-check-path "/" \
    --health-check-interval-seconds 30 \
    --region us-east-1
```

2. **Create Application Load Balancer**
```bash
aws elbv2 create-load-balancer \
    --name sre-copilot-alb \
    --subnets <SUBNET_1> <SUBNET_2> \
    --security-groups <ALB_SECURITY_GROUP> \
    --region us-east-1
```

3. **Configure HTTPS Listener (with ACM Certificate)**
```bash
# Request certificate
aws acm request-certificate \
    --domain-name srecopilot.example.com \
    --validation-method DNS \
    --region us-east-1

# Create HTTPS listener
aws elbv2 create-listener \
    --load-balancer-arn <ALB_ARN> \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=<CERT_ARN> \
    --default-actions Type=forward,TargetGroupArn=<TG_ARN>
```

4. **Configure Route 53**
```bash
# Create alias record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id <ZONE_ID> \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "srecopilot.example.com",
                "Type": "A",
                "AliasTarget": {
                    "HostedZoneId": "<ALB_ZONE_ID>",
                    "DNSName": "<ALB_DNS_NAME>",
                    "EvaluateTargetHealth": true
                }
            }
        }]
    }'
```

### Benefits
- HTTPS encryption
- Health checks
- Auto-scaling capability
- Professional URL: `https://srecopilot.example.com`

## Option 4: CloudFront + S3 + API Gateway (Serverless Frontend)

### Architecture
```
CloudFront → S3 (Static Assets) → API Gateway → Lambda → EC2
```

### When to Use
- If you want to separate frontend from backend
- Global distribution needed
- Want to cache static content

## Option 5: AWS Amplify Hosting (If Converting to React)

### Steps
1. Convert Streamlit to React app
2. Deploy backend as API
3. Use Amplify for hosting

### Benefits
- Automatic CI/CD
- Built-in authentication
- Global CDN

## Option 6: EC2 with Nginx Reverse Proxy (Cost-Effective)

### Setup on Current Instance

1. **Install Nginx**
```bash
sudo yum install -y nginx
```

2. **Configure Nginx**
```bash
sudo tee /etc/nginx/conf.d/streamlit.conf > /dev/null <<EOF
server {
    listen 80;
    server_name srecopilot.example.com;

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
}
EOF

sudo nginx -t
sudo systemctl start nginx
sudo systemctl enable nginx
```

3. **Add SSL with Let's Encrypt**
```bash
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d srecopilot.example.com
```

4. **Update Security Group**
```bash
# Allow HTTP (80) and HTTPS (443)
aws ec2 authorize-security-group-ingress \
    --group-id sg-066d8a7f3a5ff0c62 \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region us-east-1

aws ec2 authorize-security-group-ingress \
    --group-id sg-066d8a7f3a5ff0c62 \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region us-east-1
```

## Option 7: Container-Based Deployment (ECS/Fargate)

### Dockerfile
```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Deploy to ECS with ALB
- Managed container service
- Auto-scaling
- Load balanced
- HTTPS support

## Recommended Approach for Production

### For Quick Setup (Option 6):
1. Use Nginx reverse proxy on current EC2
2. Get free SSL from Let's Encrypt
3. Use Route 53 for DNS
4. Cost: ~$5/month (Route 53 hosted zone)

### For Enterprise (Option 3):
1. Application Load Balancer
2. AWS Certificate Manager (free SSL)
3. Route 53
4. Auto Scaling Group
5. Cost: ~$20-30/month (ALB) + Route 53

### For Global Scale (Option 4):
1. CloudFront distribution
2. Multiple regions
3. API Gateway
4. Cost: Pay per use

## Security Best Practices

1. **Always use HTTPS in production**
2. **Implement authentication**:
   ```python
   # Add to streamlit_app.py
   import streamlit_authenticator as stauth
   ```

3. **Restrict access by IP if needed**:
   ```bash
   # Security group rule for specific IPs
   aws ec2 authorize-security-group-ingress \
       --group-id sg-066d8a7f3a5ff0c62 \
       --protocol tcp \
       --port 443 \
       --cidr YOUR_OFFICE_IP/32
   ```

4. **Use AWS WAF with ALB** for additional protection

5. **Enable CloudWatch logging** for access monitoring

## Quick Start Commands

### Option 1: Test Current Setup
```bash
# Check if port 8501 is open
curl http://44.202.201.32:8501
```

### Option 2: Set up Nginx (Recommended for now)
```bash
# Install and configure Nginx
sudo yum install -y nginx
# Then follow Option 6 configuration above
```

### Option 3: Future-proof with ALB
```bash
# Create infrastructure as code with Terraform/CloudFormation
# See Option 3 above for AWS CLI commands
```

## DNS Providers

1. **AWS Route 53**: $0.50/month per hosted zone
2. **Cloudflare**: Free tier available
3. **Google Domains**: $12/year includes basic DNS
4. **Namecheap**: Competitive pricing

## Monitoring and Maintenance

1. **Set up health checks**
2. **Configure CloudWatch alarms**
3. **Enable AWS Systems Manager Session Manager** for secure access
4. **Regular security updates**

## Cost Estimates

| Option | Monthly Cost | Setup Complexity | Features |
|--------|-------------|------------------|----------|
| Direct IP | $0 | Low | Basic |
| Elastic IP + Route 53 | $5 | Low | Persistent IP |
| Nginx + Let's Encrypt | $5 | Medium | HTTPS, Professional |
| ALB + Route 53 | $25-30 | Medium | Enterprise-ready |
| CloudFront + ALB | $50+ | High | Global, Cached |

## Next Steps

1. **Choose an option based on requirements**
2. **Register a domain name** (if needed)
3. **Implement chosen solution**
4. **Test thoroughly**
5. **Set up monitoring**

For immediate access with a professional setup, Option 6 (Nginx reverse proxy) provides the best balance of features and simplicity.