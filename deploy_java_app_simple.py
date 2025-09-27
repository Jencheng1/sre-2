#!/usr/bin/env python3
"""
Deploy a simple Java Spring Boot application to SRE-DEMO instance
This is a simplified version that creates a runnable JAR
"""

import boto3
import time
import base64

def deploy_java_app():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"  # SRE-DEMO
    
    print("🚀 Deploying Java Spring Boot Application to SRE-DEMO")
    print("=" * 60)
    
    # Create a simple Spring Boot app that simulates memory leak
    deploy_commands = [
        # Create directories
        "sudo mkdir -p /opt/payment-service/{src/main/java/com/example,src/main/resources,target}",
        "cd /opt/payment-service",
        
        # Create the main Java file
        """cat > src/main/java/com/example/PaymentService.java << 'EOF'
package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;
import javax.annotation.PostConstruct;
import java.util.*;
import java.util.concurrent.*;

@SpringBootApplication
@RestController
@EnableScheduling
public class PaymentService {
    
    // This will cause memory leak
    private static final Map<String, byte[]> leakyCache = new ConcurrentHashMap<>();
    private static long counter = 0;
    
    public static void main(String[] args) {
        SpringApplication.run(PaymentService.class, args);
    }
    
    @PostConstruct
    public void init() {
        System.out.println("Payment Service v2.1.0 started - with unbounded cache");
    }
    
    @Scheduled(fixedDelay = 1000) // Every second
    public void simulateMemoryLeak() {
        String key = "transaction-" + (counter++);
        byte[] data = new byte[1024]; // 1KB per entry
        Arrays.fill(data, (byte)42);
        leakyCache.put(key, data);
        
        if (counter % 60 == 0) {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            System.out.println(String.format("[WARN] TransactionCache size: %d entries, Memory: %.1f%%", 
                leakyCache.size(), percentUsed));
                
            if (percentUsed > 85) {
                System.out.println("[ERROR] Memory usage critical! GC overhead limit may be exceeded");
            }
        }
    }
    
    @GetMapping("/")
    public Map<String, Object> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "payment-service");
        response.put("version", "2.1.0");
        response.put("cacheSize", leakyCache.size());
        response.put("status", "running");
        return response;
    }
    
    @GetMapping("/health")
    public Map<String, Object> health() {
        long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
        long maxMemory = Runtime.getRuntime().maxMemory();
        
        Map<String, Object> health = new HashMap<>();
        health.put("status", usedMemory < maxMemory * 0.9 ? "UP" : "DOWN");
        health.put("cacheSize", leakyCache.size());
        health.put("memoryUsed", usedMemory);
        health.put("memoryMax", maxMemory);
        health.put("memoryPercent", (double) usedMemory / maxMemory * 100);
        return health;
    }
}

@Component
class CustomHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
        long maxMemory = Runtime.getRuntime().maxMemory();
        double percentUsed = (double) usedMemory / maxMemory * 100;
        
        if (percentUsed > 90) {
            return Health.down()
                .withDetail("memory", "Critical - " + String.format("%.1f%%", percentUsed))
                .build();
        } else if (percentUsed > 75) {
            return Health.status("WARNING")
                .withDetail("memory", String.format("%.1f%%", percentUsed))
                .build();
        }
        
        return Health.up()
            .withDetail("memory", String.format("%.1f%%", percentUsed))
            .build();
    }
}
EOF""",
        
        # Create application.properties
        """cat > src/main/resources/application.properties << 'EOF'
server.port=8080
spring.application.name=payment-service
management.endpoints.web.exposure.include=*
management.endpoint.health.show-details=always
management.metrics.export.cloudwatch.namespace=JavaApp/SpringBoot
management.metrics.export.cloudwatch.enabled=false
logging.level.root=INFO
EOF""",
        
        # Create pom.xml
        """cat > pom.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
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
        <version>2.7.10</version>
    </parent>
    
    <properties>
        <java.version>11</java.version>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
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
EOF""",
        
        # Build the application
        "echo '🔨 Building application...'",
        "cd /opt/payment-service",
        "sudo mvn clean package -DskipTests 2>&1 | tail -20",
        
        # Create systemd service
        """sudo cat > /etc/systemd/system/payment-service.service << 'EOF'
[Unit]
Description=Payment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/payment-service
ExecStart=/usr/bin/java -Xmx256m -Xms128m -jar /opt/payment-service/target/payment-service-2.1.0.jar
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF""",
        
        # Start the service
        "sudo systemctl daemon-reload",
        "sudo systemctl enable payment-service",
        "sudo systemctl restart payment-service",
        "sleep 5",
        
        # Check status
        "sudo systemctl status payment-service --no-pager",
        "echo",
        "echo '📊 Testing endpoints:'",
        "curl -s http://localhost:8080/ | jq . || echo 'Main endpoint not ready'",
        "curl -s http://localhost:8080/health | jq . || echo 'Health endpoint not ready'",
        "curl -s http://localhost:8080/actuator/health | jq . || echo 'Actuator not ready'",
        
        # Start CloudWatch agent
        "echo",
        "echo '☁️ Starting CloudWatch agent...'",
        "sudo systemctl start amazon-cloudwatch-agent || echo 'CloudWatch agent start failed'",
        
        "echo",
        "echo '✅ Deployment complete!'"
    ]
    
    try:
        print("📤 Sending deployment commands...")
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': deploy_commands
            },
            TimeoutSeconds=300
        )
        
        command_id = response['Command']['CommandId']
        print(f"Command ID: {command_id}")
        
        # Wait for deployment
        print("\n⏳ Deploying application (this may take 2-3 minutes)...")
        time.sleep(30)
        
        # Check results
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Deployment Output:")
        print("-" * 60)
        if result['StandardOutputContent']:
            # Show last part of output
            output_lines = result['StandardOutputContent'].split('\n')
            for line in output_lines[-50:]:
                print(line)
        
        if result['Status'] == 'Success':
            print("\n✅ Java application deployed successfully!")
            return True
        else:
            print(f"\n❌ Deployment failed: {result['Status']}")
            if result.get('StandardErrorContent'):
                print(f"Error: {result['StandardErrorContent']}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        return False

def setup_metrics_pusher():
    """Setup script to push JVM metrics to CloudWatch"""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("\n📊 Setting up metrics collection...")
    
    metrics_script = """#!/bin/bash
# Push JVM metrics to CloudWatch

INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
NAMESPACE="JavaApp/SpringBoot"

while true; do
    # Get health data
    HEALTH=$(curl -s http://localhost:8080/health)
    
    if [ $? -eq 0 ]; then
        # Extract metrics
        CACHE_SIZE=$(echo "$HEALTH" | jq -r '.cacheSize // 0')
        MEM_PERCENT=$(echo "$HEALTH" | jq -r '.memoryPercent // 0')
        
        # Get actuator metrics
        JVM_USED=$(curl -s http://localhost:8080/actuator/metrics/jvm.memory.used | jq -r '.measurements[0].value // 0' 2>/dev/null)
        GC_PAUSE=$(curl -s http://localhost:8080/actuator/metrics/jvm.gc.pause | jq -r '.measurements[0].value // 0' 2>/dev/null)
        THREADS=$(curl -s http://localhost:8080/actuator/metrics/jvm.threads.live | jq -r '.measurements[0].value // 0' 2>/dev/null)
        
        # Push to CloudWatch
        aws cloudwatch put-metric-data \
            --namespace "$NAMESPACE" \
            --metric-data \
            "[
                {
                    \"MetricName\": \"HeapMemoryUsed\",
                    \"Value\": $MEM_PERCENT,
                    \"Unit\": \"Percent\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                },
                {
                    \"MetricName\": \"App_CacheSize\",
                    \"Value\": $CACHE_SIZE,
                    \"Unit\": \"Count\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                },
                {
                    \"MetricName\": \"JVM_HeapUsedPercent\",
                    \"Value\": $MEM_PERCENT,
                    \"Unit\": \"Percent\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                }
            ]" \
            --region us-east-1
        
        echo "$(date): Pushed metrics - Cache: $CACHE_SIZE, Memory: ${MEM_PERCENT}%"
    else
        echo "$(date): Application not responding"
    fi
    
    sleep 60
done
"""
    
    commands = [
        f"cat > /opt/monitoring/scripts/push_metrics.sh << 'EOF'\n{metrics_script}\nEOF",
        "chmod +x /opt/monitoring/scripts/push_metrics.sh",
        "pkill -f push_metrics.sh || true",
        "nohup /opt/monitoring/scripts/push_metrics.sh > /var/log/push_metrics.log 2>&1 &",
        "echo 'Metrics pusher started'"
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands}
        )
        print("✅ Metrics collection script deployed")
        return True
    except Exception as e:
        print(f"❌ Error setting up metrics: {e}")
        return False

if __name__ == "__main__":
    if deploy_java_app():
        setup_metrics_pusher()
        
        print("\n📊 Next Steps:")
        print("1. Wait 2-3 minutes for metrics to start flowing")
        print("2. Check Grafana dashboard: http://localhost:3000/d/java-app-monitoring")
        print("3. Run test suite: python3 test_jvm_monitoring_complete.py")
        
        print("\n🔗 Application Endpoints:")
        print("   Main: http://SRE-DEMO:8080/")
        print("   Health: http://SRE-DEMO:8080/health")
        print("   Actuator: http://SRE-DEMO:8080/actuator/health")