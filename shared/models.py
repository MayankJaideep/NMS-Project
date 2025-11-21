"""
Database models for SCNMS
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base
import enum


class DeviceStatus(str, enum.Enum):
    """Device status enumeration"""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class AlarmSeverity(str, enum.Enum):
    """Alarm severity levels"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    WARNING = "warning"
    INFO = "info"


class AlarmStatus(str, enum.Enum):
    """Alarm status enumeration"""
    RAISED = "raised"
    ACKNOWLEDGED = "acknowledged"
    CLEARED = "cleared"
    CLOSED = "closed"


class ProtocolType(str, enum.Enum):
    """Supported protocol types"""
    SNMP = "snmp"
    NETCONF = "netconf"
    RESTCONF = "restconf"
    SSH = "ssh"


class Device(Base):
    """Network device model"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    hostname = Column(String(255), nullable=True)
    vendor = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    status = Column(Enum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Protocol support
    snmp_enabled = Column(Boolean, default=False)
    snmp_community = Column(String(100), nullable=True)
    snmp_version = Column(String(10), default="2c")
    
    netconf_enabled = Column(Boolean, default=False)
    netconf_username = Column(String(100), nullable=True)
    netconf_password = Column(String(255), nullable=True)
    
    restconf_enabled = Column(Boolean, default=False)
    restconf_username = Column(String(100), nullable=True)
    restconf_password = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_polled = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    metrics = relationship("Metric", back_populates="device")
    alarms = relationship("Alarm", back_populates="device")


class Metric(Base):
    """Network metrics model"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    device = relationship("Device", back_populates="metrics")


class Alarm(Base):
    """Alarm model for lifecycle management"""
    __tablename__ = "alarms"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    alarm_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlarmSeverity), nullable=False)
    status = Column(Enum(AlarmStatus), default=AlarmStatus.RAISED)
    
    # Alarm lifecycle timestamps
    raised_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    cleared_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    source = Column(String(50), nullable=True)  # snmp_trap, polling, manual
    tags = Column(Text, nullable=True)  # JSON string for additional tags
    
    # Relationships
    device = relationship("Device", back_populates="alarms")


class PollingJob(Base):
    """Polling job configuration"""
    __tablename__ = "polling_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    protocol = Column(Enum(ProtocolType), nullable=False)
    oid_or_path = Column(String(500), nullable=False)
    polling_interval = Column(Integer, default=60)  # seconds
    enabled = Column(Boolean, default=True)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    next_execution = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AlarmRule(Base):
    """Alarm rule configuration"""
    __tablename__ = "alarm_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metric_name = Column(String(100), nullable=False)
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # >, <, >=, <=, ==, !=
    duration_seconds = Column(Integer, default=0)  # 0 means immediate
    severity = Column(Enum(AlarmSeverity), nullable=False)
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
