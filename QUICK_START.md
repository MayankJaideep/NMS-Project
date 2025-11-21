# 🚀 SCNMS Quick Start Guide

## ✅ What's Ready Right Now

### 📊 Sample Data Loaded Successfully!

**You now have:**
- ✅ **6,000 metrics** (CPU, Memory, Bandwidth, etc.)
- ✅ **25 alarms** (7 active, 6 acknowledged, 12 cleared)
- ✅ **5 devices** (4 active network devices)
- ✅ **6 hours** of historical data
- ✅ **Real-time dashboards** ready to view

---

## 🎯 START HERE (5 Minutes)

### Step 1: Open Grafana

```bash
# Open in your browser
http://localhost:3000
```

**Login:**
- Username: `admin`
- Password: `admin`

### Step 2: View Your Dashboards

1. Click **☰ (hamburger menu)** in top-left
2. Click **Dashboards**
3. You'll see 3 dashboards - **open each one!**

---

## 📈 The 3 Dashboards Explained

### 1. 🚨 Alarm Lifecycle Dashboard

**What You'll See:**
- **7 Active Alarms** showing right now
- **Alarm breakdown by severity**:
  - Critical alarms (red)
  - Major alarms (orange)  
  - Minor alarms (yellow)
- **Alarms over time** - trends chart
- **Active alarms table** - detailed list

**Try This:**
- Change time range (top-right corner)
- Click on different severity levels
- Enable auto-refresh (30 seconds)

### 2. 📊 Network Utilization Dashboard

**What You'll See:**
- **Total bandwidth** across all devices
- **Bandwidth by device** - compare traffic
  - Core-Switch-01: Highest traffic
  - Router-01: Medium traffic
  - Others: Lower traffic
- **Interface utilization** heatmap
- **Top interfaces** by usage

**Try This:**
- Zoom into specific time ranges
- Compare inbound vs outbound traffic
- Look for traffic spikes

### 3. ❤️ Device Health Dashboard

**What You'll See:**
- **4 devices UP** (all healthy)
- **CPU usage** per device:
  - Core-Switch-01: ~45-85%
  - Router-01: ~50-85%
  - Access switches: Lower
- **Memory usage** per device
- **Temperature monitoring**
- **Complete device inventory table**

**Try This:**
- Watch CPU/Memory gauges
- Check temperature trends
- Review device status table

---

## 💡 Quick Tips

### Change Time Range
- Top-right corner: Click time selector
- Try: "Last 6 hours" (all your data)
- Or: "Last 1 hour" (recent data)

### Auto-Refresh
- Top-right: Click refresh dropdown
- Select: "30s" or "1m"
- Dashboard updates automatically!

### Zoom In/Out
- **Zoom In**: Click and drag on any chart
- **Zoom Out**: Click "Zoom out" button or double-click
- **Reset**: Click 🔄 refresh icon

### Full Screen
- Click panel title → View → Fullscreen
- Press `ESC` to exit

---

## 🔧 Using the API

### See All Devices

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
    "status": "UP",
    "vendor": "Cisco",
    "model": "Catalyst 9300"
  },
  // ... 4 more devices
]
```

### Add a New Device

```bash
curl -X POST "http://localhost:8000/api/v1/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My-New-Switch",
    "ip_address": "10.0.0.50",
    "snmp_enabled": true,
    "snmp_community": "public",
    "snmp_version": "2c"
  }'
```

### Interactive API Documentation

```bash
# Open in browser
http://localhost:8000/docs
```

- Click any endpoint to expand
- Click **"Try it out"**
- Edit parameters
- Click **"Execute"**
- See results instantly!

---

## 📊 Your Sample Data Breakdown

### Devices (5 total)
| Device | IP | Status | Role |
|--------|-----|--------|------|
| Core-Switch-01 | 192.168.1.1 | UP | Main campus switch |
| Access-Switch-01 | 192.168.1.2 | UP | Building A access |
| Router-01 | 192.168.1.254 | UP | Campus router |
| Firewall-01 | 192.168.1.253 | UP | Security firewall |
| Test-Device | 192.168.100.1 | UNKNOWN | Test device |

### Metrics (6,000 data points)
- **10 metric types** per device
- **Every 2 minutes** for 6 hours
- **150 timestamps** total

**Metric Types:**
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

### Alarms (25 total)
- **7 Active** (needs attention)
- **6 Acknowledged** (being handled)
- **12 Cleared** (resolved)

**By Severity:**
- Critical: 2 active
- Major: 3 active
- Minor: 2 active
- Warning: 0 active

---

## 🎨 Customize Your Experience

### Create Your Own Dashboard

1. In Grafana: Click **+ → Dashboard**
2. Click **"Add visualization"**
3. Select **Prometheus** as data source
4. Write a query (or use examples below)
5. Choose chart type (graph, gauge, table, etc.)
6. Click **"Apply"** and **"Save"**

### Example Queries

**Average CPU:**
```promql
avg(scnms_metric{metric_name="cpu_utilization"})
```

**Max Memory by Device:**
```promql
max by (device_name) (scnms_metric{metric_name="memory_utilization"})
```

**Total Bandwidth:**
```promql
sum(scnms_metric{metric_name="bandwidth_in"})
```

---

## 🔍 What to Look For

### Healthy Signs ✅
- All devices showing "UP"
- CPU < 80% most of the time
- Memory < 90%
- Temperature < 65°C
- Minimal packet loss (<1%)

### Warning Signs ⚠️
- CPU consistently >80%
- Memory >90%
- Temperature >70°C
- Many active critical alarms
- Sudden bandwidth spikes

---

## 📚 Need More Help?

### Full Documentation
- **USER_GUIDE.md** - Complete tutorial (15+ pages)
- **DEPLOYMENT.md** - Production setup
- **README.md** - Project overview

### Common Commands

```bash
# Check system status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Start everything
docker-compose up -d
```

### Troubleshooting

**Dashboard shows "No Data"?**
```bash
# Check if containers running
docker-compose ps

# Restart Grafana
docker-compose restart grafana
```

**Can't login to Grafana?**
- URL: http://localhost:3000
- User: `admin`
- Pass: `admin`

---

## 🎯 Your First 15 Minutes

### Minute 1-5: Explore Dashboards
1. Open Grafana (http://localhost:3000)
2. Login (admin/admin)
3. Open each of the 3 dashboards
4. Change time range to "Last 6 hours"

### Minute 6-10: Understand the Data
1. Look at alarm counts
2. Check which devices have high CPU
3. Compare bandwidth between devices
4. Review active alarms in table

### Minute 11-15: Try the API
1. Open API docs (http://localhost:8000/docs)
2. Try GET /api/v1/devices
3. Try GET /api/v1/health/services
4. Explore other endpoints

---

## 🚀 What's Next?

### This Week
- [ ] Explore all 3 Grafana dashboards
- [ ] Try the interactive API at /docs
- [ ] Read the USER_GUIDE.md
- [ ] Customize dashboard time ranges

### Next Week
- [ ] Add your own device via API
- [ ] Create a custom dashboard
- [ ] Set up alarm notifications
- [ ] Export some data

### Going to Production
- [ ] Configure real network devices
- [ ] Set up SNMP on your switches/routers
- [ ] Create custom alarm rules
- [ ] Set up backups
- [ ] Enable SSL/authentication

---

## ✅ You're All Set!

**Your SCNMS is fully operational with real data!**

👉 **Start here:** http://localhost:3000

Open Grafana now and see your network monitoring in action! 🎉

---

**Questions?** Check USER_GUIDE.md for detailed explanations!
