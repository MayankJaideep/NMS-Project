# 🎯 INSTANT LIVE DATA - Complete Setup (3 Commands)

**Goal**: Show LIVE network management data in Grafana with real-time updates every 5 seconds!

---

## 🚀 Quick Start (Copy & Paste)

### Step 1: Start the Live Data Exporter

```bash
cd "/home/sujan-rathod/Desktop/NMS/NMS project"
./start_live_exporter.sh
```

**What it does**:
- ✅ Installs `prometheus-client` (if needed)
- ✅ Starts exporter on port 9001
- ✅ Generates live data every 5 seconds

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

**Leave this running!** Open a new terminal for Step 2.

---

### Step 2: Add to Prometheus (New Terminal)

```bash
# Add the exporter to Prometheus config
cd "/home/sujan-rathod/Desktop/NMS/NMS project"

cat >> config/prometheus.yml << 'EOF'

  # NMS Live Data Exporter
  - job_name: 'nms-live-exporter'
    scrape_interval: 5s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:9001']
        labels:
          service: 'nms_live_data'
          environment: 'demo'
EOF

# Restart Prometheus
docker-compose restart prometheus

echo "✅ Prometheus updated! Waiting for it to restart..."
sleep 5
echo "✅ Done! Prometheus is now scraping live data"
```

**Verify it's working**:
```bash
curl 'http://localhost:9090/api/v1/query?query=nms_device_reboots_total'
```

Should return data with `"status":"success"`

---

### Step 3: View in Grafana

**Open Grafana**: http://localhost:3000  
**Login**: admin / admin

#### Option A: Quick Panel (30 seconds)

1. Click **+** → **Dashboard** → **Add visualization**
2. Select **Prometheus**
3. In query box, enter:
   ```promql
   nms_interface_traffic_mbps
   ```
4. Legend format: `{{device_name}} - {{interface}}`
5. Visualization type: **Time series**
6. Click **Apply**

**You'll see**: 20 lines (5 devices × 4 interfaces) updating every 5 seconds! 📊

#### Option B: Complete Dashboard (2 minutes)

Create these panels:

**Panel 1: Device Reboots**
- Query: `sum(nms_device_reboots_total)`
- Type: Stat
- Title: "Total Device Reboots"

**Panel 2: Interface Traffic**
- Query: `nms_interface_traffic_mbps`
- Type: Time series
- Legend: `{{device_name}} - {{interface}}`
- Title: "Network Traffic (Mbps)"

**Panel 3: API Latency**
- Query: `nms_api_latency_seconds`
- Type: Time series
- Legend: `{{api_endpoint}}`
- Title: "API Response Time (seconds)"

**Panel 4: CPU Usage**
- Query: `nms_device_cpu_percent`
- Type: Time series
- Legend: `{{device_name}}`
- Title: "CPU Utilization %"

**Panel 5: Device Status**
- Query: `nms_device_status`
- Type: Time series
- Legend: `{{device_name}}`
- Title: "Device Status (1=UP, 0=DOWN)"

**Dashboard Settings**:
- Time range: **Last 15 minutes**
- Refresh: **5s** (auto-updates every 5 seconds!)

---

## 📊 What You'll See

### Real-Time Data Updates:

```
Device Reboots: Increases every 50 seconds
  └─ Counter showing total reboots

Interface Traffic: 20 lines (5 devices × 4 interfaces)
  └─ core-router-01 - eth0:  87 Mbps ⬆️⬇️
  └─ core-router-01 - eth1: 142 Mbps ⬆️⬇️
  └─ core-switch-01 - eth0: 103 Mbps ⬆️⬇️
  └─ (17 more lines...)

API Latency: 4 lines (4 endpoints)
  └─ /api/devices:  0.45s ⬆️⬇️
  └─ /api/metrics:  1.23s ⬆️⬇️
  └─ /api/alarms:   0.87s ⬆️⬇️
  └─ /api/device/update: 0.62s ⬆️⬇️

CPU Usage: 5 lines (5 devices)
  └─ core-router-01:   67% ⬆️⬇️
  └─ core-switch-01:   45% ⬆️⬇️
  └─ edge-router-01:   82% ⬆️⬇️
  └─ (2 more devices...)
```

