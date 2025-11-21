-- SCNMS Database Initialization Script
-- This script creates the initial database schema and sample data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_devices_ip_address ON devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_metrics_device_timestamp ON metrics(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_alarms_device_status ON alarms(device_id, status);
CREATE INDEX IF NOT EXISTS idx_alarms_severity ON alarms(severity);
CREATE INDEX IF NOT EXISTS idx_alarms_raised_at ON alarms(raised_at);

-- Insert sample alarm rules
INSERT INTO alarm_rules (name, description, metric_name, threshold_value, comparison_operator, duration_seconds, severity, enabled) VALUES
('High CPU Usage', 'CPU utilization above 80%', 'cpu_utilization', 80.0, '>', 300, 'major', true),
('High Memory Usage', 'Memory utilization above 90%', 'memory_utilization', 90.0, '>', 60, 'critical', true),
('Interface Down', 'Network interface is down', 'interface_status', 0, '==', 0, 'critical', true),
('High Interface Utilization', 'Interface utilization above 90%', 'interface_utilization', 90.0, '>', 300, 'major', true),
('High Packet Loss', 'Packet loss above 1%', 'packet_loss_rate', 1.0, '>', 60, 'minor', true),
('High Latency', 'Network latency above 100ms', 'latency', 100.0, '>', 300, 'warning', true);

-- Insert sample devices (for testing)
INSERT INTO devices (name, ip_address, hostname, vendor, model, status, location, description, snmp_enabled, snmp_community, snmp_version) VALUES
('Core-Switch-01', '192.168.1.1', 'core-sw-01.campus.edu', 'Cisco', 'Catalyst 9300', 'up', 'Data Center', 'Main core switch for campus network', true, 'public', '2c'),
('Access-Switch-01', '192.168.1.2', 'access-sw-01.campus.edu', 'Cisco', 'Catalyst 2960', 'up', 'Building A', 'Access switch for Building A', true, 'public', '2c'),
('Router-01', '192.168.1.254', 'router-01.campus.edu', 'Cisco', 'ISR 4331', 'up', 'Data Center', 'Main campus router', true, 'public', '2c'),
('Firewall-01', '192.168.1.253', 'fw-01.campus.edu', 'Fortinet', 'FortiGate 100F', 'up', 'Data Center', 'Campus firewall', true, 'public', '2c');

-- Insert sample polling jobs
INSERT INTO polling_jobs (device_id, protocol, oid_or_path, polling_interval, enabled) VALUES
(1, 'snmp', '1.3.6.1.2.1.1.3.0', 60, true),  -- System uptime
(1, 'snmp', '1.3.6.1.2.1.25.3.3.1.2', 60, true),  -- CPU utilization
(1, 'snmp', '1.3.6.1.2.1.25.2.3.1.6', 60, true),  -- Memory utilization
(1, 'snmp', '1.3.6.1.2.1.2.2.1.8', 60, true),  -- Interface status
(1, 'snmp', '1.3.6.1.2.1.2.2.1.10', 60, true),  -- Interface in octets
(1, 'snmp', '1.3.6.1.2.1.2.2.1.16', 60, true);  -- Interface out octets

-- Create a function to clean up old metrics
CREATE OR REPLACE FUNCTION cleanup_old_metrics()
RETURNS void AS $$
BEGIN
    DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '30 days';
    DELETE FROM alarms WHERE status = 'closed' AND closed_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Create a function to update device status
CREATE OR REPLACE FUNCTION update_device_status()
RETURNS void AS $$
BEGIN
    UPDATE devices 
    SET status = 'down' 
    WHERE last_polled < NOW() - INTERVAL '5 minutes' 
    AND status = 'up';
    
    UPDATE devices 
    SET status = 'up' 
    WHERE last_polled > NOW() - INTERVAL '5 minutes' 
    AND status = 'down';
END;
$$ LANGUAGE plpgsql;
