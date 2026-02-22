"""
Vimshottari Dasha System for Vedic Astrology.
Calculates Mahadasha, Antardasha, and Pratyantardasha periods.
"""

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional
from dataclasses import dataclass

from .nakshatra import get_nakshatra, NAKSHATRA_SPAN


# Vimshottari Dasha periods (in years)
DASHA_YEARS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17
}

# Dasha sequence (fixed order starting from Ketu)
DASHA_SEQUENCE = [
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
    'Rahu', 'Jupiter', 'Saturn', 'Mercury'
]

# Total dasha cycle length
TOTAL_DASHA_YEARS = 120  # Sum of all dasha periods

# Days per year (accounting for leap years)
DAYS_PER_YEAR = 365.25


@dataclass
class DashaPeriodInfo:
    """Represents a dasha period."""
    lord: str
    start: datetime
    end: datetime
    years: float
    days: float
    is_birth_dasha: bool = False
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a date falls within this period."""
        return self.start <= date <= self.end


@dataclass
class AntardashaPeriodInfo:
    """Represents an antardasha (sub-period)."""
    lord: str
    start: datetime
    end: datetime
    days: float
    mahadasha_lord: str
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a date falls within this period."""
        return self.start <= date <= self.end


@dataclass
class PratyantardashaPeriodInfo:
    """Represents a pratyantardasha (sub-sub-period)."""
    lord: str
    start: datetime
    end: datetime
    days: float
    mahadasha_lord: str
    antardasha_lord: str
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a date falls within this period."""
        return self.start <= date <= self.end


class VimshottariDasha:
    """Calculator for Vimshottari Dasha system."""
    
    def __init__(self, moon_longitude: float, birth_datetime: datetime):
        """
        Initialize dasha calculator.
        
        Args:
            moon_longitude: Moon's sidereal longitude at birth
            birth_datetime: Birth date and time
        """
        self.moon_longitude = moon_longitude
        self.birth_dt = birth_datetime
        self.nakshatra = get_nakshatra(moon_longitude)
    
    def get_birth_dasha_lord(self) -> str:
        """
        Get the Mahadasha lord at birth based on Moon's nakshatra.
        
        Returns:
            Name of the dasha lord at birth
        """
        return self.nakshatra['lord']
    
    def get_elapsed_dasha_portion(self) -> float:
        """
        Calculate how much of the birth dasha has elapsed.
        Based on Moon's position within the nakshatra.
        
        Returns:
            Fraction of dasha elapsed (0 to 1)
        """
        nak_degree = self.nakshatra['degree']
        elapsed_fraction = nak_degree / NAKSHATRA_SPAN
        return elapsed_fraction
    
    def calculate_dasha_balance(self) -> dict:
        """
        Calculate remaining dasha period at birth.
        
        Returns:
            Dictionary with dasha balance information
        """
        birth_lord = self.get_birth_dasha_lord()
        total_years = DASHA_YEARS[birth_lord]
        elapsed_fraction = self.get_elapsed_dasha_portion()
        
        remaining_years = total_years * (1 - elapsed_fraction)
        remaining_days = remaining_years * DAYS_PER_YEAR
        end_date = self.birth_dt + timedelta(days=remaining_days)
        
        return {
            'lord': birth_lord,
            'total_years': total_years,
            'elapsed_fraction': elapsed_fraction,
            'elapsed_years': total_years * elapsed_fraction,
            'remaining_years': remaining_years,
            'remaining_days': remaining_days,
            'end_date': end_date
        }
    
    def generate_mahadasha_timeline(self, years_ahead: int = 120) -> list[DashaPeriodInfo]:
        """
        Generate complete Mahadasha timeline from birth.
        
        Args:
            years_ahead: How many years to generate (default: full 120-year cycle)
            
        Returns:
            List of DashaPeriodInfo objects
        """
        timeline = []
        balance = self.calculate_dasha_balance()
        
        # First dasha (partial)
        first_dasha = DashaPeriodInfo(
            lord=balance['lord'],
            start=self.birth_dt,
            end=balance['end_date'],
            years=balance['remaining_years'],
            days=balance['remaining_days'],
            is_birth_dasha=True
        )
        timeline.append(first_dasha)
        
        # Get sequence position
        start_idx = DASHA_SEQUENCE.index(balance['lord'])
        current_date = balance['end_date']
        
        # Calculate how many complete cycles we need
        max_date = self.birth_dt + relativedelta(years=years_ahead)
        
        # Generate subsequent dashas
        cycle = 1
        while current_date < max_date:
            lord_idx = (start_idx + cycle) % 9
            lord = DASHA_SEQUENCE[lord_idx]
            years = DASHA_YEARS[lord]
            days = years * DAYS_PER_YEAR
            end_date = current_date + timedelta(days=days)
            
            timeline.append(DashaPeriodInfo(
                lord=lord,
                start=current_date,
                end=end_date,
                years=years,
                days=days,
                is_birth_dasha=False
            ))
            
            current_date = end_date
            cycle += 1
        
        return timeline
    
    def calculate_antardasha(
        self, 
        mahadasha: DashaPeriodInfo
    ) -> list[AntardashaPeriodInfo]:
        """
        Calculate Antardasha periods within a Mahadasha.
        
        Formula: Antardasha days = (Mahadasha years × Antardasha years × 365.25) / 120
        
        Args:
            mahadasha: The Mahadasha period to subdivide
            
        Returns:
            List of AntardashaPeriodInfo objects
        """
        antardashas = []
        md_lord = mahadasha.lord
        md_years = mahadasha.years
        
        # Antardasha sequence starts from Mahadasha lord
        start_idx = DASHA_SEQUENCE.index(md_lord)
        current_date = mahadasha.start
        
        for i in range(9):
            ad_lord_idx = (start_idx + i) % 9
            ad_lord = DASHA_SEQUENCE[ad_lord_idx]
            ad_base_years = DASHA_YEARS[ad_lord]
            
            # Proportional calculation
            ad_days = (md_years * ad_base_years * DAYS_PER_YEAR) / TOTAL_DASHA_YEARS
            end_date = current_date + timedelta(days=ad_days)
            
            antardashas.append(AntardashaPeriodInfo(
                lord=ad_lord,
                start=current_date,
                end=end_date,
                days=ad_days,
                mahadasha_lord=md_lord
            ))
            
            current_date = end_date
        
        return antardashas
    
    def calculate_pratyantardasha(
        self, 
        antardasha: AntardashaPeriodInfo
    ) -> list[PratyantardashaPeriodInfo]:
        """
        Calculate Pratyantardasha periods within an Antardasha.
        
        Args:
            antardasha: The Antardasha period to subdivide
            
        Returns:
            List of PratyantardashaPeriodInfo objects
        """
        pratyantars = []
        ad_lord = antardasha.lord
        ad_days = antardasha.days
        
        # Pratyantardasha sequence starts from Antardasha lord
        start_idx = DASHA_SEQUENCE.index(ad_lord)
        current_date = antardasha.start
        
        for i in range(9):
            pd_lord_idx = (start_idx + i) % 9
            pd_lord = DASHA_SEQUENCE[pd_lord_idx]
            pd_base_years = DASHA_YEARS[pd_lord]
            
            # Further proportional breakdown
            pd_days = (ad_days * pd_base_years) / TOTAL_DASHA_YEARS
            end_date = current_date + timedelta(days=pd_days)
            
            pratyantars.append(PratyantardashaPeriodInfo(
                lord=pd_lord,
                start=current_date,
                end=end_date,
                days=pd_days,
                mahadasha_lord=antardasha.mahadasha_lord,
                antardasha_lord=ad_lord
            ))
            
            current_date = end_date
        
        return pratyantars
    
    def get_current_periods(
        self, 
        target_date: Optional[datetime] = None
    ) -> dict:
        """
        Get the currently running Mahadasha, Antardasha, and Pratyantardasha.
        
        Args:
            target_date: Date to check (default: now)
            
        Returns:
            Dictionary with current periods
        """
        if target_date is None:
            target_date = datetime.now(tz=timezone.utc)  # TASK-008: timezone-aware
        
        # Find current Mahadasha
        mahadashas = self.generate_mahadasha_timeline()
        current_md = None
        
        for md in mahadashas:
            if md.contains_date(target_date):
                current_md = md
                break
        
        if current_md is None:
            return {'error': 'Target date is outside the dasha timeline'}
        
        # Find current Antardasha
        antardashas = self.calculate_antardasha(current_md)
        current_ad = None
        
        for ad in antardashas:
            if ad.contains_date(target_date):
                current_ad = ad
                break
        
        if current_ad is None:
            return {'error': 'Could not find current Antardasha'}
        
        # Find current Pratyantardasha
        pratyantars = self.calculate_pratyantardasha(current_ad)
        current_pd = None
        
        for pd in pratyantars:
            if pd.contains_date(target_date):
                current_pd = pd
                break
        
        return {
            'target_date': target_date,
            'mahadasha': {
                'lord': current_md.lord,
                'start': current_md.start,
                'end': current_md.end,
                'years': current_md.years
            },
            'antardasha': {
                'lord': current_ad.lord,
                'start': current_ad.start,
                'end': current_ad.end,
                'days': current_ad.days
            },
            'pratyantardasha': {
                'lord': current_pd.lord if current_pd else None,
                'start': current_pd.start if current_pd else None,
                'end': current_pd.end if current_pd else None,
                'days': current_pd.days if current_pd else None
            } if current_pd else None
        }
    
    def get_full_timeline_with_antardashas(
        self, 
        years_ahead: int = 120
    ) -> list[dict]:
        """
        Generate complete timeline with nested Antardashas.
        
        Args:
            years_ahead: How many years to generate
            
        Returns:
            List of dictionaries with Mahadashas and their Antardashas
        """
        mahadashas = self.generate_mahadasha_timeline(years_ahead)
        
        result = []
        for md in mahadashas:
            antardashas = self.calculate_antardasha(md)
            
            result.append({
                'mahadasha': {
                    'lord': md.lord,
                    'start': md.start,
                    'end': md.end,
                    'years': md.years,
                    'is_birth_dasha': md.is_birth_dasha
                },
                'antardashas': [
                    {
                        'lord': ad.lord,
                        'start': ad.start,
                        'end': ad.end,
                        'days': ad.days
                    }
                    for ad in antardashas
                ]
            })
        
        return result

