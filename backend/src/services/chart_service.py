"""
Chart calculation service - orchestrates all astronomical calculations.
"""

from datetime import datetime, timezone
from typing import Optional

from ..core.ephemeris import get_planet_positions, SiderealCalculator, datetime_to_jd
from ..core.rashi import RASHIS, get_rashi
from ..core.nakshatra import get_nakshatra, NAKSHATRAS
from ..core.dasha import VimshottariDasha
from ..models.schemas import (
    BirthData,
    PlanetPositionResponse,
    NakshatraInfo,
    DashaPeriod,
    AntardashaPeriod,
    PratyantardashaPeriod,
    CurrentDashaResponse,
    DashaWithAntardashas,
    DashaTimelineResponse,
    ChartResponse,
    TransitResponse,
)


class ChartService:
    """Service for calculating Vedic astrology charts."""
    
    def __init__(self):
        pass
    
    def _position_to_response(
        self, 
        planet_name: str, 
        position
    ) -> PlanetPositionResponse:
        """Convert internal position to API response model."""
        nakshatra_info = get_nakshatra(position.longitude)
        
        return PlanetPositionResponse(
            planet=planet_name,
            longitude=round(position.longitude, 6),
            latitude=round(position.latitude, 6),
            rashi=RASHIS[position.rashi],
            rashi_index=position.rashi,
            rashi_degree=round(position.rashi_degree, 4),
            nakshatra=nakshatra_info['name'],
            nakshatra_index=position.nakshatra,
            nakshatra_pada=position.nakshatra_pada,
            is_retrograde=position.is_retrograde,
            speed=round(position.speed, 6)
        )
    
    def calculate_planet_positions(
        self, 
        birth_data: BirthData
    ) -> tuple[list[PlanetPositionResponse], PlanetPositionResponse]:
        """
        Calculate all planet positions for birth data.
        
        Returns:
            Tuple of (planet_positions, ascendant)
        """
        positions = get_planet_positions(
            dt=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone=birth_data.timezone,
            ayanamsa=birth_data.ayanamsa
        )
        
        planet_responses = []
        ascendant = None
        
        for planet_name, position in positions.items():
            response = self._position_to_response(planet_name, position)
            
            if planet_name == 'ASCENDANT':
                ascendant = response
            else:
                planet_responses.append(response)
        
        return planet_responses, ascendant
    
    def get_moon_nakshatra(self, birth_data: BirthData) -> NakshatraInfo:
        """Get Moon's nakshatra (Janma Nakshatra)."""
        positions = get_planet_positions(
            dt=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone=birth_data.timezone,
            ayanamsa=birth_data.ayanamsa
        )
        
        moon_position = positions['MOON']
        nakshatra_info = get_nakshatra(moon_position.longitude)
        
        return NakshatraInfo(
            index=nakshatra_info['index'],
            name=nakshatra_info['name'],
            lord=nakshatra_info['lord'],
            pada=nakshatra_info['pada'],
            degree=round(nakshatra_info['degree'], 4),
            deity=nakshatra_info['deity'],
            symbol=nakshatra_info['symbol'],
            gana=nakshatra_info['gana']
        )
    
    def _create_dasha_calculator(self, birth_data: BirthData) -> VimshottariDasha:
        """Create dasha calculator for birth data."""
        positions = get_planet_positions(
            dt=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone=birth_data.timezone,
            ayanamsa=birth_data.ayanamsa
        )
        
        moon_longitude = positions['MOON'].longitude
        return VimshottariDasha(moon_longitude, birth_data.date)
    
    def get_dasha_timeline(
        self, 
        birth_data: BirthData,
        years_ahead: int = 120
    ) -> DashaTimelineResponse:
        """
        Get complete Mahadasha/Antardasha timeline.
        
        Args:
            birth_data: Birth information
            years_ahead: How many years to generate
            
        Returns:
            Complete dasha timeline response
        """
        dasha_calc = self._create_dasha_calculator(birth_data)
        moon_nakshatra = self.get_moon_nakshatra(birth_data)
        
        # Get balance info
        balance = dasha_calc.calculate_dasha_balance()
        
        # Generate full timeline with antardashas
        full_timeline = dasha_calc.get_full_timeline_with_antardashas(years_ahead)
        
        timeline_response = []
        for item in full_timeline:
            md = item['mahadasha']
            mahadasha = DashaPeriod(
                lord=md['lord'],
                start=md['start'],
                end=md['end'],
                duration_years=md['years'],
                duration_days=md['years'] * 365.25,
                is_birth_dasha=md['is_birth_dasha']
            )
            
            antardashas = [
                AntardashaPeriod(
                    lord=ad['lord'],
                    start=ad['start'],
                    end=ad['end'],
                    duration_days=ad['days'],
                    mahadasha_lord=md['lord']
                )
                for ad in item['antardashas']
            ]
            
            timeline_response.append(DashaWithAntardashas(
                mahadasha=mahadasha,
                antardashas=antardashas
            ))
        
        return DashaTimelineResponse(
            birth_data=birth_data,
            moon_nakshatra=moon_nakshatra,
            birth_dasha_lord=balance['lord'],
            dasha_balance={
                'total_years': balance['total_years'],
                'elapsed_years': round(balance['elapsed_years'], 4),
                'remaining_years': round(balance['remaining_years'], 4),
                'remaining_days': round(balance['remaining_days'], 2)
            },
            timeline=timeline_response
        )
    
    def get_current_periods(
        self, 
        birth_data: BirthData,
        target_date: Optional[datetime] = None
    ) -> CurrentDashaResponse:
        """
        Get currently running Dasha/Antardasha/Pratyantardasha.
        
        Args:
            birth_data: Birth information
            target_date: Date to check (default: now)
            
        Returns:
            Current periods response
        """
        if target_date is None:
            target_date = datetime.now(tz=timezone.utc)  # TASK-008: timezone-aware
        
        dasha_calc = self._create_dasha_calculator(birth_data)
        current = dasha_calc.get_current_periods(target_date)
        
        if 'error' in current:
            raise ValueError(current['error'])
        
        mahadasha = DashaPeriod(
            lord=current['mahadasha']['lord'],
            start=current['mahadasha']['start'],
            end=current['mahadasha']['end'],
            duration_years=current['mahadasha']['years'],
            duration_days=current['mahadasha']['years'] * 365.25,
            is_birth_dasha=False
        )
        
        antardasha = AntardashaPeriod(
            lord=current['antardasha']['lord'],
            start=current['antardasha']['start'],
            end=current['antardasha']['end'],
            duration_days=current['antardasha']['days'],
            mahadasha_lord=current['mahadasha']['lord']
        )
        
        pratyantardasha = None
        if current.get('pratyantardasha'):
            pd = current['pratyantardasha']
            pratyantardasha = PratyantardashaPeriod(
                lord=pd['lord'],
                start=pd['start'],
                end=pd['end'],
                duration_days=pd['days'],
                mahadasha_lord=current['mahadasha']['lord'],
                antardasha_lord=current['antardasha']['lord']
            )
        
        return CurrentDashaResponse(
            target_date=target_date,
            mahadasha=mahadasha,
            antardasha=antardasha,
            pratyantardasha=pratyantardasha
        )
    
    def calculate_full_chart(self, birth_data: BirthData) -> ChartResponse:
        """
        Generate complete Vedic birth chart with Dasha.
        
        Args:
            birth_data: Birth information
            
        Returns:
            Complete chart response
        """
        # Calculate positions
        planets, ascendant = self.calculate_planet_positions(birth_data)
        
        # Get Moon nakshatra
        moon_nakshatra = self.get_moon_nakshatra(birth_data)
        
        # Get current dasha
        current_dasha = self.get_current_periods(birth_data)
        
        # Get mahadasha timeline (simplified, without antardashas)
        dasha_calc = self._create_dasha_calculator(birth_data)
        mahadashas = dasha_calc.generate_mahadasha_timeline(years_ahead=120)
        
        mahadasha_timeline = [
            DashaPeriod(
                lord=md.lord,
                start=md.start,
                end=md.end,
                duration_years=md.years,
                duration_days=md.days,
                is_birth_dasha=md.is_birth_dasha
            )
            for md in mahadashas
        ]
        
        # Get ayanamsa value
        calculator = SiderealCalculator(birth_data.ayanamsa)
        jd = datetime_to_jd(birth_data.date, birth_data.timezone)
        ayanamsa_value = calculator.get_ayanamsa(jd)
        
        return ChartResponse(
            birth_data=birth_data,
            ayanamsa_value=round(ayanamsa_value, 6),
            planets=planets,
            ascendant=ascendant,
            moon_nakshatra=moon_nakshatra,
            current_dasha=current_dasha,
            mahadasha_timeline=mahadasha_timeline
        )
    
    def calculate_transits(
        self, 
        birth_data: BirthData,
        transit_date: datetime
    ) -> TransitResponse:
        """
        Get planetary transits for a specific date.
        
        Args:
            birth_data: Birth information
            transit_date: Date to calculate transits
            
        Returns:
            Transit response with natal and transit positions
        """
        # Get natal positions
        natal_planets, _ = self.calculate_planet_positions(birth_data)
        
        # Create transit birth data (same location, different time)
        transit_birth = BirthData(
            date=transit_date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone=birth_data.timezone,
            ayanamsa=birth_data.ayanamsa
        )
        
        # Get transit positions
        transit_planets, _ = self.calculate_planet_positions(transit_birth)
        
        return TransitResponse(
            transit_date=transit_date,
            natal_positions=natal_planets,
            transit_positions=transit_planets
        )

