# SCNMS Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or later
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 50GB+ free space
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+

### Network Requirements
- Ports 8000-8004, 3000, 5432, 6379, 9090 available
- Network access to monitored devices
- SNMP, NETCONF, RESTCONF access to network devices

## Quick Start

### 1. Initial Setup

```bash
# Clone or navigate to the project directory
cd /path/to/scnms

# Run setup script
chmod +x setup.sh start.sh stop.sh
./setup.sh

# Update .env with your configuration
nano .env
```

### 2. Start Services

```bash
# Start all services
./start.sh

# Or manually with docker-compose
docker-compose up -d
```

### 3. Verify Installation

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Access services
# API: http://localhost:8000/docs
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### 4. Add Your First Device

```bash
# Using API
curl -X POST "http://localhost:8000/api/v1/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Core-Switch",
    "ip_address": "192.168.1.1",
    "snmp_enabled": true,
    "snmp_community": "public",
    "snmp_version": "2c"
  }'
```

## Production Deployment

### 1. Security Hardening

#### Update Default Credentials
```bash
# Generate strong secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
SECRET_KEY=<generated-key>
POSTGRES_PASSWORD=<strong-password>
GF_SECURITY_ADMIN_PASSWORD=<strong-password>
```

#### Configure Firewall
```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp  # API
sudo ufw allow 3000/tcp  # Grafana
sudo ufw deny 5432/tcp   # PostgreSQL (internal only)
sudo ufw deny 6379/tcp   # Redis (internal only)
```

### 2. SSL/TLS Configuration

#### Using Nginx Reverse Proxy
```bash
# Install Nginx
sudo apt-get install nginx certbot python3-certbot-nginx

# Configure SSL
sudo certbot --nginx -d scnms.yourdomain.com
```

#### Nginx Configuration Example
```nginx
server {
    listen 443 ssl http2;
    server_name scnms.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/scnms.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scnms.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /grafana/ {
        proxy_pass http://localhost:3000/;
    }
}
```

### 3. Database Backup

#### Automated PostgreSQL Backup
```bash
# Create backup script
cat > /usr/local/bin/backup-scnms.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/scnms"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec scnms-postgres pg_dump -U scnms scnms | \
  gzip > $BACKUP_DIR/scnms_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-scnms.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-scnms.sh" | crontab -
```

### 4. Monitoring & Alerting

#### Configure Alertmanager (Optional)
```yaml
# config/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'team-email'
  group_by: ['alertname', 'cluster', 'service']

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'ops-team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'alertmanager'
        auth_password: 'password'
```

### 5. Scaling Considerations

#### Horizontal Scaling
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  poller:
    deploy:
      replicas: 3
      
  data-ingestion:
    deploy:
      replicas: 2
```

#### Database Connection Pooling
Update `shared/database.py` with connection pool settings:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | localhost |
| `POSTGRES_PORT` | PostgreSQL port | 5432 |
| `POSTGRES_DB` | Database name | scnms |
| `REDIS_HOST` | Redis host | localhost |
| `SNMP_COMMUNITY` | Default SNMP community | public |
| `LOG_LEVEL` | Logging level | INFO |

### SNMP Configuration

#### Add SNMP v3 Device
```bash
curl -X POST "http://localhost:8000/api/v1/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Secure-Router",
    "ip_address": "192.168.1.254",
    "snmp_enabled": true,
    "snmp_version": "3",
    "snmp_username": "admin",
    "snmp_auth_protocol": "SHA",
    "snmp_auth_password": "authpass",
    "snmp_priv_protocol": "AES",
    "snmp_priv_password": "privpass"
  }'
```

### Alarm Rules

Create custom alarm rules via API:
```bash
curl -X POST "http://localhost:8000/api/v1/alarm-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU Alert",
    "metric_name": "cpu_utilization",
    "threshold_value": 85.0,
    "comparison_operator": ">",
    "duration_seconds": 300,
    "severity": "major",
    "enabled": true
  }'
```

## Monitoring

### Service Health Checks

```bash
# Check all services
curl http://localhost:8000/api/v1/health/services

# Individual service health
curl http://localhost:8001/health  # Device Discovery
curl http://localhost:8002/health  # Poller
curl http://localhost:8003/health  # Data Ingestion
curl http://localhost:8004/health  # Alarm Manager
```

### Logs

```bash
# View all logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f api
docker-compose logs -f poller
docker-compose logs -f alarm-manager

# Export logs
docker-compose logs > scnms_logs.txt
```

### Metrics

Access Prometheus metrics:
- Device Discovery: http://localhost:8001/metrics
- Poller: http://localhost:8002/metrics
- Data Ingestion: http://localhost:8003/metrics
- Alarm Manager: http://localhost:8004/metrics

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it scnms-postgres psql -U scnms -d scnms

# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait for init, then start other services
```

#### 3. Device Discovery Fails

```bash
# Test SNMP connectivity
snmpwalk -v2c -c public 192.168.1.1 system

# Check firewall rules
sudo ufw status

# Verify network connectivity
ping 192.168.1.1
```

#### 4. High Memory Usage

```bash
# Check resource usage
docker stats

# Limit container resources (docker-compose.yml)
services:
  poller:
    mem_limit: 2g
    cpus: 1.0
```

#### 5. Grafana Dashboards Not Loading

```bash
# Check Grafana logs
docker-compose logs grafana

# Verify Prometheus datasource
curl http://localhost:3000/api/datasources

# Restart Grafana
docker-compose restart grafana
```

### Debug Mode

Enable debug logging:
```bash
# Update .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

### Performance Tuning

#### PostgreSQL
```bash
# Increase shared buffers (postgres container)
docker exec -it scnms-postgres bash
echo "shared_buffers = 256MB" >> /var/lib/postgresql/data/postgresql.conf
```

#### Redis
```bash
# Enable persistence
docker exec -it scnms-redis redis-cli CONFIG SET save "900 1 300 10"
```

## Maintenance

### Regular Tasks

1. **Daily**: Check service health and logs
2. **Weekly**: Review alarm statistics and trends
3. **Monthly**: Update dependencies and security patches
4. **Quarterly**: Review and optimize database performance

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild services
docker-compose build

# Restart with new images
docker-compose up -d
```

### Cleanup

```bash
# Remove old logs
docker-compose logs --tail=0 -f > /dev/null

# Clean Docker system
docker system prune -a --volumes

# Archive old metrics (PostgreSQL)
docker exec -it scnms-postgres psql -U scnms -d scnms \
  -c "DELETE FROM metrics WHERE timestamp < NOW() - INTERVAL '90 days';"
```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review documentation: `README.md`
- Create GitHub issue with logs and configuration details
