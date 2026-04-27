"""
Gateway entry point.

FastAPI equivalent of Express:
  app = FastAPI()      →  const app = express()
  @app.get("/path")    →  app.get('/path', handler)
  uvicorn runs this    →  node index.js
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="GatewayLM",
    description="LLM API gateway — rate limiting, fallback routing, observability",
    version="0.1.0",
)


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness probe. Returns 200 when the process is up."""
    return JSONResponse({"status": "ok", "version": "0.1.0"})
