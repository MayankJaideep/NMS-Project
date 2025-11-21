"""
Alarm Escalation Worker
Subscribes to Redis `alarms` events and sends notifications based on severity and
configured escalation policies (Slack webhook and email optional).
"""
import asyncio
import json
from typing import Optional
from datetime import datetime

import httpx
import redis.asyncio as aioredis

from shared.logger import configure_logging, get_logger
from shared.config import settings

configure_logging()
logger = get_logger("escalation_worker")


class EscalationWorker:
    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self.slack_webhook = getattr(settings, 'slack_webhook_url', None)

    async def initialize(self):
        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                decode_responses=True
            )
            logger.info("Escalation worker initialized")
        except Exception as e:
            logger.error("Failed to initialize escalation worker", error=str(e))
            raise

    async def run(self):
        if not self.redis_client:
            return

        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe('alarms')

        async for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            try:
                event = json.loads(message['data'])
                await self.handle_event(event)
            except Exception as e:
                logger.error("Failed to handle alarm event", error=str(e))

    async def handle_event(self, event: dict):
        severity = event.get('severity')
        alarm_id = event.get('alarm_id')
        status = event.get('status')
        ts = event.get('timestamp') or datetime.utcnow().isoformat()

        # Example policy: notify Slack for CRITICAL or MAJOR when raised
        if status in ('RAISED', 'raised') and severity in ('CRITICAL', 'MAJOR'):
            await self.notify_slack(event)

    async def notify_slack(self, event: dict):
        if not self.slack_webhook:
            logger.debug("Slack webhook not configured; skipping Slack notify")
            return

        text = f"Alarm {event.get('alarm_id')} - {event.get('event_type')} - severity={event.get('severity')} status={event.get('status')}"
        payload = {"text": text}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(self.slack_webhook, json=payload)
                if resp.status_code >= 300:
                    logger.warning("Slack notify failed", status=resp.status_code, body=resp.text)
                else:
                    logger.info("Sent Slack notification", alarm_id=event.get('alarm_id'))
        except Exception as e:
            logger.error("Failed to send Slack notification", error=str(e))


async def main():
    worker = EscalationWorker()
    await worker.initialize()
    await worker.run()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("services.escalation.worker:main", host='0.0.0.0', port=8011)
