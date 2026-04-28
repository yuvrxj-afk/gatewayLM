"""
Gateway entry point.

FastAPI equivalent of Express:
  app = FastAPI()      →  const app = express()
  @app.get("/path")    →  app.get('/path', handler)
  uvicorn runs this    →  node index.js
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from .providers.health import health_check_loop
from .routers import admin, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start health checker background task on startup
    task = asyncio.create_task(health_check_loop())
    yield
    # Cancel it cleanly on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="GatewayLM",
    description="LLM API gateway — rate limiting, fallback routing, observability",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(admin.router)

FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness probe. Returns 200 when the process is up."""
    return JSONResponse({"status": "ok", "version": "0.1.0"})


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
