"""
FastAPI application entry point for Vedic Astrology API.

"""

import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .api.dependencies import verify_api_key
from .api.routes import router
from .api.advanced_routes import router as advanced_router
from .api.prediction_routes import router as prediction_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment flags
# ---------------------------------------------------------------------------
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "production") == "production"

# ---------------------------------------------------------------------------
# Rate limiter  
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ---------------------------------------------------------------------------
# Create FastAPI app 
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Vedic Astrology API",
    description="""
    A comprehensive Vedic Astrology API providing accurate astronomical calculations
    for zodiac positions, Vimshottari Dasha, and Antardasha periods using traditional
    Jyotish methods.

    ## Features

    ### Core Features
    - **Planetary Positions**: Sidereal zodiac positions using Swiss Ephemeris
    - **Rashi (Zodiac Signs)**: Traditional Vedic sign calculations
    - **Nakshatras**: 27 lunar mansions with pada calculations
    - **Vimshottari Dasha**: Complete Mahadasha/Antardasha/Pratyantardasha timeline
    - **Ayanamsa Options**: Lahiri, Krishnamurti, and Raman systems

    ### Advanced Features
    - **Divisional Charts**: All 16 Shodashavarga charts (D-1 to D-60)
    - **Shadbala**: Six-fold planetary strength analysis
    - **Ashtakavarga**: Transit prediction system with bindu calculations
    - **Yogas**: Detection of Rajayogas, Dhana Yogas, and more
    - **Panchanga**: Tithi, Nakshatra, Yoga, Karana, Vara calculations

    ### Dasha Predictions
    - **Detailed Predictions**: In-depth predictions for all Dasha periods
    - **Life Areas**: Health, Wealth, Career, Relationships, General outlook
    - **Remedies**: Gemstones, Mantras, Favorable/Unfavorable activities
    - **Combination Matrix**: All 81 Mahadasha-Antardasha combinations

    ## Accuracy

    Uses the Swiss Ephemeris for planetary calculations, which provides
    accuracy within arcseconds for modern dates.
    """,
    version="0.2.0",
    # hide interactive docs in production
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
)

# ---------------------------------------------------------------------------
# Attach rate limiter state 
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
#  Global exception handler — never leak internal details
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that logs the full error but returns a safe generic message."""
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# ---------------------------------------------------------------------------
#  Request body size limit middleware (64 KB)
# ---------------------------------------------------------------------------
class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    MAX_BODY_BYTES = 64_000  # 64 KB

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_BODY_BYTES:
            logger.warning(
                "Rejected oversized request (%s bytes) from %s",
                content_length,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                {"detail": "Request body too large. Maximum allowed size is 64 KB."},
                status_code=413,
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Security response headers middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        # Only set HSTS on HTTPS (no local dev breakage)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


# Order matters: register middleware in reverse application order.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(MaxBodySizeMiddleware)

# ---------------------------------------------------------------------------
# CORS — tightened to only what's actually used
# ---------------------------------------------------------------------------
_default_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://vedi-cyan.vercel.app",
]
_extra_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "").split(",")
    if o.strip()
]
_allowed_origins = list(dict.fromkeys(_default_origins + _extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],        # only methods routes actually use
    allow_headers=["Content-Type", "X-API-Key"],     # explicit whitelist
    expose_headers=[],
)

# ---------------------------------------------------------------------------
# Include routers with API key auth on every route
# ---------------------------------------------------------------------------
_auth = [Depends(verify_api_key)]

app.include_router(router, dependencies=_auth)
app.include_router(advanced_router, dependencies=_auth)
app.include_router(prediction_router, dependencies=_auth)


# ---------------------------------------------------------------------------
# Root endpoint  (no route enumeration)
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    """Minimal root endpoint — no route disclosure."""
    return {
        "name": "Vedic Astrology API",
        "version": "0.2.0",
        "status": "operational",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
