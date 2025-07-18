#!/bin/bash

echo "Testing ClickHouse connection..."
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Testing local connection:"
curl -s "http://localhost:8123/" && echo "✅ Local connection works"

echo ""
echo "Testing network connection:"
curl -s "http://$LOCAL_IP:8123/" && echo "✅ Network connection works"

echo ""
echo "Testing authenticated connection:"
curl -u admin:secret123 -s "http://$LOCAL_IP:8123/" && echo "✅ Authenticated connection works"

echo ""
echo "Testing query:"
curl -u admin:secret123 -s "http://$LOCAL_IP:8123/" -d "SELECT 'Hello from ClickHouse!'" && echo ""

echo ""
echo "Connection endpoints:"
echo "- Local: http://localhost:8123"
echo "- Network: http://$LOCAL_IP:8123"
echo "- TCP: $LOCAL_IP:9000"