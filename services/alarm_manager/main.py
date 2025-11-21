"""
Alarm Manager Service - SCNMS Microservice
Handles alarm lifecycle management: Raise -> Acknowledge -> Clear -> Close
Processes SNMP traps and metric-based alarms
"""
import asyncio
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import redis.asyncio as aioredis
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST

from shared.database import get_db, get_redis
from shared.models import Alarm, AlarmRule, Device, Metric, AlarmStatus, AlarmSeverity
from shared.schemas import (
    AlarmCreate, AlarmUpdate, Alarm as AlarmSchema,
    AlarmRuleCreate, AlarmRule as AlarmRuleSchema,
    HealthCheck
)
from shared.logger import configure_logging, get_logger
from shared.config import settings

# Configure logging
configure_logging()
logger = get_logger("alarm_manager")

app = FastAPI(
    title="SCNMS Alarm Manager Service",
    description="Alarm lifecycle management and event processing",
    version="1.0.0"
)

# Prometheus metrics
ALARM_COUNT = Counter('alarms_total', 'Total alarms', 'severity', 'status')
ALARM_DURATION = Histogram('alarm_processing_duration_seconds', 'Alarm processing duration')
ACTIVE_ALARMS = Gauge('alarm_active', 'Active alarms')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# WebSocket connections for real-time alarm updates
active_connections: List[WebSocket] = []


