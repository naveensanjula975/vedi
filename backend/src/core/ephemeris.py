"""
Swiss Ephemeris integration for Vedic Astrology calculations.
Handles planetary positions with sidereal (Vedic) zodiac calculations.
"""

import swisseph as swe
from datetime import datetime
from typing import NamedTuple
from dataclasses import dataclass
import pytz
import logging

logger = logging.getLogger(__name__)

# Use the ephemeris data bundled with pyswisseph.  Passing an empty string
# (or the result of swe.get_library_path()) lets the library locate its own
# bundled .se1 files instead of searching a hard-coded filesystem path that
# would not exist on Heroku dynos.
try:
    swe.set_ephe_path('')
except Exception as _e:
    logger.warning("swe.set_ephe_path('') failed: %s — using default ephemeris path", _e)


class PlanetPosition(NamedTuple):
    """Represents a planet's position in the sidereal zodiac."""
    longitude: float
    latitude: float
    distance: float
    speed: float
    rashi: int           # 0-11 (Mesha to Meena)
    rashi_degree: float  # Degree within rashi
    nakshatra: int       # 0-26 (Ashwini to Revati)
    nakshatra_pada: int  # 1-4
    is_retrograde: bool


# Planet constants (Vedic order)
PLANETS = {
    'SUN': swe.SUN,
    'MOON': swe.MOON,
    'MARS': swe.MARS,
    'MERCURY': swe.MERCURY,
    'JUPITER': swe.JUPITER,
    'VENUS': swe.VENUS,
    'SATURN': swe.SATURN,
    'RAHU': swe.MEAN_NODE,  # True node: swe.TRUE_NODE
    'KETU': None,           # Calculated as Rahu + 180°
}

# Ayanamsa options
AYANAMSA = {
    'LAHIRI': swe.SIDM_LAHIRI,
    'KRISHNAMURTI': swe.SIDM_KRISHNAMURTI,
    'RAMAN': swe.SIDM_RAMAN,
}

# Nakshatra span in degrees (360° / 27)
NAKSHATRA_SPAN = 13.333333333333334


def datetime_to_jd(dt: datetime, timezone: str = "Etc/GMT+4") -> float:
    """Convert datetime to Julian Day number."""
    if dt.tzinfo is None:
        tz = pytz.timezone(timezone)
        dt = tz.localize(dt)
    
    # Convert to UTC
    utc_dt = dt.astimezone(pytz.UTC)
    
    # Calculate Julian Day
    jd = swe.julday(
        utc_dt.year,
        utc_dt.month,
        utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )
    return jd


class SiderealCalculator:
    """Calculator for sidereal (Vedic) astronomical positions."""
    
    def __init__(self, ayanamsa: str = 'LAHIRI'):
        """
        Initialize calculator with specified ayanamsa.
        
        Args:
            ayanamsa: Ayanamsa system to use ('LAHIRI', 'KRISHNAMURTI', 'RAMAN')
        """
        self.ayanamsa_name = ayanamsa
        swe.set_sid_mode(AYANAMSA[ayanamsa])
    
    def get_ayanamsa(self, jd: float) -> float:
        """Get ayanamsa value for given Julian Day."""
        return swe.get_ayanamsa(jd)
    
    def tropical_to_sidereal(self, tropical_lon: float, jd: float) -> float:
        """Convert tropical longitude to sidereal."""
        ayanamsa = self.get_ayanamsa(jd)
        sidereal = tropical_lon - ayanamsa
        return sidereal % 360
    
    def get_planet_position(self, planet_id: int, jd: float) -> tuple:
        """
        Get planetary position for a given Julian Day.
        
        Returns:
            tuple: (longitude, latitude, distance, speed_lon, speed_lat, speed_dist)
        """
        # Use sidereal flag for automatic sidereal calculation
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result, ret_flags = swe.calc_ut(jd, planet_id, flags)
        return result
    
    def get_ascendant(self, jd: float, latitude: float, longitude: float) -> float:
        """
        Calculate the Ascendant (Lagna) for given location and time.
        
        Args:
            jd: Julian Day number
            latitude: Geographic latitude
            longitude: Geographic longitude
            
        Returns:
            Sidereal longitude of the Ascendant
        """
        # Calculate houses using Placidus system
        cusps, ascmc = swe.houses(jd, latitude, longitude, b'P')
        
        # ascmc[0] is the Ascendant (tropical)
        tropical_asc = ascmc[0]
        
        # Convert to sidereal
        ayanamsa = self.get_ayanamsa(jd)
        sidereal_asc = (tropical_asc - ayanamsa) % 360
        
        return sidereal_asc


