#!/bin/bash

SERVER="91.229.91.147"
PASS="%56EM6wNxI%V"
SERVICE="avtoban-bot"

echo "🚀 Deploying to Avtoban Server..."
echo "================================"

# Clone/update repo first if needed
echo "📦 Setting up repository..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$SERVER 'if [ ! -d /opt/abtoban ]; then git clone https://github.com/wind86861-lab/abtoban.git /opt/abtoban; fi'

# Deploy to server
echo "📦 Deploying code to server..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$SERVER 'cd /opt/abtoban && git pull origin main'

# Restart service
echo "🔄 Restarting bot service..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$SERVER 'systemctl restart avtoban-bot'

# Show logs
echo "📋 Showing bot logs (Ctrl+C to stop)..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$SERVER "journalctl -u $SERVICE --no-pager -f --since 'now'"
