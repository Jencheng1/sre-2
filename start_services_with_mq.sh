#\!/bin/bash

echo "========================================"
echo "STARTING SERVICES WITH MQ CREDENTIALS"
echo "========================================"

# Stop existing services
pkill -f "java.*bank-a" || true
pkill -f "java.*bank-b" || true

echo "Starting Bank A with MQ credentials..."
cd banking_demo/bank-a
nohup java -Xmx256m -Xms128m \
  -Dspring.jms.template.default-destination=PAYMENT.REQUEST \
  -Dspring.jms.listener.concurrency=1-5 \
  -Dibm.mq.queueManager=QM1 \
  -Dibm.mq.channel=PAYMENT.CHANNEL \
  -Dibm.mq.connName='localhost(1414)' \
  -Dibm.mq.user=app \
  -Dibm.mq.password=passw0rd \
  -jar bank-a.jar > bank-a.log 2>&1 &
cd ../..

echo "Starting Bank B with MQ credentials..."
cd banking_demo/bank-b
nohup java -Xmx256m -Xms128m \
  -Dserver.servlet.context-path=/api \
  -Dspring.jms.template.default-destination=PAYMENT.RESPONSE \
  -Dspring.jms.listener.concurrency=1-5 \
  -Dibm.mq.queueManager=QM1 \
  -Dibm.mq.channel=PAYMENT.CHANNEL \
  -Dibm.mq.connName='localhost(1414)' \
  -Dibm.mq.user=app \
  -Dibm.mq.password=passw0rd \
  -jar bank-b.jar > bank-b.log 2>&1 &
cd ../..

echo "Waiting for services to start (40 seconds)..."
sleep 40

echo ""
echo "Checking service status:"
curl -s http://localhost:8081/actuator/health  < /dev/null |  jq -r '.status' | xargs -I {} echo "Bank A: {}"
curl -s http://localhost:8082/api/actuator/health | jq -r '.status' | xargs -I {} echo "Bank B: {}"

echo ""
echo "✅ Services started with MQ credentials\!"
echo ""
echo "Services running:"
echo "  - Bank A: http://localhost:8081"
echo "  - Bank B: http://localhost:8082"
echo "  - IBM MQ: localhost:1414"
echo "  - Jaeger: http://localhost:16686"
