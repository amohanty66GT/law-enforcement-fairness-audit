"""
Statistical Analysis Agent - Performs chi-square tests and effect-size calculations.
Compares distributions across regions, offense types, and weapon categories.
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
from typing import Dict, List, Optional, Tuple, Any
import warnings

from .base import BaseAgent, AgentMessage, AgentExecutionContext, StatisticalResult, ProcessingError, ValidationResult

class StatisticalAnalysisAgent(BaseAgent):
    """Agent responsible for statistical analysis and hypothesis testing."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("statistical_analysis_agent", config)
        self.confidence_level = self.config.get("confidence_level", 0.95)
        self.alpha = 1 - self.confidence_level
        self.min_sample_size = self.config.get("min_sample_size", 30)
        self.min_expected_frequency = self.config.get("min_expected_frequency", 5)
        
    def execute(self, context: AgentExecutionContext, input_data: Any) -> AgentMessage:
        """Execute statistical analysis on classified data."""
        self.log_execution("starting_statistical_analysis", {"record_count": len(input_data)})
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(input_data)
            
            # Prepare data for analysis
            analysis_df = self._prepare_analysis_data(df)
            
            # Perform various statistical tests
            statistical_results = {}
            
            # Geographic distribution analysis
            if self._has_geographic_data(analysis_df):
                statistical_results["geographic_analysis"] = self._analyze_geographic_distribution(analysis_df)
            
            # Weapon category analysis
            if self._has_weapon_data(analysis_df):
                statistical_results["weapon_analysis"] = self._analyze_weapon_distribution(analysis_df)
            
            # Serious crime analysis
            if self._has_severity_data(analysis_df):
                statistical_results["severity_analysis"] = self._analyze_severity_distribution(analysis_df)
            
            # Cross-tabulation analyses
            statistical_results["cross_tabulation_analysis"] = self._perform_cross_tabulation_analysis(analysis_df)
            
            # Generate summary statistics
            summary_stats = self._generate_summary_statistics(analysis_df, statistical_results)
            
            self.log_execution("statistical_analysis_completed", {
                "analyses_performed": len(statistical_results),
                "significant_results": sum(1 for result in statistical_results.values() 
                                         if isinstance(result, dict) and result.get("significant", False))
            })
            
            return self.create_message(
                message_type="statistical_analysis_results",
                data={
                    "statistical_results": statistical_results,
                    "summary_statistics": summary_stats,
                    "analysis_metadata": {
                        "confidence_level": self.confidence_level,
                        "alpha": self.alpha,
                        "min_sample_size": self.min_sample_size,
                        "records_analyzed": len(analysis_df)
                    }
                },
                metadata={
                    "analysis_time": pd.Timestamp.now().isoformat(),
                    "agent_version": "1.0"
                }
            )
            
        except Exception as e:
            self.log_execution("statistical_analysis_failed", {"error": str(e)})
            raise ProcessingError(self.agent_id, f"Statistical analysis failed: {str(e)}")
    
    def _prepare_analysis_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for statistical analysis."""
        analysis_df = df.copy()
        
        # Extract geographic information
        if 'place_of_birth' in analysis_df.columns:
            analysis_df['state'] = analysis_df['place_of_birth'].str.extract(r', ([A-Z]{2})$')
        
        # Convert date columns
        date_columns = ['publication', 'modified', 'publication_date']
        for col in date_columns:
            if col in analysis_df.columns:
                analysis_df[f'{col}_parsed'] = pd.to_datetime(analysis_df[col], errors='coerce')
                analysis_df[f'{col}_year'] = analysis_df[f'{col}_parsed'].dt.year
        
        # Clean categorical variables
        categorical_columns = ['weapon_category', 'severity_type', 'state']
        for col in categorical_columns:
            if col in analysis_df.columns:
                analysis_df[col] = analysis_df[col].fillna('unknown').astype(str)
        
        return analysis_df
    
    def _has_geographic_data(self, df: pd.DataFrame) -> bool:
        """Check if geographic analysis is possible."""
        return 'state' in df.columns and df['state'].notna().sum() >= self.min_sample_size
    
    def _has_weapon_data(self, df: pd.DataFrame) -> bool:
        """Check if weapon analysis is possible."""
        return 'weapon_category' in df.columns and len(df) >= self.min_sample_size
    
    def _has_severity_data(self, df: pd.DataFrame) -> bool:
        """Check if severity analysis is possible."""
        return 'severity_flag' in df.columns and len(df) >= self.min_sample_size
    
    def _analyze_geographic_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze geographic distribution patterns."""
        results = {"test_type": "geographic_distribution"}
        
        try:
            # Filter valid states
            geo_df = df[df['state'].notna() & (df['state'] != 'unknown')].copy()
            
            if len(geo_df) < self.min_sample_size:
                return {"error": "Insufficient geographic data", "sample_size": len(geo_df)}
            
            # State distribution
            state_counts = geo_df['state'].value_counts()
            
            # Chi-square goodness of fit test (assuming uniform distribution)
            expected_freq = len(geo_df) / len(state_counts)
            
            if expected_freq >= self.min_expected_frequency:
                chi2_stat, p_value = stats.chisquare(state_counts.values)
                
                results.update({
                    "chi_square_statistic": float(chi2_stat),
                    "p_value": float(p_value),
                    "degrees_of_freedom": len(state_counts) - 1,
                    "significant": p_value < self.alpha,
                    "effect_size": self._calculate_effect_size_goodness_of_fit(chi2_stat, len(geo_df)),
                    "interpretation": self._interpret_geographic_test(p_value, state_counts),
                    "state_distribution": state_counts.to_dict()
                })
            else:
                results["error"] = "Expected frequencies too low for chi-square test"
            
        except Exception as e:
            results["error"] = f"Geographic analysis failed: {str(e)}"
        
        return results
    
    def _analyze_weapon_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze weapon category distribution."""
        results = {"test_type": "weapon_distribution"}
        
        try:
            weapon_counts = df['weapon_category'].value_counts()
            
            # Chi-square goodness of fit test
            expected_freq = len(df) / len(weapon_counts)
            
            if expected_freq >= self.min_expected_frequency:
                chi2_stat, p_value = stats.chisquare(weapon_counts.values)
                
                results.update({
                    "chi_square_statistic": float(chi2_stat),
                    "p_value": float(p_value),
                    "degrees_of_freedom": len(weapon_counts) - 1,
                    "significant": p_value < self.alpha,
                    "effect_size": self._calculate_effect_size_goodness_of_fit(chi2_stat, len(df)),
                    "interpretation": self._interpret_weapon_test(p_value, weapon_counts),
                    "weapon_distribution": weapon_counts.to_dict()
                })
            else:
                results["error"] = "Expected frequencies too low for chi-square test"
                
        except Exception as e:
            results["error"] = f"Weapon analysis failed: {str(e)}"
        
        return results
    
    def _analyze_severity_distribution(self, df: pd.DataFrame) -> Dict:
        """Analyze serious crime distribution."""
        results = {"test_type": "severity_distribution"}
        
        try:
            serious_count = df['severity_flag'].sum()
            total_count = len(df)
            non_serious_count = total_count - serious_count
            
            # Binomial test (assuming 50% expected rate)
            expected_rate = 0.5
            p_value = stats.binom_test(serious_count, total_count, expected_rate, alternative='two-sided')
            
            # Effect size (Cohen's h for proportions)
            observed_rate = serious_count / total_count
            effect_size = 2 * (np.arcsin(np.sqrt(observed_rate)) - np.arcsin(np.sqrt(expected_rate)))
            
            results.update({
                "binomial_test_p_value": float(p_value),
                "observed_serious_rate": float(observed_rate),
                "expected_serious_rate": expected_rate,
                "serious_count": int(serious_count),
                "total_count": int(total_count),
                "significant": p_value < self.alpha,
                "effect_size": float(effect_size),
                "interpretation": self._interpret_severity_test(p_value, observed_rate, expected_rate)
            })
            
        except Exception as e:
            results["error"] = f"Severity analysis failed: {str(e)}"
        
        return results
    
    def _perform_cross_tabulation_analysis(self, df: pd.DataFrame) -> Dict:
        """Perform cross-tabulation analyses between variables."""
        results = {"test_type": "cross_tabulation"}
        cross_tab_results = {}
        
        # Define variable pairs for analysis
        variable_pairs = [
            ('weapon_category', 'severity_flag'),
            ('state', 'weapon_category'),
            ('state', 'severity_flag')
        ]
        
        for var1, var2 in variable_pairs:
            if var1 in df.columns and var2 in df.columns:
                try:
                    cross_tab_result = self._analyze_variable_association(df, var1, var2)
                    cross_tab_results[f"{var1}_vs_{var2}"] = cross_tab_result
                except Exception as e:
                    cross_tab_results[f"{var1}_vs_{var2}"] = {"error": str(e)}
        
        results["associations"] = cross_tab_results
        return results
    
    def _analyze_variable_association(self, df: pd.DataFrame, var1: str, var2: str) -> Dict:
        """Analyze association between two categorical variables."""
        # Create contingency table
        contingency_table = pd.crosstab(df[var1], df[var2])
        
        # Check minimum expected frequencies
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        if (expected < self.min_expected_frequency).any():
            return {
                "error": "Expected frequencies too low for chi-square test",
                "min_expected": float(expected.min())
            }
        
        # Calculate effect size (Cramér's V)
        n = contingency_table.sum().sum()
        cramers_v_value = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
        
        return {
            "chi_square_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "significant": p_value < self.alpha,
            "cramers_v": float(cramers_v_value),
            "effect_size_interpretation": self._interpret_cramers_v(cramers_v_value),
            "contingency_table": contingency_table.to_dict(),
            "interpretation": self._interpret_association_test(var1, var2, p_value, cramers_v_value)
        }
    
    def _calculate_effect_size_goodness_of_fit(self, chi2_stat: float, n: int) -> float:
        """Calculate effect size for goodness of fit test (Cramér's V)."""
        return np.sqrt(chi2_stat / n)
    
    def _interpret_geographic_test(self, p_value: float, state_counts: pd.Series) -> str:
        """Interpret geographic distribution test results."""
        if p_value < self.alpha:
            most_common = state_counts.index[0]
            least_common = state_counts.index[-1]
            return (f"Significant geographic bias detected (p={p_value:.4f}). "
                   f"Most common state: {most_common} ({state_counts[most_common]} cases), "
                   f"least common: {least_common} ({state_counts[least_common]} cases).")
        else:
            return f"No significant geographic bias detected (p={p_value:.4f}). Distribution appears uniform."
    
    def _interpret_weapon_test(self, p_value: float, weapon_counts: pd.Series) -> str:
        """Interpret weapon distribution test results."""
        if p_value < self.alpha:
            most_common = weapon_counts.index[0]
            return (f"Significant weapon distribution bias detected (p={p_value:.4f}). "
                   f"Most common weapon category: {most_common} ({weapon_counts[most_common]} cases).")
        else:
            return f"No significant weapon distribution bias detected (p={p_value:.4f})."
    
    def _interpret_severity_test(self, p_value: float, observed_rate: float, expected_rate: float) -> str:
        """Interpret severity distribution test results."""
        if p_value < self.alpha:
            direction = "higher" if observed_rate > expected_rate else "lower"
            return (f"Serious crime rate ({observed_rate:.1%}) is significantly {direction} "
                   f"than expected ({expected_rate:.1%}), p={p_value:.4f}.")
        else:
            return f"Serious crime rate ({observed_rate:.1%}) not significantly different from expected ({expected_rate:.1%})."
    
    def _interpret_association_test(self, var1: str, var2: str, p_value: float, cramers_v: float) -> str:
        """Interpret association test results."""
        if p_value < self.alpha:
            strength = self._interpret_cramers_v(cramers_v)
            return (f"Significant association between {var1} and {var2} (p={p_value:.4f}). "
                   f"Effect size: {strength} (Cramér's V = {cramers_v:.3f}).")
        else:
            return f"No significant association between {var1} and {var2} (p={p_value:.4f})."
    
    def _interpret_cramers_v(self, cramers_v: float) -> str:
        """Interpret Cramér's V effect size."""
        if cramers_v < 0.1:
            return "negligible"
        elif cramers_v < 0.3:
            return "small"
        elif cramers_v < 0.5:
            return "medium"
        else:
            return "large"
    
    def _generate_summary_statistics(self, df: pd.DataFrame, statistical_results: Dict) -> Dict:
        """Generate summary statistics for the dataset."""
        summary = {
            "dataset_summary": {
                "total_records": len(df),
                "date_range": self._get_date_range(df),
                "geographic_coverage": self._get_geographic_summary(df),
                "weapon_summary": self._get_weapon_summary(df),
                "severity_summary": self._get_severity_summary(df)
            },
            "statistical_summary": {
                "tests_performed": len(statistical_results),
                "significant_results": sum(1 for result in statistical_results.values() 
                                         if isinstance(result, dict) and result.get("significant", False)),
                "confidence_level": self.confidence_level
            }
        }
        
        return summary
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict:
        """Get date range information."""
        date_cols = [col for col in df.columns if 'date' in col.lower() or col in ['publication', 'modified']]
        
        for col in date_cols:
            try:
                dates = pd.to_datetime(df[col], errors='coerce').dropna()
                if len(dates) > 0:
                    return {
                        "start_date": dates.min().isoformat(),
                        "end_date": dates.max().isoformat(),
                        "span_days": (dates.max() - dates.min()).days
                    }
            except:
                continue
        
        return {"error": "No valid date information found"}
    
    def _get_geographic_summary(self, df: pd.DataFrame) -> Dict:
        """Get geographic distribution summary."""
        if 'state' in df.columns:
            state_counts = df['state'].value_counts()
            return {
                "unique_states": len(state_counts),
                "most_common_state": state_counts.index[0] if len(state_counts) > 0 else None,
                "geographic_coverage": state_counts.to_dict()
            }
        return {"error": "No geographic data available"}
    
    def _get_weapon_summary(self, df: pd.DataFrame) -> Dict:
        """Get weapon category summary."""
        if 'weapon_category' in df.columns:
            weapon_counts = df['weapon_category'].value_counts()
            return {
                "weapon_categories": len(weapon_counts),
                "most_common_weapon": weapon_counts.index[0] if len(weapon_counts) > 0 else None,
                "weapon_distribution": weapon_counts.to_dict()
            }
        return {"error": "No weapon data available"}
    
    def _get_severity_summary(self, df: pd.DataFrame) -> Dict:
        """Get severity classification summary."""
        if 'severity_flag' in df.columns:
            serious_count = df['severity_flag'].sum()
            return {
                "total_records": len(df),
                "serious_crimes": int(serious_count),
                "serious_crime_rate": float(serious_count / len(df)) if len(df) > 0 else 0.0
            }
        return {"error": "No severity data available"}
    
    def validate_input(self, input_data: Any) -> ValidationResult:
        """Validate input data for statistical analysis."""
        errors = []
        warnings = []
        
        if not isinstance(input_data, list):
            errors.append("Input data must be a list of records")
        elif len(input_data) < self.min_sample_size:
            errors.append(f"Insufficient sample size: {len(input_data)} < {self.min_sample_size}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )