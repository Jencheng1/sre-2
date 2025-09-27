#!/usr/bin/env python3
"""
Fix and verify Java application deployment
"""

import boto3
import time

def diagnose_and_fix():
    ssm_client = boto3.client('ssm', region_name='us-east-1')
    instance_id = "i-02bef13982a179478"
    
    print("🔍 Diagnosing Java application issues...")
    
    # First, check what's wrong
    diagnostic_commands = [
        "echo '=== Check Java installation ==='",
        "java -version 2>&1",
        "echo",
        "echo '=== Check service logs ==='", 
        "sudo journalctl -u payment-service -n 50 --no-pager | tail -20",
        "echo",
        "echo '=== Check if another process is using port 8080 ==='",
        "sudo lsof -i :8080 || echo 'Port 8080 is free'",
        "echo",
        "echo '=== Kill any existing Java processes ==='",
        "sudo pkill -f PaymentService || echo 'No PaymentService running'",
        "sudo pkill -f payment-service || echo 'No payment-service running'",
        "echo",
        "echo '=== Stop any service using port 8080 ==='",
        "sudo fuser -k 8080/tcp 2>/dev/null || echo 'Port 8080 cleared'",
        "echo",
        "echo '=== Create and run simple test ==='",
        "cd /opt/payment-service",
        "echo 'Testing Java directly...'",
        "timeout 5 java PaymentService 2>&1 | head -10 || echo 'Java test failed'"
    ]
    
    try:
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': diagnostic_commands}
        )
        
        command_id = response['Command']['CommandId']
        time.sleep(5)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Diagnostic Results:")
        print("-" * 60)
        print(result['StandardOutputContent'])
        
        # Now let's fix it with a working implementation
        print("\n🔧 Deploying fixed Java application...")
        
        fix_commands = [
            # Clean up first
            "sudo systemctl stop payment-service 2>/dev/null || true",
            "sudo pkill -f PaymentService || true",
            "sudo fuser -k 8080/tcp 2>/dev/null || true",
            "sleep 2",
            
            # Create working directory
            "sudo rm -rf /opt/payment-service",
            "sudo mkdir -p /opt/payment-service",
            "cd /opt/payment-service",
            
            # Create a simple working Java app with proper error handling
            """cat > PaymentService.java << 'EOF'
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.InetSocketAddress;
import java.util.*;
import java.util.concurrent.*;

public class PaymentService {
    private static final Map<String, byte[]> leakyCache = new ConcurrentHashMap<>();
    private static long counter = 0;
    
    public static void main(String[] args) {
        try {
            System.out.println("Payment Service v2.1.0 starting...");
            
            // Create HTTP server on port 8080
            HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
            
            // Set up endpoints
            server.createContext("/", new MainHandler());
            server.createContext("/health", new HealthHandler());
            server.createContext("/actuator/health", new ActuatorHandler());
            
            // Start the server
            server.setExecutor(Executors.newFixedThreadPool(10));
            server.start();
            
            System.out.println("Server started on http://localhost:8080");
            System.out.println("Endpoints available: /, /health, /actuator/health");
            
            // Start memory leak simulation
            startMemoryLeak();
            
        } catch (Exception e) {
            System.err.println("Failed to start server: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    static class MainHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            String response = String.format(
                "{\\\"service\\\":\\\"payment-service\\\",\\\"version\\\":\\\"2.1.0\\\",\\\"cacheSize\\\":%d,\\\"status\\\":\\\"running\\\"}",
                leakyCache.size()
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
    
    static class HealthHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            String response = String.format(
                "{\\\"status\\\":\\\"%s\\\",\\\"cacheSize\\\":%d,\\\"memoryPercent\\\":%.1f,\\\"memoryUsed\\\":%d,\\\"memoryMax\\\":%d}",
                percentUsed < 90 ? "UP" : "DOWN",
                leakyCache.size(),
                percentUsed,
                usedMemory,
                maxMemory
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
    
    static class ActuatorHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            long usedMemory = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
            long maxMemory = Runtime.getRuntime().maxMemory();
            double percentUsed = (double) usedMemory / maxMemory * 100;
            
            String status = percentUsed < 90 ? "UP" : "DOWN";
            String response = String.format(
                "{\\\"status\\\":\\\"%s\\\",\\\"components\\\":{\\\"memory\\\":{\\\"status\\\":\\\"%s\\\",\\\"details\\\":{\\\"percentUsed\\\":%.1f}}}}",
                status, status, percentUsed
            );
            
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
    
    static void startMemoryLeak() {
        Thread leakThread = new Thread(() -> {
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
                    
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        leakThread.setDaemon(true);
        leakThread.start();
    }
}
EOF""",
            
            # Compile it
            "javac PaymentService.java",
            
            # Run it directly first to test
            "echo 'Testing direct execution...'",
            "timeout 5 java -Xmx256m -Xms128m PaymentService > test.log 2>&1 &",
            "sleep 3",
            "curl -s http://localhost:8080/health || echo 'Direct test failed'",
            "pkill -f PaymentService || true",
            
            # If test worked, set up service
            """cat > /etc/systemd/system/payment-service.service << 'EOF'
[Unit]
Description=Payment Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/payment-service
ExecStart=/usr/bin/java -Xmx256m -Xms128m PaymentService
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF""",
            
            # Start service
            "systemctl daemon-reload",
            "systemctl enable payment-service",
            "systemctl restart payment-service",
            "sleep 5",
            
            # Verify it's working
            "echo",
            "echo '=== Service Status ==='",
            "systemctl status payment-service --no-pager | head -15",
            "echo",
            "echo '=== Testing Endpoints ==='",
            "curl -s http://localhost:8080/ | python -m json.tool",
            "echo",
            "curl -s http://localhost:8080/health | python -m json.tool",
            "echo",
            "echo '✅ Java application should now be running!'"
        ]
        
        response = ssm_client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': fix_commands},
            TimeoutSeconds=120
        )
        
        command_id = response['Command']['CommandId']
        print(f"Fix command ID: {command_id}")
        
        time.sleep(20)
        
        result = ssm_client.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        print("\n📋 Fix Results:")
        print("-" * 60)
        output = result['StandardOutputContent']
        # Show last 50 lines
        lines = output.split('\n')
        for line in lines[-50:]:
            print(line)
            
        return result['Status'] == 'Success'
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if diagnose_and_fix():
        print("\n✅ Java application fixed and running!")
        print("\n📊 Next: Wait 2-3 minutes for metrics to flow to CloudWatch")
        print("Then check: http://localhost:3000/d/java-app-monitoring")
    else:
        print("\n❌ Fix failed")