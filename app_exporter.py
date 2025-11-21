#!/usr/bin/env python3
"""
Network Management System (NMS) Metrics Exporter
Generates live network data for Prometheus/Grafana visualization

This exporter simulates real-time network management metrics including:
- Device reboots (counter)
- Interface traffic (gauge with labels)
- API latency (gauge)
"""

import time
import random
from prometheus_client import Counter, Gauge, start_http_server
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# METRIC DEFINITIONS
# ==============================================================================

# Counter: Total number of device reboots
# Counters only go up and are used for counting events
nms_device_reboots_total = Counter(
    'nms_device_reboots_total',
    'Total count of device reboots in the network',
    ['device_name', 'device_type']  # Labels for dimensionality
)

# Gauge: Current interface traffic in Mbps
# Gauges can go up and down, representing current values
nms_interface_traffic_mbps = Gauge(
    'nms_interface_traffic_mbps',
    'Current network interface traffic rate in Mbps',
    ['device_name', 'interface']  # Labels: device and interface name
)

# Gauge: API call latency in seconds
# Simulates monitoring API response times
nms_api_latency_seconds = Gauge(
    'nms_api_latency_seconds',
    'API call latency in seconds',
    ['api_endpoint', 'method']  # Labels: endpoint and HTTP method
)

# ==============================================================================
# ADDITIONAL METRICS FOR RICHER DASHBOARDS
# ==============================================================================

# Device status (1 = up, 0 = down)
nms_device_status = Gauge(
    'nms_device_status',
    'Device operational status (1=up, 0=down)',
    ['device_name', 'device_type', 'location']
)

# CPU utilization percentage
nms_device_cpu_percent = Gauge(
    'nms_device_cpu_percent',
    'Device CPU utilization percentage',
    ['device_name', 'device_type']
)

# Memory utilization percentage
nms_device_memory_percent = Gauge(
    'nms_device_memory_percent',
    'Device memory utilization percentage',
    ['device_name', 'device_type']
)

# Packet loss percentage
nms_interface_packet_loss_percent = Gauge(
    'nms_interface_packet_loss_percent',
    'Interface packet loss percentage',
    ['device_name', 'interface']
)

# ==============================================================================
# SIMULATION DATA
# ==============================================================================

# Network devices in our simulated environment
DEVICES = [
    {'name': 'core-router-01', 'type': 'router', 'location': 'datacenter-1'},
    {'name': 'core-switch-01', 'type': 'switch', 'location': 'datacenter-1'},
    {'name': 'edge-router-01', 'type': 'router', 'location': 'branch-office'},
    {'name': 'access-switch-01', 'type': 'switch', 'location': 'floor-3'},
    {'name': 'firewall-01', 'type': 'firewall', 'location': 'datacenter-1'},
]

# Network interfaces per device
INTERFACES = ['eth0', 'eth1', 'eth2', 'eth3']

# API endpoints to monitor
API_ENDPOINTS = [
    {'endpoint': '/api/devices', 'method': 'GET'},
    {'endpoint': '/api/metrics', 'method': 'GET'},
    {'endpoint': '/api/alarms', 'method': 'GET'},
    {'endpoint': '/api/device/update', 'method': 'POST'},
]

# ==============================================================================
# DATA GENERATION LOGIC
# ==============================================================================

# Global cycle counter
cycle_count = 0

