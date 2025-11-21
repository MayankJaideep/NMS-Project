# 📚 SCNMS Complete User Guide

**Smart Campus Network Monitoring System - How to Use**

---

## 🎯 Quick Start (5 Minutes)

### What You Just Got
✅ **6,000 metrics** across 4 devices over 6 hours  
✅ **25 alarms** with different severity levels  
✅ **Real-time dashboards** ready to view  
✅ **Full API access** for automation

---

## 🌐 Access Your System

| Service | URL | Login |
|---------|-----|-------|
| **Grafana Dashboards** | http://localhost:3000 | admin / admin |
| **API Documentation** | http://localhost:8000/docs | No login needed |
| **Prometheus Metrics** | http://localhost:9090 | No login needed |

---

## 📊 Part 1: Using Grafana Dashboards

### Step 1: Open Grafana

```bash
# Open in your browser
http://localhost:3000
```

**First Time Login:**
- Username: `admin`
- Password: `admin`
- You'll be asked to change password (you can skip for now)

### Step 2: Navigate to Dashboards

1. Click **☰ menu** (top left)
2. Select **Dashboards**
3. You'll see a folder or dashboard list
4. Look for these 3 dashboards:

   - 🚨 **SCNMS - Alarm Lifecycle Dashboard**
   - 📈 **SCNMS - Network Utilization Dashboard**
   - ❤️ **SCNMS - Device Health Dashboard**

### Step 3: Explore the Alarm Dashboard

**What You'll See:**

1. **Active Alarms Count** (top left)
   - Shows how many alarms are currently active
   - Color changes: Green (0-5), Yellow (5-10), Red (10+)

2. **Critical Alarms** (top)
   - Immediate attention needed
   - Should be 2 active critical alarms

3. **Alarms by Severity** (pie chart)
   - Visual breakdown: Critical, Major, Minor, Warning
   - Click on slices to filter

4. **Alarm Trend Over Time** (line chart)
   - Shows alarms raised vs cleared
   - Helps spot patterns

5. **Recent Active Alarms Table** (bottom)
   - Lists all current alarms
   - Shows device, severity, status

**How to Use:**
- **Change Time Range**: Top-right corner (default: Last 24h)
- **Auto-Refresh**: Top-right dropdown (set to 30s or 1m)
- **Filter by Device**: Click on device names in legends
- **Zoom In**: Click and drag on any chart

### Step 4: Network Utilization Dashboard

**Key Metrics:**

1. **Total Bandwidth** (top)
   - Combined network throughput
   - Measured in Mbps or Gbps

2. **Bandwidth by Device** (chart)
   - Compare traffic across devices
   - Core-Switch-01 should show highest

3. **Interface Utilization Heatmap**
   - Visual representation over time
   - Darker colors = higher usage

4. **Top 10 Interfaces** (bar chart)
   - Busiest network interfaces
   - Quick identification of bottlenecks

**Tips:**
- Look for **sudden spikes** = potential issues
- Compare **inbound vs outbound** traffic
- Check **utilization percentage** (>80% = concern)

### Step 5: Device Health Dashboard

**Health Indicators:**

1. **Devices UP/DOWN** (gauges)
   - Should show 4/4 devices UP
   - Immediate status overview

2. **CPU Utilization by Device** (bar gauges)
   - Core-Switch-01: ~45-85%
   - Router-01: ~50-85%
   - Others: Lower

3. **Memory Utilization**
   - Similar layout to CPU
   - Track memory consumption

4. **Temperature Monitoring**
   - Device temperature graphs
   - Normal range: 35-65°C
   - Warning: >65°C

5. **Device Inventory Table** (bottom)
   - Complete device list
   - Status, vendor, model, location

**What to Watch For:**
- ⚠️ CPU >80% for extended periods
- ⚠️ Memory >90%
- ⚠️ Temperature >70°C
- ✅ All devices status = "UP"

---

## 🔧 Part 2: Using the REST API

### Access API Documentation

```bash
# Open in browser
http://localhost:8000/docs
```

This opens **Swagger UI** - interactive API documentation!

### Common API Operations

#### 1. List All Devices

**Method**: GET  
**Endpoint**: `/api/v1/devices`

