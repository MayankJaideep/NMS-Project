#!/usr/bin/env python3
"""
Generate sample data for SCNMS demonstration
Creates realistic network metrics and alarms
"""
import random
import requests
from datetime import datetime, timedelta
import time

API_BASE = "http://localhost:8000/api/v1"

def generate_metrics():
    """Generate 100 sample metrics for the 4 devices"""
    print("Generating sample metrics...")
    
    device_ids = [1, 2, 3, 4]
    
    # Metric templates with realistic ranges
    metrics_templates = [
        {"name": "cpu_utilization", "unit": "%", "range": (10, 95)},
        {"name": "memory_utilization", "unit": "%", "range": (20, 90)},
        {"name": "interface_utilization", "unit": "%", "range": (5, 85)},
        {"name": "bandwidth_in", "unit": "bps", "range": (1000000, 10000000000)},
        {"name": "bandwidth_out", "unit": "bps", "range": (1000000, 10000000000)},
        {"name": "packets_per_second", "unit": "pps", "range": (1000, 50000)},
        {"name": "latency", "unit": "ms", "range": (1, 150)},
        {"name": "packet_loss_rate", "unit": "%", "range": (0, 5)},
        {"name": "temperature", "unit": "C", "range": (25, 75)},
        {"name": "interface_errors", "unit": "count", "range": (0, 100)},
    ]
    
    metrics_data = []
    current_time = datetime.now()
    
    # Generate metrics for last 6 hours
    for i in range(100):
        # Spread over 6 hours
        timestamp = current_time - timedelta(minutes=i*3)
        
        for device_id in device_ids:
            # Random metrics for each device
            for template in random.sample(metrics_templates, 3):  # 3 random metrics per device
                value_range = template["range"]
                value = random.uniform(value_range[0], value_range[1])
                
                metric = {
                    "device_id": device_id,
                    "metric_name": template["name"],
                    "metric_value": round(value, 2),
                    "unit": template["unit"],
                    "timestamp": timestamp.isoformat()
                }
                metrics_data.append(metric)
    
    return metrics_data

def post_metrics_to_db():
    """Insert metrics directly into database"""
    import psycopg2
    from datetime import datetime, timedelta
    import random
    
    print("Connecting to database...")
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="scnms",
        user="scnms",
        password="scnms"
    )
    cursor = conn.cursor()
    
    device_ids = [1, 2, 3, 4]
    
    metrics_templates = [
        {"name": "cpu_utilization", "unit": "%", "range": (10, 95)},
        {"name": "memory_utilization", "unit": "%", "range": (20, 90)},
        {"name": "interface_utilization", "unit": "%", "range": (5, 85)},
        {"name": "bandwidth_in", "unit": "Mbps", "range": (10, 1000)},
        {"name": "bandwidth_out", "unit": "Mbps", "range": (10, 1000)},
        {"name": "packets_per_second", "unit": "pps", "range": (1000, 50000)},
        {"name": "latency", "unit": "ms", "range": (1, 150)},
        {"name": "packet_loss_rate", "unit": "%", "range": (0, 5)},
        {"name": "temperature", "unit": "C", "range": (25, 75)},
        {"name": "interface_errors", "unit": "count", "range": (0, 100)},
    ]
    
    current_time = datetime.now()
    count = 0
    
    print("Inserting metrics...")
    # Generate 150 data points
    for i in range(150):
        timestamp = current_time - timedelta(minutes=i*2)
        
        for device_id in device_ids:
            for template in metrics_templates:
                value_range = template["range"]
                # Add some variation - devices have different patterns
                if device_id == 1:  # Core switch - higher load
                    value = random.uniform(value_range[0] * 1.2, value_range[1] * 0.9)
                elif device_id == 4:  # Firewall - consistent load
                    value = random.uniform(value_range[0] * 0.7, value_range[1] * 0.6)
                else:
                    value = random.uniform(value_range[0], value_range[1])
                
                cursor.execute(
                    """
                    INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (device_id, template["name"], round(value, 2), template["unit"], timestamp)
                )
                count += 1
    
    conn.commit()
    print(f"✓ Inserted {count} metric data points")
    
    # Create some alarms
    print("\nGenerating sample alarms...")
    alarm_count = 0
    
    alarm_templates = [
        {"severity": "critical", "title": "High CPU Usage", "description": "CPU utilization above 80%"},
        {"severity": "major", "title": "High Memory Usage", "description": "Memory utilization above 75%"},
        {"severity": "warning", "title": "High Latency", "description": "Network latency above 100ms"},
        {"severity": "minor", "title": "Interface Errors", "description": "Interface error rate increasing"},
    ]
    
    for i in range(20):
        device_id = random.choice(device_ids)
        template = random.choice(alarm_templates)
        raised_time = current_time - timedelta(hours=random.randint(1, 24))
        
        # Some alarms are acknowledged, some cleared
        status = random.choice(["raised", "raised", "acknowledged", "cleared"])
        acknowledged_at = None
        cleared_at = None
        
        if status in ["acknowledged", "cleared"]:
            acknowledged_at = raised_time + timedelta(minutes=random.randint(5, 30))
        if status == "cleared":
            cleared_at = acknowledged_at + timedelta(minutes=random.randint(10, 60))
        
        alarm_id = f"alarm-{device_id}-{int(raised_time.timestamp())}-{i}"
        
        cursor.execute(
            """
            INSERT INTO alarms 
            (device_id, alarm_id, title, description, severity, status, source, 
             raised_at, acknowledged_at, acknowledged_by, cleared_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (device_id, alarm_id, template["title"], template["description"],
             template["severity"], status, "threshold", raised_time, 
             acknowledged_at, "admin" if acknowledged_at else None, cleared_at)
        )
        alarm_count += 1
    
    conn.commit()
    print(f"✓ Created {alarm_count} sample alarms")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*50)
    print("✅ Sample data generation complete!")
    print("="*50)
    print(f"\nTotal Metrics: {count}")
    print(f"Total Alarms: {alarm_count}")
    print(f"Devices: 4")
    print(f"Time Range: Last 6 hours")
    print("\nYou can now:")
    print("1. Open Grafana: http://localhost:3000")
    print("2. View dashboards with real data!")

if __name__ == "__main__":
    print("="*50)
    print("SCNMS Sample Data Generator")
    print("="*50)
    print()
    
    try:
        post_metrics_to_db()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. PostgreSQL is running (docker-compose ps)")
        print("2. Database is accessible on localhost:5432")
        print("3. Install psycopg2: pip install psycopg2-binary")
