"""
Configuration management for SCNMS microservices
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "scnms"
    postgres_user: str = "scnms"
    postgres_password: str = "scnms"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    # Prometheus Configuration
    prometheus_url: str = "http://localhost:9090"
    prometheus_pushgateway_url: str = "http://localhost:9091"
    
    # Service Configuration
    log_level: str = "INFO"
    max_workers: int = 4
    service_name: str = "scnms"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # SNMP Configuration
    snmp_community: str = "public"
    snmp_timeout: int = 5
    snmp_retries: int = 3
    
    # NETCONF Configuration
    netconf_username: str = "admin"
    netconf_password: str = "admin"
    netconf_timeout: int = 30
    
    # RESTCONF Configuration
    restconf_username: str = "admin"
    restconf_password: str = "admin"
    restconf_timeout: int = 30
    
    # Polling Configuration
    polling_interval: int = 60
    batch_size: int = 100
    max_concurrent_polls: int = 10
    # Poller retry/backoff
    max_poll_retries: int = 3
    poll_backoff_base: float = 1.0
    
    # Alarm Configuration
    alarm_retention_days: int = 30
    alarm_cleanup_interval: int = 3600

    # OpenNMS integration
    open_nms_url: Optional[str] = None
    open_nms_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
