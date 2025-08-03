#!/usr/bin/env python3
"""
Best practices and incident resolution documents for knowledge base.
"""

class KnowledgeBaseDocuments:
    """Collection of best practices and resolution guides."""
    
    def __init__(self):
        self.best_practices = self._define_best_practices()
        self.resolution_guides = self._define_resolution_guides()
        
    def _define_best_practices(self):
        """Define SRE best practices documents."""
        return [
            {
                'id': 'BP-001',
                'title': 'Database Connection Pool Management',
                'category': 'performance',
                'content': """
Database Connection Pool Best Practices

Overview:
Proper database connection pool management is critical for application performance and reliability.

Key Practices:
1. Connection Pool Sizing
   - Set minimum pool size based on baseline load
   - Maximum pool size should be: (number of worker threads) * (average connections per request)
   - Monitor pool utilization and adjust accordingly

2. Connection Lifecycle Management
   - Always use try-with-resources or finally blocks
   - Set appropriate connection timeout (typically 30 seconds)
   - Implement connection validation queries
   - Enable connection leak detection

3. Monitoring and Alerting
   - Track active vs idle connections
   - Alert on pool exhaustion (>80% utilization)
   - Monitor connection wait times
   - Log slow queries and connection acquisition

4. Configuration Examples:
   ```
   # HikariCP Configuration
   maximumPoolSize: 20
   minimumIdle: 5
   connectionTimeout: 30000
   idleTimeout: 600000
   maxLifetime: 1800000
   leakDetectionThreshold: 60000
   ```

5. Troubleshooting:
   - Check for connection leaks in application code
   - Review transaction boundaries
   - Analyze query execution times
   - Verify network latency to database

Common Pitfalls:
- Not closing connections in finally blocks
- Oversized connection pools causing database overload
- Missing connection validation
- Incorrect timeout configurations
""",
                'tags': ['database', 'performance', 'connection-pool', 'best-practice']
            },
            {
                'id': 'BP-002',
                'title': 'Security Group Management',
                'category': 'security',
                'content': """
AWS Security Group Best Practices

Overview:
Security groups act as virtual firewalls controlling inbound and outbound traffic.

Key Practices:
1. Principle of Least Privilege
   - Only open required ports
   - Restrict source IPs to known ranges
   - Use separate security groups for each tier
   - Never use 0.0.0.0/0 for production resources

2. Change Management
   - Implement approval process for changes
   - Use infrastructure as code (Terraform/CloudFormation)
   - Document all security group rules
   - Regular audits of existing rules

3. Monitoring and Compliance
   - Enable AWS Config rules for security groups
   - Set up CloudWatch alarms for changes
   - Use AWS Security Hub for compliance
   - Regular penetration testing

4. Naming Conventions
   - Use descriptive names: <environment>-<application>-<tier>-sg
   - Tag with owner, purpose, and environment
   - Document rule purposes in descriptions

5. Common Patterns:
   ```
   # Web Tier
   Inbound: 443 from ALB security group
   Outbound: 3306 to database security group
   
   # Database Tier  
   Inbound: 3306 from application security group
   Outbound: None (explicit deny)
   ```

Incident Response:
- Immediately revert unauthorized changes
- Review CloudTrail for who made changes
- Check for any exploitation attempts
- Update incident response runbook
""",
                'tags': ['security', 'aws', 'security-groups', 'best-practice']
            },
            {
                'id': 'BP-003',
                'title': 'Circuit Breaker Pattern Implementation',
                'category': 'resilience',
                'content': """
Circuit Breaker Pattern for Microservices

Overview:
Circuit breakers prevent cascading failures in distributed systems.

States:
1. Closed (Normal Operation)
   - All requests pass through
   - Monitor failure rate
   - Count consecutive failures

2. Open (Failure Mode)
   - Reject requests immediately
   - Return cached/default response
   - Start timeout timer

3. Half-Open (Testing)
   - Allow limited requests through
   - Test if service recovered
   - Return to closed or open state

Implementation Guidelines:
1. Failure Threshold Configuration
   - Set failure percentage (e.g., 50%)
   - Minimum request volume (e.g., 20 requests)
   - Time window (e.g., 60 seconds)

2. Timeout Configuration
   - Request timeout: 1-5 seconds
   - Circuit open duration: 30-60 seconds
   - Half-open test requests: 1-3

3. Monitoring Metrics
   - Circuit state changes
   - Failure rates by endpoint
   - Response times
   - Fallback execution count

4. Code Example:
   ```python
   @circuit_breaker(
       failure_threshold=0.5,
       recovery_timeout=30,
       expected_exception=RequestException
   )
   def call_external_service():
       return requests.get(url, timeout=5)
   ```

5. Fallback Strategies
   - Return cached data
   - Provide degraded functionality
   - Queue for retry
   - Return error gracefully

Testing:
- Chaos engineering exercises
- Load testing with failures
- Validate fallback behavior
- Monitor recovery times
""",
                'tags': ['resilience', 'microservices', 'circuit-breaker', 'best-practice']
            },
            {
                'id': 'BP-004',
                'title': 'CDN Cache Strategy',
                'category': 'performance',
                'content': """
CDN Caching Best Practices

Overview:
Effective CDN caching improves performance and reduces origin load.

Cache Strategy:
1. Cache Headers Configuration
   - Static assets: Cache-Control: max-age=31536000
   - Dynamic content: Cache-Control: max-age=300, stale-while-revalidate=86400
   - Private content: Cache-Control: private, no-cache

2. Cache Invalidation
   - Use versioned URLs for static assets
   - Targeted path invalidation only
   - Implement cache warming after invalidation
   - Rate limit invalidation requests

3. Origin Shield Configuration
   - Enable origin shield for global traffic
   - Configure appropriate shield location
   - Monitor origin request reduction

4. Performance Optimization
   - Enable compression (gzip/brotli)
   - Implement HTTP/2 push
   - Use appropriate cache keys
   - Enable edge computing for personalization

5. Monitoring and Metrics
   - Cache hit ratio (target >90%)
   - Origin bandwidth usage
   - Edge response times
   - 4xx/5xx error rates

Common Issues:
- Cache stampede after invalidation
- Incorrect cache headers
- Missing vary headers
- Query parameter pollution

Troubleshooting:
- Check cache headers with curl
- Monitor origin load during invalidation
- Validate cache key configuration
- Review CDN access logs
""",
                'tags': ['cdn', 'performance', 'caching', 'best-practice']
            },
            {
                'id': 'BP-005',
                'title': 'Secret Management',
                'category': 'security',
                'content': """
Secrets Management Best Practices

Overview:
Proper secret management prevents security breaches and data leaks.

Key Principles:
1. Never Store Secrets in Code
   - Use environment variables
   - Leverage secret management services
   - Implement pre-commit hooks
   - Regular repository scanning

2. AWS Secrets Manager Usage
   - Enable automatic rotation
   - Use IAM policies for access control
   - Implement versioning
   - Monitor access patterns

3. Implementation Pattern:
   ```python
   import boto3
   from botocore.exceptions import ClientError
   
   def get_secret(secret_name):
       session = boto3.session.Session()
       client = session.client('secretsmanager')
       
       try:
           response = client.get_secret_value(SecretId=secret_name)
           return response['SecretString']
       except ClientError as e:
           raise e
   ```

4. Access Control
   - Use IAM roles, not users
   - Implement least privilege
   - Regular access reviews
   - Enable CloudTrail logging

5. Rotation Strategy
   - Database passwords: 30 days
   - API keys: 90 days
   - Certificates: Before expiration
   - Service accounts: 180 days

Incident Response:
- Immediately rotate compromised secrets
- Review access logs
- Update affected systems
- Implement additional monitoring
""",
                'tags': ['security', 'secrets', 'aws', 'best-practice']
            },
            {
                'id': 'BP-006',
                'title': 'Lambda Performance Optimization',
                'category': 'performance',
                'content': """
AWS Lambda Performance Best Practices

Overview:
Optimize Lambda functions for performance and cost efficiency.

Cold Start Mitigation:
1. Provisioned Concurrency
   - Configure for critical functions
   - Use predictive scaling
   - Monitor utilization metrics
   - Cost-benefit analysis

2. Code Optimization
   - Minimize deployment package size
   - Lazy load dependencies
   - Use Lambda layers for shared code
   - Optimize container images

3. Memory Configuration
   - Start with 1GB for testing
   - Monitor memory usage
   - CPU scales with memory
   - Find optimal cost/performance ratio

4. Connection Management
   - Reuse connections across invocations
   - Initialize outside handler
   - Use connection pooling
   - Implement keep-alive

5. Code Example:
   ```python
   # Initialize outside handler
   import boto3
   
   # Reuse clients
   dynamodb = boto3.resource('dynamodb')
   table = dynamodb.Table('MyTable')
   
   def lambda_handler(event, context):
       # Use initialized resources
       response = table.get_item(Key={'id': event['id']})
       return response['Item']
   ```

Monitoring:
- Cold start frequency
- Duration percentiles
- Memory utilization
- Concurrent executions
- Throttling rates

Cost Optimization:
- Right-size memory allocation
- Use ARM-based Graviton2
- Implement caching strategies
- Consider Step Functions for orchestration
""",
                'tags': ['lambda', 'performance', 'serverless', 'best-practice']
            }
        ]
        
    def _define_resolution_guides(self):
        """Define incident resolution guides."""
        return [
            {
                'id': 'RG-001',
                'title': 'Resolving Database Connection Pool Exhaustion',
                'category': 'performance',
                'content': """
Resolution Guide: Database Connection Pool Exhaustion

Symptoms:
- Application timeouts
- "Connection pool exhausted" errors
- High database CPU with low query count
- Increasing response times

Immediate Actions:
1. Increase connection pool size temporarily
   ```sql
   -- Check current connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Kill idle connections
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'idle' 
   AND state_change < current_timestamp - interval '10 minutes';
   ```

2. Restart affected application pods
   ```bash
   kubectl rollout restart deployment/app-name
   ```

3. Enable connection pool metrics
   ```yaml
   logging:
     level:
       com.zaxxer.hikari: DEBUG
   ```

Root Cause Analysis:
1. Check for connection leaks
   - Review recent code changes
   - Look for missing close() calls
   - Check transaction boundaries

2. Analyze slow queries
   ```sql
   SELECT query, total_time, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

3. Review pool configuration
   - Validate pool size calculations
   - Check timeout settings
   - Review validation queries

Long-term Fixes:
1. Implement connection leak detection
2. Add circuit breakers for database calls
3. Optimize slow queries
4. Implement read replicas for read traffic
5. Add connection pool monitoring dashboard

Prevention:
- Load test with realistic scenarios
- Implement gradual rollout
- Monitor pool metrics continuously
- Regular code reviews for resource management
""",
                'tags': ['database', 'performance', 'resolution', 'connection-pool']
            },
            {
                'id': 'RG-002',
                'title': 'Responding to Unauthorized Access',
                'category': 'security',
                'content': """
Resolution Guide: Unauthorized Access Incident

Immediate Response (First 15 minutes):
1. Isolate affected resources
   ```bash
   # Remove security group rules
   aws ec2 revoke-security-group-ingress --group-id sg-xxxxx --protocol all
   
   # Disable compromised IAM credentials
   aws iam update-access-key --access-key-id AKIA... --status Inactive
   ```

2. Preserve evidence
   ```bash
   # Snapshot affected instances
   aws ec2 create-snapshot --volume-id vol-xxxxx --description "Security incident YYYY-MM-DD"
   
   # Export CloudTrail logs
   aws cloudtrail lookup-events --start-time 2024-01-01 --end-time 2024-01-02 > incident_logs.json
   ```

3. Enable enhanced monitoring
   - Turn on VPC Flow Logs
   - Enable GuardDuty if not active
   - Set up CloudWatch alarms

Investigation Steps:
1. Timeline reconstruction
   - Review CloudTrail for API calls
   - Check VPC Flow Logs for network traffic
   - Analyze application logs

2. Impact assessment
   - Identify accessed resources
   - Check for data exfiltration
   - Review privilege escalation attempts

3. Attack vector identification
   - Compromised credentials
   - Vulnerable application
   - Misconfigured security groups

Remediation:
1. Rotate all potentially compromised credentials
2. Patch identified vulnerabilities
3. Update security group rules
4. Implement additional access controls
5. Review and update IAM policies

Post-Incident:
1. Document lessons learned
2. Update incident response playbook
3. Implement additional monitoring
4. Security awareness training
5. Third-party security audit
""",
                'tags': ['security', 'incident-response', 'resolution', 'unauthorized-access']
            },
            {
                'id': 'RG-003',
                'title': 'Recovering from Service Outage',
                'category': 'outage',
                'content': """
Resolution Guide: Service Outage Recovery

Initial Assessment (First 5 minutes):
1. Verify the outage
   ```bash
   # Check service health
   curl -f https://api.example.com/health || echo "Service Down"
   
   # Check all regions
   for region in us-east-1 us-west-2 eu-west-1; do
     echo "Checking $region"
     aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:$region:...
   done
   ```

2. Activate incident response
   - Page on-call team
   - Open incident channel
   - Start incident timeline
   - Notify stakeholders

3. Check dependencies
   - Database connectivity
   - Third-party APIs
   - DNS resolution
   - Certificate validity

Recovery Actions:
1. Attempt quick fixes
   ```bash
   # Restart services
   kubectl rollout restart deployment --all
   
   # Scale up capacity
   kubectl scale deployment app --replicas=10
   
   # Clear caches if needed
   redis-cli FLUSHALL
   ```

2. Failover procedures
   - Switch to DR region
   - Enable maintenance page
   - Route to backup systems
   - Activate read-only mode

3. Root cause investigation
   - Check recent deployments
   - Review system metrics
   - Analyze error logs
   - Identify failure cascade

Communication:
1. Status page updates
   - Initial acknowledgment
   - Regular updates (15-min intervals)
   - Resolution notification
   - Post-mortem schedule

2. Customer communication
   - Impact assessment
   - Workaround instructions
   - ETA for resolution
   - Compensation details

Post-Outage:
1. Blameless post-mortem
2. Update runbooks
3. Implement preventive measures
4. Load test recovery procedures
5. Review SLOs and error budgets
""",
                'tags': ['outage', 'disaster-recovery', 'resolution', 'incident-response']
            }
        ]
        
    def get_all_documents(self):
        """Get all documents for knowledge base ingestion."""
        documents = []
        
        # Add best practices
        for bp in self.best_practices:
            documents.append({
                'document_id': bp['id'],
                'title': bp['title'],
                'content': bp['content'],
                'metadata': {
                    'type': 'best_practice',
                    'category': bp['category'],
                    'tags': bp['tags']
                }
            })
            
        # Add resolution guides
        for rg in self.resolution_guides:
            documents.append({
                'document_id': rg['id'],
                'title': rg['title'],
                'content': rg['content'],
                'metadata': {
                    'type': 'resolution_guide',
                    'category': rg['category'],
                    'tags': rg['tags']
                }
            })
            
        return documents


if __name__ == "__main__":
    kb = KnowledgeBaseDocuments()
    
    print("Best Practices:")
    print("=" * 50)
    for bp in kb.best_practices:
        print(f"- {bp['id']}: {bp['title']}")
        
    print("\nResolution Guides:")
    print("=" * 50)
    for rg in kb.resolution_guides:
        print(f"- {rg['id']}: {rg['title']}")