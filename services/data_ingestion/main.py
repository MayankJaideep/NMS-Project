"""
Data Ingestion Service - SCNMS Microservice
Handles data formatting and pushing to Prometheus
"""
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import httpx
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, push_to_gateway

from shared.database import get_db, get_redis
from shared.models import Device, Metric, DeviceStatus
from shared.schemas import Metric as MetricSchema, HealthCheck
from shared.logger import configure_logging, get_logger
from shared.config import settings

# Configure logging
configure_logging()
logger = get_logger("data_ingestion")

app = FastAPI(
    title="SCNMS Data Ingestion Service",
    description="Data formatting and Prometheus integration",
    version="1.0.0"
)


class PrometheusMetrics:
    """Prometheus metrics collector and pusher"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics = {}
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        # Device metrics
        self.metrics['device_status'] = Gauge(
            'scnms_device_status',
            'Device status (1=up, 0=down)',
            ['device_id', 'device_name', 'ip_address', 'vendor', 'model'],
            registry=self.registry
        )
        
        self.metrics['device_uptime'] = Gauge(
            'scnms_device_uptime_seconds',
            'Device uptime in seconds',
            ['device_id', 'device_name', 'ip_address'],
            registry=self.registry
        )
        
        # Interface metrics
        self.metrics['interface_status'] = Gauge(
            'scnms_interface_status',
            'Interface status (1=up, 0=down)',
            ['device_id', 'device_name', 'interface_name', 'interface_index'],
            registry=self.registry
        )
        
        self.metrics['interface_speed'] = Gauge(
            'scnms_interface_speed_bps',
            'Interface speed in bits per second',
            ['device_id', 'device_name', 'interface_name', 'interface_index'],
            registry=self.registry
        )
        
        self.metrics['interface_utilization'] = Gauge(
            'scnms_interface_utilization_percent',
            'Interface utilization percentage',
            ['device_id', 'device_name', 'interface_name', 'interface_index', 'direction'],
            registry=self.registry
        )
        
        self.metrics['interface_bytes'] = Counter(
            'scnms_interface_bytes_total',
            'Total bytes transmitted/received',
            ['device_id', 'device_name', 'interface_name', 'interface_index', 'direction'],
            registry=self.registry
        )
        
        self.metrics['interface_packets'] = Counter(
            'scnms_interface_packets_total',
            'Total packets transmitted/received',
            ['device_id', 'device_name', 'interface_name', 'interface_index', 'direction'],
            registry=self.registry
        )
        
        self.metrics['interface_errors'] = Counter(
            'scnms_interface_errors_total',
            'Total interface errors',
            ['device_id', 'device_name', 'interface_name', 'interface_index', 'error_type'],
            registry=self.registry
        )
        
        # System metrics
        self.metrics['cpu_utilization'] = Gauge(
            'scnms_cpu_utilization_percent',
            'CPU utilization percentage',
            ['device_id', 'device_name', 'cpu_index'],
            registry=self.registry
        )
        
        self.metrics['memory_utilization'] = Gauge(
            'scnms_memory_utilization_percent',
            'Memory utilization percentage',
            ['device_id', 'device_name'],
            registry=self.registry
        )
        
        self.metrics['temperature'] = Gauge(
            'scnms_temperature_celsius',
            'Device temperature in Celsius',
            ['device_id', 'device_name', 'sensor_name'],
            registry=self.registry
        )
        
        # Network metrics
        self.metrics['latency'] = Histogram(
            'scnms_latency_seconds',
            'Network latency in seconds',
            ['device_id', 'device_name', 'target'],
            registry=self.registry
        )
        
        self.metrics['packet_loss'] = Gauge(
            'scnms_packet_loss_percent',
            'Packet loss percentage',
            ['device_id', 'device_name', 'target'],
            registry=self.registry
        )
        
        # Service metrics
        self.metrics['polling_duration'] = Histogram(
            'scnms_polling_duration_seconds',
            'Polling duration in seconds',
            ['device_id', 'device_name', 'protocol'],
            registry=self.registry
        )
        
        self.metrics['polling_errors'] = Counter(
            'scnms_polling_errors_total',
            'Total polling errors',
            ['device_id', 'device_name', 'protocol', 'error_type'],
            registry=self.registry
        )
    
    def update_device_metrics(self, device: Device, metrics_data: Dict[str, Any]):
        """Update device-level metrics"""
        try:
            # Device status
            status_value = 1 if device.status == DeviceStatus.UP else 0
            self.metrics['device_status'].labels(
                device_id=device.id,
                device_name=device.name,
                ip_address=device.ip_address,
                vendor=device.vendor or 'unknown',
                model=device.model or 'unknown'
            ).set(status_value)
            
            # Device uptime
            if 'sysUpTime' in metrics_data:
                uptime = self._parse_uptime(metrics_data['sysUpTime'])
                self.metrics['device_uptime'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    ip_address=device.ip_address
                ).set(uptime)
            
            # System metrics
            if 'cpu_utilization' in metrics_data:
                cpu_value = float(metrics_data['cpu_utilization'])
                self.metrics['cpu_utilization'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    cpu_index='0'
                ).set(cpu_value)
            
            if 'memory_utilization' in metrics_data:
                memory_value = float(metrics_data['memory_utilization'])
                self.metrics['memory_utilization'].labels(
                    device_id=device.id,
                    device_name=device.name
                ).set(memory_value)
            
        except Exception as e:
            logger.error("Failed to update device metrics", device_id=device.id, error=str(e))
    
    def update_interface_metrics(self, device: Device, interface_data: Dict[str, Any]):
        """Update interface-level metrics"""
        try:
            interface_name = interface_data.get('interface_name', 'unknown')
            interface_index = interface_data.get('interface_index', '0')
            
            # Interface status
            if 'ifOperStatus' in interface_data:
                status_value = 1 if interface_data['ifOperStatus'] == '1' else 0
                self.metrics['interface_status'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index
                ).set(status_value)
            
            # Interface speed
            if 'ifSpeed' in interface_data:
                speed = float(interface_data['ifSpeed'])
                self.metrics['interface_speed'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index
                ).set(speed)
            
            # Interface utilization (calculated from octets and speed)
            if 'ifInOctets' in interface_data and 'ifSpeed' in interface_data:
                in_octets = float(interface_data['ifInOctets'])
                speed = float(interface_data['ifSpeed'])
                if speed > 0:
                    utilization = (in_octets * 8) / speed * 100
                    self.metrics['interface_utilization'].labels(
                        device_id=device.id,
                        device_name=device.name,
                        interface_name=interface_name,
                        interface_index=interface_index,
                        direction='in'
                    ).set(utilization)
            
            if 'ifOutOctets' in interface_data and 'ifSpeed' in interface_data:
                out_octets = float(interface_data['ifOutOctets'])
                speed = float(interface_data['ifSpeed'])
                if speed > 0:
                    utilization = (out_octets * 8) / speed * 100
                    self.metrics['interface_utilization'].labels(
                        device_id=device.id,
                        device_name=device.name,
                        interface_name=interface_name,
                        interface_index=interface_index,
                        direction='out'
                    ).set(utilization)
            
            # Interface counters
            if 'ifInOctets' in interface_data:
                in_octets = float(interface_data['ifInOctets'])
                self.metrics['interface_bytes'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index,
                    direction='in'
                ).inc(in_octets)
            
            if 'ifOutOctets' in interface_data:
                out_octets = float(interface_data['ifOutOctets'])
                self.metrics['interface_bytes'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index,
                    direction='out'
                ).inc(out_octets)
            
            # Interface errors
            if 'ifInErrors' in interface_data:
                in_errors = float(interface_data['ifInErrors'])
                self.metrics['interface_errors'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index,
                    error_type='in'
                ).inc(in_errors)
            
            if 'ifOutErrors' in interface_data:
                out_errors = float(interface_data['ifOutErrors'])
                self.metrics['interface_errors'].labels(
                    device_id=device.id,
                    device_name=device.name,
                    interface_name=interface_name,
                    interface_index=interface_index,
                    error_type='out'
                ).inc(out_errors)
            
        except Exception as e:
            logger.error("Failed to update interface metrics", device_id=device.id, error=str(e))
    
    def _parse_uptime(self, uptime_str: str) -> float:
        """Parse SNMP uptime string to seconds"""
        try:
            # SNMP uptime format: "123456:12:34:56.78"
            parts = uptime_str.split(':')
            if len(parts) >= 4:
                days = int(parts[0])
                hours = int(parts[1])
                minutes = int(parts[2])
                seconds = float(parts[3])
                return days * 86400 + hours * 3600 + minutes * 60 + seconds
            return 0.0
        except (ValueError, IndexError):
            return 0.0
    
    async def push_metrics(self):
        """Push metrics to Prometheus Pushgateway"""
        try:
            push_to_gateway(
                settings.prometheus_pushgateway_url,
                job='scnms-data-ingestion',
                registry=self.registry
            )
            logger.info("Metrics pushed to Prometheus")
        except Exception as e:
            logger.error("Failed to push metrics to Prometheus", error=str(e))


class DataIngestionService:
    """Main data ingestion service"""
    
    def __init__(self):
        self.prometheus_metrics = PrometheusMetrics()
        self.redis = get_redis()
        self.running = False
    
    async def start_ingestion(self):
        """Start the data ingestion process"""
        self.running = True
        logger.info("Data ingestion service started")
        
        while self.running:
            try:
                # Process metrics from database
                await self._process_metrics()
                
                # Process Redis messages
                await self._process_redis_messages()
                
                # Push metrics to Prometheus
                await self.prometheus_metrics.push_metrics()
                
                # Wait before next iteration
                await asyncio.sleep(30)  # Process every 30 seconds
                
            except Exception as e:
                logger.error("Data ingestion error", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop_ingestion(self):
        """Stop the data ingestion process"""
        self.running = False
        logger.info("Data ingestion service stopped")
    
    async def _process_metrics(self, db: Session = None):
        """Process metrics from database"""
        if not db:
            return
        
        try:
            # Get recent metrics (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            metrics = db.query(Metric).filter(
                Metric.timestamp >= cutoff_time
            ).order_by(Metric.timestamp.desc()).all()
            
            # Group metrics by device
            device_metrics = {}
            for metric in metrics:
                if metric.device_id not in device_metrics:
                    device_metrics[metric.device_id] = []
                device_metrics[metric.device_id].append(metric)
            
            # Process metrics for each device
            for device_id, device_metric_list in device_metrics.items():
                device = db.query(Device).filter(Device.id == device_id).first()
                if not device:
                    continue
                
                # Convert metrics to dictionary
                metrics_data = {}
                for metric in device_metric_list:
                    metrics_data[metric.metric_name] = metric.metric_value
                
                # Update Prometheus metrics
                self.prometheus_metrics.update_device_metrics(device, metrics_data)
                
                # Process interface metrics
                await self._process_interface_metrics(device, metrics_data)
            
        except Exception as e:
            logger.error("Failed to process metrics", error=str(e))
    
    async def _process_interface_metrics(self, device: Device, metrics_data: Dict[str, Any]):
        """Process interface-specific metrics"""
        try:
            # Group interface metrics by interface index
            interface_metrics = {}
            
            for metric_name, value in metrics_data.items():
                if 'interface' in metric_name.lower():
                    # Extract interface index from metric name
                    # This is a simplified approach - in production, you'd have better parsing
                    if 'ifInOctets' in metric_name or 'ifOutOctets' in metric_name:
                        interface_index = '1'  # Simplified - would extract from OID
                        if interface_index not in interface_metrics:
                            interface_metrics[interface_index] = {}
                        
                        if 'ifInOctets' in metric_name:
                            interface_metrics[interface_index]['ifInOctets'] = value
                        elif 'ifOutOctets' in metric_name:
                            interface_metrics[interface_index]['ifOutOctets'] = value
                        elif 'ifSpeed' in metric_name:
                            interface_metrics[interface_index]['ifSpeed'] = value
                        elif 'ifOperStatus' in metric_name:
                            interface_metrics[interface_index]['ifOperStatus'] = value
            
            # Update interface metrics
            for interface_index, interface_data in interface_metrics.items():
                interface_data['interface_index'] = interface_index
                interface_data['interface_name'] = f"interface-{interface_index}"
                self.prometheus_metrics.update_interface_metrics(device, interface_data)
            
        except Exception as e:
            logger.error("Failed to process interface metrics", device_id=device.id, error=str(e))
    
    async def _process_redis_messages(self):
        """Process messages from Redis"""
        try:
            # Get messages from Redis pub/sub
            pubsub = self.redis.pubsub()
            pubsub.subscribe('polling_results')
            
            # Process messages (non-blocking)
            message = pubsub.get_message(timeout=1)
            if message and message['type'] == 'message':
                data = json.loads(message['data'])
                await self._handle_polling_results(data)
            
            pubsub.close()
            
        except Exception as e:
            logger.error("Failed to process Redis messages", error=str(e))
    
    async def _handle_polling_results(self, data: Dict[str, Any]):
        """Handle polling results from Redis"""
        try:
            device_id = data.get('device_id')
            results = data.get('results', [])
            
            logger.info("Processing polling results", device_id=device_id, result_count=len(results))
            
            # Process each result
            for result in results:
                if result.get('success') and 'data' in result:
                    # Update Prometheus metrics with new data
                    # This would integrate with the metrics processing logic
                    pass
            
        except Exception as e:
            logger.error("Failed to handle polling results", error=str(e))


# Initialize service
ingestion_service = DataIngestionService()


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=time.time(),
        service="data_ingestion"
    )


@app.post("/ingest")
async def ingest_metrics(
    device_id: int,
    metrics_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Manually ingest metrics for a device"""
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Update Prometheus metrics
        ingestion_service.prometheus_metrics.update_device_metrics(device, metrics_data)
        
        # Process interface metrics if present
        await ingestion_service._process_interface_metrics(device, metrics_data)
        
        logger.info("Metrics ingested", device_id=device_id, metric_count=len(metrics_data))
        
        return {"message": "Metrics ingested successfully", "device_id": device_id}
        
    except Exception as e:
        logger.error("Failed to ingest metrics", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to ingest metrics: {str(e)}")


@app.get("/metrics/{device_id}")
async def get_device_metrics(
    device_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get metrics for a specific device"""
    try:
        query = db.query(Metric).filter(Metric.device_id == device_id)
        
        if start_time:
            query = query.filter(Metric.timestamp >= start_time)
        if end_time:
            query = query.filter(Metric.timestamp <= end_time)
        
        metrics = query.order_by(desc(Metric.timestamp)).limit(limit).all()
        
        return {
            "device_id": device_id,
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error("Failed to get device metrics", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@app.post("/start")
async def start_ingestion(background_tasks: BackgroundTasks):
    """Start the data ingestion process"""
    background_tasks.add_task(ingestion_service.start_ingestion)
    return {"message": "Data ingestion started"}


@app.post("/stop")
async def stop_ingestion():
    """Stop the data ingestion process"""
    await ingestion_service.stop_ingestion()
    return {"message": "Data ingestion stopped"}


@app.get("/prometheus/metrics")
async def get_prometheus_metrics():
    """Get Prometheus metrics in text format"""
    try:
        from prometheus_client import generate_latest
        
        # Generate metrics in Prometheus format
        metrics_text = generate_latest(ingestion_service.prometheus_metrics.registry)
        return metrics_text
        
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from fastapi.responses import PlainTextResponse
        
        # Generate metrics in Prometheus format
        metrics_text = generate_latest(ingestion_service.prometheus_metrics.registry)
        return PlainTextResponse(metrics_text, media_type=CONTENT_TYPE_LATEST)
    
    except Exception as e:
        logger.error("Failed to generate Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate metrics")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
