"""
Statistical bias detection and fairness metrics.
Implements chi-square tests, representation analysis, and temporal trend detection.
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, pearsonr
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasAnalyzer:
    """Performs statistical analysis to detect bias patterns."""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
        
    def analyze_geographic_bias(self, df: pd.DataFrame) -> Dict:
        """
        Analyze geographic representation bias.
        
        Args:
            df: DataFrame with geographic and population features
            
        Returns:
            Dictionary with bias analysis results
        """
        results = {
            'method': 'geographic_representation_analysis',
            'confidence_level': self.confidence_level
        }
        
        # Filter out unknown states
        geo_df = df[df['birth_state'] != 'UNKNOWN'].copy()
        
        if len(geo_df) < 50:  # Minimum sample size
            results['error'] = 'Insufficient data for geographic analysis'
            return results
        
        # Calculate representation ratios
        state_counts = geo_df['birth_state'].value_counts()
        state_populations = geo_df.groupby('birth_state')['birth_state_population'].first()
        
        # Expected vs observed representation
        total_cases = len(geo_df)
        total_population = state_populations.sum()
        
        representation_data = []
        for state in state_counts.index:
            observed = state_counts[state]
            population = state_populations.get(state, 0)
            
            if population > 0:
                expected = (population / total_population) * total_cases
                ratio = observed / expected if expected > 0 else 0
                
                representation_data.append({
                    'state': state,
                    'observed_cases': observed,
                    'population_millions': population,
                    'expected_cases': expected,
                    'representation_ratio': ratio,
                    'over_represented': ratio > 1.2,  # 20% threshold
                    'under_represented': ratio < 0.8
                })
        
        representation_df = pd.DataFrame(representation_data)
        
        # Chi-square test for independence
        if len(representation_df) > 1:
            observed_counts = representation_df['observed_cases'].values
            expected_counts = representation_df['expected_cases'].values
            
            # Filter out very small expected counts
            valid_mask = expected_counts >= 5
            if valid_mask.sum() > 1:
                chi2_stat, p_value = stats.chisquare(
                    observed_counts[valid_mask], 
                    expected_counts[valid_mask]
                )
                
                # Add some debugging info
                logger.info(f"Geographic bias test: chi2={chi2_stat:.3f}, p={p_value:.6f}, states={valid_mask.sum()}")
                
                results.update({
                    'chi_square_statistic': chi2_stat,
                    'p_value': p_value,
                    'significant_bias': p_value < self.alpha,
                    'interpretation': self._interpret_geographic_bias(p_value, representation_df)
                })
        
        results['representation_analysis'] = representation_df.to_dict('records')
        results['summary_stats'] = {
            'states_analyzed': len(representation_df),
            'over_represented_states': len(representation_df[representation_df['over_represented']]),
            'under_represented_states': len(representation_df[representation_df['under_represented']]),
            'mean_representation_ratio': representation_df['representation_ratio'].mean(),
            'std_representation_ratio': representation_df['representation_ratio'].std()
        }
        
        return results
    
    def analyze_categorical_bias(self, df: pd.DataFrame, baseline_df: pd.DataFrame = None) -> Dict:
        """
        Analyze bias in crime category representation.
        
        Args:
            df: Wanted persons DataFrame
            baseline_df: Crime statistics DataFrame for comparison
            
        Returns:
            Dictionary with categorical bias analysis
        """
        results = {
            'method': 'categorical_representation_analysis',
            'confidence_level': self.confidence_level
        }
        
        # Analyze wanted list category distribution
        category_counts = df['crime_family'].value_counts()
        category_proportions = category_counts / len(df)
        
        results['wanted_distribution'] = {
            'counts': category_counts.to_dict(),
            'proportions': category_proportions.to_dict()
        }
        
        # Compare with baseline if available
        if baseline_df is not None:
            baseline_counts = baseline_df.groupby('crime_family')['count'].sum()
            baseline_proportions = baseline_counts / baseline_counts.sum()
            
            results['baseline_distribution'] = {
                'counts': baseline_counts.to_dict(),
                'proportions': baseline_proportions.to_dict()
            }
            
            # Calculate representation ratios
            comparison_data = []
            for category in category_proportions.index:
                wanted_prop = category_proportions[category]
                baseline_prop = baseline_proportions.get(category, 0)
                
                if baseline_prop > 0:
                    ratio = wanted_prop / baseline_prop
                    comparison_data.append({
                        'category': category,
                        'wanted_proportion': wanted_prop,
                        'baseline_proportion': baseline_prop,
                        'representation_ratio': ratio,
                        'over_represented': ratio > 1.5,
                        'under_represented': ratio < 0.5
                    })
            
            comparison_df = pd.DataFrame(comparison_data)
            results['category_comparison'] = comparison_df.to_dict('records')
            
            # Statistical test
            if len(comparison_df) > 1:
                # Chi-square test for category independence
                contingency_table = pd.crosstab(
                    df['crime_family'], 
                    ['wanted'] * len(df)
                )
                
                if baseline_df is not None and len(baseline_df) > 0:
                    baseline_table = baseline_df.groupby('crime_family')['count'].sum()
                    
                    # Align categories
                    common_categories = set(contingency_table.index) & set(baseline_table.index)
                    if len(common_categories) > 1:
                        wanted_counts = [contingency_table.loc[cat, 'wanted'] for cat in common_categories]
                        baseline_counts = [baseline_table.loc[cat] for cat in common_categories]
                        
                        chi2_stat, p_value = stats.chisquare(wanted_counts, baseline_counts)
                        
                        results.update({
                            'chi_square_statistic': chi2_stat,
                            'p_value': p_value,
                            'significant_bias': p_value < self.alpha
                        })
        
        return results
    
    def analyze_temporal_trends(self, df: pd.DataFrame) -> Dict:
        """
        Analyze temporal trends in representation patterns.
        
        Args:
            df: DataFrame with temporal features
            
        Returns:
            Dictionary with temporal trend analysis
        """
        results = {
            'method': 'temporal_trend_analysis',
            'confidence_level': self.confidence_level
        }
        
        # Yearly trends by category
        yearly_trends = df.groupby(['publication_year', 'crime_family']).size().unstack(fill_value=0)
        
        results['yearly_category_counts'] = yearly_trends.to_dict()
        
        # Calculate trend statistics for each category
        trend_analysis = {}
        for category in yearly_trends.columns:
            years = yearly_trends.index.values
            counts = yearly_trends[category].values
            
            if len(years) > 2 and counts.sum() > 0:
                # Linear trend analysis
                correlation, p_value = pearsonr(years, counts)
                
                # Calculate percentage change
                if counts[0] > 0:
                    pct_change = ((counts[-1] - counts[0]) / counts[0]) * 100
                else:
                    pct_change = 0
                
                trend_analysis[category] = {
                    'correlation_with_time': correlation,
                    'trend_p_value': p_value,
                    'significant_trend': p_value < self.alpha,
                    'trend_direction': 'increasing' if correlation > 0 else 'decreasing',
                    'percent_change': pct_change,
                    'total_cases': counts.sum()
                }
        
        results['trend_analysis'] = trend_analysis
        
        # Case persistence analysis
        persistence_analysis = self._analyze_case_persistence(df)
        results['persistence_analysis'] = persistence_analysis
        
        return results
    
    def analyze_case_persistence(self, df: pd.DataFrame) -> Dict:
        """
        Analyze how long cases persist on wanted lists by category.
        
        Args:
            df: DataFrame with case age and category data
            
        Returns:
            Dictionary with persistence analysis
        """
        return self._analyze_case_persistence(df)
    
    def _analyze_case_persistence(self, df: pd.DataFrame) -> Dict:
        """Internal method for case persistence analysis."""
        
        persistence_data = df.groupby('crime_family')['case_age_days'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
        
        # Statistical tests for persistence differences
        categories = df['crime_family'].unique()
        if len(categories) > 1:
            # ANOVA test for differences in persistence across categories
            category_ages = [df[df['crime_family'] == cat]['case_age_days'].dropna() 
                           for cat in categories if len(df[df['crime_family'] == cat]) > 5]
            
            if len(category_ages) > 1:
                f_stat, p_value = stats.f_oneway(*category_ages)
                
                return {
                    'persistence_by_category': persistence_data.to_dict(),
                    'anova_f_statistic': f_stat,
                    'anova_p_value': p_value,
                    'significant_differences': p_value < self.alpha,
                    'interpretation': self._interpret_persistence_differences(p_value, persistence_data)
                }
        
        return {
            'persistence_by_category': persistence_data.to_dict(),
            'note': 'Insufficient data for statistical comparison'
        }
    
    def _interpret_geographic_bias(self, p_value: float, representation_df: pd.DataFrame) -> str:
        """Interpret geographic bias analysis results."""
        
        if p_value < self.alpha:
            over_rep = representation_df[representation_df['over_represented']]
            under_rep = representation_df[representation_df['under_represented']]
            
            interpretation = f"Significant geographic bias detected (p={p_value:.4f}). "
            
            if len(over_rep) > 0:
                interpretation += f"Over-represented states: {', '.join(over_rep['state'].tolist())}. "
            
            if len(under_rep) > 0:
                interpretation += f"Under-represented states: {', '.join(under_rep['state'].tolist())}."
                
            return interpretation
        else:
            return f"No significant geographic bias detected (p={p_value:.4f}). Representation appears proportional to population."
    
    def _interpret_persistence_differences(self, p_value: float, persistence_data: pd.DataFrame) -> str:
        """Interpret case persistence analysis results."""
        
        if p_value < self.alpha:
            # Find categories with longest and shortest persistence
            longest = persistence_data['mean'].idxmax()
            shortest = persistence_data['mean'].idxmin()
            
            return (f"Significant differences in case persistence detected (p={p_value:.4f}). "
                   f"'{longest}' cases persist longest (avg: {persistence_data.loc[longest, 'mean']:.0f} days), "
                   f"while '{shortest}' cases are resolved fastest (avg: {persistence_data.loc[shortest, 'mean']:.0f} days).")
        else:
            return f"No significant differences in case persistence across categories (p={p_value:.4f})."

if __name__ == "__main__":
    # Test bias analysis with sample data
    sample_data = pd.DataFrame({
        'birth_state': ['CA', 'TX', 'CA', 'NY', 'FL'] * 20,
        'birth_state_population': [39.5, 29.1, 39.5, 19.8, 21.5] * 20,
        'crime_family': ['Violent', 'White Collar', 'Drug Related', 'Cyber Crime', 'Violent'] * 20,
        'publication_year': [2021, 2022, 2023, 2022, 2023] * 20,
        'case_age_days': np.random.normal(365, 200, 100)
    })
    
    analyzer = BiasAnalyzer()
    
    # Test geographic bias
    geo_results = analyzer.analyze_geographic_bias(sample_data)
    print("Geographic Bias Analysis:")
    print(f"Significant bias: {geo_results.get('significant_bias', 'N/A')}")
    
    # Test categorical bias
    cat_results = analyzer.analyze_categorical_bias(sample_data)
    print("\nCategorical Distribution:")
    print(cat_results['wanted_distribution']['proportions'])
    
    # Test temporal trends
    temporal_results = analyzer.analyze_temporal_trends(sample_data)
    print("\nTemporal Trends:")
    print(f"Categories analyzed: {len(temporal_results['trend_analysis'])}")