-- Add metric_unit column to metrics table
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS metric_unit VARCHAR(20);

-- Update existing records with default unit if needed
UPDATE metrics SET metric_unit = 'percent' WHERE metric_name LIKE '%utilization%';
UPDATE metrics SET metric_unit = 'bytes' WHERE metric_name LIKE '%memory%' OR metric_name LIKE '%disk%';
UPDATE metrics SET metric_unit = 'bps' WHERE metric_name LIKE '%bandwidth%' OR metric_name LIKE '%throughput%';
UPDATE metrics SET metric_unit = 'ms' WHERE metric_name LIKE '%latency%' OR metric_name LIKE '%response_time%';
UPDATE metrics SET metric_unit = 'count' WHERE metric_unit IS NULL;
