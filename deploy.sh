#!/bin/bash

echo "🚀 Deploying Abtoban Bot..."
echo "================================"

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop containers
echo "⏹️ Stopping containers..."
docker compose down

# Build and start containers
echo "🔨 Building and starting containers..."
docker compose up -d --build

# Show status
echo "📊 Container status:"
docker compose ps

echo ""
echo "✅ Deployment complete!"
echo "📋 Check logs with: docker compose logs -f bot"
