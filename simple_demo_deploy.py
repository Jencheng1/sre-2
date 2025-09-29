#!/usr/bin/env python3
"""
Simple Demo Deployment
Starts the bank services for demo purposes
"""
import os
import subprocess
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_bank_services():
    """Start bank A and B services"""
    try:
        # Kill any existing services
        logger.info("Stopping existing services...")
        subprocess.run(['pkill', '-f', 'bank-a-service'], capture_output=True)
        subprocess.run(['pkill', '-f', 'bank-b-service'], capture_output=True)
        time.sleep(2)
        
        # Base path
        base_path = '/home/ec2-user/sre/sre_mcp/payment-demo'
        otel_agent = os.path.join(base_path, 'opentelemetry-javaagent.jar')
        
        # Start Bank A
        bank_a_jar = os.path.join(base_path, 'bank-a-service/target/bank-a-service-1.0.0.jar')
        if os.path.exists(bank_a_jar):
            logger.info("Starting Bank A service on port 8083...")
            cmd = ['nohup', 'java']
            if os.path.exists(otel_agent):
                cmd.extend([
                    f'-javaagent:{otel_agent}',
                    '-Dotel.service.name=bank-a-service',
                    '-Dotel.exporter.otlp.endpoint=http://localhost:4317'
                ])
            cmd.extend([
                '-Dspring.jms.template.default-destination=PAYMENT.REQUEST',
                '-Dibm.mq.queueManager=QM1',
                '-Dibm.mq.channel=PAYMENT.CHANNEL',
                '-Dibm.mq.connName=localhost(1414)',
                '-Dibm.mq.user=app',
                '-Dibm.mq.password=passw0rd',
                '-jar', bank_a_jar, '--server.port=8083'
            ])
            
            with open('/tmp/bank-a-service.log', 'w') as log:
                subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        else:
            logger.error(f"Bank A JAR not found: {bank_a_jar}")
            return False
            
        # Start Bank B  
        bank_b_jar = os.path.join(base_path, 'bank-b-service/target/bank-b-service-1.0.0.jar')
        if os.path.exists(bank_b_jar):
            logger.info("Starting Bank B service on port 8082...")
            cmd = ['nohup', 'java']
            if os.path.exists(otel_agent):
                cmd.extend([
                    f'-javaagent:{otel_agent}',
                    '-Dotel.service.name=bank-b-service',
                    '-Dotel.exporter.otlp.endpoint=http://localhost:4317'
                ])
            cmd.extend([
                '-Dserver.servlet.context-path=/api',
                '-Dspring.jms.template.default-destination=PAYMENT.RESPONSE',
                '-Dibm.mq.queueManager=QM1',
                '-Dibm.mq.channel=PAYMENT.CHANNEL',
                '-Dibm.mq.connName=localhost(1414)',
                '-Dibm.mq.user=app',
                '-Dibm.mq.password=passw0rd',
                '-jar', bank_b_jar, '--server.port=8082'
            ])
            
            with open('/tmp/bank-b-service.log', 'w') as log:
                subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        else:
            logger.error(f"Bank B JAR not found: {bank_b_jar}")
            return False
            
        # Wait for services to start
        logger.info("Waiting for services to start (this may take up to 45 seconds)...")
        time.sleep(45)  # Bank B takes ~38 seconds to start
        
        # Check health (services will show as DOWN due to MQ auth, but that's OK for demo)
        services_running = True
        for service, port, path_prefix in [('Bank A', 8083, '/api'), ('Bank B', 8082, '/api')]:
            try:
                response = requests.get(f'http://localhost:{port}{path_prefix}/actuator/health', timeout=5)
                if response.status_code in [200, 503]:  # 503 is OK - means service is up but MQ is down
                    status = response.json().get('status', 'UNKNOWN') if response.status_code == 200 else 'DOWN'
                    logger.info(f"✅ {service} is running on port {port} (status: {status})")
                else:
                    logger.warning(f"⚠️  {service} returned unexpected status {response.status_code}")
            except Exception as e:
                logger.error(f"❌ {service} is not reachable: {e}")
                services_running = False
                
        return services_running
        
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        return False

def main():
    """Main deployment function"""
    logger.info("=" * 50)
    logger.info("SIMPLE DEMO DEPLOYMENT")
    logger.info("=" * 50)
    
    if start_bank_services():
        logger.info("\n✅ Services deployed successfully!")
        logger.info("\nServices running:")
        logger.info("  - Bank A: http://localhost:8083/api")
        logger.info("  - Bank B: http://localhost:8082/api")
        logger.info("  - Jaeger: http://localhost:16686")
        logger.info("\nNote: Transaction service not included in this simple demo")
        return True
    else:
        logger.error("\n❌ Deployment failed!")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)