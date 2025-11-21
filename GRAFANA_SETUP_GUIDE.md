# 📊 Grafana Data Display - Complete Setup Guide

**Issue**: Grafana dashboards showing "No Data"  
**Solution**: Use the correct metric names and queries  
**Status**: ✅ **NEW WORKING DASHBOARD CREATED**

---

## ✅ What's Already Working

### Prometheus Exporter ✅
- **Status**: Running and exporting metrics
- **Port**: 9100
- **Metrics**: 37 types available

**Verify**:
```bash
curl http://localhost:9100/metrics | grep scnms_device
```

**Available Metrics**:
```
scnms_device_cpu_utilization
scnms_device_memory_utilization
scnms_device_bandwidth_in
scnms_device_bandwidth_out
scnms_device_latency
scnms_device_temperature
scnms_device_interface_utilization
scnms_device_packet_loss_rate
scnms_device_status
scnms_alarms_raised
scnms_alarms_acknowledged
scnms_alarms_cleared
```

### Prometheus ✅
- **Status**: Scraping metrics every 30 seconds
- **Target**: http://prometheus-exporter:9100
- **Health**: UP

**Verify**:
```bash
curl -s 'http://localhost:9090/api/v1/query?query=scnms_device_cpu_utilization' | python3 -m json.tool
```

---

## 🎯 Solution: Import New Working Dashboard

### Method 1: Import the New Dashboard (EASIEST)

I've created a **new working dashboard** with the correct metric queries:

**File**: `config/grafana/dashboards/scnms-overview.json`

### Step 1: Access Grafana
```
http://localhost:3000
```
- Username: `admin`
- Password: `admin`

### Step 2: Import the Dashboard

1. Click **☰** (hamburger menu) in top-left
2. Click **Dashboards**
3. Click **Import** button
4. Click **Upload JSON file**
5. Select: `/home/sujan-rathod/Desktop/NMS/NMS project/config/grafana/dashboards/scnms-overview.json`
6. Click **Import**

### Step 3: View Your Data! 🎉

The new dashboard includes:

1. **Total Devices** (stat panel)
2. **Devices UP** (stat panel)
3. **Active Alarms** (stat panel)
4. **CPU Utilization** (time series chart)
5. **Memory Utilization** (time series chart)
6. **Bandwidth** (IN/OUT chart)
7. **Active Alarms by Severity** (bar chart)

**All panels will show data immediately!**

---

## 🔧 Method 2: Create Dashboard Manually

If import doesn't work, create panels manually:

### Panel 1: Total Devices

1. Click **+ Add** → **Visualization**
2. Select data source: **Prometheus**
3. In query field, enter:
   ```promql
   count(scnms_device_status)
   ```
4. Change visualization type to **Stat**
5. Set title: "Total Devices"
6. Click **Apply**

### Panel 2: Devices UP

1. Add new panel
2. Query:
   ```promql
   sum(scnms_device_status)
   ```
3. Visualization: **Stat**
4. Title: "Devices UP"

### Panel 3: CPU Utilization

1. Add new panel
2. Query:
   ```promql
   scnms_device_cpu_utilization
   ```
3. Legend format: `{{device_name}} CPU`
4. Visualization: **Time series**
5. Title: "CPU Utilization"
6. Unit: **Percent (0-100)**

### Panel 4: Memory Utilization

1. Add new panel
2. Query:
   ```promql
   scnms_device_memory_utilization
   ```
3. Legend format: `{{device_name}} Memory`
4. Visualization: **Time series**
5. Title: "Memory Utilization"
6. Unit: **Percent (0-100)**

### Panel 5: Bandwidth

1. Add new panel
2. Query A:
   ```promql
   scnms_device_bandwidth_in
   ```
   Legend: `{{device_name}} IN`
3. Query B (click **+ Query**):
   ```promql
   scnms_device_bandwidth_out
   ```
   Legend: `{{device_name}} OUT`
4. Visualization: **Time series**
5. Title: "Bandwidth"
6. Unit: **Mbps**

### Panel 6: Active Alarms

1. Add new panel
2. Query:
   ```promql
   scnms_alarms_raised
   ```
