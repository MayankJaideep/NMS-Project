"""
Multi-Protocol Poller Service - SCNMS Microservice
Handles SNMP, NETCONF, and RESTCONF data collection from network devices
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import concurrent.futures
from datetime import datetime, timedelta
import json
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST

from shared.database import get_db, get_redis
from shared.models import Device, PollingJob, Metric, DeviceStatus
from shared.schemas import (
    PollingJobCreate, PollingJob as PollingJobSchema,
    Metric as MetricSchema, HealthCheck
)
from shared.logger import configure_logging, get_logger
from shared.config import settings

# Configure logging
configure_logging()
logger = get_logger("poller")

app = FastAPI(
    title="SCNMS Multi-Protocol Poller Service",
    description="Network device polling via SNMP, NETCONF, and RESTCONF",
    version="1.0.0"
)

# Prometheus metrics
# Polling metrics
POLL_COUNT = Counter('polls_total', 'Total polls', ['protocol', 'status', 'device_type'])
POLL_DURATION = Histogram('poll_duration_seconds', 'Poll duration', ['protocol', 'device_type'])
ACTIVE_POLLS = Gauge('poll_active', 'Active polls')

# New metrics for enhanced monitoring
POLL_ERRORS = Counter('poll_errors_total', 'Total polling errors', ['error_type', 'protocol'])
METRICS_COLLECTED = Counter('metrics_collected_total', 'Total metrics collected', ['metric_type'])
DEVICE_POLL_DURATION = Histogram('device_poll_duration_seconds', 'Time taken to poll a device', ['device_type'])
QUEUE_SIZE = Gauge('poll_queue_size', 'Number of devices waiting to be polled')
LAST_SUCCESSFUL_POLL = Gauge('last_successful_poll_timestamp', 'Timestamp of last successful poll', ['device_id', 'device_name'])
RESPONSE_SIZE_BYTES = Histogram('poll_response_size_bytes', 'Size of poll responses in bytes', ['protocol'])
POLL_INTERVAL = Gauge('poll_interval_seconds', 'Configured poll interval for jobs', ['job_type'])

# Resource usage metrics
PROCESS_CPU_SECONDS = Counter('process_cpu_seconds_total', 'Total CPU seconds used by the process')
PROCESS_MEMORY_BYTES = Gauge('process_memory_bytes', 'Memory usage of the process in bytes')

# Custom metrics for network-specific monitoring
INTERFACE_UTILIZATION = Gauge('interface_utilization_percent', 'Interface utilization percentage', 
                             ['device_id', 'interface_name', 'direction'])
CPU_UTILIZATION = Gauge('device_cpu_utilization_percent', 'Device CPU utilization percentage', 
                       ['device_id', 'cpu_core'])
MEMORY_UTILIZATION = Gauge('device_memory_utilization_percent', 'Device memory utilization percentage', 
                          ['device_id', 'memory_type'])
DEVICE_UPTIME = Gauge('device_uptime_seconds', 'Device uptime in seconds', 
                     ['device_id', 'device_name'])
INTERFACE_ERRORS = Counter('interface_errors_total', 'Total interface errors', 
                          ['device_id', 'interface_name', 'error_type'])
INTERFACE_DISCARDS = Counter('interface_discards_total', 'Total interface discards', 
                            ['device_id', 'interface_name', 'direction'])
INTERFACE_OCTETS = Counter('interface_octets_total', 'Total octets transmitted/received', 
                          ['device_id', 'interface_name', 'direction'])
INTERFACE_PACKETS = Counter('interface_packets_total', 'Total packets transmitted/received', 
                           ['device_id', 'interface_name', 'direction'])
INTERFACE_SPEED = Gauge('interface_speed_bps', 'Interface speed in bits per second', 
                       ['device_id', 'interface_name', 'duplex'])
INTERFACE_STATUS = Gauge('interface_status', 'Interface status (1=up, 0=down, -1=unknown)', 
                        ['device_id', 'interface_name', 'admin_status'])

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class SNMPPoller:
    """SNMP polling implementation"""
    
    def __init__(self):
        self.common_oids = {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'ifNumber': '1.3.6.1.2.1.2.1.0',
            'ifIndex': '1.3.6.1.2.1.2.2.1.1',
            'ifDescr': '1.3.6.1.2.1.2.2.1.2',
            'ifType': '1.3.6.1.2.1.2.2.1.3',
            'ifMtu': '1.3.6.1.2.1.2.2.1.4',
            'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
            'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',
            'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',
            'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',
            'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
            'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11',
            'ifInNUcastPkts': '1.3.6.1.2.1.2.2.1.12',
            'ifInDiscards': '1.3.6.1.2.1.2.2.1.13',
            'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
            'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
            'ifOutUcastPkts': '1.3.6.1.2.1.2.2.1.17',
            'ifOutNUcastPkts': '1.3.6.1.2.1.2.2.1.18',
            'ifOutDiscards': '1.3.6.1.2.1.2.2.1.19',
            'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',
            'ifOutQLen': '1.3.6.1.2.1.2.2.1.21'
        }
    
    async def poll_device(self, device: Device, oids: List[str]) -> Dict[str, Any]:
        """Poll device using SNMP"""
        start_time = time.time()
        try:
            from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
            
            results = {}
            response_size = 0
            
            for oid in oids:
                try:
                    for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                        SnmpEngine(),
                        CommunityData(device.snmp_community or settings.snmp_community),
                        UdpTransportTarget((device.ip_address, 161), timeout=settings.snmp_timeout, retries=settings.snmp_retries),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid))
                    ):
                        if errorIndication:
                            error_msg = str(errorIndication)
                            logger.warning("SNMP error indication", device_id=device.id, oid=oid, error=error_msg)
                            POLL_ERRORS.labels(error_type='snmp_indication', protocol='snmp').inc()
                            continue
                        elif errorStatus:
                            error_msg = errorStatus.prettyPrint()
                            logger.warning("SNMP error status", device_id=device.id, oid=oid, error=error_msg)
                            POLL_ERRORS.labels(error_type='snmp_status', protocol='snmp').inc()
                            continue
                        else:
                            for varBind in varBinds:
                                results[oid] = str(varBind[1])
                                break
                except Exception as e:
                    logger.error("SNMP polling failed", device_id=device.id, oid=oid, error=str(e))
                    continue
            
            return {
                'success': len(results) > 0,
                'data': results,
                'timestamp': datetime.now(),
                'device_id': device.id
            }
            
        except Exception as e:
            logger.error("SNMP polling failed", device_id=device.id, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(),
                'device_id': device.id
            }


class NETCONFPoller:
    """NETCONF polling implementation"""
    
    async def poll_device(self, device: Device, paths: List[str]) -> Dict[str, Any]:
        """Poll device using NETCONF"""
        try:
            from ncclient import manager
            
            results = {}
            
            with manager.connect(
                host=device.ip_address,
                port=830,
                username=device.netconf_username or settings.netconf_username,
                password=device.netconf_password or settings.netconf_password,
                timeout=settings.netconf_timeout,
                hostkey_verify=False
            ) as m:
                for path in paths:
                    try:
                        # Get configuration data
                        config_data = m.get_config(source='running', filter=('xpath', path)).data_xml
                        results[path] = config_data
                    except Exception as e:
                        logger.warning("NETCONF path polling failed", device_id=device.id, path=path, error=str(e))
                        continue
                
                # Get operational data
                try:
                    operational_data = m.get().data_xml
                    results['operational'] = operational_data
                except Exception as e:
                    logger.warning("NETCONF operational data failed", device_id=device.id, error=str(e))
            
            return {
                'success': len(results) > 0,
                'data': results,
                'timestamp': datetime.now(),
                'device_id': device.id
            }
            
        except Exception as e:
            logger.error("NETCONF polling failed", device_id=device.id, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(),
                'device_id': device.id
            }


class RESTCONFPoller:
    """RESTCONF polling implementation"""
    
    async def poll_device(self, device: Device, paths: List[str]) -> Dict[str, Any]:
        """Poll device using RESTCONF"""
        try:
            import httpx
            
            results = {}
            
            async with httpx.AsyncClient(timeout=settings.restconf_timeout) as client:
                auth = (
                    device.restconf_username or settings.restconf_username,
                    device.restconf_password or settings.restconf_password
                )
                
                for path in paths:
                    try:
                        response = await client.get(
                            f"https://{device.ip_address}:443/restconf/data/{path}",
                            auth=auth,
                            verify=False
                        )
                        
                        if response.status_code == 200:
                            results[path] = response.json()
                        else:
                            logger.warning("RESTCONF path polling failed", 
                                        device_id=device.id, 
                                        path=path, 
                                        status=response.status_code)
                    except Exception as e:
                        logger.warning("RESTCONF path polling error", device_id=device.id, path=path, error=str(e))
                        continue
            
            return {
                'success': len(results) > 0,
                'data': results,
                'timestamp': datetime.now(),
                'device_id': device.id
            }
            
        except Exception as e:
            logger.error("RESTCONF polling failed", device_id=device.id, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(),
                'device_id': device.id
            }


class MultiProtocolPoller:
    """Main polling service coordinator"""
    
    def __init__(self):
        self.snmp_poller = SNMPPoller()
        self.netconf_poller = NETCONFPoller()
        self.restconf_poller = RESTCONFPoller()
        self.redis = get_redis()
        self._last_poll_time = {}
        self._polling_intervals = {}
    
    async def poll_job(self, job: PollingJob, device: Device) -> Dict[str, Any]:
        """Execute a single polling job"""
        # Retry loop with exponential backoff for transient failures
        attempts = getattr(settings, 'max_poll_retries', 3)
        backoff_base = getattr(settings, 'poll_backoff_base', 1.0)
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                if job.protocol.value == 'snmp':
                    result = await self.snmp_poller.poll_device(device, [job.oid_or_path])
                elif job.protocol.value == 'netconf':
                    result = await self.netconf_poller.poll_device(device, [job.oid_or_path])
                elif job.protocol.value == 'restconf':
                    result = await self.restconf_poller.poll_device(device, [job.oid_or_path])
                else:
                    raise ValueError(f"Unsupported protocol: {job.protocol}")

                # Update job execution time
                job.last_executed = datetime.now()
                job.next_execution = datetime.now() + timedelta(seconds=job.polling_interval)

                return result

            except Exception as e:
                last_exc = e
                logger.warning("Polling job attempt failed", job_id=job.id, device_id=device.id, attempt=attempt, error=str(e))
                # Backoff before next retry
                await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))

        logger.error("Polling job failed after retries", job_id=job.id, device_id=device.id, error=str(last_exc))
        return {
            'success': False,
            'error': str(last_exc),
            'timestamp': datetime.now(),
            'device_id': device.id,
            'job_id': job.id
        }
    
    async def poll_device(self, device: Device, db: Session) -> Dict[str, Any]:
        """Poll all jobs for a specific device"""
        try:
            # Get all enabled polling jobs for the device
            jobs = db.query(PollingJob).filter(
                and_(
                    PollingJob.device_id == device.id,
                    PollingJob.enabled == True,
                    or_(
                        PollingJob.next_execution <= datetime.now(),
                        PollingJob.next_execution.is_(None)
                    )
                )
            ).all()
            
            if not jobs:
                return {'success': True, 'message': 'No jobs to execute', 'device_id': device.id}
            
            results = []
            
            # Execute jobs concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=settings.max_concurrent_polls) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, asyncio.run, self.poll_job(job, device))
                    for job in jobs
                ]
                
                job_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(job_results):
                    if isinstance(result, dict):
                        results.append(result)
                        
                        # Store metrics in database
                        if result.get('success') and 'data' in result:
                            await self._store_metrics(device, jobs[i], result['data'], db)
                    
                    # Update job in database
                    jobs[i].last_executed = datetime.now()
                    jobs[i].next_execution = datetime.now() + timedelta(seconds=jobs[i].polling_interval)
            
            # Update device last_polled timestamp
            device.last_polled = datetime.now()
            device.status = DeviceStatus.UP
            
            db.commit()
            
            # Publish results to Redis for other services
            await self._publish_results(device.id, results)
            
            logger.info("Device polling completed", 
                      device_id=device.id, 
                      jobs_executed=len(jobs),
                      successful=len([r for r in results if r.get('success')]))
            
            return {
                'success': True,
                'device_id': device.id,
                'jobs_executed': len(jobs),
                'results': results
            }
            
        except Exception as e:
            logger.error("Device polling failed", device_id=device.id, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'device_id': device.id
            }
    
    async def _store_metrics(self, device: Device, job: PollingJob, data: Dict[str, Any], db: Session):
        """Store collected metrics in database"""
        try:
            for key, value in data.items():
                # Convert value to float if possible
                try:
                    metric_value = float(value)
                except (ValueError, TypeError):
                    metric_value = 0.0
                
                # Create metric record
                metric = Metric(
                    device_id=device.id,
                    metric_name=f"{job.protocol.value}_{key}",
                    metric_value=metric_value,
                    metric_unit=self._get_metric_unit(key),
                    timestamp=datetime.now()
                )
                
                db.add(metric)
            
            db.commit()
            
        except Exception as e:
            logger.error("Failed to store metrics", device_id=device.id, job_id=job.id, error=str(e))
    
    def _get_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for metric"""
        if 'octets' in metric_name.lower() or 'bytes' in metric_name.lower():
            return 'bytes'
        elif 'pkts' in metric_name.lower() or 'packets' in metric_name.lower():
            return 'packets'
        elif 'utilization' in metric_name.lower() or 'usage' in metric_name.lower():
            return 'percent'
        elif 'time' in metric_name.lower() or 'uptime' in metric_name.lower():
            return 'seconds'
        else:
            return 'count'
    
    async def _publish_results(self, device_id: int, results: List[Dict[str, Any]]):
        """Publish polling results to Redis for other services"""
        try:
            message = {
                'device_id': device_id,
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            
            self.redis.publish('polling_results', json.dumps(message))
            
        except Exception as e:
            logger.error("Failed to publish results", device_id=device_id, error=str(e))


# Initialize poller service
poller_service = MultiProtocolPoller()


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=time.time(),
        service="poller"
    )


