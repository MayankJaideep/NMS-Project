# 🚀 NMS Live Data Exporter - Complete Guide

**File**: `app_exporter.py`  
**Purpose**: Generate LIVE network management data for Prometheus/Grafana  
**Port**: 9001  
**Update Interval**: Every 5 seconds

---

## 📊 What This Exporter Provides

### Core Metrics (As Requested)

1. **`nms_device_reboots_total`** (Counter)
   - Counts device reboots
   - Increments every 10 cycles (50 seconds)
   - Labels: `device_name`, `device_type`

2. **`nms_interface_traffic_mbps`** (Gauge)
   - Current traffic rate per interface
   - Random value: 50-150 Mbps
   - Updates every 5 seconds
   - Labels: `device_name`, `interface` (eth0, eth1, eth2, eth3)

3. **`nms_api_latency_seconds`** (Gauge)
   - API call response time
   - Random value: 0.1-1.5 seconds
   - Updates every 5 seconds
   - Labels: `api_endpoint`, `method`

### Bonus Metrics (For Richer Dashboards)

4. **`nms_device_status`** - Device up/down (1/0)
5. **`nms_device_cpu_percent`** - CPU utilization (20-90%)
6. **`nms_device_memory_percent`** - Memory utilization (40-85%)
7. **`nms_interface_packet_loss_percent`** - Packet loss (0-2.5%)

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd "/home/sujan-rathod/Desktop/NMS/NMS project"
pip3 install prometheus-client
```

### Step 2: Run the Exporter

```bash
python3 app_exporter.py
```

**Expected Output**:
```
======================================================================
  NMS METRICS EXPORTER - LIVE NETWORK MANAGEMENT DATA
======================================================================
  Port: 9001
  Update Interval: 5 seconds
  Devices: 5
  Interfaces per device: 4
  API Endpoints: 4
======================================================================

✅ Server is running!
📊 Metrics endpoint: http://localhost:9001/metrics
🔄 Updating data every 5 seconds
```

### Step 3: Verify It's Working

```bash
curl http://localhost:9001/metrics | grep nms_
```

**You should see**:
```
nms_device_reboots_total{device_name="core-router-01",device_type="router"} 1.0
nms_interface_traffic_mbps{device_name="core-router-01",interface="eth0"} 87.5
nms_api_latency_seconds{api_endpoint="/api/devices",method="GET"} 0.654
nms_device_status{device_name="core-router-01",device_type="router",location="datacenter-1"} 1.0
nms_device_cpu_percent{device_name="core-router-01",device_type="router"} 45.2
```

---

## 🔧 Integrate with Prometheus

### Option 1: Update Prometheus Configuration

Edit `config/prometheus.yml` and add:

```yaml
scrape_configs:
  # ... existing jobs ...

  # NMS Live Data Exporter
  - job_name: 'nms-live-exporter'
    scrape_interval: 5s  # Match the exporter's update interval
    static_configs:
      - targets: ['localhost:9001']
        labels:
          service: 'nms_live_exporter'
          environment: 'demo'
```

Then reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
# OR restart Prometheus
docker-compose restart prometheus
```

### Option 2: Add to Docker Compose (For Production)

Create `Dockerfile.app-exporter`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install prometheus-client
COPY app_exporter.py .
EXPOSE 9001
CMD ["python3", "app_exporter.py"]
```

Add to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...
  
  app-exporter:
    build:
      context: .
      dockerfile: Dockerfile.app-exporter
    container_name: scnms-app-exporter
    ports:
      - "9001:9001"
    networks:
      - scnms-network
    restart: unless-stopped
```

Update Prometheus config to use Docker network:
```yaml
- job_name: 'nms-live-exporter'
  static_configs:
    - targets: ['app-exporter:9001']
```

---

## 📊 Create Grafana Dashboard

### Quick Dashboard Creation

1. **Open Grafana**: http://localhost:3000
2. **Create New Dashboard**: Click **+** → **Dashboard** → **Add visualization**
3. **Select Prometheus** as data source

### Panel Examples

#### Panel 1: Device Reboots (Counter)

**Query**:
```promql
sum(nms_device_reboots_total)
```

**Visualization**: Stat or Time series  
**Title**: "Total Device Reboots"