class AlarmManagerService:
    """Alarm management and lifecycle orchestration"""
    
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.alarm_rules_cache: Dict[int, AlarmRule] = {}
        
    async def initialize(self):
        """Initialize service connections"""
        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                decode_responses=True
            )
            logger.info("Alarm Manager Service initialized")
        except Exception as e:
            logger.error("Failed to initialize Alarm Manager Service", error=str(e))
            raise
    
    async def process_metric_alarm(self, metric: Dict[str, Any], db: Session) -> Optional[Alarm]:
        """Process metric and check against alarm rules"""
        try:
            # Get all enabled alarm rules for this metric
            rules = db.query(AlarmRule).filter(
                and_(
                    AlarmRule.metric_name == metric['metric_name'],
                    AlarmRule.enabled == True
                )
            ).all()
            
            for rule in rules:
                # Evaluate alarm condition
                if self._evaluate_condition(
                    metric['metric_value'],
                    rule.threshold_value,
                    rule.comparison_operator
                ):
                    # Check if alarm already exists
                    alarm_id = self._generate_alarm_id(metric['device_id'], rule.id)
                    existing_alarm = db.query(Alarm).filter(
                        and_(
                            Alarm.alarm_id == alarm_id,
                            Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
                        )
                    ).first()
                    
                    if not existing_alarm:
                        # Create new alarm
                        alarm = await self._create_alarm(
                            device_id=metric['device_id'],
                            alarm_id=alarm_id,
                            title=f"{rule.name} - {metric.get('metric_name', 'Unknown')}",
                            description=f"{rule.description or ''} Current value: {metric['metric_value']}",
                            severity=rule.severity,
                            source="polling",
                            db=db
                        )
                        logger.info(
                            "Alarm raised",
                            alarm_id=alarm_id,
                            device_id=metric['device_id'],
                            rule=rule.name
                        )
                        return alarm
                else:
                    # Check if alarm should be auto-cleared
                    alarm_id = self._generate_alarm_id(metric['device_id'], rule.id)
                    await self._auto_clear_alarm(alarm_id, db)
            
            return None
            
        except Exception as e:
            logger.error("Failed to process metric alarm", error=str(e), metric=metric)
            return None
    
    async def process_snmp_trap(self, trap_data: Dict[str, Any], db: Session) -> Optional[Alarm]:
        """Process SNMP trap and create alarm if needed"""
        try:
            device_ip = trap_data.get('source_ip')
            
            # Find device by IP
            device = db.query(Device).filter(Device.ip_address == device_ip).first()
            if not device:
                logger.warning("Trap received from unknown device", ip=device_ip)
                return None
            
            # Generate alarm from trap
            alarm_id = self._generate_trap_alarm_id(device.id, trap_data)
            
            # Check if alarm already exists
            existing_alarm = db.query(Alarm).filter(
                and_(
                    Alarm.alarm_id == alarm_id,
                    Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
                )
            ).first()
            
            if not existing_alarm:
                severity = self._determine_trap_severity(trap_data)
                alarm = await self._create_alarm(
                    device_id=device.id,
                    alarm_id=alarm_id,
                    title=f"SNMP Trap: {trap_data.get('trap_type', 'Unknown')}",
                    description=trap_data.get('message', 'SNMP trap received'),
                    severity=severity,
                    source="snmp_trap",
                    db=db
                )
                logger.info("Alarm created from SNMP trap", alarm_id=alarm_id, device_id=device.id)
                return alarm
            
            return None
            
        except Exception as e:
            logger.error("Failed to process SNMP trap", error=str(e), trap=trap_data)
            return None
    
    async def acknowledge_alarm(self, alarm_id: str, acknowledged_by: str, db: Session) -> Optional[Alarm]:
        """Acknowledge an alarm"""
        try:
            alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
            if not alarm:
                raise HTTPException(status_code=404, detail="Alarm not found")
            
            if alarm.status != AlarmStatus.RAISED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Alarm cannot be acknowledged. Current status: {alarm.status}"
                )
            
            alarm.status = AlarmStatus.ACKNOWLEDGED
            alarm.acknowledged_at = datetime.utcnow()
            alarm.acknowledged_by = acknowledged_by
            
            db.commit()
            db.refresh(alarm)
            
            # Publish event to Redis
            await self._publish_alarm_event("acknowledged", alarm)
            
            logger.info(
                "Alarm acknowledged",
                alarm_id=alarm_id,
                acknowledged_by=acknowledged_by
            )
            
            return alarm
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to acknowledge alarm", error=str(e), alarm_id=alarm_id)
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to acknowledge alarm")
    
    async def clear_alarm(self, alarm_id: str, db: Session) -> Optional[Alarm]:
        """Clear an alarm"""
        try:
            alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
            if not alarm:
                raise HTTPException(status_code=404, detail="Alarm not found")
            
            if alarm.status in [AlarmStatus.CLEARED, AlarmStatus.CLOSED]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Alarm already cleared/closed. Current status: {alarm.status}"
                )
            
            alarm.status = AlarmStatus.CLEARED
            alarm.cleared_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alarm)
            
            # Publish event to Redis
            await self._publish_alarm_event("cleared", alarm)
            
            logger.info("Alarm cleared", alarm_id=alarm_id)
            
            return alarm
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to clear alarm", error=str(e), alarm_id=alarm_id)
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to clear alarm")
    
    async def close_alarm(self, alarm_id: str, db: Session) -> Optional[Alarm]:
        """Close an alarm"""
        try:
            alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
            if not alarm:
                raise HTTPException(status_code=404, detail="Alarm not found")
            
            if alarm.status != AlarmStatus.CLEARED:
                raise HTTPException(
                    status_code=400,
                    detail="Only cleared alarms can be closed"
                )
            
            alarm.status = AlarmStatus.CLOSED
            alarm.closed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(alarm)
            
            # Publish event to Redis
            await self._publish_alarm_event("closed", alarm)
            
            logger.info("Alarm closed", alarm_id=alarm_id)
            
            return alarm
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to close alarm", error=str(e), alarm_id=alarm_id)
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to close alarm")
    
    async def _create_alarm(
        self,
        device_id: int,
        alarm_id: str,
        title: str,
        description: str,
        severity: AlarmSeverity,
        source: str,
        db: Session
    ) -> Alarm:
        """Create a new alarm"""
        alarm = Alarm(
            device_id=device_id,
            alarm_id=alarm_id,
            title=title,
            description=description,
            severity=severity,
            status=AlarmStatus.RAISED,
            source=source,
            raised_at=datetime.utcnow()
        )
        
        db.add(alarm)
        db.commit()
        db.refresh(alarm)
        
        # Publish event to Redis
        await self._publish_alarm_event("raised", alarm)
        
        # Send to WebSocket clients
        await self._broadcast_alarm(alarm)
        
        return alarm
    
    async def _auto_clear_alarm(self, alarm_id: str, db: Session):
        """Automatically clear an alarm if condition is no longer met"""
        try:
            alarm = db.query(Alarm).filter(
                and_(
                    Alarm.alarm_id == alarm_id,
                    Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
                )
            ).first()
            
            if alarm:
                alarm.status = AlarmStatus.CLEARED
                alarm.cleared_at = datetime.utcnow()
                db.commit()
                
                await self._publish_alarm_event("auto_cleared", alarm)
                logger.info("Alarm auto-cleared", alarm_id=alarm_id)
                
        except Exception as e:
            logger.error("Failed to auto-clear alarm", error=str(e), alarm_id=alarm_id)
    
    def _evaluate_condition(self, value: float, threshold: float, operator: str) -> bool:
        """Evaluate alarm condition"""
        operators = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y
        }
        
        op_func = operators.get(operator)
        if op_func:
            return op_func(value, threshold)
        return False
    
    def _generate_alarm_id(self, device_id: int, rule_id: int) -> str:
        """Generate unique alarm ID"""
        data = f"device_{device_id}_rule_{rule_id}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_trap_alarm_id(self, device_id: int, trap_data: Dict[str, Any]) -> str:
        """Generate unique alarm ID for SNMP trap"""
        trap_type = trap_data.get('trap_type', 'unknown')
        data = f"device_{device_id}_trap_{trap_type}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _determine_trap_severity(self, trap_data: Dict[str, Any]) -> AlarmSeverity:
        """Determine severity from SNMP trap data"""
        # Simple heuristic based on trap type
        trap_type = trap_data.get('trap_type', '').lower()
        
        if 'critical' in trap_type or 'down' in trap_type:
            return AlarmSeverity.CRITICAL
        elif 'major' in trap_type or 'error' in trap_type:
            return AlarmSeverity.MAJOR
        elif 'minor' in trap_type or 'warning' in trap_type:
            return AlarmSeverity.WARNING
        else:
            return AlarmSeverity.INFO
    
    async def _publish_alarm_event(self, event_type: str, alarm: Alarm):
        """Publish alarm event to Redis"""
        try:
            if self.redis_client:
                event = {
                    'event_type': event_type,
                    'alarm_id': alarm.alarm_id,
                    'device_id': alarm.device_id,
                    'severity': alarm.severity.value,
                    'status': alarm.status.value,
                    'timestamp': datetime.utcnow().isoformat()
                }
                await self.redis_client.publish('alarms', json.dumps(event))
        except Exception as e:
            logger.error("Failed to publish alarm event", error=str(e))
    
    async def _broadcast_alarm(self, alarm: Alarm):
        """Broadcast alarm to WebSocket clients"""
        if active_connections:
            alarm_data = {
                'id': alarm.id,
                'alarm_id': alarm.alarm_id,
                'device_id': alarm.device_id,
                'title': alarm.title,
                'severity': alarm.severity.value,
                'status': alarm.status.value,
                'raised_at': alarm.raised_at.isoformat()
            }
            
            disconnected = []
            for connection in active_connections:
                try:
                    await connection.send_json(alarm_data)
                except Exception:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                active_connections.remove(conn)