def generate_network_data():
    """
    Main function to generate simulated network management data.
    Updates all metrics with realistic values.
    """
    global cycle_count
    cycle_count += 1
    
    logger.info(f"=== Cycle {cycle_count} - Generating network data ===")
    
    # 1. DEVICE REBOOTS (every 10 cycles)
    if cycle_count % 10 == 0:
        # Randomly select a device to "reboot"
        device = random.choice(DEVICES)
        nms_device_reboots_total.labels(
            device_name=device['name'],
            device_type=device['type']
        ).inc()
        logger.info(f"  📊 Device reboot: {device['name']} (total reboots incremented)")
    
    # 2. INTERFACE TRAFFIC (for each device and interface)
    for device in DEVICES:
        for interface in INTERFACES:
            # Generate random traffic between 50 and 150 Mbps
            traffic = random.uniform(50, 150)
            nms_interface_traffic_mbps.labels(
                device_name=device['name'],
                interface=interface
            ).set(traffic)
            
            # Also generate packet loss (usually low)
            packet_loss = random.uniform(0, 2.5)  # 0-2.5% packet loss
            nms_interface_packet_loss_percent.labels(
                device_name=device['name'],
                interface=interface
            ).set(packet_loss)
    
    logger.info(f"  📊 Interface traffic updated for {len(DEVICES)} devices x {len(INTERFACES)} interfaces")
    
    # 3. API LATENCY (for each endpoint)
    for api in API_ENDPOINTS:
        # Generate random latency between 0.1 and 1.5 seconds
        latency = random.uniform(0.1, 1.5)
        nms_api_latency_seconds.labels(
            api_endpoint=api['endpoint'],
            method=api['method']
        ).set(latency)
    
    logger.info(f"  📊 API latency updated for {len(API_ENDPOINTS)} endpoints")
    
    # 4. DEVICE STATUS (mostly up, occasionally down)
    for device in DEVICES:
        # 95% chance device is up, 5% chance it's down
        status = 1 if random.random() > 0.05 else 0
        nms_device_status.labels(
            device_name=device['name'],
            device_type=device['type'],
            location=device['location']
        ).set(status)
    
    # 5. CPU AND MEMORY UTILIZATION
    for device in DEVICES:
        # CPU: random between 20% and 90%
        cpu = random.uniform(20, 90)
        nms_device_cpu_percent.labels(
            device_name=device['name'],
            device_type=device['type']
        ).set(cpu)
        
        # Memory: random between 40% and 85%
        memory = random.uniform(40, 85)
        nms_device_memory_percent.labels(
            device_name=device['name'],
            device_type=device['type']
        ).set(memory)
    
    logger.info(f"  📊 Device status, CPU, and memory updated for {len(DEVICES)} devices")
    logger.info(f"  ✅ Cycle {cycle_count} complete\n")

# ==============================================================================
# MAIN EXPORTER LOGIC
# ==============================================================================

def main():
    """
    Main function to start the Prometheus exporter.
    """
    # Configuration
    EXPORTER_PORT = 9001
    UPDATE_INTERVAL = 5  # seconds
    
    # Print startup banner
    print("=" * 70)
    print("  NMS METRICS EXPORTER - LIVE NETWORK MANAGEMENT DATA")
    print("=" * 70)
    print(f"  Port: {EXPORTER_PORT}")
    print(f"  Update Interval: {UPDATE_INTERVAL} seconds")
    print(f"  Devices: {len(DEVICES)}")
    print(f"  Interfaces per device: {len(INTERFACES)}")
    print(f"  API Endpoints: {len(API_ENDPOINTS)}")
    print("=" * 70)
    print(f"\n✅ Starting HTTP server on port {EXPORTER_PORT}...")
    
    # Start the Prometheus HTTP server
    try:
        start_http_server(EXPORTER_PORT)
        logger.info(f"✅ Metrics server started successfully on port {EXPORTER_PORT}")
        logger.info(f"📊 Metrics available at: http://localhost:{EXPORTER_PORT}/metrics")
        logger.info(f"🔄 Data will update every {UPDATE_INTERVAL} seconds")
        print(f"\n✅ Server is running!")
        print(f"📊 Metrics endpoint: http://localhost:{EXPORTER_PORT}/metrics")
        print(f"🔄 Updating data every {UPDATE_INTERVAL} seconds\n")
        print("=" * 70)
        print("  Available Metrics:")
        print("=" * 70)
        print("  • nms_device_reboots_total          - Device reboot counter")
        print("  • nms_interface_traffic_mbps        - Interface traffic (Mbps)")
        print("  • nms_api_latency_seconds           - API response time")
        print("  • nms_device_status                 - Device up/down status")
        print("  • nms_device_cpu_percent            - CPU utilization")
        print("  • nms_device_memory_percent         - Memory utilization")
        print("  • nms_interface_packet_loss_percent - Packet loss")
        print("=" * 70)
        print("\nPress Ctrl+C to stop the exporter\n")
        
    except OSError as e:
        logger.error(f"❌ Failed to start server on port {EXPORTER_PORT}: {e}")
        logger.error(f"   Port may already be in use. Try a different port.")
        return
    
    # Generate initial data
    logger.info("Generating initial data...")
    generate_network_data()
    
    # Main loop - update metrics every UPDATE_INTERVAL seconds
    try:
        while True:
            time.sleep(UPDATE_INTERVAL)
            generate_network_data()
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("  ⚠️  Shutdown signal received")
        print("=" * 70)
        logger.info("Exporter stopped by user")
        print(f"\n📊 Total cycles completed: {cycle_count}")
        print(f"⏱️  Total runtime: {cycle_count * UPDATE_INTERVAL} seconds")
        print("\n✅ Exporter stopped gracefully\n")

# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == '__main__':
    main()
