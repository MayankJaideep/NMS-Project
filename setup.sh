#!/bin/bash
# SCNMS Setup Script
# This script sets up the development or production environment

set -e

echo "================================"
echo "SCNMS Setup Script"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please update with your configuration."
else
    echo "✓ .env file already exists."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p config/grafana/provisioning/datasources
mkdir -p config/grafana/provisioning/dashboards
mkdir -p config/grafana/dashboards
mkdir -p logs
mkdir -p data/prometheus
mkdir -p data/grafana
mkdir -p data/postgres
echo "✓ Directories created."

# Set permissions
echo "Setting permissions..."
chmod -R 755 config
chmod +x setup.sh
echo "✓ Permissions set."

# Pull Docker images
echo "Pulling Docker images..."
docker-compose pull

# Build custom images
echo "Building SCNMS services..."
docker-compose build

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run: docker-compose up -d"
echo "3. Access services:"
echo "   - API: http://localhost:8000/docs"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo ""