**All updating LIVE every 5 seconds!** 🔥

---

## 🎨 Complete Example Queries

### Basic Queries

| Query | What It Shows |
|-------|---------------|
| `nms_device_reboots_total` | Reboots per device |
| `nms_interface_traffic_mbps` | Traffic per interface |
| `nms_api_latency_seconds` | API response times |
| `nms_device_cpu_percent` | CPU % per device |
| `nms_device_memory_percent` | Memory % per device |
| `nms_device_status` | Device up/down status |

### Advanced Queries

| Query | What It Shows |
|-------|---------------|
| `sum(nms_device_reboots_total)` | Total reboots across all devices |
| `avg(nms_interface_traffic_mbps)` | Average traffic across interfaces |
| `max(nms_api_latency_seconds)` | Slowest API endpoint |
| `nms_device_cpu_percent > 70` | Devices with high CPU |
| `nms_device_status == 0` | Devices that are DOWN |
| `topk(5, nms_interface_traffic_mbps)` | Top 5 busiest interfaces |

### Rate Calculations

| Query | What It Shows |
|-------|---------------|
| `rate(nms_device_reboots_total[1m])` | Reboot rate per minute |
| `avg_over_time(nms_interface_traffic_mbps[5m])` | 5-min average traffic |
| `increase(nms_device_reboots_total[1h])` | Reboots in last hour |

---

## ✅ Verification Checklist

After setup, verify:

- [ ] **Exporter running**: `curl http://localhost:9001/metrics` returns data
- [ ] **Prometheus scraping**: Check http://localhost:9090/targets (should see `nms-live-exporter` as UP)
- [ ] **Data in Prometheus**: `curl 'http://localhost:9090/api/v1/query?query=nms_interface_traffic_mbps'` returns results
- [ ] **Grafana shows data**: Create a panel with query and see live lines
- [ ] **Auto-refresh working**: Watch data change every 5 seconds

---

## 🎯 Demo Scenarios

### Scenario 1: Watch Traffic Spike

Watch the traffic lines in real-time. Every 5 seconds, they'll jump to new random values (50-150 Mbps).

**Query**: `nms_interface_traffic_mbps{device_name="core-router-01"}`

### Scenario 2: Count Device Reboots

Leave it running for 2 minutes. You'll see reboots increment 3 times (every 50 seconds).

**Query**: `sum(nms_device_reboots_total)`

### Scenario 3: Monitor API Performance

Watch API latency fluctuate between 0.1-1.5 seconds.

**Query**: `nms_api_latency_seconds`

### Scenario 4: Detect Device Failures

Occasionally (5% chance), a device will show status 0 (DOWN).

**Query**: `nms_device_status == 0`

---

## 🛠️ Customization

### Change Update Frequency

Edit `app_exporter.py` line 289:
```python
UPDATE_INTERVAL = 5  # Change to 10 for slower updates
```

### Change Port

Edit `app_exporter.py` line 288:
```python
EXPORTER_PORT = 9001  # Change to any free port
```

### Add More Devices

Edit `app_exporter.py` lines 97-103:
```python
DEVICES = [
    {'name': 'core-router-01', 'type': 'router', 'location': 'datacenter-1'},
    {'name': 'your-new-device', 'type': 'switch', 'location': 'floor-2'},
    # Add more here...
]
```

---

## 📱 One-Liner Commands

### Check Exporter
```bash
curl -s http://localhost:9001/metrics | grep -E "nms_device_reboots_total|nms_interface_traffic_mbps|nms_api_latency_seconds" | head -10
```