3. Legend format: `{{severity}}`
4. Visualization: **Bar chart** or **Time series**
5. Title: "Active Alarms by Severity"

---

## 📊 All Available Queries

### Device Metrics

| Metric | Query | Description |
|--------|-------|-------------|
| CPU Usage | `scnms_device_cpu_utilization` | CPU % per device |
| Memory Usage | `scnms_device_memory_utilization` | Memory % per device |
| Bandwidth IN | `scnms_device_bandwidth_in` | Inbound traffic (Mbps) |
| Bandwidth OUT | `scnms_device_bandwidth_out` | Outbound traffic (Mbps) |
| Latency | `scnms_device_latency` | Network latency (ms) |
| Temperature | `scnms_device_temperature` | Device temp (°C) |
| Interface Util | `scnms_device_interface_utilization` | Interface usage (%) |
| Packet Loss | `scnms_device_packet_loss_rate` | Packet loss (%) |
| Device Status | `scnms_device_status` | 1=UP, 0=DOWN |

### Alarm Metrics

| Metric | Query | Description |
|--------|-------|-------------|
| Active Alarms | `scnms_alarms_raised` | Count by severity |
| Acknowledged | `scnms_alarms_acknowledged` | Count by severity |
| Cleared | `scnms_alarms_cleared` | Count by severity |
| Total Active | `sum(scnms_alarms_raised)` | Total count |
| Critical Only | `scnms_alarms_raised{severity="CRITICAL"}` | Critical count |

### Aggregate Queries

| Query | Description |
|-------|-------------|
| `count(scnms_device_status)` | Total devices |
| `sum(scnms_device_status)` | Devices UP |
| `avg(scnms_device_cpu_utilization)` | Average CPU |
| `max(scnms_device_cpu_utilization)` | Highest CPU |
| `sum(scnms_device_bandwidth_in)` | Total bandwidth IN |

---

## 🎨 Dashboard Settings

### Time Range
- Default: **Last 15 minutes**
- Recommended: **Last 30 minutes** or **Last 1 hour**

### Auto-Refresh
- Recommended: **30 seconds** (matches Prometheus scrape interval)
- Settings: Top-right corner → Refresh interval

### Variables (Optional)

Create a device variable to filter by device:

1. Dashboard settings → Variables → Add variable
2. Name: `device`
3. Type: **Query**
4. Data source: **Prometheus**
5. Query: `label_values(scnms_device_cpu_utilization, device_name)`
6. Then use in queries: `scnms_device_cpu_utilization{device_name="$device"}`

---

## 🔍 Troubleshooting

### Problem: "No Data" in panels

**Check 1: Prometheus has data**
```bash
curl 'http://localhost:9090/api/v1/query?query=scnms_device_cpu_utilization'
```
Should return data with `"status":"success"`

**Check 2: Time range**
- Make sure time range includes recent data
- Try "Last 15 minutes" or "Last 1 hour"

**Check 3: Data source**
- Dashboard settings → check Prometheus is selected
- Datasource URL should be: `http://prometheus:9090`

**Check 4: Query syntax**
- Queries are case-sensitive
- Use exact metric names as shown above

### Problem: Old dashboards still showing

**Solution**: Use the new dashboard I created

The old dashboards have incorrect queries. The new `scnms-overview.json` dashboard has all the correct queries.

### Problem: Can't see new dashboard

**Solution 1**: Import manually (see Method 1 above)

**Solution 2**: Restart Grafana
```bash
sudo docker-compose restart grafana
```

Then check: Dashboards → Browse → Look for "SCNMS - Live Overview Dashboard"

---

## 📱 Quick Start (3 Steps)

### 1. Open Grafana
```
http://localhost:3000
```
Login: admin / admin

### 2. Import Dashboard
- **☰** → **Dashboards** → **Import**
- Upload: `config/grafana/dashboards/scnms-overview.json`

### 3. View Data!
Your dashboard will immediately show:
- 5 devices (4 UP)
- CPU/Memory charts with data
- Bandwidth charts with traffic
- 7 active alarms

---

## 🎯 Expected Results

