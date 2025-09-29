#!/bin/bash
# Fix IBM MQ Authentication Issues

echo "========================================"
echo "FIXING IBM MQ AUTHENTICATION"
echo "========================================"

# Set up MQ authentication for the demo user
echo "1. Setting up MQ user permissions..."

# Create and configure the app user in MQ
docker exec payment-ibm-mq bash -c "
# Disable channel authentication for demo purposes
echo 'ALTER QMGR CHLAUTH(DISABLED)' | runmqsc QM1

# Set connection authentication to optional
echo 'ALTER QMGR CONNAUTH(\"\")' | runmqsc QM1
echo 'REFRESH SECURITY TYPE(CONNAUTH)' | runmqsc QM1

# Grant full permissions to all users for demo
echo 'SET AUTHREC OBJTYPE(QMGR) PRINCIPAL(\"*\") AUTHADD(ALL)' | runmqsc QM1
echo 'SET AUTHREC OBJTYPE(QUEUE) PROFILE(\"*\") PRINCIPAL(\"*\") AUTHADD(ALL)' | runmqsc QM1
echo 'SET AUTHREC OBJTYPE(TOPIC) PROFILE(\"*\") PRINCIPAL(\"*\") AUTHADD(ALL)' | runmqsc QM1
echo 'SET AUTHREC OBJTYPE(CHANNEL) PROFILE(\"*\") PRINCIPAL(\"*\") AUTHADD(ALL)' | runmqsc QM1

# Display the changes
echo 'DISPLAY QMGR CHLAUTH' | runmqsc QM1
"

echo ""
echo "2. Creating required queues..."
docker exec payment-ibm-mq bash -c "
echo 'DEFINE QLOCAL(PAYMENT.REQUEST) REPLACE' | runmqsc QM1
echo 'DEFINE QLOCAL(PAYMENT.RESPONSE) REPLACE' | runmqsc QM1
echo 'DEFINE QLOCAL(PAYMENT.TRANSFER.QUEUE) REPLACE' | runmqsc QM1
echo 'DISPLAY QLOCAL(PAYMENT.*)' | runmqsc QM1
"

echo ""
echo "3. Restarting MQ to apply changes..."
docker restart payment-ibm-mq

# Wait for MQ to start
echo "Waiting for MQ to restart..."
sleep 10

# Check MQ status
echo ""
echo "4. Checking MQ status..."
docker exec payment-ibm-mq dspmq

echo ""
echo "✅ MQ authentication fix complete!"
echo ""
echo "Now restart the bank services:"
echo "  ./deploy_memory_leak.sh"