#!/usr/bin/env python3
"""
Deploy a simple Java Spring Boot test application to SRE-DEMO instance
This creates a minimal app that exposes Actuator endpoints for monitoring
"""

import boto3
import json
import time
from datetime import datetime

class JavaTestAppDeployment:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.instance_id = "i-02bef13982a179478"  # SRE-DEMO
        
    def create_java_application(self):
        """Create a simple Spring Boot application with memory leak potential"""
        print("📝 Creating Java Spring Boot test application...")
        
        # Simple Spring Boot application with actuator
        java_app = """
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.boot.actuate.autoconfigure.metrics.MeterRegistryCustomizer;
import org.springframework.context.annotation.Bean;
import io.micrometer.core.instrument.MeterRegistry;
import java.util.*;
import java.util.concurrent.*;

@SpringBootApplication
@RestController
public class PaymentService {
    
    // This cache will grow without bounds - simulating memory leak
    private static final Map<String, Transaction> transactionCache = new ConcurrentHashMap<>();
    private static final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    private static long transactionCounter = 0;
    
    public static void main(String[] args) {
        SpringApplication.run(PaymentService.class, args);
    }
    
    @PostConstruct
    public void init() {
        // Simulate continuous transaction processing
        scheduler.scheduleAtFixedRate(() -> {
            // Add new transaction to cache every second
            String transId = "TXN-" + (++transactionCounter);
            transactionCache.put(transId, new Transaction(transId, Math.random() * 1000));
            
            // Log cache size periodically
            if (transactionCounter % 60 == 0) {
                System.out.println("[INFO] TransactionCache size: " + transactionCache.size() + 
                                 " entries, estimated memory: " + (transactionCache.size() * 1024 / 1048576.0) + "MB");
            }
        }, 5, 1, TimeUnit.SECONDS);
    }
    
    @GetMapping("/")
    public String home() {
        return "Payment Service v2.1.0 - Cache Size: " + transactionCache.size();
    }
    
    @GetMapping("/health")
    public Map<String, Object> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("cacheSize", transactionCache.size());
        health.put("heapUsed", Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory());
        health.put("heapMax", Runtime.getRuntime().maxMemory());
        return health;
    }
    
    @Bean
    MeterRegistryCustomizer<MeterRegistry> metricsCommonTags() {
        return registry -> registry.config().commonTags("application", "payment-service");
    }
    
    // Transaction class that holds some data
    static class Transaction {
        String id;
        double amount;
        byte[] data = new byte[1024]; // 1KB per transaction
        
        Transaction(String id, double amount) {
            this.id = id;
            this.amount = amount;
            Arrays.fill(data, (byte) 42); // Fill with dummy data
        }
    }
}
"""

        # application.yml for Spring Boot
        app_config = """
server:
  port: 8080

spring:
  application:
    name: payment-service

management:
  endpoints:
    web:
      exposure:
        include: "*"
  metrics:
    export:
      cloudwatch:
        namespace: JavaApp/SpringBoot
        enabled: true
        step: 1m
  endpoint:
    health:
      show-details: always

logging:
  level:
    root: INFO
"""

        # pom.xml for Maven
        pom_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>payment-service</artifactId>
    <version>2.1.0</version>
    <packaging>jar</packaging>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>2.7.0</version>
    </parent>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-registry-cloudwatch2</artifactId>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""

        # Deployment script
        deploy_script = f"""#!/bin/bash
# Spring Boot App Deployment Script

echo "📦 Deploying Payment Service v2.1.0..."

# Create app directory
sudo mkdir -p /opt/payment-service
cd /opt/payment-service

# Create the Java file
cat > PaymentService.java << 'EOF'
{java_app}
EOF

# Create application.yml
mkdir -p src/main/resources
cat > src/main/resources/application.yml << 'EOF'
{app_config}
EOF

# Create pom.xml
cat > pom.xml << 'EOF'
{pom_xml}
EOF

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "📦 Installing Java..."
    sudo yum install -y java-11-openjdk-devel maven
fi

# Build the application
echo "🔨 Building application..."
mvn clean package -DskipTests

# Create systemd service
sudo cat > /etc/systemd/system/payment-service.service << 'EOF'
[Unit]
Description=Payment Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/payment-service
ExecStart=/usr/bin/java -Xmx512m -Xms256m -jar /opt/payment-service/target/payment-service-2.1.0.jar
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Start the service
sudo systemctl daemon-reload
sudo systemctl enable payment-service
sudo systemctl restart payment-service

echo "✅ Payment Service deployed and started!"
echo "📊 Actuator endpoints available at:"
echo "   http://localhost:8080/actuator/health"
echo "   http://localhost:8080/actuator/metrics"
echo "   http://localhost:8080/actuator/metrics/jvm.memory.used"
"""

        return deploy_script
        
    def deploy_to_instance(self):
        """Deploy the Java application to SRE-DEMO instance"""
        print(f"\n🚀 Deploying to instance {self.instance_id}...")
        
        deploy_script = self.create_java_application()
        
        # Deploy using SSM
        try:
            response = self.ssm_client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={
                    'commands': deploy_script.split('\n')
                },
                TimeoutSeconds=300
            )
            
            command_id = response['Command']['CommandId']
            print(f"✅ Deployment initiated (Command ID: {command_id})")
            
            # Wait for completion
            print("⏳ Waiting for deployment to complete...")
            time.sleep(10)
            
            # Check status
            result = self.ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=self.instance_id
            )
            
            if result['Status'] == 'Success':
                print("✅ Java application deployed successfully!")
                return True
            else:
                print(f"❌ Deployment failed: {result['StatusDetails']}")
                return False
                
        except Exception as e:
            print(f"❌ Error during deployment: {e}")
            return False
            
    def create_actuator_metrics_collector(self):
        """Create a script to collect and push actuator metrics to CloudWatch"""
        print("\n📊 Setting up Actuator metrics collection...")
        
        collector_script = """#!/bin/bash
# Actuator Metrics Collector for CloudWatch

while true; do
    # Check if service is running
    if systemctl is-active --quiet payment-service; then
        # Get health endpoint
        HEALTH=$(curl -s http://localhost:8080/health || echo '{}')
        
        # Extract cache size if available
        CACHE_SIZE=$(echo "$HEALTH" | jq -r '.cacheSize // 0')
        
        # Get JVM metrics from actuator
        JVM_HEAP=$(curl -s http://localhost:8080/actuator/metrics/jvm.memory.used | jq -r '.measurements[0].value // 0')
        JVM_MAX=$(curl -s http://localhost:8080/actuator/metrics/jvm.memory.max | jq -r '.measurements[0].value // 0')
        
        # Calculate heap percentage
        if [ "$JVM_MAX" -gt 0 ]; then
            HEAP_PERCENT=$(awk "BEGIN {printf \"%.2f\", ($JVM_HEAP / $JVM_MAX) * 100}")
        else
            HEAP_PERCENT=0
        fi
        
        # Push to CloudWatch
        aws cloudwatch put-metric-data \
            --namespace "JavaApp/SpringBoot" \
            --metric-name "App_CacheSize" \
            --value "$CACHE_SIZE" \
            --unit "Count" \
            --dimensions Application=payment-service,InstanceId=$(ec2-metadata --instance-id | cut -d' ' -f2) \
            --region us-east-1
            
        aws cloudwatch put-metric-data \
            --namespace "JavaApp/SpringBoot" \
            --metric-name "JVM_HeapUsedPercent" \
            --value "$HEAP_PERCENT" \
            --unit "Percent" \
            --dimensions Application=payment-service,InstanceId=$(ec2-metadata --instance-id | cut -d' ' -f2) \
            --region us-east-1
            
        echo "$(date): Pushed metrics - Cache: $CACHE_SIZE, Heap: $HEAP_PERCENT%"
    else
        echo "$(date): Payment service not running"
    fi
    
    sleep 60
done
"""
        
        try:
            # Deploy collector script
            response = self.ssm_client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={
                    'commands': [
                        f'cat > /opt/monitoring/actuator_collector.sh << "EOF"\n{collector_script}\nEOF',
                        'chmod +x /opt/monitoring/actuator_collector.sh',
                        'nohup /opt/monitoring/actuator_collector.sh > /var/log/actuator_collector.log 2>&1 &',
                        'echo "Actuator metrics collector started"'
                    ]
                }
            )
            
            print(f"✅ Actuator metrics collector deployed")
            return True
            
        except Exception as e:
            print(f"⚠️ Error deploying collector: {e}")
            return False

