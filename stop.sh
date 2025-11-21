#!/bin/bash
# SCNMS Stop Script
# Gracefully stop all SCNMS services

set -e

echo "Stopping SCNMS services..."
docker-compose down

echo ""
echo "✓ All services stopped."
echo ""
echo "To remove volumes (WARNING: This will delete all data):"
echo "  docker-compose down -v"
echo ""
