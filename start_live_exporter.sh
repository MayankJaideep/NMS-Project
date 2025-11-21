#!/bin/bash

echo "========================================================================"
echo "  🚀 NMS LIVE DATA EXPORTER - STARTUP SCRIPT"
echo "========================================================================"
echo ""

# Check if prometheus-client is installed
echo "📦 Checking dependencies..."
if python3 -c "import prometheus_client" 2>/dev/null; then
    echo "✅ prometheus-client is installed"
else
    echo "⚠️  prometheus-client not found. Installing..."
    pip3 install prometheus-client
    if [ $? -eq 0 ]; then
        echo "✅ prometheus-client installed successfully"
    else
        echo "❌ Failed to install prometheus-client"
        echo "   Try manually: pip3 install prometheus-client"
        exit 1
    fi
fi

echo ""
echo "========================================================================"
echo "  ✅ Starting NMS Live Data Exporter..."
echo "========================================================================"
echo ""
echo "  📊 Metrics will be available at: http://localhost:9001/metrics"
echo "  🔄 Data updates every 5 seconds"
echo "  ⏹️  Press Ctrl+C to stop"
echo ""
echo "========================================================================"
echo ""

# Start the exporter
python3 app_exporter.py