def main():
    """Deploy Java test application"""
    print("🚀 Deploying Java Test Application to SRE-DEMO")
    print("=" * 60)
    
    deployer = JavaTestAppDeployment()
    
    # Deploy the application
    if deployer.deploy_to_instance():
        # Setup metrics collection
        deployer.create_actuator_metrics_collector()
        
        print("\n✅ Deployment Complete!")
        print("\n📊 Application Details:")
        print("   - Name: payment-service v2.1.0")
        print("   - Port: 8080")
        print("   - Features: Memory leak simulation via unbounded cache")
        print("   - Actuator: Enabled with all endpoints")
        
        print("\n🔗 Endpoints:")
        print("   - Health: http://sre-demo:8080/health")
        print("   - Metrics: http://sre-demo:8080/actuator/metrics")
        print("   - Home: http://sre-demo:8080/")
        
        print("\n📈 Metrics Collection:")
        print("   - JVM heap usage percentage")
        print("   - Transaction cache size")
        print("   - Pushing to CloudWatch every minute")
        
        print("\n⚠️ Memory Leak Behavior:")
        print("   - Cache grows by 1 transaction/second")
        print("   - Each transaction uses ~1KB memory")
        print("   - No eviction policy implemented")
        print("   - Will eventually cause OutOfMemoryError")
        
        return 0
    else:
        print("\n❌ Deployment failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())