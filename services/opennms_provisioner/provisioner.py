#!/usr/bin/env python3
"""Provisioner: reads devices from device_discovery service and posts to OpenNMS mock."""
import os
import requests
from typing import List

OPENNMS_URL = os.environ.get('OPEN_NMS_URL', 'http://localhost:8980')
DEVICE_DISCOVERY_URL = os.environ.get('DEVICE_DISCOVERY_URL', 'http://device-discovery:8001')


def fetch_devices() -> List[dict]:
    """Fetch devices from device_discovery `/devices` API (host or container)."""
    url = f"{DEVICE_DISCOVERY_URL}/devices"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


def provision_to_opennms(devices: List[dict]):
    url = f"{OPENNMS_URL}/rest/nodes"
    payload = []
    for d in devices:
        payload.append({
            'label': d.get('name') or d.get('hostname') or d.get('ip_address'),
            'ipAddress': d.get('ip_address'),
            'sysName': d.get('hostname') or d.get('name'),
            'location': d.get('location') or 'unknown',
            'cpu': d.get('cpu', 5.0)
        })

    if not payload:
        print('No devices to provision')
        return

    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    print('Provisioned', len(payload), 'devices to OpenNMS')
    print(resp.json())


def main():
    try:
        devices = fetch_devices()
    except Exception as e:
        print('Failed fetching devices from device_discovery:', e)
        return

    try:
        provision_to_opennms(devices)
    except Exception as e:
        print('Failed provisioning to OpenNMS:', e)


if __name__ == '__main__':
    main()