def get_planet_positions(
    dt: datetime,
    latitude: float,
    longitude: float,
    timezone: str = "Etc/GMT+4",
    ayanamsa: str = "LAHIRI"
) -> dict[str, PlanetPosition]:
    """
    Calculate positions of all planets for given birth data.
    
    Args:
        dt: Birth datetime
        latitude: Birth place latitude
        longitude: Birth place longitude
        timezone: Timezone string
        ayanamsa: Ayanamsa to use
        
    Returns:
        Dictionary of planet names to their positions
    """
    from .rashi import get_rashi
    from .nakshatra import get_nakshatra
    
    calculator = SiderealCalculator(ayanamsa)
    jd = datetime_to_jd(dt, timezone)
    
    positions = {}
    
    for planet_name, planet_id in PLANETS.items():
        if planet_name == 'KETU':
            # Ketu is always 180° from Rahu
            rahu_pos = positions['RAHU']
            ketu_lon = (rahu_pos.longitude + 180) % 360
            ketu_speed = rahu_pos.speed  # Same speed as Rahu
            
            rashi_idx, rashi_name, rashi_deg = get_rashi(ketu_lon)
            nak_info = get_nakshatra(ketu_lon)
            
            positions['KETU'] = PlanetPosition(
                longitude=ketu_lon,
                latitude=-rahu_pos.latitude,  # Opposite latitude
                distance=rahu_pos.distance,
                speed=ketu_speed,
                rashi=rashi_idx,
                rashi_degree=rashi_deg,
                nakshatra=nak_info['index'],
                nakshatra_pada=nak_info['pada'],
                is_retrograde=ketu_speed < 0
            )
        else:
            result = calculator.get_planet_position(planet_id, jd)
            lon, lat, dist, speed_lon = result[0], result[1], result[2], result[3]
            
            rashi_idx, rashi_name, rashi_deg = get_rashi(lon)
            nak_info = get_nakshatra(lon)
            
            positions[planet_name] = PlanetPosition(
                longitude=lon,
                latitude=lat,
                distance=dist,
                speed=speed_lon,
                rashi=rashi_idx,
                rashi_degree=rashi_deg,
                nakshatra=nak_info['index'],
                nakshatra_pada=nak_info['pada'],
                is_retrograde=speed_lon < 0
            )
    
    # Calculate Ascendant
    asc_lon = calculator.get_ascendant(jd, latitude, longitude)
    rashi_idx, rashi_name, rashi_deg = get_rashi(asc_lon)
    nak_info = get_nakshatra(asc_lon)
    
    positions['ASCENDANT'] = PlanetPosition(
        longitude=asc_lon,
        latitude=0.0,
        distance=0.0,
        speed=0.0,
        rashi=rashi_idx,
        rashi_degree=rashi_deg,
        nakshatra=nak_info['index'],
        nakshatra_pada=nak_info['pada'],
        is_retrograde=False
    )
    
    return positions


def calculate_navamsa(sidereal_longitude: float) -> int:
    """
    Calculate Navamsa (D-9) position.
    Each Navamsa = 3°20' (360° / 108 = 3.333°)
    
    Args:
        sidereal_longitude: Planet's sidereal longitude
        
    Returns:
        Navamsa rashi index (0-11)
    """
    navamsa_span = 360 / 108  # 3.333...
    navamsa_number = int(sidereal_longitude / navamsa_span)
    
    # Map to rashi (cycles through 12 signs)
    navamsa_rashi = navamsa_number % 12
    return navamsa_rashi