# Initialize service
alarm_service = AlarmManagerService()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    await alarm_service.initialize()
    # Start background tasks
    asyncio.create_task(alarm_cleanup_task())
    asyncio.create_task(metric_processor_task())
    asyncio.create_task(trap_processor_task())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if alarm_service.redis_client:
        await alarm_service.redis_client.close()


# API Endpoints

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Service health check"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="alarm_manager",
        version="1.0.0"
    )


@app.get("/alarms", response_model=List[AlarmSchema])
async def list_alarms(
    status: Optional[AlarmStatus] = None,
    severity: Optional[AlarmSeverity] = None,
    device_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List alarms with optional filters"""
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


@app.get("/alarms/{alarm_id}", response_model=AlarmSchema)
async def get_alarm(alarm_id: str, db: Session = Depends(get_db)):
    """Get alarm by ID"""
    alarm = db.query(Alarm).filter(Alarm.alarm_id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return alarm


@app.post("/alarms/{alarm_id}/acknowledge", response_model=AlarmSchema)
async def acknowledge_alarm_endpoint(
    alarm_id: str,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an alarm"""
    return await alarm_service.acknowledge_alarm(alarm_id, acknowledged_by, db)


@app.post("/alarms/{alarm_id}/clear", response_model=AlarmSchema)
async def clear_alarm_endpoint(alarm_id: str, db: Session = Depends(get_db)):
    """Clear an alarm"""
    return await alarm_service.clear_alarm(alarm_id, db)


@app.post("/alarms/{alarm_id}/close", response_model=AlarmSchema)
async def close_alarm_endpoint(alarm_id: str, db: Session = Depends(get_db)):
    """Close an alarm"""
    return await alarm_service.close_alarm(alarm_id, db)


@app.get("/alarms/stats/summary")
async def get_alarm_stats(db: Session = Depends(get_db)):
    """Get alarm statistics"""
    try:
        total_alarms = db.query(Alarm).count()
        
        stats_by_status = {}
        for status in AlarmStatus:
            count = db.query(Alarm).filter(Alarm.status == status).count()
            stats_by_status[status.value] = count
        
        stats_by_severity = {}
        for severity in AlarmSeverity:
            count = db.query(Alarm).filter(
                and_(
                    Alarm.severity == severity,
                    Alarm.status.in_([AlarmStatus.RAISED, AlarmStatus.ACKNOWLEDGED])
                )
            ).count()
            stats_by_severity[severity.value] = count
        
        return {
            'total_alarms': total_alarms,
            'by_status': stats_by_status,
            'active_by_severity': stats_by_severity,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get alarm stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve alarm statistics")


@app.websocket("/ws/alarms")
async def websocket_alarms(websocket: WebSocket):
    """WebSocket endpoint for real-time alarm updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


# Alarm Rules Management

@app.get("/alarm-rules", response_model=List[AlarmRuleSchema])
async def list_alarm_rules(db: Session = Depends(get_db)):
    """List all alarm rules"""
    rules = db.query(AlarmRule).all()
    return rules


@app.post("/alarm-rules", response_model=AlarmRuleSchema)
async def create_alarm_rule(rule: AlarmRuleCreate, db: Session = Depends(get_db)):
    """Create new alarm rule"""
    try:
        db_rule = AlarmRule(**rule.dict())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        
        logger.info("Alarm rule created", rule_name=rule.name)
        return db_rule
        
    except Exception as e:
        logger.error("Failed to create alarm rule", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create alarm rule")


@app.delete("/alarm-rules/{rule_id}")
async def delete_alarm_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete alarm rule"""
    rule = db.query(AlarmRule).filter(AlarmRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alarm rule not found")
    
    db.delete(rule)
    db.commit()
    
    logger.info("Alarm rule deleted", rule_id=rule_id)
    return {"message": "Alarm rule deleted successfully"}


# Background Tasks

async def alarm_cleanup_task():
    """Background task to cleanup old closed alarms"""
    while True:
        try:
            await asyncio.sleep(settings.alarm_cleanup_interval)
            
            db = next(get_db())
            cutoff_date = datetime.utcnow() - timedelta(days=settings.alarm_retention_days)
            
            deleted = db.query(Alarm).filter(
                and_(
                    Alarm.status == AlarmStatus.CLOSED,
                    Alarm.closed_at < cutoff_date
                )
            ).delete()
            
            db.commit()
            
            if deleted > 0:
                logger.info("Cleaned up old alarms", count=deleted)
                
        except Exception as e:
            logger.error("Alarm cleanup task failed", error=str(e))


async def metric_processor_task():
    """Background task to process metrics from Redis queue"""
    while True:
        try:
            if not alarm_service.redis_client:
                await asyncio.sleep(5)
                continue
            
            # Subscribe to metrics channel
            pubsub = alarm_service.redis_client.pubsub()
            await pubsub.subscribe('metrics')
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        metric_data = json.loads(message['data'])
                        db = next(get_db())
                        await alarm_service.process_metric_alarm(metric_data, db)
                    except Exception as e:
                        logger.error("Failed to process metric", error=str(e))
                        
        except Exception as e:
            logger.error("Metric processor task failed", error=str(e))
            await asyncio.sleep(5)


async def trap_processor_task():
    """Background task to process SNMP traps from Redis 'traps' channel"""
    while True:
        try:
            if not alarm_service.redis_client:
                await asyncio.sleep(5)
                continue

            pubsub = alarm_service.redis_client.pubsub()
            await pubsub.subscribe('traps')

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        trap_data = json.loads(message['data'])
                        db = next(get_db())
                        await alarm_service.process_snmp_trap(trap_data, db)
                    except Exception as e:
                        logger.error("Failed to process trap", error=str(e))
                        continue

        except Exception as e:
            logger.error("Trap processor task failed", error=str(e))
            await asyncio.sleep(5)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
