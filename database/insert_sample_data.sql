-- Insert 600 sample metrics (150 timestamps x 4 devices x 10 metrics each)
-- This creates realistic network monitoring data for the last 6 hours

DO $$
DECLARE
    device_id_var INTEGER;
    timestamp_var TIMESTAMP;
    metric_count INTEGER := 0;
BEGIN
    -- Generate metrics for each device over the last 6 hours
    FOR i IN 0..149 LOOP
        timestamp_var := NOW() - (i * INTERVAL '2 minutes');
        
        FOR device_id_var IN 1..4 LOOP
            -- CPU Utilization
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'cpu_utilization', 
                    CASE device_id_var
                        WHEN 1 THEN 45 + random() * 40  -- Core switch: 45-85%
                        WHEN 2 THEN 25 + random() * 30  -- Access switch: 25-55%
                        WHEN 3 THEN 50 + random() * 35  -- Router: 50-85%
                        WHEN 4 THEN 30 + random() * 25  -- Firewall: 30-55%
                    END, '%', timestamp_var);
            
            -- Memory Utilization
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'memory_utilization',
                    CASE device_id_var
                        WHEN 1 THEN 50 + random() * 35  -- 50-85%
                        WHEN 2 THEN 35 + random() * 25  -- 35-60%
                        WHEN 3 THEN 55 + random() * 30  -- 55-85%
                        WHEN 4 THEN 45 + random() * 30  -- 45-75%
                    END, '%', timestamp_var);
            
            -- Interface Utilization
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'interface_utilization',
                    20 + random() * 60, '%', timestamp_var);
            
            -- Bandwidth In (Mbps)
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'bandwidth_in',
                    CASE device_id_var
                        WHEN 1 THEN 100 + random() * 800   -- Core: 100-900 Mbps
                        WHEN 2 THEN 20 + random() * 180    -- Access: 20-200 Mbps
                        WHEN 3 THEN 150 + random() * 750   -- Router: 150-900 Mbps
                        WHEN 4 THEN 50 + random() * 350    -- Firewall: 50-400 Mbps
                    END, 'Mbps', timestamp_var);
            
            -- Bandwidth Out (Mbps)
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'bandwidth_out',
                    CASE device_id_var
                        WHEN 1 THEN 80 + random() * 600
                        WHEN 2 THEN 15 + random() * 150
                        WHEN 3 THEN 120 + random() * 600
                        WHEN 4 THEN 40 + random() * 300
                    END, 'Mbps', timestamp_var);
            
            -- Packets per Second
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'packets_per_second',
                    5000 + random() * 40000, 'pps', timestamp_var);
            
            -- Latency (ms)
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'latency',
                    5 + random() * 95, 'ms', timestamp_var);
            
            -- Packet Loss Rate
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'packet_loss_rate',
                    random() * 3, '%', timestamp_var);
            
            -- Temperature
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'temperature',
                    35 + random() * 30, 'C', timestamp_var);
            
            -- Interface Errors
            INSERT INTO metrics (device_id, metric_name, metric_value, unit, timestamp)
            VALUES (device_id_var, 'interface_errors',
                    floor(random() * 50), 'count', timestamp_var);
            
            metric_count := metric_count + 10;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE 'Inserted % metric records', metric_count;
END $$;

-- Insert 25 sample alarms with different severities and statuses
DO $$
DECLARE
    alarm_count INTEGER := 0;
    device_id_var INTEGER;
    raised_time TIMESTAMP;
    ack_time TIMESTAMP;
    clear_time TIMESTAMP;
    alarm_id_var VARCHAR;
