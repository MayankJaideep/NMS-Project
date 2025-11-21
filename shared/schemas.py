"""
Pydantic schemas for API serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from shared.models import DeviceStatus, AlarmSeverity, AlarmStatus, ProtocolType


# Device Schemas
class DeviceBase(BaseModel):
    name: str
    ip_address: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class DeviceCreate(DeviceBase):
    snmp_enabled: bool = False
    snmp_community: Optional[str] = None
    snmp_version: str = "2c"
    netconf_enabled: bool = False
    netconf_username: Optional[str] = None
    netconf_password: Optional[str] = None
    restconf_enabled: bool = False
    restconf_username: Optional[str] = None
    restconf_password: Optional[str] = None


class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    snmp_enabled: Optional[bool] = None
    snmp_community: Optional[str] = None
    snmp_version: Optional[str] = None
    netconf_enabled: Optional[bool] = None
    netconf_username: Optional[str] = None
    netconf_password: Optional[str] = None
    restconf_enabled: Optional[bool] = None
    restconf_username: Optional[str] = None
    restconf_password: Optional[str] = None


class Device(DeviceBase):
    id: int
    status: DeviceStatus
    snmp_enabled: bool
    snmp_community: Optional[str]
    snmp_version: str
    netconf_enabled: bool
    netconf_username: Optional[str]
    restconf_enabled: bool
    restconf_username: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_polled: Optional[datetime]
    
    class Config:
        from_attributes = True


# Metric Schemas
class MetricBase(BaseModel):
    metric_name: str
    metric_value: float
    metric_unit: Optional[str] = None


class MetricCreate(MetricBase):
    device_id: int
    timestamp: Optional[datetime] = None


class Metric(MetricBase):
    id: int
    device_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Alarm Schemas
class AlarmBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: AlarmSeverity
    source: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class AlarmCreate(AlarmBase):
    device_id: int
    alarm_id: str


class AlarmUpdate(BaseModel):
    status: Optional[AlarmStatus] = None
    acknowledged_by: Optional[str] = None


class Alarm(AlarmBase):
    id: int
    device_id: int
    alarm_id: str
    status: AlarmStatus
    raised_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    cleared_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Polling Job Schemas
class PollingJobBase(BaseModel):
    device_id: int
    protocol: ProtocolType
    oid_or_path: str
    polling_interval: int = 60
    enabled: bool = True


class PollingJobCreate(PollingJobBase):
    pass


class PollingJob(PollingJobBase):
    id: int
    last_executed: Optional[datetime]
    next_execution: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Alarm Rule Schemas
class AlarmRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    metric_name: str
    threshold_value: float
    comparison_operator: str
    duration_seconds: int = 0
    severity: AlarmSeverity
    enabled: bool = True


class AlarmRuleCreate(AlarmRuleBase):
    pass


class AlarmRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison_operator: Optional[str] = None
    duration_seconds: Optional[int] = None
    severity: Optional[AlarmSeverity] = None
    enabled: Optional[bool] = None


class AlarmRule(AlarmRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# API Response Schemas
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    service: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime


# Discovery Schemas
class DiscoveryRequest(BaseModel):
    network_range: str = Field(..., description="Network range to scan (e.g., 192.168.1.0/24)")
    protocols: List[ProtocolType] = Field(default=[ProtocolType.SNMP], description="Protocols to use for discovery")
    timeout: int = Field(default=5, description="Timeout per device in seconds")


class DiscoveryResult(BaseModel):
    device: Device
    discovered_protocols: List[ProtocolType]
    discovery_time: float
    success: bool
    error: Optional[str] = None


# Metrics Query Schemas
class MetricsQuery(BaseModel):
    device_ids: Optional[List[int]] = None
    metric_names: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=1000, le=10000)


class MetricsResponse(BaseModel):
    metrics: List[Metric]
    total_count: int
    query_time: float
