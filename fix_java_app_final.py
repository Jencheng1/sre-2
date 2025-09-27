#!/usr/bin/env python3
"""
Fix Java application - deploy a simple working version
"""

import boto3
import time

def deploy_working_java_app():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("🔧 Fixing Java Application Deployment")
    print("=" * 60)
    
    commands = [
        # Stop any existing service
        "sudo systemctl stop payment-service 2>/dev/null || true",
        "sudo pkill -f PaymentService || true",
        "sudo pkill -f payment-service || true",
        "sleep 2",
        
        # Clean and recreate directory
        "sudo rm -rf /opt/payment-service",
        "sudo mkdir -p /opt/payment-service",
        "cd /opt/payment-service",
        
        # Create a simple Java HTTP server with memory leak
        """cat > PaymentService.java << 'EOF'
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.*;
import java.util.concurrent.*;

public class PaymentService {
    private static final Map<String, byte[]> leakyCache = new ConcurrentHashMap<>();
    private static long counter = 0;
    private static final int PORT = 8090;
    
    public static void main(String[] args) throws Exception {
        System.out.println("Payment Service v2.1.0 starting on port " + PORT + "...");
        
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        
        // Root endpoint
        server.createContext("/", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                String response = String.format(
                    "{\\"service\\":\\"payment-service\\",\\"version\\":\\"2.1.0\\",\\"cacheSize\\":%d,\\"status\\":\\"running\\"}",
                    leakyCache.size()
                );
                sendResponse(exchange, 200, response);
            }
        });
        
        // Health endpoint
        server.createContext("/health", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
                long maxMemory = Runtime.getRuntime().maxMemory();
                double percentUsed = (double) usedMemory / maxMemory * 100;
                
                String response = String.format(
                    "{\\"status\\":\\"%s\\",\\"cacheSize\\":%d,\\"memoryPercent\\":%.1f,\\"memoryUsed\\":%d,\\"memoryMax\\":%d}",
                    percentUsed < 90 ? "UP" : "DOWN",
                    leakyCache.size(),
                    percentUsed,
                    usedMemory,
                    maxMemory
                );
                sendResponse(exchange, 200, response);
            }
        });
        
        // Actuator health endpoint
        server.createContext("/actuator/health", new HttpHandler() {
            @Override
            public void handle(HttpExchange exchange) throws IOException {
                long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
                long maxMemory = Runtime.getRuntime().maxMemory();
                double percentUsed = (double) usedMemory / maxMemory * 100;
                
                String status = percentUsed < 90 ? "UP" : "DOWN";
                String response = String.format(
                    "{\\"status\\":\\"%s\\",\\"components\\":{\\"memory\\":{\\"status\\":\\"%s\\",\\"details\\":{\\"percentUsed\\":%.1f}}}}",
                    status, status, percentUsed
                );
                sendResponse(exchange, 200, response);
            }
        });
        
        server.setExecutor(Executors.newFixedThreadPool(10));
        server.start();
        
        System.out.println("Server started on http://localhost:" + PORT);
        System.out.println("Endpoints: /, /health, /actuator/health");
        
        // Start memory leak simulation thread
        Thread leakThread = new Thread(() -> {
            while (true) {
                try {
                    // Add 1KB to cache every second
                    String key = "txn-" + (counter++);
                    byte[] data = new byte[1024];
                    Arrays.fill(data, (byte)42);
                    leakyCache.put(key, data);
                    
                    // Log every minute
                    if (counter % 60 == 0) {
                        long used = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
                        long max = Runtime.getRuntime().maxMemory();
                        double pct = (double) used / max * 100;
                        
                        String level = pct > 85 ? "ERROR" : (pct > 70 ? "WARN" : "INFO");
                        System.out.println(String.format(
                            "[%s] Cache: %d entries, Memory: %.1f%% used",
                            level, leakyCache.size(), pct
                        ));
                        
                        if (pct > 85) {
                            System.out.println("[ERROR] Memory usage critical! GC overhead limit may be exceeded");
                        }
                    }
                    
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        leakThread.setDaemon(true);
        leakThread.start();
        
        System.out.println("Memory leak simulation started - adding 1KB/second");
    }
    
    private static void sendResponse(HttpExchange exchange, int code, String response) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(code, response.getBytes().length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(response.getBytes());
        }
    }
}
EOF""",
        
        # Compile the Java file
        "javac PaymentService.java",
        "ls -la",
        
        # Create systemd service with classpath
        """cat > /etc/systemd/system/payment-service.service << 'EOF'
[Unit]
Description=Payment Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/java -Xmx256m -Xms128m -cp /opt/payment-service PaymentService
WorkingDirectory=/opt/payment-service
Restart=always
RestartSec=5
User=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF""",
        
        # Reload and start service
        "systemctl daemon-reload",
        "systemctl enable payment-service",
        "systemctl start payment-service",
        "sleep 5",
        
        # Verify it's running
        "echo '=== Service Status ==='",
        "systemctl is-active payment-service",
        "systemctl status payment-service --no-pager | head -20",
        "echo",
        "echo '=== Port Check ==='",
        "netstat -tlpn | grep 8090 || ss -tlpn | grep 8090",
        "echo",
        "echo '=== Test Endpoints ==='",
        "curl -s http://localhost:8090/ | python -m json.tool",
        "echo",
        "curl -s http://localhost:8090/health | python -m json.tool",
        
        # Set up metrics collection
        "mkdir -p /opt/monitoring/scripts",
        """cat > /opt/monitoring/scripts/collect_jvm_metrics.sh << 'EOF'
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)

echo "Starting JVM metrics collection for $INSTANCE_ID"

while true; do
    HEALTH=$(curl -s http://localhost:8090/health 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$HEALTH" ]; then
        CACHE=$(echo "$HEALTH" | grep -o '"cacheSize":[0-9]*' | cut -d: -f2)
        MEM=$(echo "$HEALTH" | grep -o '"memoryPercent":[0-9.]*' | cut -d: -f2)
        
        CACHE=${CACHE:-0}
        MEM=${MEM:-0}
        
        # Calculate simulated metrics
        GC_PAUSE=$(awk "BEGIN {print int($MEM * 3)}")
        CPU_UTIL=$(awk "BEGIN {print 20 + ($MEM > 60 ? ($MEM - 60) * 2 : 0)}")
        
        # Push all metrics to CloudWatch
        aws cloudwatch put-metric-data \
            --namespace "JavaApp/SpringBoot" \
            --region us-east-1 \
            --metric-data \
            "[
                {
                    \\"MetricName\\": \\"HeapMemoryUsed\\",
                    \\"Value\\": ${MEM},
                    \\"Unit\\": \\"Percent\\",
                    \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}, {\\"Name\\": \\"Application\\", \\"Value\\": \\"payment-service\\"}]
                },
                {
                    \\"MetricName\\": \\"App_CacheSize\\",
                    \\"Value\\": ${CACHE},
                    \\"Unit\\": \\"Count\\",
                    \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}]
                },
                {
                    \\"MetricName\\": \\"JVM_HeapUsedPercent\\",
                    \\"Value\\": ${MEM},
                    \\"Unit\\": \\"Percent\\",
                    \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}]
                },
                {
                    \\"MetricName\\": \\"GCPauseTime\\",
                    \\"Value\\": ${GC_PAUSE},
                    \\"Unit\\": \\"Milliseconds\\",
                    \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}]
                }
            ]"
        
        echo "$(date): Pushed metrics - Cache: $CACHE, Memory: ${MEM}%, GC: ${GC_PAUSE}ms"
        
        # Also push a CPU spike metric when memory is high
        if (( $(echo "$MEM > 70" | bc -l) )); then
            aws cloudwatch put-metric-data \
                --namespace "SREDemo/Application" \
                --region us-east-1 \
                --metric-data \
                "[{
                    \\"MetricName\\": \\"CPUUtilization\\",
                    \\"Value\\": ${CPU_UTIL},
                    \\"Unit\\": \\"Percent\\",
                    \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}, {\\"Name\\": \\"InstanceName\\", \\"Value\\": \\"SRE-DEMO\\"}]
                }]"
            echo "   High memory detected - pushed CPU spike metric: ${CPU_UTIL}%"
        fi
    else
        echo "$(date): Application not responding, retrying..."
    fi
    sleep 60
done
EOF""",
        
        "chmod +x /opt/monitoring/scripts/collect_jvm_metrics.sh",
        "pkill -f collect_jvm_metrics.sh || true",
        "nohup /opt/monitoring/scripts/collect_jvm_metrics.sh > /var/log/jvm_metrics.log 2>&1 &",
        "echo",
        "echo '✅ Java application deployed and metrics collection started!'"
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands},
            TimeoutSeconds=120
        )
        
        command_id = response['Command']['CommandId']
        print(f"Command ID: {command_id}")
        
        print("\n⏳ Deploying application...")
        time.sleep(20)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Deployment Results:")
        print("-" * 60)
        if result['StandardOutputContent']:
            lines = result['StandardOutputContent'].split('\n')
            for line in lines[-60:]:
                print(line)
        
        if result['Status'] == 'Success':
            print("\n✅ Java application successfully deployed!")
            return True
        else:
            print(f"\n❌ Deployment failed: {result['Status']}")
            if result.get('StandardErrorContent'):
                print(f"Error: {result['StandardErrorContent']}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def push_initial_metrics():
    """Push some initial metrics to seed CloudWatch"""
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("\n📊 Pushing initial metrics to CloudWatch...")
    
    commands = [
        """
INSTANCE_ID="i-02bef13982a179478"
for i in {1..5}; do
    VALUE=$((35 + i * 5))
    aws cloudwatch put-metric-data \
        --namespace "JavaApp/SpringBoot" \
        --region us-east-1 \
        --metric-data \
        "[{
            \\"MetricName\\": \\"HeapMemoryUsed\\",
            \\"Value\\": $VALUE,
            \\"Unit\\": \\"Percent\\",
            \\"Timestamp\\": \\"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\\",
            \\"Dimensions\\": [{\\"Name\\": \\"InstanceId\\", \\"Value\\": \\"$INSTANCE_ID\\"}]
        }]"
    echo "Pushed test metric $i: $VALUE%"
    sleep 2
done
echo "Initial metrics pushed"
"""
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': commands}
        )
        print("✅ Initial metrics pushed")
    except Exception as e:
        print(f"⚠️ Could not push initial metrics: {e}")

if __name__ == "__main__":
    if deploy_working_java_app():
        push_initial_metrics()
        
        print("\n🎉 DEPLOYMENT COMPLETE!")
        print("\n📊 The Java application is now running:")
        print("   - Port: 8090")
        print("   - Memory leak: 1KB/second")
        print("   - Metrics pushed every 60 seconds")
        print("   - CPU spike correlation when memory > 70%")
        
        print("\n🔗 Test the endpoints:")
        print("   curl http://SRE-DEMO:8090/")
        print("   curl http://SRE-DEMO:8090/health")
        
        print("\n⏳ Next steps:")
        print("   1. Wait 2-3 minutes for metrics")
        print("   2. Check Grafana dashboards")
        print("   3. Run verification test")
    else:
        print("\n❌ Deployment failed")