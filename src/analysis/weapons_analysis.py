"""
Weapons in Serious Crimes Analysis module.
Analyzes weapon usage patterns in serious crimes with ethical constraints.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaponsAnalyzer:
    """Analyzes weapon patterns in serious crimes with ethical safeguards."""
    
    def __init__(self):
        self.weapon_categories = ['firearm', 'knife', 'blunt_object', 'none', 'unknown', 'other']
        
    def analyze_weapon_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze weapon usage patterns in serious crimes.
        
        Args:
            df: DataFrame with weapon and severity features
            
        Returns:
            Dictionary with weapon analysis results
        """
        results = {
            'method': 'weapons_in_serious_crimes_analysis',
            'ethical_note': 'Analysis is aggregate-only and avoids tactical insights',
            'limitations': 'Subject to reporting bias and missing data limitations'
        }
        
        # Filter for serious crimes only
        serious_crimes_df = df[df['severity_flag'] == True].copy()
        
        if len(serious_crimes_df) == 0:
            results['error'] = 'No serious crimes found in dataset'
            return results
        
        results['total_serious_crimes'] = len(serious_crimes_df)
        results['total_all_crimes'] = len(df)
        results['serious_crime_percentage'] = (len(serious_crimes_df) / len(df)) * 100
        
        # Weapon distribution in serious crimes
        weapon_dist = self._analyze_weapon_distribution(serious_crimes_df)
        results['weapon_distribution'] = weapon_dist
        
        # Temporal trends
        temporal_trends = self._analyze_temporal_trends(serious_crimes_df)
        results['temporal_trends'] = temporal_trends
        
        # Regional patterns
        regional_patterns = self._analyze_regional_patterns(serious_crimes_df)
        results['regional_patterns'] = regional_patterns
        
        # Data quality metrics
        data_quality = self._analyze_data_quality(serious_crimes_df)
        results['data_quality'] = data_quality
        
        # Comparison with all crimes (if requested)
        comparison = self._compare_serious_vs_all_crimes(df, serious_crimes_df)
        results['serious_vs_all_comparison'] = comparison
        
        logger.info(f"Weapons analysis complete for {len(serious_crimes_df)} serious crimes")
        return results
    
    def _analyze_weapon_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze distribution of weapon categories."""
        
        weapon_counts = df['weapon_category'].value_counts()
        weapon_percentages = (weapon_counts / len(df) * 100).round(2)
        
        return {
            'counts': weapon_counts.to_dict(),
            'percentages': weapon_percentages.to_dict(),
            'most_common': weapon_counts.index[0] if len(weapon_counts) > 0 else 'unknown',
            'least_common': weapon_counts.index[-1] if len(weapon_counts) > 0 else 'unknown'
        }
    
    def _analyze_temporal_trends(self, df: pd.DataFrame) -> Dict:
        """Analyze weapon usage trends over time."""
        
        if 'publication_year' not in df.columns:
            return {'error': 'No temporal data available'}
        
        # Yearly weapon trends
        yearly_trends = df.groupby(['publication_year', 'weapon_category']).size().unstack(fill_value=0)
        
        # Calculate percentages by year
        yearly_percentages = yearly_trends.div(yearly_trends.sum(axis=1), axis=0) * 100
        
        # Unknown weapon percentage over time
        unknown_trend = yearly_percentages.get('unknown', pd.Series()).to_dict()
        
        return {
            'yearly_counts': yearly_trends.to_dict(),
            'yearly_percentages': yearly_percentages.to_dict(),
            'unknown_weapon_trend': unknown_trend,
            'years_analyzed': list(yearly_trends.index)
        }
    
    def _analyze_regional_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze weapon patterns by region."""
        
        if 'birth_region' not in df.columns:
            return {'error': 'No regional data available'}
        
        # Regional weapon distribution
        regional_dist = df.groupby(['birth_region', 'weapon_category']).size().unstack(fill_value=0)
        
        # Calculate percentages by region
        regional_percentages = regional_dist.div(regional_dist.sum(axis=1), axis=0) * 100
        
        return {
            'regional_counts': regional_dist.to_dict(),
            'regional_percentages': regional_percentages.to_dict(),
            'regions_analyzed': list(regional_dist.index)
        }
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict:
        """Analyze data quality metrics for weapon information."""
        
        total_records = len(df)
        unknown_weapons = len(df[df['weapon_category'] == 'unknown'])
        missing_weapon_data = len(df[df['weapon_raw'].isna() | (df['weapon_raw'] == '')])
        
        return {
            'total_records': total_records,
            'unknown_weapons': unknown_weapons,
            'unknown_weapon_percentage': (unknown_weapons / total_records * 100) if total_records > 0 else 0,
            'missing_weapon_data': missing_weapon_data,
            'missing_data_percentage': (missing_weapon_data / total_records * 100) if total_records > 0 else 0,
            'data_completeness_score': ((total_records - unknown_weapons - missing_weapon_data) / total_records * 100) if total_records > 0 else 0
        }
    
    def _compare_serious_vs_all_crimes(self, all_df: pd.DataFrame, serious_df: pd.DataFrame) -> Dict:
        """Compare weapon patterns between serious crimes and all crimes."""
        
        # Weapon distribution in all crimes
        all_weapon_dist = all_df['weapon_category'].value_counts(normalize=True) * 100
        
        # Weapon distribution in serious crimes
        serious_weapon_dist = serious_df['weapon_category'].value_counts(normalize=True) * 100
        
        # Calculate differences
        comparison_data = []
        for weapon in self.weapon_categories:
            all_pct = all_weapon_dist.get(weapon, 0)
            serious_pct = serious_weapon_dist.get(weapon, 0)
            difference = serious_pct - all_pct
            
            comparison_data.append({
                'weapon_category': weapon,
                'all_crimes_percentage': round(all_pct, 2),
                'serious_crimes_percentage': round(serious_pct, 2),
                'difference': round(difference, 2),
                'over_represented_in_serious': difference > 5,  # 5% threshold
                'under_represented_in_serious': difference < -5
            })
        
        return {
            'comparison_data': comparison_data,
            'all_crimes_total': len(all_df),
            'serious_crimes_total': len(serious_df)
        }
    
    def generate_weapons_summary(self, results: Dict) -> str:
        """Generate a text summary of weapons analysis results."""
        
        if 'error' in results:
            return f"Weapons analysis could not be completed: {results['error']}"
        
        summary_parts = []
        
        # Basic statistics
        summary_parts.append(f"Analyzed {results['total_serious_crimes']} serious crimes out of {results['total_all_crimes']} total records ({results['serious_crime_percentage']:.1f}%)")
        
        # Weapon distribution
        if 'weapon_distribution' in results:
            weapon_dist = results['weapon_distribution']
            most_common = weapon_dist['most_common']
            summary_parts.append(f"Most common weapon category in serious crimes: {most_common}")
        
        # Data quality
        if 'data_quality' in results:
            data_quality = results['data_quality']
            unknown_pct = data_quality['unknown_weapon_percentage']
            summary_parts.append(f"Unknown weapon information: {unknown_pct:.1f}% of serious crimes")
        
        # Temporal trends
        if 'temporal_trends' in results and 'unknown_weapon_trend' in results['temporal_trends']:
            trend_data = results['temporal_trends']['unknown_weapon_trend']
            if trend_data:
                years = sorted(trend_data.keys())
                if len(years) >= 2:
                    start_unknown = trend_data[years[0]]
                    end_unknown = trend_data[years[-1]]
                    trend_direction = "increased" if end_unknown > start_unknown else "decreased"
                    summary_parts.append(f"Unknown weapon percentage {trend_direction} from {start_unknown:.1f}% to {end_unknown:.1f}% over time")
        
        # Ethical note
        summary_parts.append("Note: Analysis is aggregate-only and subject to reporting bias and missing data limitations")
        
        return ". ".join(summary_parts) + "."

if __name__ == "__main__":
    # Test weapons analysis with sample data
    import numpy as np
    
    np.random.seed(42)
    
    # Create sample data with weapon information
    sample_data = pd.DataFrame({
        'title': [
            'Armed Bank Robbery', 'Knife Attack', 'Murder Investigation', 
            'Fraud Case', 'Shooting Incident', 'Assault with Bat'
        ] * 20,
        'description': [
            'Armed with handgun', 'Stabbing with knife', 'Homicide case',
            'Financial fraud', 'Firearm involved', 'Blunt object assault'
        ] * 20,
        'weapon_category': [
            'firearm', 'knife', 'unknown', 'none', 'firearm', 'blunt_object'
        ] * 20,
        'weapon_raw': [
            'Armed with handgun', 'Stabbing with knife', 'Homicide case',
            'Financial fraud', 'Firearm involved', 'Blunt object assault'
        ] * 20,
        'severity_flag': [True, True, True, False, True, True] * 20,
        'publication_year': np.random.choice([2021, 2022, 2023], 120),
        'birth_region': np.random.choice(['West', 'South', 'Northeast'], 120),
        'public_notice_flag': [True] * 120
    })
    
    analyzer = WeaponsAnalyzer()
    results = analyzer.analyze_weapon_patterns(sample_data)
    
    print("Weapons Analysis Results:")
    print(f"Total serious crimes: {results.get('total_serious_crimes', 'N/A')}")
    print(f"Weapon distribution: {results.get('weapon_distribution', {}).get('percentages', 'N/A')}")
    
    summary = analyzer.generate_weapons_summary(results)
    print(f"\nSummary: {summary}")