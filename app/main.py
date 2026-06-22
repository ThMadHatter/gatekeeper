import logging
import sys
import time
from fastapi import FastAPI, Request
from app.routers import proxmox
from app.config import settings

# Configure Logging
logging_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
handlers = [logging.StreamHandler(sys.stdout)]

# Optional log file
if settings.LOG_FILE:
    try:
        handlers.append(logging.FileHandler(settings.LOG_FILE))
    except Exception as e:
        print(f"Warning: Could not set up log file handler: {e}", file=sys.stderr)

logging.basicConfig(
    level=logging_level,
    format=log_format,
    handlers=handlers
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Proxmox Gatekeeper API")

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method

    # Log incoming request (avoid logging sensitive headers if any)
    logger.info(f"Incoming request: {method} {path}")

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(f"Completed request: {method} {path} - Status: {response.status_code} - Duration: {duration:.4f}s")

    return response

app.include_router(proxmox.router)

@app.get("/")
async def root():
    return {"message": "Proxmox Gatekeeper API is running"}
