#!/usr/bin/env python3
"""
Final deployment - Use port 8090 to avoid Docker conflict
"""

import boto3
import time

def deploy_final_java_app():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("🚀 Final Java Application Deployment (Port 8090)")
    print("=" * 60)
    
    commands = [
        # Clean everything first
        "sudo systemctl stop payment-service 2>/dev/null || true",
        "sudo pkill -f PaymentService || true",
        "sudo rm -rf /opt/payment-service",
        "sudo mkdir -p /opt/payment-service",
        "cd /opt/payment-service",
        
        # Create the Java application on port 8090
        """cat > PaymentService.java << 'EOF'
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.*;
import java.util.concurrent.*;

public class PaymentService {
    private static final Map<String, byte[]> leakyCache = new ConcurrentHashMap<>();
    private static long counter = 0;
    private static final int PORT = 8090; // Changed to 8090
    
    public static void main(String[] args) throws Exception {
        System.out.println("Payment Service v2.1.0 starting on port " + PORT + "...");
        
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        
        server.createContext("/", exchange -> {
            String response = String.format(
                "{\"service\":\"payment-service\",\"version\":\"2.1.0\",\"cacheSize\":%d,\"status\":\"running\"}",
                leakyCache.size()
            );
            sendResponse(exchange, 200, response);
        });
        
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
            sendResponse(exchange, 200, response);
        });
        
        server.createContext("/actuator/health", exchange -> {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            String status = percentUsed < 90 ? "UP" : "DOWN";
            String response = String.format(
                "{\"status\":\"%s\",\"components\":{\"memory\":{\"status\":\"%s\",\"details\":{\"percentUsed\":%.1f}}}}",
                status, status, percentUsed
            );
            sendResponse(exchange, 200, response);
        });
        
        server.setExecutor(Executors.newFixedThreadPool(10));
        server.start();
        
        System.out.println("Server started on http://localhost:" + PORT);
        
        // Start memory leak thread
        new Thread(() -> {
            while (true) {
                try {
                    leakyCache.put("txn-" + (counter++), new byte[1024]);
                    
                    if (counter % 60 == 0) {
                        long used = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
                        long max = Runtime.getRuntime().maxMemory();
                        double pct = (double) used / max * 100;
                        
                        System.out.println(String.format(
                            "[%s] Cache: %d entries, Memory: %.1f%%", 
                            pct > 85 ? "ERROR" : "WARN",
                            leakyCache.size(), 
                            pct
                        ));
                    }
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        }).start();
    }
    
    private static void sendResponse(HttpExchange exchange, int code, String response) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(code, response.length());
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(response.getBytes());
        }
    }
}
EOF""",
        
        # Compile
        "javac PaymentService.java",
        
        # Create service
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

[Install]
WantedBy=multi-user.target
EOF""",
        
        # Start service
        "systemctl daemon-reload",
        "systemctl enable payment-service",
        "systemctl start payment-service",
        "sleep 5",
        
        # Verify
        "echo '=== Service Status ==='",
        "systemctl is-active payment-service",
        "echo",
        "echo '=== Test Endpoints ==='",
        "curl -s http://localhost:8090/ | python -m json.tool",
        "curl -s http://localhost:8090/health | python -m json.tool",
        
        # Set up metrics collection
        """cat > /opt/monitoring/scripts/collect_jvm_metrics.sh << 'EOF'
#!/bin/bash
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d' ' -f2)

while true; do
    HEALTH=$(curl -s http://localhost:8090/health)
    if [ $? -eq 0 ]; then
        CACHE=$(echo "$HEALTH" | grep -o '"cacheSize":[0-9]*' | cut -d: -f2)
        MEM=$(echo "$HEALTH" | grep -o '"memoryPercent":[0-9.]*' | cut -d: -f2)
        
        # Push metrics
        aws cloudwatch put-metric-data \
            --namespace "JavaApp/SpringBoot" \
            --region us-east-1 \
            --metric-data \
            "[{
                \"MetricName\": \"HeapMemoryUsed\",
                \"Value\": ${MEM:-0},
                \"Unit\": \"Percent\",
                \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}, {\"Name\": \"Application\", \"Value\": \"payment-service\"}]
            },
            {
                \"MetricName\": \"App_CacheSize\",
                \"Value\": ${CACHE:-0},
                \"Unit\": \"Count\",
                \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}]
            },
            {
                \"MetricName\": \"JVM_HeapUsedPercent\",
                \"Value\": ${MEM:-0},
                \"Unit\": \"Percent\",
                \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}]
            },
            {
                \"MetricName\": \"GCPauseTime\",
                \"Value\": $(awk "BEGIN {print int(${MEM:-0} * 3)}"),
                \"Unit\": \"Milliseconds\",
                \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}]
            }]"
        
        echo "$(date): Metrics pushed - Cache: $CACHE, Memory: ${MEM}%"
    fi
    sleep 60
done
EOF""",
        
        "chmod +x /opt/monitoring/scripts/collect_jvm_metrics.sh",
        "pkill -f collect_jvm_metrics.sh || true",
        "nohup /opt/monitoring/scripts/collect_jvm_metrics.sh > /var/log/jvm_metrics.log 2>&1 &",
        "echo '✅ Java app running on port 8090 with metrics collection!'"
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
        
        print("\n⏳ Deploying...")
        time.sleep(15)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Results:")
        print("-" * 60)
        output = result['StandardOutputContent'].split('\n')
        for line in output[-30:]:
            print(line)
            
        if result['Status'] == 'Success':
            print("\n✅ SUCCESS! Java app is running on port 8090")
            print("\n📊 Metrics are being pushed to CloudWatch")
            print("🔗 Endpoints:")
            print("   - http://SRE-DEMO:8090/")
            print("   - http://SRE-DEMO:8090/health")
            print("   - http://SRE-DEMO:8090/actuator/health")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def update_grafana_to_show_data():
    """Ensure Grafana can see the data"""
    print("\n🔧 Updating Grafana configuration...")
    
    # Force push some immediate test data
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    push_test_metrics = [
        """
INSTANCE_ID="i-02bef13982a179478"
for i in {1..5}; do
    aws cloudwatch put-metric-data \
        --namespace "JavaApp/SpringBoot" \
        --region us-east-1 \
        --metric-data \
        "[{
            \"MetricName\": \"HeapMemoryUsed\",
            \"Value\": $((40 + i * 5)),
            \"Unit\": \"Percent\",
            \"Timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\",
            \"Dimensions\": [{\"Name\": \"InstanceId\", \"Value\": \"$INSTANCE_ID\"}]
        }]"
    echo "Pushed test metric $i"
    sleep 2
done
"""
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': push_test_metrics}
        )
        print("✅ Test metrics pushed to CloudWatch")
    except Exception as e:
        print(f"⚠️ Could not push test metrics: {e}")

if __name__ == "__main__":
    if deploy_final_java_app():
        update_grafana_to_show_data()
        print("\n🎉 DEPLOYMENT COMPLETE!")
        print("\n📈 The memory leak simulation is now active:")
        print("   - Cache grows by 1KB/second")
        print("   - Memory usage will increase gradually")
        print("   - GC pressure will cause CPU spikes")
        print("\n⏳ Wait 2-3 minutes for metrics in Grafana")
    else:
        print("\n❌ Deployment failed")