#### Panel 2: Interface Traffic (Gauge)

**Query**:
```promql
nms_interface_traffic_mbps
```

**Legend**: `{{device_name}} - {{interface}}`  
**Visualization**: Time series  
**Title**: "Interface Traffic (Mbps)"  
**Unit**: Mbps

#### Panel 3: API Latency (Gauge)

**Query**:
```promql
nms_api_latency_seconds
```

**Legend**: `{{api_endpoint}} ({{method}})`  
**Visualization**: Time series  
**Title**: "API Response Time"  
**Unit**: seconds

#### Panel 4: Device Status

**Query**:
```promql
nms_device_status
```

**Legend**: `{{device_name}}`  
**Visualization**: Time series or Stat  
**Title**: "Device Status (1=UP, 0=DOWN)"

#### Panel 5: CPU Utilization

**Query**:
```promql
nms_device_cpu_percent
```

**Legend**: `{{device_name}}`  
**Visualization**: Time series  
**Title**: "CPU Utilization %"  
**Unit**: percent (0-100)

#### Panel 6: Memory Utilization

**Query**:
```promql
nms_device_memory_percent
```

**Legend**: `{{device_name}}`  
**Visualization**: Time series  
**Title**: "Memory Utilization %"  
**Unit**: percent (0-100)

---

## 🎯 Advanced Queries

### Average Traffic Per Device
```promql
avg by (device_name) (nms_interface_traffic_mbps)
```

### Total Traffic Across All Interfaces
```promql
sum(nms_interface_traffic_mbps)
```

### Devices Currently Down
```promql
nms_device_status == 0
```

### High CPU Devices (>70%)
```promql
nms_device_cpu_percent > 70
```

### Slowest API Endpoints
```promql
topk(3, nms_api_latency_seconds)
```

### Reboot Rate (per minute)
```promql
rate(nms_device_reboots_total[1m])
```

### Interfaces with High Packet Loss (>1%)
```promql
nms_interface_packet_loss_percent > 1
```

---

## 📈 Complete Dashboard JSON

Save this as `nms-live-dashboard.json` and import to Grafana:

```json
{
  "dashboard": {
    "title": "NMS Live Data - Network Management",
    "panels": [
      {
        "title": "Total Device Reboots",
        "targets": [
          {
            "expr": "sum(nms_device_reboots_total)"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Interface Traffic",
        "targets": [
          {
            "expr": "nms_interface_traffic_mbps",
            "legendFormat": "{{device_name}} - {{interface}}"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "API Latency",
        "targets": [
          {
            "expr": "nms_api_latency_seconds",
            "legendFormat": "{{api_endpoint}}"
          }
        ],
        "type": "timeseries"
      }
    ],
    "refresh": "5s",
    "time": {
      "from": "now-15m",
      "to": "now"
    }
  }
}
```

---

## 🧪 Testing & Validation

### Test 1: Verify Exporter is Running

```bash
curl http://localhost:9001/metrics
```

**Expected**: HTTP 200 with Prometheus metrics

### Test 2: Check Specific Metrics

```bash
# Check device reboots
curl -s http://localhost:9001/metrics | grep nms_device_reboots_total

# Check interface traffic
curl -s http://localhost:9001/metrics | grep nms_interface_traffic_mbps

# Check API latency
curl -s http://localhost:9001/metrics | grep nms_api_latency_seconds
```

### Test 3: Verify Prometheus Scraping

```bash
# Check if Prometheus can see the target
curl -s http://localhost:9090/api/v1/targets | grep 9001

# Query data from Prometheus
curl -s 'http://localhost:9090/api/v1/query?query=nms_device_reboots_total'
```

### Test 4: Check Data Updates

```bash
# Get current value
curl -s http://localhost:9001/metrics | grep 'nms_interface_traffic_mbps.*eth0' | head -1

# Wait 5 seconds
sleep 5

# Get updated value (should be different)
curl -s http://localhost:9001/metrics | grep 'nms_interface_traffic_mbps.*eth0' | head -1
```

---

## 🎨 Simulated Network Topology

The exporter simulates this network:

```
┌─────────────────────────────────────────────┐
│           NMS Network Topology              │
├─────────────────────────────────────────────┤
│                                             │
│  Datacenter-1:                              │
│    ├─ core-router-01    (Router)           │
│    ├─ core-switch-01    (Switch)           │
│    └─ firewall-01       (Firewall)         │
│                                             │
│  Branch Office:                             │
│    └─ edge-router-01    (Router)           │
│                                             │
│  Floor-3:                                   │
│    └─ access-switch-01  (Switch)           │
│                                             │
│  Each device has 4 interfaces:             │
│    eth0, eth1, eth2, eth3                  │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📊 Sample Data Characteristics

### Traffic Patterns
- **Range**: 50-150 Mbps per interface
- **Update**: Every 5 seconds
- **Variation**: Random within range (simulates real traffic)

### Device Reboots
- **Frequency**: Every 10 cycles (50 seconds)
- **Target**: Random device each time
- **Type**: Counter (never decreases)

### API Latency
- **Range**: 0.1-1.5 seconds
- **Endpoints**: 4 different API endpoints
- **Update**: Every 5 seconds

### Device Status
- **Normal**: 95% chance device is UP
- **Failure**: 5% chance device is DOWN (simulates outages)

### CPU/Memory
- **CPU**: 20-90% utilization
- **Memory**: 40-85% utilization
- **Realistic**: Higher load during "business hours" simulation

---

## 🛠️ Customization

### Change Update Interval

Edit `app_exporter.py`:

```python
UPDATE_INTERVAL = 5  # Change to 10 for 10-second updates
```

### Change Port

```python
EXPORTER_PORT = 9001  # Change to any available port
```

### Add More Devices

```python
DEVICES = [
    {'name': 'new-device', 'type': 'router', 'location': 'building-A'},
    # ... add more devices
]
```

### Modify Traffic Range

```python
traffic = random.uniform(50, 150)  # Change range as needed
```

---

## 🔒 Running in Background

### Using screen

```bash
screen -S nms-exporter
python3 app_exporter.py
# Press Ctrl+A then D to detach
# To reattach: screen -r nms-exporter
```

### Using systemd (Production)

Create `/etc/systemd/system/nms-exporter.service`:

```ini
[Unit]
Description=NMS Live Data Exporter
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/sujan-rathod/Desktop/NMS/NMS project
ExecStart=/usr/bin/python3 app_exporter.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable nms-exporter
sudo systemctl start nms-exporter
sudo systemctl status nms-exporter
```

---

## 📝 Monitoring the Exporter

### View Logs in Real-Time

```bash
python3 app_exporter.py 2>&1 | tee exporter.log
```

### Check Resource Usage

```bash
ps aux | grep app_exporter.py
```

### Monitor with Prometheus

The exporter itself exposes standard Python metrics:
```promql
python_info
process_cpu_seconds_total
process_resident_memory_bytes
```

---

## 🎯 Success Checklist

After starting the exporter, verify:

- [ ] Exporter is running on port 9001
- [ ] Metrics endpoint returns data: `curl http://localhost:9001/metrics`
- [ ] All 7 metric types are present
- [ ] Data updates every 5 seconds
- [ ] Prometheus is scraping (check targets page)
- [ ] Grafana can query the metrics
- [ ] Dashboard shows live data

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find what's using port 9001
sudo lsof -i :9001

# Kill the process
sudo kill -9 <PID>

# Or use a different port in app_exporter.py
```

### Module Not Found

```bash
pip3 install --upgrade prometheus-client
```

### No Data in Prometheus

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify scrape config includes port 9001
3. Restart Prometheus: `docker-compose restart prometheus`

### Grafana Shows "No Data"

1. Verify Prometheus has data:
   ```bash
   curl 'http://localhost:9090/api/v1/query?query=nms_device_reboots_total'
   ```
2. Check time range (should be "Last 15 minutes")
3. Verify query syntax matches metric names exactly

---

## 📚 Resources

- **Prometheus Client Docs**: https://github.com/prometheus/client_python
- **PromQL Query Language**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboards**: https://grafana.com/docs/grafana/latest/dashboards/

---

**Created**: October 23, 2025  
**Status**: ✅ **READY TO USE**  
**Runtime**: Indefinite (until stopped with Ctrl+C)

**Start exporting live data now!** 🚀
