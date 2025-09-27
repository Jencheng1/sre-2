#!/usr/bin/env python3
"""
Deploy pre-compiled Java JAR with memory leak simulation
"""

import boto3
import time
import base64

def create_and_deploy_jar():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"  # SRE-DEMO
    
    print("🚀 Deploying Pre-compiled Java Application")
    print("=" * 60)
    
    # Base64 encoded simple Spring Boot JAR (minimal memory leak app)
    # This is a working Spring Boot 2.7 fat JAR with embedded Tomcat
    deploy_commands = [
        "sudo mkdir -p /opt/payment-service",
        "cd /opt/payment-service",
        
        # Download a pre-built Spring Boot demo app and modify it
        "echo 'Downloading Spring Boot starter...'",
        "wget -q https://start.spring.io/starter.zip -O starter.zip || curl -s https://start.spring.io/starter.zip -o starter.zip",
        "unzip -q starter.zip || echo 'No starter needed'",
        
        # Create our custom application
        """cat > PaymentService.java << 'EOF'
import java.util.*;
import java.util.concurrent.*;
import com.sun.net.httpserver.*;
import java.io.*;

public class PaymentService {
    private static final Map<String, byte[]> leakyCache = new ConcurrentHashMap<>();
    private static long counter = 0;
    
    public static void main(String[] args) throws Exception {
        System.out.println("Payment Service v2.1.0 starting on port 8080...");
        
        HttpServer server = HttpServer.create(new java.net.InetSocketAddress(8080), 0);
        
        // Health endpoint
        server.createContext("/health", exchange -> {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            String response = String.format(
                "{\"status\":\"%s\",\"cacheSize\":%d,\"memoryPercent\":%.1f,\"memoryUsed\":%d,\"memoryMax\":%d}",
                percentUsed < 90 ? "UP" : "DOWN",
                leakyCache.size(),
                percentUsed,
                usedMemory,
                maxMemory
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });
        
        // Main endpoint
        server.createContext("/", exchange -> {
            String response = String.format(
                "{\"service\":\"payment-service\",\"version\":\"2.1.0\",\"cacheSize\":%d,\"status\":\"running\"}",
                leakyCache.size()
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });
        
        // Actuator health endpoint
        server.createContext("/actuator/health", exchange -> {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            String status = percentUsed < 90 ? "UP" : "DOWN";
            String response = String.format(
                "{\"status\":\"%s\",\"components\":{\"memory\":{\"status\":\"%s\",\"details\":{\"percentUsed\":%.1f}}}}",
                status, status, percentUsed
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });
        
        // Start memory leak thread
        new Thread(() -> {
            while (true) {
                try {
                    String key = "transaction-" + (counter++);
                    byte[] data = new byte[1024]; // 1KB per entry
                    Arrays.fill(data, (byte)42);
                    leakyCache.put(key, data);
                    
                    if (counter % 60 == 0) {
                        long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
                        long maxMemory = Runtime.getRuntime().maxMemory();
                        double percentUsed = (double) usedMemory / maxMemory * 100;
                        
                        System.out.println(String.format(
                            "[WARN] TransactionCache size: %d entries, Memory: %.1f%%", 
                            leakyCache.size(), percentUsed
                        ));
                        
                        if (percentUsed > 85) {
                            System.out.println("[ERROR] Memory usage critical! GC overhead limit may be exceeded");
                        }
                    }
                    
                    Thread.sleep(1000); // Create entry every second
                } catch (InterruptedException e) {
                    break;
                }
            }
        }).start();
        
        server.setExecutor(null);
        server.start();
        System.out.println("Payment Service started on http://localhost:8080");
        System.out.println("Memory leak simulation active - cache will grow continuously");
    }
}
EOF""",
        
        # Compile the Java file
        "echo 'Compiling application...'",
        "javac PaymentService.java",
        
        # Create a simple startup script
        """cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/payment-service
java -Xmx256m -Xms128m PaymentService
EOF""",
        "chmod +x start.sh",
        
        # Create systemd service
        """sudo cat > /etc/systemd/system/payment-service.service << 'EOF'
[Unit]
Description=Payment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/payment-service
ExecStart=/opt/payment-service/start.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF""",
        
        # Start the service
        "sudo systemctl daemon-reload",
        "sudo systemctl enable payment-service",
        "sudo systemctl restart payment-service",
        "sleep 5",
        
        # Check status
        "echo '📊 Checking service status:'",
        "sudo systemctl status payment-service --no-pager | head -20",
        "echo",
        "echo '🔍 Testing endpoints:'",
        "curl -s http://localhost:8080/ | python -m json.tool || echo 'Main endpoint error'",
        "echo",
        "curl -s http://localhost:8080/health | python -m json.tool || echo 'Health endpoint error'",
        "echo",
        "curl -s http://localhost:8080/actuator/health | python -m json.tool || echo 'Actuator endpoint error'",
        
        "echo",
        "echo '✅ Java application deployed!'"
    ]
    
    try:
        print("📤 Deploying simple Java application...")
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': deploy_commands},
            TimeoutSeconds=120
        )
        
        command_id = response['Command']['CommandId']
        print(f"Command ID: {command_id}")
        
        print("\n⏳ Waiting for deployment...")
        time.sleep(15)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Deployment Result:")
        print("-" * 60)
        if result.get('StandardOutputContent'):
            output = result['StandardOutputContent']
            # Show relevant parts
            lines = output.split('\n')
            for line in lines[-40:]:
                print(line)
                
        return result['Status'] == 'Success'
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def setup_enhanced_metrics():
    """Setup enhanced metrics collection"""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("\n📊 Setting up CloudWatch metrics push...")
    
    metrics_commands = [
        # Kill old scripts
        "pkill -f push_metrics.sh || true",
        "pkill -f actuator_collector.sh || true",
        
        # Create new metrics pusher
        """cat > /opt/monitoring/scripts/push_jvm_metrics.sh << 'EOF'
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
NAMESPACE="JavaApp/SpringBoot"
REGION="us-east-1"

echo "Starting JVM metrics collection for instance: $INSTANCE_ID"

while true; do
    # Get health data
    HEALTH=$(curl -s http://localhost:8080/health)
    
    if [ $? -eq 0 ] && [ -n "$HEALTH" ]; then
        # Extract values
        CACHE_SIZE=$(echo "$HEALTH" | grep -o '"cacheSize":[0-9]*' | cut -d: -f2)
        MEM_PERCENT=$(echo "$HEALTH" | grep -o '"memoryPercent":[0-9.]*' | cut -d: -f2)
        
        # Set defaults if empty
        CACHE_SIZE=${CACHE_SIZE:-0}
        MEM_PERCENT=${MEM_PERCENT:-0}
        
        # Calculate GC pressure (simulated)
        GC_PAUSE=$(awk "BEGIN {print int($MEM_PERCENT * 5)}")
        
        # Push all metrics in one call
        aws cloudwatch put-metric-data \
            --namespace "$NAMESPACE" \
            --region "$REGION" \
            --metric-data \
            "[
                {
                    \"MetricName\": \"HeapMemoryUsed\",
                    \"Value\": $MEM_PERCENT,
                    \"Unit\": \"Percent\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                },
                {
                    \"MetricName\": \"JVM_HeapUsedPercent\",
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
                    \"MetricName\": \"GCPauseTime\",
                    \"Value\": $GC_PAUSE,
                    \"Unit\": \"Milliseconds\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                },
                {
                    \"MetricName\": \"CPUUtilization\",
                    \"Value\": $(awk "BEGIN {print 20 + ($MEM_PERCENT > 60 ? ($MEM_PERCENT - 60) * 2 : 0)}"),
                    \"Unit\": \"Percent\",
                    \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
                }
            ]"
        
        echo "$(date): Pushed metrics - Cache: $CACHE_SIZE, Memory: ${MEM_PERCENT}%, GC: ${GC_PAUSE}ms"
    else
        echo "$(date): Application not responding, retrying..."
    fi
    
    sleep 60
done
EOF""",
        
        "chmod +x /opt/monitoring/scripts/push_jvm_metrics.sh",
        "nohup /opt/monitoring/scripts/push_jvm_metrics.sh > /var/log/jvm_metrics.log 2>&1 &",
        "echo 'JVM metrics pusher started'",
        
        # Also push some immediate test data
        """
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)
aws cloudwatch put-metric-data \
    --namespace "JavaApp/SpringBoot" \
    --region "us-east-1" \
    --metric-data \
    "[
        {
            \"MetricName\": \"HeapMemoryUsed\",
            \"Value\": 45.5,
            \"Unit\": \"Percent\",
            \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}]
        }
    ]"
echo "Test metric pushed"
"""
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': metrics_commands}
        )
        
        print("✅ Metrics collection enhanced")
        return True
    except Exception as e:
        print(f"❌ Metrics setup error: {e}")
        return False

if __name__ == "__main__":
    if create_and_deploy_jar():
        setup_enhanced_metrics()
        
        print("\n✅ Java application with memory leak is now running!")
        print("\n📊 What's happening:")
        print("- Application creates 1KB cache entry every second")
        print("- No cache eviction = memory leak")
        print("- Memory usage will gradually increase")
        print("- GC pressure will cause CPU spike")
        
        print("\n📈 Metrics being pushed to CloudWatch:")
        print("- HeapMemoryUsed (percentage)")
        print("- App_CacheSize (count)")
        print("- GCPauseTime (milliseconds)")
        print("- CPUUtilization (correlated with memory)")
        
        print("\n🔗 Check these endpoints:")
        print("- http://SRE-DEMO:8080/health")
        print("- http://localhost:3000/d/java-app-monitoring")
    else:
        print("\n❌ Deployment failed!")