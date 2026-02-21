"""
FastAPI application entry point for Vedic Astrology API.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.advanced_routes import router as advanced_router
from .api.prediction_routes import router as prediction_router

# Create FastAPI app
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
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
# Production Vercel URL is always included as a hardcoded default.
# To add more URLs (e.g. preview deployments), set the CORS_ORIGINS env var
# on Heroku: heroku config:set CORS_ORIGINS="https://other-preview.vercel.app"
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(advanced_router)
app.include_router(prediction_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Vedic Astrology API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "features": {
            "core": "/api/v1/chart",
            "dasha": "/api/v1/dasha/timeline",
            "divisional": "/api/v1/advanced/divisional/{division}",
            "shadbala": "/api/v1/advanced/shadbala",
            "ashtakavarga": "/api/v1/advanced/ashtakavarga",
            "yogas": "/api/v1/advanced/yogas",
            "panchanga": "/api/v1/advanced/panchanga",
            "predictions": {
                "current": "/api/v1/predictions/current",
                "timeline": "/api/v1/predictions/timeline",
                "mahadasha": "/api/v1/predictions/mahadasha/{lord}",
                "antardasha": "/api/v1/predictions/antardasha/{md_lord}/{ad_lord}",
                "remedies": "/api/v1/predictions/remedies"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