@app.get("/jobs", response_model=List[PollingJobSchema])
async def get_polling_jobs(
    skip: int = 0,
    limit: int = 100,
    device_id: int = None,
    enabled: bool = None,
    db: Session = Depends(get_db)
):
    """Get polling jobs with optional filtering"""
    query = db.query(PollingJob)
    
    if device_id:
        query = query.filter(PollingJob.device_id == device_id)
    if enabled is not None:
        query = query.filter(PollingJob.enabled == enabled)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@app.post("/jobs", response_model=PollingJobSchema)
async def create_polling_job(job: PollingJobCreate, db: Session = Depends(get_db)):
    """Create a new polling job"""
    db_job = PollingJob(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    logger.info("Polling job created", job_id=db_job.id, device_id=db_job.device_id)
    return db_job


@app.put("/jobs/{job_id}", response_model=PollingJobSchema)
async def update_polling_job(
    job_id: int,
    job_update: dict,
    db: Session = Depends(get_db)
):
    """Update polling job"""
    job = db.query(PollingJob).filter(PollingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Polling job not found")
    
    for field, value in job_update.items():
        if hasattr(job, field):
            setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    logger.info("Polling job updated", job_id=job_id)
    return job


@app.delete("/jobs/{job_id}")
async def delete_polling_job(job_id: int, db: Session = Depends(get_db)):
    """Delete polling job"""
    job = db.query(PollingJob).filter(PollingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Polling job not found")
    
    db.delete(job)
    db.commit()
    
    logger.info("Polling job deleted", job_id=job_id)
    return {"message": "Polling job deleted successfully"}


@app.post("/poll/{device_id}")
async def poll_device_now(device_id: int, db: Session = Depends(get_db)):
    """Manually trigger polling for a device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    result = await poller_service.poll_device(device, db)
    return result


@app.post("/poll/all")
async def poll_all_devices(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Poll all devices (background task)"""
    devices = db.query(Device).filter(Device.status == DeviceStatus.UP).all()
    
    async def poll_all():
        for device in devices:
            try:
                await poller_service.poll_device(device, db)
            except Exception as e:
                logger.error("Failed to poll device", device_id=device.id, error=str(e))
    
    background_tasks.add_task(poll_all)
    
    return {"message": f"Polling initiated for {len(devices)} devices"}


@app.get("/metrics/{device_id}")
async def get_device_metrics(
    device_id: int,
    metric_name: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Get metrics for a specific device"""
    query = db.query(Metric).filter(Metric.device_id == device_id)
    
    if metric_name:
        query = query.filter(Metric.metric_name == metric_name)
    if start_time:
        query = query.filter(Metric.timestamp >= start_time)
    if end_time:
        query = query.filter(Metric.timestamp <= end_time)
    
    metrics = query.order_by(Metric.timestamp.desc()).limit(limit).all()
    return metrics


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