### Check Prometheus Has Data
```bash
curl -s 'http://localhost:9090/api/v1/query?query=nms_interface_traffic_mbps' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Found {len(d[\"data\"][\"result\"])} metrics')"
```

### Watch Live Updates
```bash
watch -n 5 'curl -s http://localhost:9001/metrics | grep "nms_interface_traffic_mbps.*eth0" | head -5'
```

---

## 🐛 Troubleshooting

### Exporter won't start

**Error**: `Address already in use`
```bash
# Find what's using port 9001
sudo lsof -i :9001
# Kill it or change the port in app_exporter.py
```

### Prometheus not scraping

```bash
# Check Prometheus config
cat config/prometheus.yml | grep -A 5 "nms-live-exporter"

# Restart Prometheus
docker-compose restart prometheus
```

### Grafana shows "No Data"

1. **Check time range**: Set to "Last 15 minutes"
2. **Check query**: Copy exact metric name from exporter
3. **Check Prometheus**: Query `http://localhost:9090/graph` and test query there first

### Need to restart everything

```bash
# Stop exporter (Ctrl+C in its terminal)
# Restart all services
docker-compose restart prometheus grafana
# Start exporter again
./start_live_exporter.sh
```

---

## 🎓 Learning Resources

### Understanding the Metrics

**Counter** (`nms_device_reboots_total`):
- Only goes up (never decreases)
- Resets to 0 if exporter restarts
- Use `rate()` or `increase()` for meaningful queries

**Gauge** (`nms_interface_traffic_mbps`, `nms_api_latency_seconds`):
- Can go up and down
- Represents current state
- Use directly or with `avg()`, `max()`, etc.

### Best Practices

1. **Set refresh interval**: Match exporter update (5s)
2. **Use labels**: Filter by device, interface, etc.
3. **Aggregate**: Use `sum()`, `avg()` for overview panels
4. **Alert on thresholds**: CPU > 80%, Latency > 1.0s
5. **Show rates**: Use `rate()` for counters

---

## 🎉 Success Criteria

You'll know it's working when:

✅ Terminal shows "Cycle X complete" every 5 seconds  
✅ `curl http://localhost:9001/metrics` returns metrics  
✅ Prometheus targets page shows `nms-live-exporter` as UP  
✅ Grafana panels show lines that update every 5 seconds  
✅ Values change each refresh (traffic, latency, etc.)  
✅ Reboot counter increases every ~50 seconds  

---

## 📊 Expected Performance

- **CPU Usage**: < 1%
- **Memory**: ~30-50 MB
- **Network**: Minimal (Prometheus scrapes locally)
- **Data Points**: ~140 per cycle (7 metrics × 20 labels)
- **Storage**: ~1 MB per hour in Prometheus

---

## 🚀 Next Steps

Once you have live data:

1. **Create alerts**: CPU > 80%, High latency, Device down
2. **Build dashboards**: Network overview, Per-device view
3. **Experiment**: Modify the exporter to add new metrics
4. **Compare**: Run alongside your real NMS system

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `app_exporter.py` | Main exporter script |
| `start_live_exporter.sh` | One-command startup |
| `APP_EXPORTER_GUIDE.md` | Detailed documentation |
| `LIVE_DATA_SETUP.md` | This quick start guide |

---

**Created**: October 23, 2025  
**Status**: ✅ **READY TO USE**  
**Time to Setup**: **3 minutes**

**Start seeing LIVE data in Grafana NOW!** 🚀

---

## 💡 Pro Tips

1. **Run in screen/tmux**: Keep exporter running when you close terminal
2. **Create systemd service**: Auto-start on boot (see APP_EXPORTER_GUIDE.md)
3. **Monitor the monitor**: Add alerts if exporter goes down
4. **Save your dashboard**: Export JSON for future use
5. **Combine with real data**: Run both exporters (9100 + 9001)

---

**Need help?** Check `APP_EXPORTER_GUIDE.md` for complete documentation!
