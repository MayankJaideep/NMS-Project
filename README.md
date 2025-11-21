# Smart Campus Network Monitoring System (SCNMS)

## Overview

SCNMS is a production-ready, microservices-based Network Monitoring System designed for university campus environments. It provides unified monitoring, alarm lifecycle management, and rich observability dashboards for multi-vendor network infrastructure.

## Architecture

### Microservices Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Device        │    │   Multi-        │    │   Data          │
│   Discovery     │    │   Protocol      │    │   Ingestion     │
│   Service       │    │   Poller        │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Alarm         │    │   Redis         │    │   API           │
│   Manager       │    │   Message       │    │   Service       │
│   Service       │    │   Queue         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   PostgreSQL    │    │   Grafana       │
│   TSDB          │    │   Database      │    │   Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Message Queue**: Redis 7.x
- **Databases**: PostgreSQL 15+ (metadata), Prometheus (time-series)
- **Monitoring**: Grafana 10.x
- **Containerization**: Docker & Docker Compose
- **Protocols**: SNMP v2c/v3, NETCONF, RESTCONF

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd scnms
```

2. **Start all services:**
```bash
docker-compose up -d
```

3. **Access the services:**
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Development Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start individual services:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=scnms postgres:15

# Start services
python -m services.device_discovery
python -m services.poller
python -m services.data_ingestion
python -m services.alarm_manager
python -m services.api
```

## Services Overview

### 1. Device Discovery Service
- **Port**: 8001
- **Function**: Network device discovery and inventory management
- **Endpoints**: `/devices`, `/devices/{id}`, `/discover`

### 2. Multi-Protocol Poller Service
- **Port**: 8002
- **Function**: SNMP, NETCONF, RESTCONF data collection
- **Features**: Graceful failure handling, retry logic, protocol-specific optimizations

### 3. Data Ingestion Service
- **Port**: 8003
- **Function**: Format and push metrics to Prometheus
- **Features**: Batch processing, data validation, metric transformation

### 4. Alarm Manager Service
- **Port**: 8004
- **Function**: Alarm lifecycle management (Raise → Acknowledge → Clear)
- **Features**: SNMP trap processing, rule-based alarm generation

### 5. API Service
- **Port**: 8000
- **Function**: RESTful API for frontend integration
- **Features**: OpenAPI documentation, authentication, rate limiting

## Configuration

### Environment Variables

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=scnms
POSTGRES_USER=scnms
POSTGRES_PASSWORD=scnms

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Prometheus
PROMETHEUS_URL=http://localhost:9090

# Service Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4
```

## Monitoring & Observability

### Key Dashboards

1. **Device Health Dashboard**
   - Device status overview
   - CPU/Memory utilization
   - Interface status
   - Connectivity metrics

2. **Network Utilization Dashboard**
   - Bandwidth utilization
   - Traffic patterns
   - Top talkers
   - Historical trends

3. **Alarm Lifecycle Dashboard**
   - Active alarms
   - Alarm trends
   - Acknowledgment status
   - Resolution times

### Metrics Collected

- **System Metrics**: CPU, Memory, Disk, Temperature
- **Network Metrics**: Interface utilization, packet rates, errors
- **Performance Metrics**: Latency, jitter, packet loss
- **Availability Metrics**: Uptime, downtime, MTTR

## API Documentation

### Core Endpoints

```bash
# Device Management
GET    /api/v1/devices              # List all devices
POST   /api/v1/devices              # Add new device
GET    /api/v1/devices/{id}         # Get device details
PUT    /api/v1/devices/{id}         # Update device
DELETE /api/v1/devices/{id}         # Remove device

# Monitoring
GET    /api/v1/metrics              # Get current metrics
GET    /api/v1/metrics/history      # Get historical data
GET    /api/v1/health               # Service health check

# Alarms
GET    /api/v1/alarms               # List alarms
POST   /api/v1/alarms/{id}/ack      # Acknowledge alarm
POST   /api/v1/alarms/{id}/clear    # Clear alarm
```

## Deployment

### Production Deployment

1. **Configure environment variables**
2. **Set up SSL certificates**
3. **Configure reverse proxy (nginx)**
4. **Set up monitoring and alerting**
5. **Configure backup strategies**

### Scaling

- **Horizontal Scaling**: Add more poller instances
- **Database Scaling**: Read replicas for PostgreSQL
- **Caching**: Redis cluster for high availability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team
