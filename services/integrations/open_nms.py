"""
OpenNMS Bridge
Subscribes to Redis `alarms` events and forwards them to an OpenNMS REST endpoint.
"""
import asyncio
import json
import os
from typing import Optional
from datetime import datetime

import httpx
import redis.asyncio as aioredis

from shared.logger import configure_logging, get_logger
from shared.config import settings

configure_logging()
logger = get_logger("open_nms_bridge")


class OpenNMSBridge:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.open_nms_url = getattr(settings, 'open_nms_url', None)
        self.open_nms_api_key = getattr(settings, 'open_nms_api_key', None)

    async def initialize(self):
        try:
            if not self.open_nms_url:
                logger.warning("OpenNMS URL not configured; bridge will remain idle")
                return

            self.redis_client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                decode_responses=True
            )
            logger.info("OpenNMS bridge initialized")
        except Exception as e:
            logger.error("Failed to initialize OpenNMS bridge", error=str(e))
            raise

    async def run(self):
        if not self.redis_client:
            logger.info("Redis client not available; skipping bridge run")
            return

        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('alarms')

        async for message in pubsub.listen():
            if message['type'] != 'message':
                continue

            try:
                event = json.loads(message['data'])
                await self._forward_to_open_nms(event)
            except Exception as e:
                logger.error("Failed to handle alarm message", error=str(e))

    async def _forward_to_open_nms(self, event: dict):
        if not self.open_nms_url:
            return

        payload = {
            'eventType': event.get('event_type'),
            'alarmId': event.get('alarm_id'),
            'deviceId': event.get('device_id'),
            'severity': event.get('severity'),
            'status': event.get('status'),
            'timestamp': event.get('timestamp') or datetime.utcnow().isoformat()
        }

        headers = {'Content-Type': 'application/json'}
        if self.open_nms_api_key:
            headers['Authorization'] = f"Bearer {self.open_nms_api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.open_nms_url, json=payload, headers=headers)
                if resp.status_code >= 300:
                    logger.warning("OpenNMS returned non-2xx", status=resp.status_code, body=resp.text)
                else:
                    logger.info("Forwarded alarm to OpenNMS", alarm_id=event.get('alarm_id'))
        except Exception as e:
            logger.error("Failed to forward to OpenNMS", error=str(e), alarm_id=event.get('alarm_id'))


async def main():
    bridge = OpenNMSBridge()
    await bridge.initialize()
    await bridge.run()


if __name__ == '__main__':
    # Run the async bridge directly; avoid requiring uvicorn in the lightweight bridge
    import asyncio
    asyncio.run(main())
