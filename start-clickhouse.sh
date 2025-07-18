#!/bin/bash

echo "Starting ClickHouse Docker container..."

# Create necessary directories
mkdir -p data logs

# Start the container
docker-compose up -d

# Wait for container to be ready
echo "Waiting for ClickHouse to start..."
sleep 10

# Check if it's running
if docker-compose ps | grep -q "Up"; then
    echo "✅ ClickHouse is running!"
    echo ""
    echo "Connection Information:"
    echo "======================"
    echo "HTTP Interface: http://$(hostname -I | awk '{print $1}'):8123"
    echo "TCP Interface: $(hostname -I | awk '{print $1}'):9000"
    echo ""
    echo "Users:"
    echo "- default (no password) - for local testing"
    echo "- admin (password: secret123) - full access"
    echo "- readonly (password: readonly123) - read-only access"
    echo ""
    echo "Test connection from another computer:"
    echo "curl -u admin:secret123 http://$(hostname -I | awk '{print $1}'):8123/"
    echo ""
    echo "View logs with: docker-compose logs -f"
else
    echo "❌ Failed to start ClickHouse"
    docker-compose logs
fi
