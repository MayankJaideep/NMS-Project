"""
Device Discovery Service - SCNMS Microservice
Handles network device discovery and inventory management
"""
import asyncio
import ipaddress
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import concurrent.futures
import time
from prometheus_client import generate_latest, Counter, Histogram, Gauge, CONTENT_TYPE_LATEST

from shared.database import get_db, get_redis
from shared.models import Device, DeviceStatus, ProtocolType
from shared.schemas import (
    DeviceCreate, DeviceUpdate, Device as DeviceSchema,
    DiscoveryRequest, DiscoveryResult, HealthCheck
)
from shared.logger import configure_logging, get_logger
from shared.config import settings

# Configure logging
configure_logging()
logger = get_logger("device_discovery")

app = FastAPI(
    title="SCNMS Device Discovery Service",
    description="Network device discovery and inventory management",
    version="1.0.0"
)

# Prometheus metrics
DISCOVERY_COUNT = Counter('device_discoveries_total', 'Total device discoveries', 'status')
DISCOVERY_DURATION = Histogram('device_discovery_duration_seconds', 'Device discovery duration')
ACTIVE_DISCOVERIES = Gauge('device_discovery_active', 'Active discovery tasks')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class DeviceDiscoveryService:
    """Device discovery and management service"""
    
    def __init__(self):
        self.snmp_oids = {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0'
        }
    
    async def discover_device(self, ip: str, protocols: List[ProtocolType]) -> Dict[str, Any]:
        """Discover a single device using specified protocols"""
        discovery_result = {
            'ip': ip,
            'success': False,
            'protocols': {},
            'device_info': {},
            'error': None
        }
        
        try:
            # Test SNMP connectivity
            if ProtocolType.SNMP in protocols:
                snmp_info = await self._test_snmp(ip)
                discovery_result['protocols']['snmp'] = snmp_info['success']
                if snmp_info['success']:
                    discovery_result['device_info'].update(snmp_info['data'])
            
            # Test NETCONF connectivity
            if ProtocolType.NETCONF in protocols:
                netconf_info = await self._test_netconf(ip)
                discovery_result['protocols']['netconf'] = netconf_info['success']
                if netconf_info['success']:
                    discovery_result['device_info'].update(netconf_info['data'])
            
            # Test RESTCONF connectivity
            if ProtocolType.RESTCONF in protocols:
                restconf_info = await self._test_restconf(ip)
                discovery_result['protocols']['restconf'] = restconf_info['success']
                if restconf_info['success']:
                    discovery_result['device_info'].update(restconf_info['data'])
            
            # Determine if discovery was successful
            discovery_result['success'] = any(discovery_result['protocols'].values())
            
        except Exception as e:
            logger.error("Device discovery failed", ip=ip, error=str(e))
            discovery_result['error'] = str(e)
        
        return discovery_result
    
    async def _test_snmp(self, ip: str) -> Dict[str, Any]:
        """Test SNMP connectivity and gather basic info"""
        try:
            from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
            
            result = {'success': False, 'data': {}}
            
            # Test basic SNMP connectivity
            for (errorIndication, errorStatus, errorIndex, varBinds) in getCmd(
                SnmpEngine(),
                CommunityData(settings.snmp_community),
                UdpTransportTarget((ip, 161), timeout=settings.snmp_timeout, retries=settings.snmp_retries),
                ContextData(),
                ObjectType(ObjectIdentity(self.snmp_oids['sysDescr']))
            ):
                if errorIndication:
                    result['error'] = str(errorIndication)
                    break
                elif errorStatus:
                    result['error'] = f"SNMP Error: {errorStatus.prettyPrint()}"
                    break
                else:
                    for varBind in varBinds:
                        result['data']['description'] = str(varBind[1])
                        result['success'] = True
            
            # Get additional system information if basic connectivity works
            if result['success']:
                for oid_name, oid in self.snmp_oids.items():
                    if oid_name == 'sysDescr':
                        continue
                    
                    try:
                        for (errorIndation, errorStatus, errorIndex, varBinds) in getCmd(
                            SnmpEngine(),
                            CommunityData(settings.snmp_community),
                            UdpTransportTarget((ip, 161), timeout=settings.snmp_timeout),
                            ContextData(),
                            ObjectType(ObjectIdentity(oid))
                        ):
                            if not errorIndation and not errorStatus:
                                for varBind in varBinds:
                                    result['data'][oid_name] = str(varBind[1])
                    except Exception:
                        continue
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': {}}
    
    async def _test_netconf(self, ip: str) -> Dict[str, Any]:
        """Test NETCONF connectivity"""
        try:
            from ncclient import manager
            
            result = {'success': False, 'data': {}}
            
            with manager.connect(
                host=ip,
                port=830,
                username=settings.netconf_username,
                password=settings.netconf_password,
                timeout=settings.netconf_timeout,
                hostkey_verify=False
            ) as m:
                # Get device capabilities
                capabilities = m.server_capabilities
                result['data']['netconf_capabilities'] = list(capabilities.keys())
                result['success'] = True
                
                # Try to get basic system info
                try:
                    system_info = m.get_config(source='running').data_xml
                    result['data']['netconf_config'] = system_info
                except Exception:
                    pass
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': {}}
    
    async def _test_restconf(self, ip: str) -> Dict[str, Any]:
        """Test RESTCONF connectivity"""
        try:
            import httpx
            
            result = {'success': False, 'data': {}}
            
            async with httpx.AsyncClient(timeout=settings.restconf_timeout) as client:
                # Test basic RESTCONF connectivity
                auth = (settings.restconf_username, settings.restconf_password)
                
                # Try to get system info
                response = await client.get(
                    f"https://{ip}:443/restconf/data/ietf-system:system-state",
                    auth=auth,
                    verify=False
                )
                
                if response.status_code == 200:
                    result['data']['restconf_data'] = response.json()
                    result['success'] = True
                else:
                    result['error'] = f"HTTP {response.status_code}: {response.text}"
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': {}}
    
    async def scan_network_range(self, network_range: str, protocols: List[ProtocolType]) -> List[Dict[str, Any]]:
        """Scan a network range for devices"""
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            ip_list = [str(ip) for ip in network.hosts()]
            
            logger.info("Starting network scan", range=network_range, ip_count=len(ip_list))
            
            # Use thread pool for concurrent discovery
            with concurrent.futures.ThreadPoolExecutor(max_workers=settings.max_concurrent_polls) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, asyncio.run, self.discover_device(ip, protocols))
                    for ip in ip_list
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filter successful discoveries
                successful_discoveries = [
                    result for result in results
                    if isinstance(result, dict) and result.get('success', False)
                ]
                
                logger.info("Network scan completed", 
                          total_ips=len(ip_list), 
                          successful=len(successful_discoveries))
                
                return successful_discoveries
                
        except Exception as e:
            logger.error("Network scan failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"Network scan failed: {str(e)}")


# Initialize service
discovery_service = DeviceDiscoveryService()


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=time.time(),
        service="device_discovery"
    )


