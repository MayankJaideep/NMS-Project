-- SCNMS Database Table Creation Script
-- Run this BEFORE init.sql

-- Create tables
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    hostname VARCHAR(255),
    vendor VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    status VARCHAR(20) DEFAULT 'unknown',
    location VARCHAR(255),
    description TEXT,
    snmp_enabled BOOLEAN DEFAULT FALSE,
    snmp_community VARCHAR(100),
    snmp_version VARCHAR(10),
    netconf_enabled BOOLEAN DEFAULT FALSE,
    netconf_username VARCHAR(100),
    netconf_password VARCHAR(255),
    restconf_enabled BOOLEAN DEFAULT FALSE,
    restconf_username VARCHAR(100),
    restconf_password VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_polled TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    unit VARCHAR(50),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    labels JSONB
);

CREATE TABLE IF NOT EXISTS alarms (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    alarm_id VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'raised',
    source VARCHAR(100),
    raised_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(100),
    cleared_at TIMESTAMP,
    closed_at TIMESTAMP,
    additional_info JSONB
);

CREATE TABLE IF NOT EXISTS alarm_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    metric_name VARCHAR(255) NOT NULL,
    threshold_value FLOAT NOT NULL,
    comparison_operator VARCHAR(5) NOT NULL,
    duration_seconds INTEGER DEFAULT 60,
    severity VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS polling_jobs (
    id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    protocol VARCHAR(20) NOT NULL,
    oid_or_path VARCHAR(500) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    interval_seconds INTEGER NOT NULL DEFAULT 300,
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_devices_ip_address ON devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_metrics_device_timestamp ON metrics(device_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_alarms_device_status ON alarms(device_id, status);
CREATE INDEX IF NOT EXISTS idx_alarms_severity ON alarms(severity);
CREATE INDEX IF NOT EXISTS idx_alarms_raised_at ON alarms(raised_at);

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alarm_rules_updated_at BEFORE UPDATE ON alarm_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
