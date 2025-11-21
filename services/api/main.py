"""
API Gateway Service - SCNMS Central API
Aggregates all microservices and provides unified RESTful API
"""
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import redis.asyncio as aioredis
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST

from shared.database import get_db, get_redis
from shared.models import (
    Device, Alarm, Metric, AlarmRule, PollingJob,
    DeviceStatus, AlarmStatus, AlarmSeverity, ProtocolType
)
from shared.schemas import (
    DeviceCreate, DeviceUpdate, Device as DeviceSchema,
    AlarmCreate, AlarmUpdate, Alarm as AlarmSchema,
    AlarmRuleCreate, AlarmRule as AlarmRuleSchema,
    PollingJobCreate, PollingJob as PollingJobSchema,
    MetricsQuery, MetricsResponse, HealthCheck,
    DiscoveryRequest
)
from shared.logger import configure_logging, get_logger
from shared.config import settings

# Configure logging
configure_logging()
logger = get_logger("api_gateway")

app = FastAPI(
    title="SCNMS API Gateway",
    description="Unified API for Smart Campus Network Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active connections')

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Service URLs
SERVICE_URLS = {
    "device_discovery": "http://device-discovery:8001",
    "poller": "http://poller:8002",
    "data_ingestion": "http://data-ingestion:8003",
    "alarm_manager": "http://alarm-manager:8004"
}


class APIGateway:
    """API Gateway service for routing and aggregation"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize service connections"""
        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                decode_responses=True
            )
            self.http_client = httpx.AsyncClient(timeout=30.0)
            logger.info("API Gateway initialized")
        except Exception as e:
            logger.error("Failed to initialize API Gateway", error=str(e))
            raise
    
    async def call_service(self, service: str, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to microservice"""
        try:
            url = f"{SERVICE_URLS.get(service)}{endpoint}"
            response = await self.http_client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "Service call failed",
                service=service,
                endpoint=endpoint,
                status=e.response.status_code
            )
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logger.error("Service call error", service=service, endpoint=endpoint, error=str(e))
            raise HTTPException(status_code=503, detail=f"Service {service} unavailable")


# Initialize gateway
api_gateway = APIGateway()


@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup"""
    await api_gateway.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if api_gateway.redis_client:
        await api_gateway.redis_client.close()
    if api_gateway.http_client:
        await api_gateway.http_client.aclose()


# Health Check Endpoints

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """API Gateway health check"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={}
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/health/services")
async def check_all_services():
    """Check health of all microservices"""
    services_health = {}
    
    for service_name, base_url in SERVICE_URLS.items():
        try:
            response = await api_gateway.http_client.get(f"{base_url}/health", timeout=5.0)
            services_health[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            services_health[service_name] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_health
    }


# Device Management Endpoints

@app.get("/api/v1/devices", response_model=List[DeviceSchema])
async def list_devices(
    status: Optional[DeviceStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all network devices"""
    try:
        query = db.query(Device)
        
        if status:
            query = query.filter(Device.status == status)
        
        devices = query.limit(limit).offset(offset).all()
        return devices
        
    except Exception as e:
        logger.error("Failed to list devices", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")


@app.post("/api/v1/devices", response_model=DeviceSchema, status_code=201)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Add a new device to inventory"""
    try:
        # Check if device with same IP exists
        existing = db.query(Device).filter(Device.ip_address == device.ip_address).first()
        if existing:
            raise HTTPException(status_code=400, detail="Device with this IP already exists")
        
        db_device = Device(**device.dict())
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        logger.info("Device created", device_id=db_device.id, ip=device.ip_address)
        return db_device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create device", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create device")


@app.get("/api/v1/devices/{device_id}", response_model=DeviceSchema)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get device details by ID"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.put("/api/v1/devices/{device_id}", response_model=DeviceSchema)
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """Update device information"""
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        update_data = device_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)
        
        db.commit()
        db.refresh(device)
        
        logger.info("Device updated", device_id=device_id)
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update device", error=str(e), device_id=device_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update device")


@app.delete("/api/v1/devices/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Remove device from inventory"""
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        db.delete(device)
        db.commit()
        
        logger.info("Device deleted", device_id=device_id)
        return {"message": "Device deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete device", error=str(e), device_id=device_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete device")


@app.post("/api/v1/devices/discover")
async def discover_devices(discovery_request: DiscoveryRequest):
    """Trigger device discovery"""
    try:
        result = await api_gateway.call_service(
            "device_discovery",
            "POST",
            "/discover",
            json=discovery_request.dict()
        )
        return result
    except Exception as e:
        logger.error("Device discovery failed", error=str(e))
        raise


# Metrics Endpoints

@app.get("/api/v1/metrics")
async def get_metrics(
    device_ids: Optional[List[int]] = Query(None),
    metric_names: Optional[List[str]] = Query(None),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Query metrics data"""
    try:
        query = db.query(Metric)
        
        if device_ids:
            query = query.filter(Metric.device_id.in_(device_ids))
        if metric_names:
            query = query.filter(Metric.metric_name.in_(metric_names))
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        metrics = query.order_by(desc(Metric.timestamp)).limit(limit).all()
        
        return {
            "metrics": metrics,
            "total_count": len(metrics),
            "query_time": 0.0
        }
        
    except Exception as e:
        logger.error("Failed to query metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@app.get("/api/v1/metrics/latest")
async def get_latest_metrics(
    device_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get latest metrics for devices"""
    try:
        # Get latest metric for each device/metric_name combination
        subquery = db.query(
            Metric.device_id,
            Metric.metric_name,
            func.max(Metric.timestamp).label('max_timestamp')
        )
        
        if device_id:
            subquery = subquery.filter(Metric.device_id == device_id)
        
        subquery = subquery.group_by(Metric.device_id, Metric.metric_name).subquery()
        
        metrics = db.query(Metric).join(
            subquery,
            and_(
                Metric.device_id == subquery.c.device_id,
                Metric.metric_name == subquery.c.metric_name,
                Metric.timestamp == subquery.c.max_timestamp
            )
        ).all()
        
        return {"metrics": metrics, "count": len(metrics)}
        
    except Exception as e:
        logger.error("Failed to get latest metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve latest metrics")


@app.get("/api/v1/devices/{device_id}/metrics")
async def get_device_metrics(
    device_id: int,
    metric_name: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get metrics for a specific device"""
    try:
        # Check device exists
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Query metrics
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(Metric).filter(
            and_(
                Metric.device_id == device_id,
                Metric.timestamp >= start_time
            )
        )
        
        if metric_name:
            query = query.filter(Metric.metric_name == metric_name)
        
        metrics = query.order_by(Metric.timestamp).all()
        
        return {
            "device_id": device_id,
            "device_name": device.name,
            "metrics": metrics,
            "count": len(metrics),
            "time_range": f"Last {hours} hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get device metrics", error=str(e), device_id=device_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve device metrics")


# Alarm Endpoints

@app.get("/api/v1/alarms", response_model=List[AlarmSchema])
async def list_alarms(
    status: Optional[AlarmStatus] = None,
    severity: Optional[AlarmSeverity] = None,
    device_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List alarms with filters"""
    try:
        query = db.query(Alarm)
        
        if status:
            query = query.filter(Alarm.status == status)
        if severity:
            query = query.filter(Alarm.severity == severity)
        if device_id:
            query = query.filter(Alarm.device_id == device_id)
        
        alarms = query.order_by(desc(Alarm.raised_at)).limit(limit).offset(offset).all()
        return alarms
        
    except Exception as e:
        logger.error("Failed to list alarms", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alarms")


@app.get("/api/v1/alarms/{alarm_id}", response_model=AlarmSchema)
async def get_alarm(alarm_id: str, db: Session = Depends(get_db)):
    """Get alarm details"""
    alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return alarm


@app.post("/api/v1/alarms/{alarm_id}/acknowledge")
async def acknowledge_alarm(alarm_id: str, acknowledged_by: str = "api_user"):
    """Acknowledge an alarm"""
    try:
        result = await api_gateway.call_service(
            "alarm_manager",
            "POST",
            f"/alarms/{alarm_id}/acknowledge",
            params={"acknowledged_by": acknowledged_by}
        )
        return result
    except Exception as e:
        logger.error("Failed to acknowledge alarm", error=str(e), alarm_id=alarm_id)
        raise


@app.post("/api/v1/alarms/{alarm_id}/clear")
async def clear_alarm(alarm_id: str):
    """Clear an alarm"""
    try:
        result = await api_gateway.call_service(
            "alarm_manager",
            "POST",
            f"/alarms/{alarm_id}/clear"
        )
        return result
    except Exception as e:
        logger.error("Failed to clear alarm", error=str(e), alarm_id=alarm_id)
        raise


@app.get("/api/v1/alarms/stats/summary")
async def get_alarm_statistics():
    """Get alarm statistics"""
    try:
        result = await api_gateway.call_service(
            "alarm_manager",
            "GET",
            "/alarms/stats/summary"
        )
        return result
    except Exception as e:
        logger.error("Failed to get alarm statistics", error=str(e))
        raise


# Alarm Rules Management

@app.get("/api/v1/alarm-rules", response_model=List[AlarmRuleSchema])
async def list_alarm_rules(db: Session = Depends(get_db)):
    """List all alarm rules"""
    rules = db.query(AlarmRule).all()
    return rules


@app.post("/api/v1/alarm-rules", response_model=AlarmRuleSchema, status_code=201)
async def create_alarm_rule(rule: AlarmRuleCreate, db: Session = Depends(get_db)):
    """Create new alarm rule"""
    try:
        db_rule = AlarmRule(**rule.dict())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        logger.info("Alarm rule created", rule_id=db_rule.id, name=rule.name)
        return db_rule
        
    except Exception as e:
        logger.error("Failed to create alarm rule", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create alarm rule")


@app.delete("/api/v1/alarm-rules/{rule_id}")
async def delete_alarm_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete alarm rule"""
    rule = db.query(AlarmRule).filter(AlarmRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alarm rule not found")
    
    db.delete(rule)
    db.commit()
    
    logger.info("Alarm rule deleted", rule_id=rule_id)
    return {"message": "Alarm rule deleted successfully"}


# Polling Jobs Management

@app.get("/api/v1/polling-jobs", response_model=List[PollingJobSchema])
async def list_polling_jobs(
    device_id: Optional[int] = None,
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List polling jobs"""
    try:
        query = db.query(PollingJob)
        
        if device_id:
            query = query.filter(PollingJob.device_id == device_id)
        if enabled is not None:
            query = query.filter(PollingJob.enabled == enabled)
        
        jobs = query.all()
        return jobs
        
    except Exception as e:
        logger.error("Failed to list polling jobs", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve polling jobs")


@app.post("/api/v1/polling-jobs", response_model=PollingJobSchema, status_code=201)
async def create_polling_job(job: PollingJobCreate, db: Session = Depends(get_db)):
    """Create new polling job"""
    try:
        db_job = PollingJob(**job.dict())
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        logger.info("Polling job created", job_id=db_job.id, device_id=job.device_id)
        return db_job
        
    except Exception as e:
        logger.error("Failed to create polling job", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create polling job")


@app.delete("/api/v1/polling-jobs/{job_id}")
async def delete_polling_job(job_id: int, db: Session = Depends(get_db)):
    """Delete polling job"""
    job = db.query(PollingJob).filter(PollingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Polling job not found")
    
    db.delete(job)
    db.commit()
    
    logger.info("Polling job deleted", job_id=job_id)
    return {"message": "Polling job deleted successfully"}


# Dashboard Summary Endpoints

@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get overall dashboard summary"""
    try:
        # Device statistics
        total_devices = db.query(Device).count()
        devices_up = db.query(Device).filter(Device.status == DeviceStatus.UP).count()
        devices_down = db.query(Device).filter(Device.status == DeviceStatus.DOWN).count()
        
        # Alarm statistics
        active_alarms = db.query(Alarm).filter(
            Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
        ).count()
        
        critical_alarms = db.query(Alarm).filter(
            and_(
                Alarm.severity == AlarmSeverity.CRITICAL,
                Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
            )
        ).count()
        
        # Recent metrics count
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_metrics = db.query(Metric).filter(Metric.timestamp >= one_hour_ago).count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "devices": {
                "total": total_devices,
                "up": devices_up,
                "down": devices_down,
                "availability": (devices_up / total_devices * 100) if total_devices > 0 else 0
            },
            "alarms": {
                "active": active_alarms,
                "critical": critical_alarms
            },
            "monitoring": {
                "metrics_last_hour": recent_metrics,
                "collection_rate": recent_metrics / 60 if recent_metrics > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard summary")


@app.get("/api/v1/dashboard/device-health")
async def get_device_health_summary(db: Session = Depends(get_db)):
    """Get device health summary with latest metrics"""
    try:
        devices = db.query(Device).filter(Device.status == DeviceStatus.UP).all()
        
        device_health = []
        for device in devices:
            # Get latest CPU and memory metrics
            cpu_metric = db.query(Metric).filter(
                and_(
                    Metric.device_id == device.id,
                    Metric.metric_name == 'cpu_utilization'
                )
            ).order_by(desc(Metric.timestamp)).first()
            
            memory_metric = db.query(Metric).filter(
                and_(
                    Metric.device_id == device.id,
                    Metric.metric_name == 'memory_utilization'
                )
            ).order_by(desc(Metric.timestamp)).first()
            
            device_health.append({
                "device_id": device.id,
                "name": device.name,
                "ip_address": device.ip_address,
                "status": device.status.value,
                "cpu_utilization": cpu_metric.metric_value if cpu_metric else None,
                "memory_utilization": memory_metric.metric_value if memory_metric else None,
                "last_polled": device.last_polled.isoformat() if device.last_polled else None
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "devices": device_health
        }
        
    except Exception as e:
        logger.error("Failed to get device health summary", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve device health")