@app.get("/devices", response_model=List[DeviceSchema])
async def get_devices(
    skip: int = 0,
    limit: int = 100,
    status: DeviceStatus = None,
    db: Session = Depends(get_db)
):
    """Get list of devices with optional filtering"""
    query = db.query(Device)
    
    if status:
        query = query.filter(Device.status == status)
    
    devices = query.offset(skip).limit(limit).all()
    return devices


@app.get("/devices/{device_id}", response_model=DeviceSchema)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get specific device by ID"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/devices", response_model=DeviceSchema)
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Create a new device"""
    # Check if device with same IP already exists
    existing_device = db.query(Device).filter(Device.ip_address == device.ip_address).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device with this IP address already exists")
    
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    logger.info("Device created", device_id=db_device.id, ip=db_device.ip_address)
    return db_device


@app.put("/devices/{device_id}", response_model=DeviceSchema)
async def update_device(
    device_id: int, 
    device_update: DeviceUpdate, 
    db: Session = Depends(get_db)
):
    """Update device information"""
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


@app.delete("/devices/{device_id}")
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a device"""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    
    logger.info("Device deleted", device_id=device_id)
    return {"message": "Device deleted successfully"}


@app.post("/discover", response_model=List[DiscoveryResult])
async def discover_network(
    request: DiscoveryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Discover devices in a network range"""
    try:
        # Perform network scan
        discoveries = await discovery_service.scan_network_range(
            request.network_range, 
            request.protocols
        )
        
        results = []
        
        for discovery in discoveries:
            try:
                # Create or update device record
                device_data = {
                    'name': discovery['device_info'].get('sysName', discovery['ip']),
                    'ip_address': discovery['ip'],
                    'hostname': discovery['device_info'].get('sysName'),
                    'vendor': self._extract_vendor(discovery['device_info'].get('description', '')),
                    'model': self._extract_model(discovery['device_info'].get('description', '')),
                    'location': discovery['device_info'].get('sysLocation'),
                    'description': discovery['device_info'].get('sysDescr'),
                    'snmp_enabled': discovery['protocols'].get('snmp', False),
                    'snmp_community': settings.snmp_community if discovery['protocols'].get('snmp') else None,
                    'netconf_enabled': discovery['protocols'].get('netconf', False),
                    'netconf_username': settings.netconf_username if discovery['protocols'].get('netconf') else None,
                    'netconf_password': settings.netconf_password if discovery['protocols'].get('netconf') else None,
                    'restconf_enabled': discovery['protocols'].get('restconf', False),
                    'restconf_username': settings.restconf_username if discovery['protocols'].get('restconf') else None,
                    'restconf_password': settings.restconf_password if discovery['protocols'].get('restconf') else None,
                    'status': DeviceStatus.UP
                }
                
                # Check if device already exists
                existing_device = db.query(Device).filter(Device.ip_address == discovery['ip']).first()
                
                if existing_device:
                    # Update existing device
                    for field, value in device_data.items():
                        if value is not None:
                            setattr(existing_device, field, value)
                    device = existing_device
                else:
                    # Create new device
                    device = Device(**device_data)
                    db.add(device)
                
                db.commit()
                db.refresh(device)
                
                # Create discovery result
                result = DiscoveryResult(
                    device=device,
                    discovered_protocols=[p for p, enabled in discovery['protocols'].items() if enabled],
                    discovery_time=0.0,  # Would be calculated in real implementation
                    success=True
                )
                results.append(result)
                
            except Exception as e:
                logger.error("Failed to process discovery result", ip=discovery['ip'], error=str(e))
                result = DiscoveryResult(
                    device=None,
                    discovered_protocols=[],
                    discovery_time=0.0,
                    success=False,
                    error=str(e)
                )
                results.append(result)
        
        logger.info("Network discovery completed", 
                  range=request.network_range, 
                  discovered=len([r for r in results if r.success]))
        
        return results
        
    except Exception as e:
        logger.error("Network discovery failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


def _extract_vendor(self, description: str) -> str:
    """Extract vendor from device description"""
    description_lower = description.lower()
    if 'cisco' in description_lower:
        return 'Cisco'
    elif 'juniper' in description_lower:
        return 'Juniper'
    elif 'arista' in description_lower:
        return 'Arista'
    elif 'fortinet' in description_lower:
        return 'Fortinet'
    elif 'hp' in description_lower or 'hewlett' in description_lower:
        return 'HP'
    elif 'dell' in description_lower:
        return 'Dell'
    else:
        return 'Unknown'


def _extract_model(self, description: str) -> str:
    """Extract model from device description"""
    # Simple model extraction - would be more sophisticated in production
    words = description.split()
    for i, word in enumerate(words):
        if word.lower() in ['catalyst', 'isr', 'asr', 'nexus']:
            if i + 1 < len(words):
                return f"{word} {words[i + 1]}"
    return 'Unknown'


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
