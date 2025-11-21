#!/usr/bin/env python3
"""
Prometheus Exporter for SCNMS
Exports metrics from PostgreSQL database to Prometheus format
"""
import os
import time
import psycopg2
from prometheus_client import start_http_server, Gauge, Counter, Info
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "scnms"),
    "user": os.getenv("POSTGRES_USER", "scnms"),
    "password": os.getenv("POSTGRES_PASSWORD", "scnms")
}

# Prometheus metrics
device_cpu_gauge = Gauge('scnms_device_cpu_utilization', 'CPU utilization percentage', ['device_id', 'device_name'])
device_memory_gauge = Gauge('scnms_device_memory_utilization', 'Memory utilization percentage', ['device_id', 'device_name'])
device_bandwidth_in_gauge = Gauge('scnms_device_bandwidth_in', 'Bandwidth inbound Mbps', ['device_id', 'device_name'])
device_bandwidth_out_gauge = Gauge('scnms_device_bandwidth_out', 'Bandwidth outbound Mbps', ['device_id', 'device_name'])
device_latency_gauge = Gauge('scnms_device_latency', 'Network latency ms', ['device_id', 'device_name'])
device_temperature_gauge = Gauge('scnms_device_temperature', 'Device temperature celsius', ['device_id', 'device_name'])
device_interface_util_gauge = Gauge('scnms_device_interface_utilization', 'Interface utilization percentage', ['device_id', 'device_name'])
device_packet_loss_gauge = Gauge('scnms_device_packet_loss_rate', 'Packet loss rate percentage', ['device_id', 'device_name'])

# Alarm metrics
alarms_raised = Gauge('scnms_alarms_raised', 'Number of raised alarms', ['severity'])
alarms_acknowledged = Gauge('scnms_alarms_acknowledged', 'Number of acknowledged alarms', ['severity'])
alarms_cleared = Gauge('scnms_alarms_cleared', 'Number of cleared alarms', ['severity'])
alarms_total = Counter('scnms_alarms_total', 'Total alarms', ['severity', 'status'])

# Device status
device_status = Gauge('scnms_device_status', 'Device status (1=UP, 0=DOWN)', ['device_id', 'device_name', 'ip_address'])

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def export_device_metrics():
    """Export latest device metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest metrics for each device/metric combination
        query = """
        WITH latest_metrics AS (
            SELECT DISTINCT ON (device_id, metric_name)
                device_id, metric_name, metric_value, timestamp
            FROM metrics
            WHERE timestamp > NOW() - INTERVAL '10 minutes'
            ORDER BY device_id, metric_name, timestamp DESC
        )
        SELECT 
            d.id, d.name, d.ip_address,
            lm.metric_name, lm.metric_value
        FROM devices d
        LEFT JOIN latest_metrics lm ON d.id = lm.device_id
        WHERE d.status = 'UP'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            device_id, device_name, ip_address, metric_name, metric_value = row
            
            if not metric_name or metric_value is None:
                continue
                
            labels = [str(device_id), device_name or f"device-{device_id}"]
            
            if metric_name == 'cpu_utilization':
                device_cpu_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'memory_utilization':
                device_memory_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'bandwidth_in':
                device_bandwidth_in_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'bandwidth_out':
                device_bandwidth_out_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'latency':
                device_latency_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'temperature':
                device_temperature_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'interface_utilization':
                device_interface_util_gauge.labels(*labels).set(metric_value)
            elif metric_name == 'packet_loss_rate':
                device_packet_loss_gauge.labels(*labels).set(metric_value)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error exporting device metrics: {e}")

def export_device_status():
    """Export device status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, name, ip_address, status FROM devices"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            device_id, name, ip_address, status = row
            status_value = 1 if status == 'UP' else 0
            device_status.labels(str(device_id), name or f"device-{device_id}", ip_address).set(status_value)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error exporting device status: {e}")

def export_alarm_metrics():
    """Export alarm statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count alarms by severity and status
        query = """
        SELECT severity, status, COUNT(*)
        FROM alarms
        WHERE raised_at > NOW() - INTERVAL '24 hours'
        GROUP BY severity, status
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Reset gauges
        for sev in ['CRITICAL', 'MAJOR', 'MINOR', 'WARNING']:
            alarms_raised.labels(sev).set(0)
            alarms_acknowledged.labels(sev).set(0)
            alarms_cleared.labels(sev).set(0)
        
        for row in rows:
            severity, status, count = row
            
            if status == 'RAISED':
                alarms_raised.labels(severity).set(count)
            elif status == 'ACKNOWLEDGED':
                alarms_acknowledged.labels(severity).set(count)
            elif status == 'CLEARED':
                alarms_cleared.labels(severity).set(count)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error exporting alarm metrics: {e}")

def collect_metrics():
    """Collect all metrics"""
    logger.info("Collecting metrics...")
    export_device_metrics()
    export_device_status()
    export_alarm_metrics()
    logger.info("Metrics collected successfully")

if __name__ == '__main__':
    logger.info("Starting SCNMS Prometheus Exporter...")
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Start Prometheus HTTP server
    port = int(os.getenv("EXPORTER_PORT", 9100))
    start_http_server(port)
    logger.info(f"Prometheus exporter listening on port {port}")
    logger.info(f"Metrics available at http://localhost:{port}/metrics")
    
    # Collect metrics every 30 seconds
    while True:
        try:
            collect_metrics()
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(30)
