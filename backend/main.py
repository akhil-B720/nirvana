"""
NIRVANA FastAPI Backend Application
National Infrastructure Reality & Verification Network using AI
"""
import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import projects, risk, ml_endpoints, reality_gap, data_endpoints, auth, evidence

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("nirvana.api")

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI app."""
    # Startup
    logger.info("Starting NIRVANA API server...")
    
    # Verify environment
    if not os.getenv("SECRET_KEY"):
        logger.warning("SECRET_KEY not set - using insecure default for development")
    
    yield
    
    # Shutdown
    logger.info("Shutting down NIRVANA API server...")


app = FastAPI(
    title="NIRVANA API",
    description="National Infrastructure Reality & Verification Network using AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite dev server default
    "http://127.0.0.1:5173",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(reality_gap.router, prefix="/api/v1")
app.include_router(ml_endpoints.router, prefix="/api/v1/ml")
app.include_router(data_endpoints.router, prefix="/api/v1/data")
app.include_router(evidence.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "name": "NIRVANA API",
        "status": "online",
        "description": "National Infrastructure Reality & Verification Network using AI",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