BEGIN
    -- Critical Alarms (5)
    FOR i IN 1..5 LOOP
        device_id_var := ((i - 1) % 4) + 1;
        raised_time := NOW() - (i * INTERVAL '2 hours');
        alarm_id_var := 'alarm-critical-' || device_id_var || '-' || i;
        
        IF i <= 2 THEN
            -- Active critical alarms
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source, raised_at)
            VALUES (device_id_var, alarm_id_var, 
                    'Critical: High CPU Usage',
                    'CPU utilization exceeded 85% for 5 minutes',
                    'critical', 'raised', 'threshold', raised_time);
        ELSE
            -- Acknowledged critical alarms
            ack_time := raised_time + INTERVAL '15 minutes';
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source, 
                               raised_at, acknowledged_at, acknowledged_by)
            VALUES (device_id_var, alarm_id_var,
                    'Critical: High Memory Usage',
                    'Memory utilization exceeded 90%',
                    'critical', 'acknowledged', 'threshold', raised_time, ack_time, 'admin');
        END IF;
        alarm_count := alarm_count + 1;
    END LOOP;
    
    -- Major Alarms (8)
    FOR i IN 1..8 LOOP
        device_id_var := ((i - 1) % 4) + 1;
        raised_time := NOW() - (i * INTERVAL '90 minutes');
        alarm_id_var := 'alarm-major-' || device_id_var || '-' || i;
        
        IF i <= 3 THEN
            -- Active major alarms
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source, raised_at)
            VALUES (device_id_var, alarm_id_var,
                    'Major: High Interface Utilization',
                    'Interface utilization above 80%',
                    'major', 'raised', 'threshold', raised_time);
        ELSIF i <= 6 THEN
            -- Acknowledged major alarms
            ack_time := raised_time + INTERVAL '30 minutes';
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source,
                               raised_at, acknowledged_at, acknowledged_by)
            VALUES (device_id_var, alarm_id_var,
                    'Major: High Bandwidth Usage',
                    'Bandwidth utilization above threshold',
                    'major', 'acknowledged', 'threshold', raised_time, ack_time, 'operator');
        ELSE
            -- Cleared major alarms
            ack_time := raised_time + INTERVAL '20 minutes';
            clear_time := ack_time + INTERVAL '45 minutes';
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source,
                               raised_at, acknowledged_at, acknowledged_by, cleared_at)
            VALUES (device_id_var, alarm_id_var,
                    'Major: High Latency',
                    'Network latency above 100ms',
                    'major', 'cleared', 'threshold', raised_time, ack_time, 'admin', clear_time);
        END IF;
        alarm_count := alarm_count + 1;
    END LOOP;
    
    -- Minor Alarms (7)
    FOR i IN 1..7 LOOP
        device_id_var := ((i - 1) % 4) + 1;
        raised_time := NOW() - (i * INTERVAL '1 hour');
        alarm_id_var := 'alarm-minor-' || device_id_var || '-' || i;
        
        IF i <= 2 THEN
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source, raised_at)
            VALUES (device_id_var, alarm_id_var,
                    'Minor: Interface Errors Increasing',
                    'Interface error rate above normal',
                    'minor', 'raised', 'threshold', raised_time);
        ELSE
            ack_time := raised_time + INTERVAL '10 minutes';
            clear_time := ack_time + INTERVAL '30 minutes';
            INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source,
                               raised_at, acknowledged_at, acknowledged_by, cleared_at)
            VALUES (device_id_var, alarm_id_var,
                    'Minor: Packet Loss Detected',
                    'Packet loss rate above 1%',
                    'minor', 'cleared', 'threshold', raised_time, ack_time, 'admin', clear_time);
        END IF;
        alarm_count := alarm_count + 1;
    END LOOP;
    
    -- Warning Alarms (5)
    FOR i IN 1..5 LOOP
        device_id_var := ((i - 1) % 4) + 1;
        raised_time := NOW() - (i * INTERVAL '45 minutes');
        alarm_id_var := 'alarm-warning-' || device_id_var || '-' || i;
        ack_time := raised_time + INTERVAL '5 minutes';
        clear_time := ack_time + INTERVAL '20 minutes';
        
        INSERT INTO alarms (device_id, alarm_id, title, description, severity, status, source,
                           raised_at, acknowledged_at, acknowledged_by, cleared_at)
        VALUES (device_id_var, alarm_id_var,
                'Warning: Temperature Rising',
                'Device temperature above 60C',
                'warning', 'cleared', 'threshold', raised_time, ack_time, 'system', clear_time);
        alarm_count := alarm_count + 1;
    END LOOP;
    
    RAISE NOTICE 'Inserted % alarm records', alarm_count;
END $$;

-- Summary
DO $$
DECLARE
    device_count INTEGER;
    metric_count INTEGER;
    alarm_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO device_count FROM devices;
    SELECT COUNT(*) INTO metric_count FROM metrics;
    SELECT COUNT(*) INTO alarm_count FROM alarms;
    
    RAISE NOTICE '';
    RAISE NOTICE '================================================';
    RAISE NOTICE '    Sample Data Generation Complete!';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Devices: %', device_count;
    RAISE NOTICE 'Metrics: %', metric_count;
    RAISE NOTICE 'Alarms:  %', alarm_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Time Range: Last 6 hours';
    RAISE NOTICE 'Data Points: Every 2 minutes';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '1. Open Grafana: http://localhost:3000';
    RAISE NOTICE '2. Login: admin / admin';
    RAISE NOTICE '3. Go to Dashboards → SCNMS';
    RAISE NOTICE '4. View: Alarm, Utilization, Device Health dashboards';
    RAISE NOTICE '================================================';
END $$;