**Try it:**
```bash
curl http://localhost:8000/api/v1/devices | python3 -m json.tool
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Core-Switch-01",
    "ip_address": "192.168.1.1",
    "status": "up",
    "vendor": "Cisco",
    "model": "Catalyst 9300"
  },
  // ... more devices
]
```

#### 2. Add a New Device

**Method**: POST  
**Endpoint**: `/api/v1/devices`

**Try it:**
```bash
curl -X POST "http://localhost:8000/api/v1/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New-Switch-01",
    "ip_address": "192.168.1.10",
    "hostname": "new-sw-01.campus.edu",
    "vendor": "Cisco",
    "model": "Catalyst 2960",
    "location": "Building B",
    "description": "New access switch",
    "snmp_enabled": true,
    "snmp_community": "public",
    "snmp_version": "2c"
  }'
```

**In Swagger UI:**
1. Expand `/api/v1/devices` POST
2. Click **"Try it out"**
3. Edit the JSON in the request body
4. Click **"Execute"**
5. See the response below

#### 3. Get Device Details

**Method**: GET  
**Endpoint**: `/api/v1/devices/{id}`

```bash
curl http://localhost:8000/api/v1/devices/1 | python3 -m json.tool
```

#### 4. Query Alarms

**Method**: GET  
**Endpoint**: `/api/v1/alarms`

**Parameters:**
- `status`: Filter by status (raised, acknowledged, cleared)
- `severity`: Filter by severity (critical, major, minor, warning)
- `device_id`: Filter by device

**Examples:**
```bash
# All active alarms
curl "http://localhost:8000/api/v1/alarms?status=raised"

# Critical alarms only
curl "http://localhost:8000/api/v1/alarms?severity=critical"

# Alarms for specific device
curl "http://localhost:8000/api/v1/alarms?device_id=1"
```

#### 5. Acknowledge an Alarm

**Method**: POST  
**Endpoint**: `/api/v1/alarms/{alarm_id}/acknowledge`

```bash
# Get alarm ID from alarms list, then:
curl -X POST "http://localhost:8000/api/v1/alarms/alarm-critical-1-1/acknowledge" \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "your-name"}'
```

#### 6. Query Metrics

**Method**: GET  
**Endpoint**: `/api/v1/metrics`

**Parameters:**
- `device_id`: Specific device (optional)
- `metric_name`: Specific metric (optional)
- `hours`: Time range in hours (default: 1)

**Examples:**
```bash
# All metrics for last hour
curl "http://localhost:8000/api/v1/metrics?hours=1"

# CPU metrics for device 1
curl "http://localhost:8000/api/v1/metrics?device_id=1&metric_name=cpu_utilization"

# Last 6 hours of data
curl "http://localhost:8000/api/v1/metrics?hours=6"
```

---

## 🎨 Part 3: Customizing Dashboards

### Create Your Own Dashboard

1. **In Grafana**: Click **+ → Dashboard**
2. **Add Panel**: Click **"Add visualization"**
3. **Choose Data Source**: Select "Prometheus"
4. **Write Query**: 
   ```promql
   # CPU usage
   scnms_metric{metric_name="cpu_utilization"}
   
   # Bandwidth
   scnms_metric{metric_name="bandwidth_in"}
   ```
5. **Customize**: Change chart type, colors, thresholds
6. **Save**: Click 💾 icon, give it a name

### Useful PromQL Queries

```promql
# Average CPU across all devices
avg(scnms_metric{metric_name="cpu_utilization"})

# Max memory usage by device
max by (device_name) (scnms_metric{metric_name="memory_utilization"})

# Total bandwidth
sum(scnms_metric{metric_name="bandwidth_in"})

# Alarms in last 24h
count(scnms_alarm_status{status="raised"})

# Device availability
count(scnms_device_status{status="up"}) / count(scnms_device_status)
```

---

## 🔔 Part 4: Managing Alarms

### Alarm Lifecycle

1. **RAISED** → Alarm triggered by threshold
2. **ACKNOWLEDGED** → Engineer aware of issue
3. **CLEARED** → Problem resolved
4. **CLOSED** → Alarm archived

### Acknowledge Alarms (Via UI)

Since Grafana shows read-only data, use the API:

```bash
# List active alarms
curl http://localhost:8000/api/v1/alarms?status=raised

# Acknowledge alarm (replace alarm-id)
curl -X POST "http://localhost:8000/api/v1/alarms/ALARM-ID/acknowledge" \
  -H "Content-Type: application/json" \
  -d '{"acknowledged_by": "your-name"}'

# Clear alarm
curl -X POST "http://localhost:8000/api/v1/alarms/ALARM-ID/clear"
```

### Create Alarm Rules

**Method**: POST  
**Endpoint**: `/api/v1/alarm-rules`

```bash
curl -X POST "http://localhost:8000/api/v1/alarm-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Very High CPU",
    "description": "CPU above 95%",
    "metric_name": "cpu_utilization",
    "threshold_value": 95.0,
    "comparison_operator": ">",
    "duration_seconds": 300,
    "severity": "critical",
    "enabled": true
  }'
```

---

## 📈 Part 5: Understanding Your Data

### Current Sample Data Includes:

**Devices (4):**
- Core-Switch-01 (192.168.1.1) - Main campus switch
- Access-Switch-01 (192.168.1.2) - Building A access
- Router-01 (192.168.1.254) - Campus router
- Firewall-01 (192.168.1.253) - Security firewall

**Metrics (10 types):**
1. CPU Utilization (%)
2. Memory Utilization (%)
3. Interface Utilization (%)
4. Bandwidth In (Mbps)
5. Bandwidth Out (Mbps)
6. Packets per Second
7. Latency (ms)
8. Packet Loss Rate (%)
9. Temperature (°C)
10. Interface Errors (count)

**Data Points:**
- 6,000 total metrics
- 150 timestamps over 6 hours
- Every 2 minutes
- 10 metrics × 4 devices × 150 timestamps

**Alarms (25 total):**
- 2 Active Critical
- 3 Active Major
- 2 Active Minor
- Rest acknowledged/cleared

---

## 🚀 Part 6: Common Tasks

### Task 1: Check System Health

```bash
# Quick health check
curl http://localhost:8000/api/v1/health/services | python3 -m json.tool
```

**All services should show "healthy"**

### Task 2: Find Devices with High CPU

**Via API:**
```bash
curl "http://localhost:8000/api/v1/metrics?metric_name=cpu_utilization&hours=1" \
  | python3 -c "import sys, json; data = json.load(sys.stdin); high_cpu = [m for m in data if m['metric_value'] > 80]; print(json.dumps(high_cpu, indent=2))"
```

**Via Grafana:**
1. Go to Device Health Dashboard
2. Look at CPU utilization gauges
3. Red = >80% (high)

### Task 3: Monitor Bandwidth Trends

**Via Grafana:**
1. Open Network Utilization Dashboard
2. Look at "Bandwidth Usage" time series
3. Zoom to specific time range
4. Identify peaks and valleys

**Via Prometheus:**
1. Open http://localhost:9090
2. Query: `scnms_metric{metric_name="bandwidth_in"}`
3. Click "Graph" tab
4. Adjust time range

### Task 4: Export Data

**Via API (JSON):**
```bash
# Export all metrics for last 6 hours
curl "http://localhost:8000/api/v1/metrics?hours=6" > metrics_export.json

# Export alarms
curl "http://localhost:8000/api/v1/alarms" > alarms_export.json

# Export devices
curl "http://localhost:8000/api/v1/devices" > devices_export.json
```

**Via Grafana:**
1. Open any dashboard
2. Click on panel title
3. Select "Inspect" → "Data"
4. Click "Download CSV"

---

## 🔍 Part 7: Troubleshooting

### Dashboard Shows "No Data"

**Check:**
```bash
# Verify metrics exist
docker-compose exec -T postgres psql -U scnms -d scnms -c "SELECT COUNT(*) FROM metrics;"

# Should show 6000+
```

**Fix:**
```bash
# Reload sample data
docker-compose exec -T postgres psql -U scnms -d scnms < database/insert_sample_data.sql
```

### Services Not Responding

**Check Status:**
```bash
docker-compose ps
```

**Restart Services:**
```bash
docker-compose restart
```

### Can't Access Grafana

**Check Port:**
```bash
sudo lsof -i :3000
```

**Restart Grafana:**
```bash
docker-compose restart grafana
```

### API Returns Errors

