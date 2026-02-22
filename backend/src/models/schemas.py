"""
Pydantic models for API request/response validation.

Security hardening applied:
    - timezone validated against IANA list (no raw pytz errors leaked)
    - name field capped at 100 characters
"""

import pytz
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, field_validator


class BirthData(BaseModel):
    """Input data for birth chart calculation."""
    date: datetime = Field(..., description="Birth date and time")
    latitude: float = Field(..., ge=-90, le=90, description="Birth place latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Birth place longitude")
    timezone: str = Field(
        default="Asia/Kolkata",
        description="IANA timezone string (e.g., 'Asia/Kolkata', 'America/New_York')",
    )
    ayanamsa: Literal["LAHIRI", "KRISHNAMURTI", "RAMAN"] = Field(
        default="LAHIRI",
        description="Ayanamsa system to use",
    )
    #  : cap name at 100 chars — it is echoed back in every response
    name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional name of the person (max 100 characters)",
    )

    #  : validate timezone against the full IANA database
    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        if v not in pytz.all_timezones_set:
            raise ValueError(
                f"Invalid timezone '{v}'. "
                "Please provide an IANA timezone string such as 'Asia/Kolkata' or 'America/New_York'."
            )
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "1990-05-15T10:30:00",
                    "latitude": 28.6139,
                    "longitude": 77.2090,
                    "timezone": "Asia/Kolkata",
                    "ayanamsa": "LAHIRI",
                    "name": "Example Person"
                }
            ]
        }
    }


class NakshatraInfo(BaseModel):
    """Nakshatra information."""
    index: int = Field(..., ge=0, le=26)
    name: str
    lord: str
    pada: int = Field(..., ge=1, le=4)
    degree: float
    deity: Optional[str] = None
    symbol: Optional[str] = None
    gana: Optional[str] = None


class PlanetPositionResponse(BaseModel):
    """Response model for planet position."""
    planet: str
    longitude: float
    latitude: float
    rashi: str
    rashi_index: int = Field(..., ge=0, le=11)
    rashi_degree: float
    nakshatra: str
    nakshatra_index: int = Field(..., ge=0, le=26)
    nakshatra_pada: int = Field(..., ge=1, le=4)
    is_retrograde: bool
    speed: float
    

class DashaPeriod(BaseModel):
    """Response model for a Mahadasha period."""
    lord: str
    start: datetime
    end: datetime
    duration_years: float
    duration_days: float
    is_birth_dasha: bool = False
    

class AntardashaPeriod(BaseModel):
    """Response model for an Antardasha period."""
    lord: str
    start: datetime
    end: datetime
    duration_days: float
    mahadasha_lord: str


class PratyantardashaPeriod(BaseModel):
    """Response model for a Pratyantardasha period."""
    lord: str
    start: datetime
    end: datetime
    duration_days: float
    mahadasha_lord: str
    antardasha_lord: str


class CurrentDashaResponse(BaseModel):
    """Response model for current running periods."""
    target_date: datetime
    mahadasha: DashaPeriod
    antardasha: AntardashaPeriod
    pratyantardasha: Optional[PratyantardashaPeriod] = None


class DashaWithAntardashas(BaseModel):
    """Mahadasha with nested Antardashas."""
    mahadasha: DashaPeriod
    antardashas: list[AntardashaPeriod]


class DashaTimelineResponse(BaseModel):
    """Response model for complete dasha timeline."""
    birth_data: BirthData
    moon_nakshatra: NakshatraInfo
    birth_dasha_lord: str
    dasha_balance: dict
    timeline: list[DashaWithAntardashas]


class ChartResponse(BaseModel):
    """Response model for complete birth chart."""
    birth_data: BirthData
    ayanamsa_value: float
    planets: list[PlanetPositionResponse]
    ascendant: PlanetPositionResponse
    moon_nakshatra: NakshatraInfo
    current_dasha: CurrentDashaResponse
    mahadasha_timeline: list[DashaPeriod]


class TransitRequest(BaseModel):
    """Request model for transit calculation."""
    birth_data: BirthData
    transit_date: datetime = Field(..., description="Date to calculate transits for")


class TransitResponse(BaseModel):
    """Response model for planetary transits."""
    transit_date: datetime
    natal_positions: list[PlanetPositionResponse]
    transit_positions: list[PlanetPositionResponse]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime

