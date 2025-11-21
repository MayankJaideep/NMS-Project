#!/bin/bash
# SCNMS Start Script
# Quick start script for SCNMS

set -e

echo "Starting SCNMS services..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from template..."
    cp .env.example .env
fi

# Start all services
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."
echo ""

services=("postgres:5432" "redis:6379" "prometheus:9090" "grafana:3000" "api:8000")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if docker-compose ps | grep -q "$name.*Up"; then
        echo "✓ $name is running"
    else
        echo "✗ $name is not running"
    fi
done

echo ""
echo "================================"
echo "SCNMS Started Successfully!"
echo "================================"
echo ""
echo "Access URLs:"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "View logs: docker-compose logs -f [service-name]"
echo "Stop services: docker-compose down"
echo ""