**Check Logs:**
```bash
docker-compose logs -f api
docker-compose logs -f device-discovery
```

---

## 💡 Part 8: Best Practices

### Daily Monitoring Routine

**Morning:**
1. Open Device Health Dashboard
2. Check all devices are "UP"
3. Review critical alarms
4. Acknowledge any new alarms

**During Day:**
1. Monitor utilization dashboard
2. Watch for bandwidth spikes
3. Check temperature trends
4. Review alarm trends

**Evening:**
1. Acknowledge all alarms
2. Export daily metrics
3. Review patterns for optimization

### Setting Up Alerts

**Create Alert Rule in Grafana:**
1. Edit panel in dashboard
2. Go to "Alert" tab
3. Set conditions (e.g., CPU > 80%)
4. Configure notification channel
5. Test alert

### Data Retention

**Current Setup:**
- Prometheus: 200 hours (~8 days)
- PostgreSQL: Unlimited (manual cleanup needed)

**Cleanup Old Data:**
```sql
-- Delete metrics older than 30 days
DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '30 days';

-- Delete closed alarms older than 90 days
DELETE FROM alarms WHERE status = 'closed' AND closed_at < NOW() - INTERVAL '90 days';
```

---

## 🎓 Part 9: Advanced Usage

### Automation with Scripts

**Auto-acknowledge alarms:**
```bash
#!/bin/bash
# auto_ack_minor.sh
ALARMS=$(curl -s "http://localhost:8000/api/v1/alarms?status=raised&severity=minor")
echo "$ALARMS" | jq -r '.[].alarm_id' | while read alarm_id; do
    curl -X POST "http://localhost:8000/api/v1/alarms/$alarm_id/acknowledge" \
        -H "Content-Type: application/json" \
        -d '{"acknowledged_by": "auto-script"}'
done
```

### Integrate with Other Tools

**Send to Slack:**
```bash
# When critical alarm
curl -X POST YOUR_SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text": "Critical alarm on Core-Switch-01"}'
```

**Export to CSV:**
```bash
# Python script
import requests
import csv

metrics = requests.get("http://localhost:8000/api/v1/metrics?hours=24").json()

with open('metrics.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
    writer.writeheader()
    writer.writerows(metrics)
```

---

## 📚 Quick Reference

### Keyboard Shortcuts in Grafana

| Key | Action |
|-----|--------|
| `?` | Show shortcuts |
| `d k` | Toggle kiosk mode |
| `t z` | Zoom out time range |
| `ctrl+s` | Save dashboard |
| `esc` | Exit fullscreen |

### Important URLs

```
Grafana:     http://localhost:3000
API Docs:    http://localhost:8000/docs
Prometheus:  http://localhost:9090
PostgreSQL:  localhost:5432 (scnms/scnms)
Redis:       localhost:6379
```

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# Restart everything
docker-compose restart

# Stop system
docker-compose down

# Start system
docker-compose up -d

# Database backup
docker-compose exec postgres pg_dump -U scnms scnms > backup.sql

# Restore database
docker-compose exec -T postgres psql -U scnms -d scnms < backup.sql
```

---

## 🎯 Next Steps

### Week 1: Learn the Basics
- [ ] Explore all 3 dashboards
- [ ] Try all API endpoints in Swagger
- [ ] Add a test device via API
- [ ] Acknowledge sample alarms

### Week 2: Customize
- [ ] Create your own dashboard
- [ ] Set up custom alarm rules
- [ ] Configure alert notifications
- [ ] Export and analyze data

### Week 3: Production Ready
- [ ] Add real network devices
- [ ] Configure SNMP on devices
- [ ] Set up backup procedures
- [ ] Document your setup

---

## 📞 Support & Resources

### Documentation Files
- `README.md` - Project overview
- `DEPLOYMENT.md` - Production deployment
- `UBUNTU_SYSTEM_REQUIREMENTS.md` - System setup
- `CODE_ANALYSIS_AND_FIXES.md` - Technical details

### Get Help
- Check logs: `docker-compose logs`
- API docs: http://localhost:8000/docs
- This guide: `USER_GUIDE.md`

---

**Congratulations! You're now ready to use SCNMS!** 🎉

Start with Grafana (http://localhost:3000) and explore the dashboards with your sample data!
