from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from prometheus_client import multiprocess
import uvicorn
import asyncio
import json

app = FastAPI(title="OpenNMS Mock")

# In-memory node store
NODES = {}

# Prometheus metrics
registry = CollectorRegistry()
node_up = Gauge('opennms_node_up', 'Node up status', ['node'], registry=registry)
node_cpu = Gauge('opennms_node_cpu_percent', 'Node CPU percent', ['node'], registry=registry)


@app.get('/')
async def root():
    return {"service": "OpenNMS Mock", "nodes": len(NODES)}


@app.get('/opennms/login.jsp')
async def opennms_login():
        # Simple HTML login page to mimic OpenNMS UI for demo/testing
        html = """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>OpenNMS Mock - Login</title>
            <style>body{font-family:Arial,Helvetica,sans-serif;background:#f5f5f5;padding:40px} .card{max-width:420px;margin:40px auto;padding:24px;background:#fff;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.08)} input[type=text],input[type=password]{width:100%;padding:8px;margin:8px 0;border:1px solid #ccc;border-radius:4px} button{background:#0b6efd;color:#fff;border:none;padding:10px 14px;border-radius:4px;cursor:pointer}</style>
        </head>
        <body>
            <div class="card">
                <h2>OpenNMS Mock</h2>
                <p>Login (mock)</p>
                <form method="post" action="/opennms/login">
                    <label>Username</label>
                    <input type="text" name="username" value="admin" />
                    <label>Password</label>
                    <input type="password" name="password" />
                    <div style="text-align:right"><button type="submit">Log in</button></div>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


@app.post('/opennms/login')
async def opennms_login_post(request: Request):
        # Accept form POST and redirect to a fake overview page (JSON summary)
        return HTMLResponse(content="<html><body><h3>Logged in (mock)</h3><p><a href=\"/opennms/overview\">Open Overview</a></p></body></html>")


@app.get('/opennms/overview')
async def opennms_overview():
        # Simple human-readable overview page linking to REST and metrics
        html = f"""
        <html><body><h2>OpenNMS Mock Overview</h2>
        <p>Nodes provisioned: {len(NODES)}</p>
        <ul>
            <li><a href="/rest/nodes">REST: /rest/nodes</a></li>
            <li><a href="/metrics">Prometheus metrics: /metrics</a></li>
        </ul>
        </body></html>
        """
        return HTMLResponse(content=html)


@app.post('/rest/nodes')
async def create_node(request: Request):
    body = await request.json()
    # Accept either single node or list
    items = body if isinstance(body, list) else [body]
    created = []
    for it in items:
        node_id = it.get('ipAddress') or it.get('label')
        if not node_id:
            continue
        NODES[node_id] = {
            'label': it.get('label') or node_id,
            'ip': it.get('ipAddress') or node_id,
            'sysName': it.get('sysName') or it.get('label') or node_id,
            'location': it.get('location', 'lab')
        }
        # initialize metrics
        node_up.labels(node=node_id).set(1)
        node_cpu.labels(node=node_id).set(float(it.get('cpu', 10.0)))
        created.append(NODES[node_id])
    return {"created": created}


@app.get('/rest/nodes')
async def list_nodes():
    return list(NODES.values())


@app.get('/metrics')
async def metrics():
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8980)
