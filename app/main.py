import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.models.schemas import CommandRequest, CommandResponse
from app.services.intent_parser import parse_command

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate limiter ───────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Quran Voice Command API",
    description="Parses Arabic/English voice commands into structured Quran app actions using Gemini Flash.",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Update allow_origins with your production domain before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ← tighten to your app's domain in production
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── Global error handler ───────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url, exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.post("/api/command", response_model=CommandResponse)
@limiter.limit("30/minute")
async def command(request: Request, req: CommandRequest):
    """Parse a voice command and return a structured Quran app action."""
    logger.info("Incoming command | ip=%s text=%r", request.client.host, req.text)
    result = await parse_command(req.text)
    return result


@app.get("/health")
async def health():
    """Server health check."""
    return {"status": "ok"}