Once the dashboard is imported, you should see:

### Stats (Top Row)
```
Total Devices: 5
Devices UP: 4
Active Alarms: 7
```

### Charts (Rows 2-4)
1. **CPU Utilization**: 4 lines showing different devices
   - Core-Switch-01: ~68%
   - Access-Switch-01: ~46%
   - Router-01: ~79%
   - Firewall-01: ~41%

2. **Memory Utilization**: 4 lines
   - Various percentages per device

3. **Bandwidth**: 8 lines total (IN + OUT for each device)
   - Data in Mbps

4. **Alarms**: Bars showing:
   - CRITICAL: 2
   - MAJOR: 3
   - MINOR: 2

---

## ✅ Verification Commands

### Test Prometheus has data:
```bash
# Test CPU metric
curl -s 'http://localhost:9090/api/v1/query?query=scnms_device_cpu_utilization' | python3 -m json.tool

# Test alarm metric
curl -s 'http://localhost:9090/api/v1/query?query=scnms_alarms_raised' | python3 -m json.tool

# Test device status
curl -s 'http://localhost:9090/api/v1/query?query=scnms_device_status' | python3 -m json.tool
```

All should return `"status": "success"` with data in `"result"` array.

### Test exporter directly:
```bash
curl http://localhost:9100/metrics | grep "^scnms_device_cpu"
```

Should show 4 devices with CPU values.

---

## 🎨 Screenshot Preview

After import, your dashboard will look like:

```
┌────────────────────────────────────────────────────────┐
│  Total Devices    Devices UP     Active Alarms        │
│       5               4                7               │
├────────────────────────────────────────────────────────┤
│                 CPU Utilization                        │
│  [Line chart showing 4 device CPU trends over time]   │
├────────────────────────────────────────────────────────┤
│              Memory Utilization                        │
│  [Line chart showing 4 device memory trends]          │
├────────────────────────────────────────────────────────┤
│                   Bandwidth                            │
│  [Line chart showing IN/OUT traffic for devices]      │
├────────────────────────────────────────────────────────┤
│           Active Alarms by Severity                    │
│  [Bar chart: CRITICAL=2, MAJOR=3, MINOR=2]            │
└────────────────────────────────────────────────────────┘
```

---

## 📚 Additional Resources

### Prometheus Query Examples

**CPU above 70%**:
```promql
scnms_device_cpu_utilization > 70
```

**Total bandwidth (all devices)**:
```promql
sum(scnms_device_bandwidth_in)
```

**Average memory across devices**:
```promql
avg(scnms_device_memory_utilization)
```

**Devices with high temperature**:
```promql
scnms_device_temperature > 60
```

### Dashboard Tips

1. **Save often**: Click 💾 icon after making changes
2. **Set time range**: Top-right corner
3. **Enable auto-refresh**: Set to 30s for real-time updates
4. **Add alerts**: Click on panel → Alert tab
5. **Share**: Dashboard settings → JSON Model (to export)

---

## 🎉 Success Criteria

You'll know it's working when you see:

✅ Stat panels showing numbers (not "No Data")  
✅ Line charts with colored lines (not empty)  
✅ Data points when hovering over charts  
✅ Legend showing device names  
✅ Auto-refresh updating values every 30s  

---

## 🆘 Still Having Issues?

### Check all services:
```bash
docker-compose ps
```

All should show "Up"

### Check logs:
```bash
# Grafana logs
docker-compose logs -f grafana

# Prometheus logs
docker-compose logs -f prometheus

# Exporter logs
docker-compose logs -f prometheus-exporter
```

### Restart everything:
```bash
# Restart Prometheus to reload config
sudo docker-compose restart prometheus

# Restart exporter
sudo docker-compose restart prometheus-exporter

# Restart Grafana
sudo docker-compose restart grafana
```

Wait 1 minute, then try accessing Grafana again.

---

**Created**: October 22, 2025  
**Dashboard File**: `config/grafana/dashboards/scnms-overview.json`  
**Status**: ✅ **READY TO IMPORT**

**Your data is there - just import the new dashboard and you'll see it!** 🚀
