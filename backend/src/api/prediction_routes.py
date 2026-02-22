"""
FastAPI routes for Dasha predictions.
Provides detailed predictions for all Dasha periods.

Security hardening applied:
    - detail=str(e) replaced with generic messages
    - Rate limiting on expensive endpoints
    - target_date uses typed Optional[datetime] instead of raw string
    - Service instantiated per-request (thread safety)
"""

import logging
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.schemas import BirthData
from ..services.prediction_service import PredictionService

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])

#  : NO module-level singleton — service is created per-request.


@router.post("/current")
async def get_current_prediction(
    request: Request,
    birth_data: BirthData,
    #  : typed datetime — Pydantic validates and returns 422 on bad input
    target_date: Optional[datetime] = Query(
        default=None,
        description="Target date in ISO 8601 format (e.g. 2026-01-15T10:30:00)",
    ),
):
    """
    Get detailed predictions for the currently running Dasha period.

    Returns predictions covering:
    - Health outlook and potential concerns
    - Wealth and financial prospects
    - Career and professional growth
    - Relationships and family life
    - General life themes and spiritual growth

    Plus remedies including gemstones, mantras, and favorable/unfavorable activities.
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_current_period_prediction(birth_data, target_date)
    except Exception:
        logger.exception("Error in get_current_prediction")
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.post("/mahadasha/{dasha_lord}")
async def get_mahadasha_prediction(
    request: Request,
    birth_data: BirthData,
    dasha_lord: Literal[
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu"
    ],
):
    """
    Get detailed predictions for a specific Mahadasha period.

    Each Mahadasha (major period) has distinct themes and effects
    on different life areas based on the ruling planet.
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_mahadasha_prediction(dasha_lord)
    except Exception:
        logger.exception("Error in get_mahadasha_prediction lord=%s", dasha_lord)
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.post("/antardasha/{mahadasha_lord}/{antardasha_lord}")
async def get_antardasha_prediction(
    request: Request,
    birth_data: BirthData,
    mahadasha_lord: Literal[
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu"
    ],
    antardasha_lord: Literal[
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu"
    ],
):
    """
    Get detailed predictions for a specific Mahadasha-Antardasha combination.

    The Antardasha (sub-period) modifies the effects of the Mahadasha
    based on the planetary relationship between the two lords.
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_antardasha_prediction(mahadasha_lord, antardasha_lord)
    except Exception:
        logger.exception(
            "Error in get_antardasha_prediction md=%s ad=%s",
            mahadasha_lord, antardasha_lord,
        )
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.post("/timeline")
@limiter.limit("10/minute")  #  : generates up to 9×120 period objects
async def get_timeline_with_predictions(
    request: Request,
    birth_data: BirthData,
    years_ahead: int = Query(
        default=80, ge=10, le=120, description="Years to calculate ahead"
    ),
):
    """
    Get complete Mahadasha timeline with predictions for each period.

    Returns:
    - Full Mahadasha sequence with start/end dates
    - Detailed predictions for each Mahadasha
    - All Antardasha periods within each Mahadasha
    - Summary predictions for each Antardasha
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_timeline_with_predictions(birth_data, years_ahead)
    except Exception:
        logger.exception("Error in get_timeline_with_predictions")
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.get("/all-dashas")
async def get_all_dasha_predictions(request: Request):
    """
    Get predictions for all 9 Dasha lords.

    Useful for understanding the general characteristics
    of each planetary period without specific birth data.
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_all_dasha_predictions()
    except Exception:
        logger.exception("Error in get_all_dasha_predictions")
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.get("/combination-matrix")
@limiter.limit("5/minute")  #  : generates 81 prediction lookups
async def get_combination_matrix(request: Request):
    """
    Get prediction summary for all 81 Mahadasha-Antardasha combinations.

    Returns a matrix showing the overall rating and trends
    for each possible planetary combination.
    """
    try:
        service = PredictionService()  #  : per-request
        return service.get_combination_matrix()
    except Exception:
        logger.exception("Error in get_combination_matrix")
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.post("/life-area/{area}")
async def get_life_area_prediction(
    request: Request,
    birth_data: BirthData,
    area: Literal["health", "wealth", "career", "relationships", "general"],
):
    """
    Get prediction for a specific life area for the current period.

    Areas:
    - health: Physical and mental health outlook
    - wealth: Financial prospects and money matters
    - career: Professional growth and job opportunities
    - relationships: Marriage, family, and social connections
    - general: Overall life themes and spiritual growth
    """
    try:
        service = PredictionService()  #  : per-request
        prediction = service.get_current_period_prediction(birth_data)

        if "predictions" in prediction and area in prediction["predictions"]:
            return {
                "area": area,
                "current_periods": prediction.get("current_periods", {}),
                "prediction": prediction["predictions"][area],
                "remedies": prediction.get("remedies", {}),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid life area: {area}")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error in get_life_area_prediction area=%s", area)
        raise HTTPException(status_code=500, detail="Internal server error.")  #  


@router.post("/remedies")
async def get_remedies(request: Request, birth_data: BirthData):
    """
    Get recommended remedies for the current Dasha period.

    Returns:
    - Gemstone recommendations
    - Mantras for the ruling planet
    - Deities to worship
    - Favorable and unfavorable activities
    - Area-specific remedies
    """
    try:
        service = PredictionService()  #  : per-request
        prediction = service.get_current_period_prediction(birth_data)

        remedies = {
            "current_periods": prediction.get("current_periods", {}),
            "gemstone": prediction.get("remedies", {}).get("gemstone"),
            "mantra": prediction.get("remedies", {}).get("mantra"),
            "deity": prediction.get("remedies", {}).get("deity"),
            "favorable_activities": prediction.get("favorable_activities", []),
            "unfavorable_activities": prediction.get("unfavorable_activities", []),
            "area_remedies": {},
        }

        for area, pred in prediction.get("predictions", {}).items():
            remedies["area_remedies"][area] = pred.get("remedies", [])

        return remedies
    except Exception:
        logger.exception("Error in get_remedies")
        raise HTTPException(status_code=500, detail="Internal server error.")  #  
