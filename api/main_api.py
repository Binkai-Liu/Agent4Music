"""FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.charts_api import router as charts_router
from api.data_api import router as data_router
from api.recommend_api import router as recommend_router
from api.task_api import router as task_router
from api.ws_log import router as ws_router
from core.task_scheduler import get_scheduler
from services.database import get_db
from visual.mermaid_gen import get_architecture_diagram, get_business_flow


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_db()
    await get_scheduler()
    yield


app = FastAPI(
    title="Agent4Music",
    description="An Agent System for Crawling, Analyzing & Visualizing Open Data of Modern Music Websites",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_router)
app.include_router(data_router)
app.include_router(charts_router)
app.include_router(recommend_router)
app.include_router(ws_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Agent4Music"}


@app.get("/api/diagrams/architecture")
async def architecture_diagram():
    return {"mermaid": get_architecture_diagram()}


@app.get("/api/diagrams/business-flow")
async def business_flow_diagram():
    return {"mermaid": get_business_flow()}


webui_dist = PROJECT_ROOT / "webui" / "dist"
if webui_dist.exists():
    app.mount("/", StaticFiles(directory=str(webui_dist), html=True), name="static")
else:

    @app.get("/", include_in_schema=False)
    async def webui_not_built():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            "<h2>Agent4Music WebUI 尚未构建</h2>"
            "<p>请运行：<code>cd webui && npm install && npm run build</code></p>"
            "<p>或直接执行 <code>./start.sh</code>（会自动构建）</p>"
            "<p><a href='/docs'>API 文档 /docs</a></p>"
        )
