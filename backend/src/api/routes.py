"""
FastAPI routes for Vedic Astrology API.

Security hardening applied:
  detail=str(e) replaced with generic messages
  Rate limiting applied to expensive endpoints
  datetime.now() replaced with timezone-aware UTC calls
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.schemas import (
    BirthData,
    ChartResponse,
    DashaTimelineResponse,
    CurrentDashaResponse,
    TransitRequest,
    TransitResponse,
    HealthResponse,
)
from ..services.chart_service import ChartService

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1", tags=["astrology"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(tz=timezone.utc),  
    )


@router.post("/chart", response_model=ChartResponse)
async def generate_chart(request: Request, birth_data: BirthData):
    """
    Generate complete Vedic birth chart with Dasha.

    This endpoint calculates:
    - All planetary positions in sidereal zodiac
    - Ascendant (Lagna)
    - Moon's nakshatra (Janma Nakshatra)
    - Current running Dasha/Antardasha/Pratyantardasha
    - Complete Mahadasha timeline
    """
    try:
        service = ChartService()
        return service.calculate_full_chart(birth_data)
    except Exception:
        logger.exception("Error in generate_chart for birth_data=%s", birth_data.date)
        raise HTTPException(status_code=500, detail="Internal server error.")  


@router.post("/dasha/timeline", response_model=DashaTimelineResponse)
@limiter.limit("30/minute")  
async def get_dasha_timeline(
    request: Request,
    birth_data: BirthData,
    years_ahead: int = Query(default=120, ge=1, le=200, description="Years to generate"),
):
    """
    Get complete Mahadasha/Antardasha timeline.

    Returns the full Vimshottari Dasha timeline with nested Antardashas
    for the specified number of years from birth.
    """
    try:
        service = ChartService()
        return service.get_dasha_timeline(birth_data, years_ahead)
    except Exception:
        logger.exception("Error in get_dasha_timeline")
        raise HTTPException(status_code=500, detail="Internal server error.")  


@router.post("/dasha/current", response_model=CurrentDashaResponse)
async def get_current_dasha(
    request: Request,
    birth_data: BirthData,
    target_date: Optional[datetime] = Query(
        default=None,
        description="Date to check (default: now, ISO 8601 format)",
    ),
):
    """
    Get currently running Dasha/Antardasha/Pratyantardasha.

    Returns the active periods for the specified target date
    (or current UTC time if not specified).
    """
    try:
        service = ChartService()
        return service.get_current_periods(birth_data, target_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # safe domain message
    except Exception:
        logger.exception("Error in get_current_dasha")
        raise HTTPException(status_code=500, detail="Internal server error.")  


@router.post("/transit", response_model=TransitResponse)
async def get_transits(request: Request, transit_request: TransitRequest):
    """
    Get planetary transits for a specific date.

    Returns both natal positions and transit positions
    for comparison and analysis.
    """
    try:
        service = ChartService()
        return service.calculate_transits(
            transit_request.birth_data, transit_request.transit_date
        )
    except Exception:
        logger.exception("Error in get_transits")
        raise HTTPException(status_code=500, detail="Internal server error.")  


@router.post("/planets")
async def get_planet_positions(request: Request, birth_data: BirthData):
    """
    Get only planetary positions (without Dasha calculations).

    Faster endpoint when you only need planet positions.
    """
    try:
        service = ChartService()
        planets, ascendant = service.calculate_planet_positions(birth_data)
        return {"planets": planets, "ascendant": ascendant}
    except Exception:
        logger.exception("Error in get_planet_positions")
        raise HTTPException(status_code=500, detail="Internal server error.")  


@router.post("/nakshatra")
async def get_moon_nakshatra(request: Request, birth_data: BirthData):
    """
    Get Moon's nakshatra (Janma Nakshatra) details.

    Returns detailed nakshatra information including
    deity, symbol, and gana.
    """
    try:
        service = ChartService()
        return service.get_moon_nakshatra(birth_data)
    except Exception:
        logger.exception("Error in get_moon_nakshatra")
        raise HTTPException(status_code=500, detail="Internal server error.")  
