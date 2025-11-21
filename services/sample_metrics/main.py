#!/usr/bin/env python3
import time
import random
from prometheus_client import start_http_server, Gauge, Counter

# Metrics matching dashboards
iface_in = Gauge('nms_interface_traffic_mbps', 'Interface traffic in Mbps', ['interface', 'direction'])
device_out = Gauge('nms_device_bandwidth_out', 'Device bandwidth out Mbps', ['device'])

# Additional sample metrics referenced by dashboards
device_cpu = Gauge('nms_device_cpu_percent', 'Device CPU percent', ['device'])
device_mem = Gauge('nms_device_memory_percent', 'Device memory percent', ['device'])
device_status = Gauge('nms_device_status', 'Device status: 1=UP,0=DOWN', ['device'])
interface_util = Gauge('nms_interface_utilization', 'Interface utilization percent', ['interface', 'device_name'])
interface_packet_loss = Gauge('nms_interface_packet_loss', 'Interface packet loss percent', ['interface', 'device_name'])
interface_latency = Gauge('nms_interface_latency', 'Interface latency ms', ['interface', 'device_name'])
interface_errors = Gauge('nms_interface_errors', 'Interface error counters', ['interface', 'device_name', 'error_type'])
interface_discards = Gauge('nms_interface_discards', 'Interface discard counters', ['interface', 'device_name', 'discard_type'])
device_reboots = Counter('nms_device_reboots_total', 'Total device reboots', ['device'])
interface_info = Gauge('nms_interface_info', 'Static interface info label', ['interface', 'device_name'])

def generate_metrics():
    # create a few sample interfaces/devices
    interfaces = ['eth0', 'eth1', 'eth2']
    devices = ['router1', 'switch1', 'switch2']
    reboot_toggle = 0
    while True:
        for d in devices:
            # CPU and memory 0-100%
            device_cpu.labels(device=d).set(random.uniform(1, 95))
            device_mem.labels(device=d).set(random.uniform(5, 95))
            # randomly make a device down occasionally
            status = 1 if random.random() > 0.05 else 0
            device_status.labels(device=d).set(status)
            # occasional reboot event
            if random.random() < 0.01:
                device_reboots.labels(device=d).inc()

        for i in interfaces:
            # random traffic between 10 and 900 Mbps
            val = random.uniform(10, 900)
            iface_in.labels(interface=i, direction='in').set(val)
            # utilization percent
            interface_util.labels(interface=i, device_name='router1').set(random.uniform(0, 100))
            interface_packet_loss.labels(interface=i, device_name='router1').set(random.uniform(0, 5))
            interface_latency.labels(interface=i, device_name='router1').set(random.uniform(1, 200))
            # error / discard counters split across types
            interface_errors.labels(interface=i, device_name='router1', error_type='crc').set(random.randint(0, 20))
            interface_errors.labels(interface=i, device_name='router1', error_type='alignment').set(random.randint(0, 5))
            interface_discards.labels(interface=i, device_name='router1', discard_type='in').set(random.randint(0, 50))
            interface_discards.labels(interface=i, device_name='router1', discard_type='out').set(random.randint(0, 50))
            # info-like label (set to 1 for presence)
            interface_info.labels(interface=i, device_name='router1').set(1)

        for d in devices:
            val = random.uniform(5, 1000)
            device_out.labels(device=d).set(val)

        time.sleep(5)

def main():
    # start up the metrics server
    start_http_server(8000)
    print('Sample metrics exporter running on :8000')
    generate_metrics()

if __name__ == '__main__':
    main()
