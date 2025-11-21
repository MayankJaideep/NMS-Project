"""
SNMP Trap Listener (HTTP + simple UDP JSON fallback)

Provides a small HTTP endpoint `/trap` that accepts JSON traps and republishes
them to Redis `traps` channel. This is easy to integrate with `snmptrapd` using
an external forwarder or simple scripts. A minimal UDP listener is included for
environments that can send JSON over UDP (useful for testing).
"""
import asyncio
import json
import socket
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import redis

from shared.config import settings
from shared.logger import configure_logging, get_logger

configure_logging()
logger = get_logger("trap_listener")

app = FastAPI(title="SNMP Trap Listener")

# Synchronous redis client from shared.database is available, but re-create here
redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, password=settings.redis_password, decode_responses=True)


@app.post("/trap")
async def receive_trap(req: Request):
    try:
        data = await req.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Basic validation
    if not isinstance(data, dict) or 'source_ip' not in data:
        raise HTTPException(status_code=400, detail="Payload must be JSON with 'source_ip' field")

    try:
        redis_client.publish('traps', json.dumps(data))
        logger.info("Published trap to Redis", source=data.get('source_ip'))
        return JSONResponse({'status': 'ok'})
    except Exception as e:
        logger.error("Failed to publish trap to Redis", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to publish trap")


def udp_json_listener(host: str = '0.0.0.0', port: int = 9162):
    """Simple UDP listener that expects JSON payloads and forwards to Redis.
    This is only for test/dev; production should use a proper SNMP trapd forwarder.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    logger.info("UDP JSON trap listener started", host=host, port=port)

    while True:
        try:
            data, addr = sock.recvfrom(65535)
            try:
                payload = json.loads(data.decode())
                payload.setdefault('source_ip', addr[0])
                redis_client.publish('traps', json.dumps(payload))
                logger.info("UDP trap forwarded to Redis", source=addr[0])
            except Exception:
                logger.warning("Received non-JSON UDP packet; ignoring", addr=addr)
        except Exception as e:
            logger.error("UDP listener error", error=str(e))


def start_udp_listener_in_thread():
    import threading
    t = threading.Thread(target=udp_json_listener, args=("0.0.0.0", 9162), daemon=True)
    t.start()


@app.on_event("startup")
async def startup_event():
    # Start UDP listener in background for testing convenience
    start_udp_listener_in_thread()
    logger.info("Trap listener HTTP endpoint ready")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8008)
