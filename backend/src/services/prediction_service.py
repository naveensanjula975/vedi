"""
Prediction Service for Dasha periods.
Integrates with the Dasha engine to provide detailed predictions.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from ..core.ephemeris import get_planet_positions
from ..core.dasha import VimshottariDasha
from ..core.predictions import DashaPredictionEngine, DashaPrediction
from ..models.schemas import BirthData


class PredictionService:
    """Service for generating Dasha predictions."""
    
    def __init__(self):
        self.prediction_engine = DashaPredictionEngine()
    
    def _get_moon_longitude(self, birth_data: BirthData) -> float:
        """Get Moon's longitude from birth data."""
        positions = get_planet_positions(
            dt=birth_data.date,
            latitude=birth_data.latitude,
            longitude=birth_data.longitude,
            timezone=birth_data.timezone,
            ayanamsa=birth_data.ayanamsa
        )
        return positions['MOON'].longitude
    
    def get_mahadasha_prediction(self, dasha_lord: str) -> Dict[str, Any]:
        """Get detailed prediction for a Mahadasha period."""
        prediction = self.prediction_engine.generate_complete_prediction(dasha_lord)
        return self._format_prediction(prediction)
    
    def get_antardasha_prediction(self, mahadasha_lord: str, 
                                  antardasha_lord: str) -> Dict[str, Any]:
        """Get detailed prediction for an Antardasha period."""
        prediction = self.prediction_engine.generate_complete_prediction(
            mahadasha_lord, 
            antardasha_lord
        )
        return self._format_prediction(prediction)
    
    def get_pratyantardasha_prediction(self, mahadasha_lord: str,
                                       antardasha_lord: str,
                                       pratyantardasha_lord: str) -> Dict[str, Any]:
        """Get detailed prediction for a Pratyantardasha period."""
        prediction = self.prediction_engine.generate_complete_prediction(
            mahadasha_lord,
            antardasha_lord,
            pratyantardasha_lord
        )
        return self._format_prediction(prediction)
    
    def get_current_period_prediction(self, birth_data: BirthData,
                                      target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get prediction for the current running Dasha period."""
        moon_lon = self._get_moon_longitude(birth_data)
        dasha = VimshottariDasha(moon_lon, birth_data.date)
        
        if target_date is None:
            target_date = datetime.now(tz=timezone.utc)  # TASK-008: timezone-aware
        
        current = dasha.get_current_periods(target_date)
        
        if not current:
            return {"error": "Could not determine current dasha periods"}
        
        mahadasha_lord = current['mahadasha']['lord']
        antardasha_lord = current.get('antardasha', {}).get('lord')
        pratyantardasha_lord = current.get('pratyantardasha', {}).get('lord')
        
        prediction = self.prediction_engine.generate_complete_prediction(
            mahadasha_lord,
            antardasha_lord,
            pratyantardasha_lord
        )
        
        result = self._format_prediction(prediction)
        
        # Add period information
        result['current_periods'] = {
            'mahadasha': {
                'lord': mahadasha_lord,
                'start': current['mahadasha']['start'].isoformat(),
                'end': current['mahadasha']['end'].isoformat()
            }
        }
        
        if antardasha_lord:
            result['current_periods']['antardasha'] = {
                'lord': antardasha_lord,
                'start': current['antardasha']['start'].isoformat(),
                'end': current['antardasha']['end'].isoformat()
            }
        
        if pratyantardasha_lord:
            result['current_periods']['pratyantardasha'] = {
                'lord': pratyantardasha_lord,
                'start': current['pratyantardasha']['start'].isoformat(),
                'end': current['pratyantardasha']['end'].isoformat()
            }
        
        return result
    
    def get_timeline_with_predictions(self, birth_data: BirthData,
                                      years_ahead: int = 80) -> List[Dict[str, Any]]:
        """Get complete Mahadasha timeline with predictions for each period."""
        moon_lon = self._get_moon_longitude(birth_data)
        dasha = VimshottariDasha(moon_lon, birth_data.date)
        
        timeline = dasha.generate_mahadasha_timeline()
        
        result = []
        for md in timeline:
            md_lord = md['lord']
            prediction = self.prediction_engine.generate_complete_prediction(md_lord)
            
            # Get Antardasha periods
            antardashas = dasha.calculate_antardasha(md)
            antardasha_list = []
            
            for ad in antardashas:
                ad_lord = ad['lord']
                ad_prediction = self.prediction_engine.generate_complete_prediction(
                    md_lord, ad_lord
                )
                
                antardasha_list.append({
                    'lord': ad_lord,
                    'start': ad['start'].isoformat(),
                    'end': ad['end'].isoformat(),
                    'days': round(ad['days'], 1),
                    'prediction_summary': {
                        'overall_theme': ad_prediction.overall_theme,
                        'overall_rating': ad_prediction.overall_rating,
                        'health': {
                            'trend': ad_prediction.predictions['health'].trend,
                            'summary': ad_prediction.predictions['health'].summary
                        },
                        'wealth': {
                            'trend': ad_prediction.predictions['wealth'].trend,
                            'summary': ad_prediction.predictions['wealth'].summary
                        },
                        'career': {
                            'trend': ad_prediction.predictions['career'].trend,
                            'summary': ad_prediction.predictions['career'].summary
                        },
                        'relationships': {
                            'trend': ad_prediction.predictions['relationships'].trend,
                            'summary': ad_prediction.predictions['relationships'].summary
                        },
                        'favorable_activities': ad_prediction.favorable_activities[:3],
                        'remedies': {
                            'gemstone': ad_prediction.gemstone,
                            'mantra': ad_prediction.mantra,
                            'deity': ad_prediction.deity
                        }
                    }
                })
            
            result.append({
                'lord': md_lord,
                'start': md['start'].isoformat(),
                'end': md['end'].isoformat(),
                'years': round(md['years'], 2),
                'is_birth_dasha': md.get('is_birth_dasha', False),
                'prediction': self._format_prediction(prediction),
                'antardashas': antardasha_list
            })
        
        return result
    
    def _format_prediction(self, prediction: DashaPrediction) -> Dict[str, Any]:
        """Format a DashaPrediction into a dictionary."""
        formatted_predictions = {}
        
        for area, pred in prediction.predictions.items():
            formatted_predictions[area] = {
                'trend': pred.trend,
                'intensity': pred.intensity,
                'summary': pred.summary,
                'details': pred.details,
                'remedies': pred.remedies,
                'keywords': pred.keywords
            }
        
        return {
            'dasha_lord': prediction.dasha_lord,
            'period_type': prediction.period_type,
            'overall_theme': prediction.overall_theme,
            'overall_rating': prediction.overall_rating,
            'predictions': formatted_predictions,
            'favorable_activities': prediction.favorable_activities,
            'unfavorable_activities': prediction.unfavorable_activities,
            'important_transits': prediction.important_transits,
            'remedies': {
                'gemstone': prediction.gemstone,
                'mantra': prediction.mantra,
                'deity': prediction.deity
            }
        }
    
    def get_all_dasha_predictions(self) -> Dict[str, Dict[str, Any]]:
        """Get predictions for all 9 Dasha lords."""
        dasha_lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 
                       'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        return {
            lord: self.get_mahadasha_prediction(lord)
            for lord in dasha_lords
        }
    
    def get_combination_matrix(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get prediction matrix for all Mahadasha-Antardasha combinations."""
        dasha_lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
                       'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        matrix = {}
        for md_lord in dasha_lords:
            matrix[md_lord] = {}
            for ad_lord in dasha_lords:
                prediction = self.prediction_engine.generate_complete_prediction(
                    md_lord, ad_lord
                )
                # Include just summary for the matrix
                matrix[md_lord][ad_lord] = {
                    'overall_theme': prediction.overall_theme,
                    'overall_rating': prediction.overall_rating,
                    'health_trend': prediction.predictions['health'].trend,
                    'wealth_trend': prediction.predictions['wealth'].trend,
                    'career_trend': prediction.predictions['career'].trend,
                    'relationships_trend': prediction.predictions['relationships'].trend,
                }
        
        return matrix

